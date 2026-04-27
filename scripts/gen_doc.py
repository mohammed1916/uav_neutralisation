import json
import csv
from docx import Document
import math
import os
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Directories: scripts live in `scripts/`, runtime outputs go to `outputs/`, documents to `docs/`.
# `BASE_DIR` is the directory containing this script (scripts/ after reorganization).
BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'outputs'))
DOCS_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'docs'))
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

# Parameters inferred from the schematic image (labels on the figure)
# Charge chamber: 1.0 L accumulator
V0 = 1.0e-3  # m^3
# Working pressure shown on accumulator: 10 bar (gauge) — matches EDD nominal WP
P0_gauge_bar = 10.0  # bar (gauge)
BAR = 1.0e5  # Pa per bar
P0_abs = (P0_gauge_bar + 1.0) * BAR  # convert to absolute Pa  (11 bar abs)
Pf = 1.0e5  # atmospheric pressure (Pa)

# Barrel geometry from figure: 52 mm ID, 700 mm length
barrel_id = 0.052  # m
barrel_length = 0.700  # m
barrel_area = math.pi * (barrel_id / 2.0) ** 2


def isothermal_work(P0, V, Pf=Pf):
    """Return theoretical isothermal work available from expansion from P0 to Pf."""
    return P0 * V * math.log(P0 / Pf)


def required_P0_for_work(W_target, V, Pf=Pf, Pmin=None, Pmax=None):
    """Find P0 (absolute Pa) such that isothermal_work(P0,V) = W_target using bisection."""
    if Pmin is None:
        Pmin = Pf * 1.000001
    if Pmax is None:
        Pmax = 300 * BAR

    def f(P):
        return isothermal_work(P, V, Pf) - W_target

    if f(Pmin) >= 0:
        return Pmin
    if f(Pmax) < 0:
        raise ValueError("Pmax too low to reach target work")

    for _ in range(100):
        mid = 0.5 * (Pmin + Pmax)
        if f(mid) > 0:
            Pmax = mid
        else:
            Pmin = mid
    return 0.5 * (Pmin + Pmax)


def insert_omml_equation(paragraph, text):
    """Insert a simple OMML math run into a python-docx paragraph.
    This creates a minimal <m:oMath><m:r><m:t>text</m:t></m:r></m:oMath> node.
    """
    # create math element
    oMath = OxmlElement('m:oMath')
    r = OxmlElement('m:r')
    t = OxmlElement('m:t')
    t.text = text
    r.append(t)
    oMath.append(r)
    paragraph._p.append(oMath)


def read_measured_csv(path):
    vals = {}
    if not os.path.exists(path):
        return vals
    try:
        with open(path, 'r', newline='') as f:
            rdr = csv.reader(f)
            hdr = next(rdr)
            for row in rdr:
                if not row:
                    continue
                key = row[0].strip()
                try:
                    vals[key] = float(row[1])
                except Exception:
                    vals[key] = row[1]
    except Exception:
        pass
    return vals


# Compute theoretical values (previously collected into an early doc)
W_ideal = isothermal_work(P0_abs, V0)
masses = [0.2, 0.5, 1.0]  # kg
efficiencies = [0.25, 0.5, 0.75]



# ---- Additional structural and thrust calculations ----
# Structural and material parameters (previously collected into a supplementary doc)
mat_yield = 276e6  # Pa (approx for 6061-T6)
mat_ultimate = 310e6  # Pa
safety_factor = 3.0
allowable = mat_yield / safety_factor

# Barrel thin-wall hoop stress: sigma_hoop = P * r / t  -> t = P * r / sigma_allowable
r_barrel = barrel_id / 2.0
t_req_hoop = P0_abs * r_barrel / allowable
t_req_axial = P0_abs * r_barrel / (2.0 * allowable)

# Compare to common wall thicknesses (kept for table generation)
common_thicknesses = [0.002, 0.003, 0.005, 0.008]


# ---- Transient 1D launcher simulation (compressible orifice + projectile motion) ----


def simulate_transient(m_payload=1.0,
                       Vc=V0,
                       P0=P0_abs,
                       A_bore=barrel_area,
                       L=barrel_length,
                       orifice_d=0.012,
                       C_d=0.8,
                       friction_coeff=0.10,
                       T=293.15,
                       gamma=1.3,
                       dt=1e-4,
                       t_max=0.2):
    """Simulate discharge and projectile motion until exit or t_max.
    Returns summary dict and time histories.
    """
    R_u = 8.31446261815324
    M_co2 = 0.04401  # kg/mol
    R_spec = R_u / M_co2

    # --- Real-gas compressibility using Redlich-Kwong EOS ---
    Tc = 304.1282  # K
    Pc_RK = 7.3773e6  # Pa
    a_RK = 0.42748 * R_u * R_u * Tc * Tc / Pc_RK
    b_RK = 0.08664 * R_u * Tc / Pc_RK

    def compressibility_Z_RK(P, T):
        # solve cubic for Z using RK in terms of Z; use simple Newton on molar volume
        # initial guess ideal Z=1
        Z = 1.0
        for _ in range(60):
            Vm = Z * R_u * T / P
            # f(Vm) = P - R*T/(Vm - b) + a/(Vm*(Vm + b)*math.sqrt(T))
            f = P - R_u * T / (Vm - b_RK) + a_RK / \
                (Vm * (Vm + b_RK) * math.sqrt(T))
            # df/dVm (approx)
            df = (R_u * T) / ((Vm - b_RK) ** 2) - a_RK * \
                ((2*Vm + b_RK)) / ((Vm * (Vm + b_RK))**2 * math.sqrt(T))
            if df == 0:
                break
            dVm = -f / df
            Vm += dVm
            if Vm <= 0:
                Vm = 1e-6
            Z_new = P * Vm / (R_u * T)
            if abs(Z_new - Z) < 1e-6:
                Z = Z_new
                break
            Z = Z_new
        return max(0.1, min(10.0, Z))

    # compute initial compressibilities and densities
    Zc = compressibility_Z_RK(P0, T)
    rho_c0 = P0 * M_co2 / (Zc * R_u * T)
    m_c = rho_c0 * Vc
    # small initial barrel volume (clearance) to avoid zero
    Vb = 1e-6
    P_atm = Pf
    Zb0 = compressibility_Z_RK(P_atm, T)
    rho_b0 = P_atm * M_co2 / (Zb0 * R_u * T)
    m_b = rho_b0 * Vb

    # geometry
    r_or = orifice_d / 2.0
    A_or = math.pi * r_or * r_or

    x = 0.0
    v = 0.0
    t = 0.0

    times = []
    xs = []
    vs = []
    Pcs = []
    Pbs = []
    mdots = []

    def critical_pratio(gamma):
        return (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))

    pr_crit = critical_pratio(gamma)

    while t < t_max and x < L:
        Vb = A_bore * x + 1e-6
        Zc = compressibility_Z_RK(max(P_atm, P0 * 1e-12), T)
        Pc = (m_c / Vc) * R_u * T / M_co2 * (1.0 / Zc) if Vc > 0 else P_atm
        Zb = compressibility_Z_RK(max(P_atm, P0 * 1e-12), T)
        Pb = (m_b / Vb) * R_u * T / M_co2 * (1.0 / Zb)

        # compute mass flow from chamber to barrel
        p_ratio = Pb / Pc if Pc > 0 else 1.0
        if p_ratio <= pr_crit:
            # choked flow
            factor = (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) /
                                               (2.0 * (gamma - 1.0)))
            mdot = C_d * A_or * Pc / \
                math.sqrt(R_spec * T) * math.sqrt(gamma) * factor
        else:
            # unchoked isentropic mass flow formula (from compressible orifice relations)
            term = (2.0 * gamma / (gamma - 1.0)) * ((p_ratio) **
                                                    (2.0/gamma) - (p_ratio) ** ((gamma+1.0)/gamma))
            if term < 0:
                mdot = 0.0
            else:
                mdot = C_d * A_or * Pc / \
                    math.sqrt(R_spec * T) * math.sqrt(term)

        # limit mdot to available mass in chamber
        mdot = min(mdot, m_c / dt)

        # update masses
        m_c -= mdot * dt
        m_b += mdot * dt

        # pressures update (use RK compressibility for chamber and barrel)
        Zc = compressibility_Z_RK(
            max(P0 * 1e-12, (m_c > 0 and (m_c*R_u*T/(M_co2*(Vc))) or P_atm)), T)
        Pc = (m_c / Vc) * R_u * T / M_co2 * (1.0 / Zc)
        Vb = A_bore * x + 1e-6
        Zb = compressibility_Z_RK(
            max(Pb if 'Pb' in locals() else P_atm, P_atm), T)
        Pb = (m_b / Vb) * R_u * T / M_co2 * (1.0 / Zb)

        # force on projectile
        F_friction = friction_coeff * (Pc * A_bore)
        F_net = max(0.0, (Pb - P_atm) * A_bore - F_friction)

        # integrate projectile motion
        a = F_net / m_payload
        v += a * dt
        x += v * dt

        times.append(t)
        xs.append(x)
        vs.append(v)
        Pcs.append(Pc)
        Pbs.append(Pb)
        mdots.append(mdot)

        t += dt

        # if chamber empty or pressure close to atm, break
        if Pc <= P_atm * 1.01:
            # allow some residual movement then stop
            if x >= L or v < 0.001:
                break

    # summaries
    impulse = m_payload * vs[-1]
    muzzle_v = vs[-1]
    peak_F = max([(Pbs[i]-P_atm)*A_bore for i in range(len(Pbs))]
                 ) if Pbs else 0.0
    avg_F = impulse / t if t > 0 else 0.0

    return {
        'time': times,
        'x': xs,
        'v': vs,
        'Pc': Pcs,
        'Pb': Pbs,
        'mdot': mdots,
        'impulse': impulse,
        'muzzle_v': muzzle_v,
        'peak_F': peak_F,
        'avg_F': avg_F,
        't_end': t,
    }


# Run a default transient simulation and write results
sim = simulate_transient(m_payload=1.0, orifice_d=0.012, C_d=0.8)

# Endcap bolt shear check values (kept for potential inclusion in final doc)
F_axial = P0_abs * math.pi * (r_barrel ** 2)
bolt_sizes = {'M6': 20e-6, 'M8': 36.6e-6, 'M10': 58e-6}
shear_strength = 240e6  # Pa (conservative shear capacity)
bolt_check = {}
for name, A_bolt in bolt_sizes.items():
    cap = A_bolt * shear_strength
    n_needed = math.ceil(F_axial / cap)
    bolt_check[name] = {'cap_N': cap, 'bolts_needed': n_needed}

out_path3 = None

# ---- Parametric sweep and detailed flange checks ----


def flange_bolt_check(F_axial, n_bolts=6, pcd=0.08, bolt_dia=0.008, mat_shear=240e6):
    # simple check: dividing axial into n_bolts shear
    A_bolt = math.pi * (bolt_dia/2.0)**2
    cap_per_bolt = A_bolt * mat_shear
    bolts_needed = math.ceil(F_axial / cap_per_bolt)
    return {'n_bolts': n_bolts, 'cap_per_bolt_N': cap_per_bolt, 'bolts_needed': bolts_needed}


def run_parametric_sweep():
    orifice_ds = [0.006, 0.008, 0.010, 0.012, 0.015, 0.018]
    Vcs = [0.5e-3, 0.8e-3, 1.0e-3, 1.2e-3]
    Cds = [0.6, 0.7, 0.8]
    rows = []
    for d in orifice_ds:
        for Vc_test in Vcs:
            for Cd in Cds:
                simr = simulate_transient(
                    m_payload=1.0, Vc=Vc_test, orifice_d=d, C_d=Cd)
                rows.append({
                    'orifice_d_m': d,
                    'Vc_m3': Vc_test,
                    'Cd': Cd,
                    'muzzle_v': simr['muzzle_v'],
                    'impulse': simr['impulse'],
                    't_end_s': simr['t_end'],
                    'peak_F': simr['peak_F']
                })
    csv_path = os.path.join(OUTPUT_DIR, 'parametric_sweep.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path = os.path.join(OUTPUT_DIR, 'parametric_sweep_summary.json')
    with open(json_path, 'w') as jf:
        json.dump(rows, jf, indent=2)

    return csv_path, json_path


csv_path, json_path = run_parametric_sweep()

# write a small verification summary file
summary = {
    'W_ideal_J': W_ideal,
    'P0_abs_Pa': P0_abs,
    'barrel_area_m2': barrel_area,
    'transient_report': out_path3,
    'structural_report': None,
    'parametric_csv': csv_path,
    'parametric_json': json_path
}
summary_path = os.path.join(OUTPUT_DIR, 'analysis_summary.json')
with open(summary_path, 'w') as sf:
    json.dump(summary, sf, indent=2)

summary_path

# ---- Generate plots from parametric sweep and final flange checks ----
try:
    import matplotlib.pyplot as plt
    with open(json_path, 'r') as jf:
        param = json.load(jf)

    orifices = sorted(list(set([round(p['orifice_d_m'], 6) for p in param])))
    Vcs_list = sorted(list(set([p['Vc_m3'] for p in param])))
    Cds_list = sorted(list(set([p['Cd'] for p in param])))

    plot_files = []
    for Vc_plot in Vcs_list:
        plt.figure()
        for Cd_plot in Cds_list:
            xs = []
            ys = []
            for o in orifices:
                match = [p for p in param if abs(p['orifice_d_m']-o) < 1e-9 and abs(
                    p['Vc_m3']-Vc_plot) < 1e-12 and abs(p['Cd']-Cd_plot) < 1e-12]
                if match:
                    xs.append(o*1e3)
                    ys.append(match[0]['muzzle_v'])
            if xs:
                plt.plot(xs, ys, marker='o', label=f'Cd={Cd_plot}')
        plt.xlabel('Orifice diameter (mm)')
        plt.ylabel('Muzzle velocity (m/s)')
        plt.title(f'Muzzle velocity vs orifice (Vc={Vc_plot*1e3:.1f} mL)')
        plt.legend()
        plt.grid(True)
        fp = os.path.join(
            OUTPUT_DIR, f'vel_vs_orifice_Vc_{int(Vc_plot*1e6)}uL.png')
        plt.savefig(fp)
        plt.close()
        plot_files.append(fp)

    # Peak force plot for Vc=1.0L
    plt.figure()
    for Cd_plot in Cds_list:
        xs = []
        ys = []
        for o in orifices:
            match = [p for p in param if abs(p['orifice_d_m']-o) < 1e-9 and abs(
                p['Vc_m3']-1.0e-3) < 1e-12 and abs(p['Cd']-Cd_plot) < 1e-12]
            if match:
                xs.append(o*1e3)
                ys.append(match[0]['peak_F'])
        if xs:
            plt.plot(xs, ys, marker='x', label=f'Cd={Cd_plot}')
    plt.xlabel('Orifice diameter (mm)')
    plt.ylabel('Peak Force (N)')
    plt.title('Peak Force vs Orifice (Vc=1.0 L)')
    plt.legend()
    plt.grid(True)
    fp2 = os.path.join(OUTPUT_DIR, 'peakF_vs_orifice_Vc_1000uL.png')
    plt.savefig(fp2)
    plt.close()
    plot_files.append(fp2)

    # Impulse plot example
    plt.figure()
    for Cd_plot in Cds_list:
        xs = []
        ys = []
        for o in orifices:
            match = [p for p in param if abs(p['orifice_d_m']-o) < 1e-9 and abs(
                p['Vc_m3']-1.0e-3) < 1e-12 and abs(p['Cd']-Cd_plot) < 1e-12]
            if match:
                xs.append(o*1e3)
                ys.append(match[0]['impulse'])
        if xs:
            plt.plot(xs, ys, marker='s', label=f'Cd={Cd_plot}')
    plt.xlabel('Orifice diameter (mm)')
    plt.ylabel('Impulse (N·s)')
    plt.title('Impulse vs Orifice (Vc=1.0 L)')
    plt.legend()
    plt.grid(True)
    fp3 = os.path.join(OUTPUT_DIR, 'impulse_vs_orifice_Vc_1000uL.png')
    plt.savefig(fp3)
    plt.close()
    plot_files.append(fp3)
except Exception:
    plot_files = []

# Detailed flange/bolt checks (assumed geometry)
flange_assumptions = {
    'n_bolts': 6,
    'pcd_m': 0.08,
    'bolt_dia_m': 0.008,
    'bolt_material_shear': 240e6
}
with open(json_path, 'r') as jf:
    param = json.load(jf)
worst = max(param, key=lambda p: p['peak_F'])
worst_peak = worst['peak_F']
flange_result = flange_bolt_check(worst_peak, n_bolts=flange_assumptions['n_bolts'], pcd=flange_assumptions[
                                  'pcd_m'], bolt_dia=flange_assumptions['bolt_dia_m'], mat_shear=flange_assumptions['bolt_material_shear'])
flange_summary_path = os.path.join(OUTPUT_DIR, 'flange_check.json')
with open(flange_summary_path, 'w') as ff:
    json.dump({'assumptions': flange_assumptions, 'worst_peak_F_N': worst_peak,
              'flange_result': flange_result, 'worst_case': worst}, ff, indent=2)

# Final summary doc
final_doc_path = None

# ---- Now assemble the single comprehensive document (after plots & checks exist) ----
try:
    complete_doc = Document()
    complete_doc.add_heading('Pneumatic Launcher — Complete Analysis', 0)

    # Inputs
    complete_doc.add_heading('Input Parameters', level=1)
    complete_doc.add_paragraph(f'Charge chamber volume: {V0*1e3:.1f} mL')
    complete_doc.add_paragraph(
        f'Working pressure (gauge): {P0_gauge_bar:.1f} bar')
    complete_doc.add_paragraph(
        f'Barrel ID: {barrel_id*1000:.0f} mm; Length: {barrel_length*1000:.0f} mm')

    # Theoretical
    complete_doc.add_heading('Theoretical Energy Estimates', level=1)
    complete_doc.add_paragraph(f'Ideal isothermal work: {W_ideal:.1f} J')
    p_thermo = complete_doc.add_paragraph('Isothermal formula: ')
    insert_omml_equation(p_thermo, 'W = P_0 V_0 ln(P_0 / P_f)')

    # Representative scenarios (presented as a concise table to avoid stray numbering)
    complete_doc.add_heading('Representative Payload Scenarios', level=1)
    scen_table = complete_doc.add_table(rows=1, cols=4)
    hdr = scen_table.rows[0].cells
    hdr[0].text = 'Mass (kg)'
    hdr[1].text = 'Efficiency (%)'
    hdr[2].text = 'Muzzle velocity (m/s)'
    hdr[3].text = 'Energy (J)'
    for m in masses:
        v_ideal = math.sqrt(2.0 * W_ideal / m)
        for eff in efficiencies:
            W_eff = W_ideal * eff
            v_eff = math.sqrt(2.0 * W_eff / m)
            r = scen_table.add_row().cells
            r[0].text = f'{m:.2f}'
            r[1].text = f'{eff*100:.0f}'
            r[2].text = f'{v_eff:.1f}'
            r[3].text = f'{W_eff:.0f}'

    # Structural summary
    complete_doc.add_heading('Structural Checks (Summary)', level=1)
    complete_doc.add_paragraph(
        f'6061-T6 yield: {mat_yield/1e6:.0f} MPa; design SF used: {safety_factor:.1f}')
    complete_doc.add_paragraph(
        f'Calculated required hoop thickness at P0: {t_req_hoop*1e3:.2f} mm')
    t_table = complete_doc.add_table(rows=1, cols=3)
    hdr = t_table.rows[0].cells
    hdr[0].text = 'Thickness (mm)'
    hdr[1].text = 'Hoop stress (MPa)'
    hdr[2].text = 'SF vs yield'
    for t in common_thicknesses:
        r = t_table.add_row().cells
        r[0].text = f'{t*1e3:.1f}'
        sigma_hoop = P0_abs * r_barrel / t
        r[1].text = f'{sigma_hoop/1e6:.1f}'
        sf = mat_yield / sigma_hoop
        r[2].text = f'{sf:.2f}'

    # Transient results
    complete_doc.add_heading('Transient 1D Simulation Results', level=1)
    complete_doc.add_paragraph(
        f"Simulated muzzle velocity: {sim['muzzle_v']:.2f} m/s")
    complete_doc.add_paragraph(f"Impulse delivered: {sim['impulse']:.2f} N·s")
    complete_doc.add_paragraph(f"Discharge time: {sim['t_end']*1e3:.1f} ms")
    complete_doc.add_paragraph(
        f"Peak force (sim): {sim['peak_F']:.0f} N; Average force: {sim['avg_F']:.0f} N")

    # Transient results summary table
    try:
        t_keys = ['Metric', 'Value']
        ttable = complete_doc.add_table(rows=1, cols=2)
        ttable.rows[0].cells[0].text = 'Metric'
        ttable.rows[0].cells[1].text = 'Value'
        rows = [
            ('Muzzle velocity (m/s)', f"{sim['muzzle_v']:.2f}"),
            ('Impulse (N·s)', f"{sim['impulse']:.2f}"),
            ('Discharge time (ms)', f"{sim['t_end']*1e3:.1f}"),
            ('Peak force (N)', f"{sim['peak_F']:.0f}"),
            ('Average force (N)', f"{sim['avg_F']:.0f}")
        ]
        for r in rows:
            rc = ttable.add_row().cells
            rc[0].text = r[0]
            rc[1].text = r[1]
    except Exception:
        pass

    # Parametric sweep table (first 30 rows)
    complete_doc.add_heading('Parametric Sweep Summary (sample)', level=1)
    with open(json_path, 'r') as jf:
        ps = json.load(jf)
    sample = ps[:30]
    if sample:
        keys = ['orifice_d_m', 'Vc_m3', 'Cd',
                'muzzle_v', 'impulse', 't_end_s', 'peak_F']
        table = complete_doc.add_table(rows=1, cols=len(keys))
        for i, k in enumerate(keys):
            table.rows[0].cells[i].text = k
        for row in sample:
            rc = table.add_row().cells
            for i, k in enumerate(keys):
                val = row.get(k, '')
                if isinstance(val, float):
                    rc[i].text = f"{val:.4f}" if abs(
                        val) < 1000 else f"{val:.1f}"
                else:
                    rc[i].text = str(val)

    # Plots
    complete_doc.add_heading('Plots', level=1)
    for pf in plot_files:
        try:
            complete_doc.add_paragraph(os.path.basename(pf))
            complete_doc.add_picture(pf)
        except Exception:
            pass

    # Engineering drawing (embed PNG preview if available)
    complete_doc.add_heading('Engineering Drawing', level=1)
    drawing_png = os.path.join(OUTPUT_DIR, 'launcher_drawing.png')
    drawing_svg = os.path.join(OUTPUT_DIR, 'launcher_drawing.svg')
    try:
        if os.path.exists(drawing_png):
            complete_doc.add_paragraph('Embedded preview:')
            try:
                complete_doc.add_picture(drawing_png)
            except Exception:
                complete_doc.add_paragraph(os.path.basename(drawing_png))
        elif os.path.exists(drawing_svg):
            complete_doc.add_paragraph(os.path.basename(drawing_svg))
        else:
            complete_doc.add_paragraph('No drawing files found in outputs/.')
    except Exception:
        pass

    # Flange and bolt check
    complete_doc.add_heading('Flange and Bolt Check', level=1)
    with open(flange_summary_path, 'r') as ff:
        flange_info = json.load(ff)
    # Present flange info as tables instead of raw JSON
    try:
        assumptions = flange_info.get('assumptions', {})
        complete_doc.add_heading('Flange Assumptions', level=2)
        if assumptions:
            a_table = complete_doc.add_table(rows=1, cols=2)
            a_table.rows[0].cells[0].text = 'Parameter'
            a_table.rows[0].cells[1].text = 'Value'
            for k, v in assumptions.items():
                rc = a_table.add_row().cells
                rc[0].text = str(k)
                rc[1].text = str(v)

        complete_doc.add_heading('Flange Check Result', level=2)
        fr = flange_info.get('flange_result', {})
        if fr:
            f_table = complete_doc.add_table(rows=1, cols=2)
            f_table.rows[0].cells[0].text = 'Metric'
            f_table.rows[0].cells[1].text = 'Value'
            for k, v in fr.items():
                rc = f_table.add_row().cells
                rc[0].text = str(k)
                rc[1].text = str(v)

        complete_doc.add_heading('Worst-case Sweep Result', level=2)
        worst = flange_info.get('worst_case', {})
        if worst:
            w_table = complete_doc.add_table(rows=1, cols=2)
            w_table.rows[0].cells[0].text = 'Metric'
            w_table.rows[0].cells[1].text = 'Value'
            for k, v in worst.items():
                rc = w_table.add_row().cells
                rc[0].text = str(k)
                rc[1].text = str(v)
    except Exception:
        complete_doc.add_paragraph(json.dumps(flange_info, indent=2))

    # Bolt shear check table (per-bolt capacities and required count)
    try:
        complete_doc.add_heading('Bolt Shear Check (endcap)', level=2)
        b_table = complete_doc.add_table(rows=1, cols=3)
        b_table.rows[0].cells[0].text = 'Bolt'
        b_table.rows[0].cells[1].text = 'Capacity (N)'
        b_table.rows[0].cells[2].text = 'Bolts required'
        for bname, info in bolt_check.items():
            rc = b_table.add_row().cells
            rc[0].text = bname
            rc[1].text = f"{info['cap_N']:.0f}"
            rc[2].text = str(info['bolts_needed'])
    except Exception:
        pass

    # (Appendix: Generated Files) removed to keep document concise per request

    # Formulas and concise conclusion
    complete_doc.add_heading('Formulas and Conclusion', level=1)
    complete_doc.add_paragraph('Key formulas used in this analysis:')
    p1 = complete_doc.add_paragraph('Isothermal work: ')
    insert_omml_equation(p1, 'W = P_0 V_0 ln(P_0 / P_f)')
    p2 = complete_doc.add_paragraph('Hoop stress (thin-wall): ')
    insert_omml_equation(p2, r'\sigma_{hoop} = P\; r / t')
    p3 = complete_doc.add_paragraph('Required thickness (hoop): ')
    insert_omml_equation(p3, r't = P\; r / \sigma_{allowable}')
    p4 = complete_doc.add_paragraph('Axial stress (thin-wall): ')
    insert_omml_equation(p4, r'\sigma_{axial} = P\; r / (2\; t)')
    complete_doc.add_paragraph('Impulse and average force: I = m * v; F_avg ≈ I / t_discharge (crude estimate)')

    # Numerical recommendation for 6061-T6
    allowable = mat_yield / safety_factor
    recommended_t_mm = max(0.0, t_req_hoop * 1e3)
    complete_doc.add_paragraph(
        f'Using 6061-T6 (yield ≈ {mat_yield/1e6:.0f} MPa) and safety factor {safety_factor:.1f}, allowable stress ≈ {allowable/1e6:.1f} MPa.')
    complete_doc.add_paragraph(
        f'Calculated required hoop thickness at working pressure ({P0_gauge_bar:.1f} bar gauge) is ≈ {recommended_t_mm:.2f} mm.')
    complete_doc.add_paragraph('Recommendation: select a standard tube/wall thickness equal to or greater than the calculated required thickness, and verify endcap/flange/bolt margins separately. Use ASME/EN pressure-vessel rules or certified fittings for the chamber when safety is critical.')

    # Barrel–Payload Geometric Compatibility Constraint section
    complete_doc.add_heading('Barrel\u2013Payload Geometric Compatibility Constraint', level=1)

    complete_doc.add_paragraph(
        'The payload\u2013sabot assembly shall fit within the barrel internal diameter under all operating '
        'conditions without interference.'
    )

    complete_doc.add_heading('Core Constraint', level=2)
    complete_doc.add_paragraph(
        'Clearance condition:\n'
        '\n'
        '    D_eq + 2\u00b7C_sab \u2264 D_barrel,min\n'
        '\n'
        'where:\n'
        '  D_eq        = \u221a(W\u00b2 + H\u00b2)   (worst-case diagonal envelope of payload cross-section)\n'
        '  C_sab       = sabot radial clearance per side\n'
        '  D_barrel,min = D_barrel,nom \u2212 manufacturing tolerance'
    )

    complete_doc.add_heading('Numerical Check', level=2)
    complete_doc.add_paragraph(
        'Given:\n'
        '  W = 40 mm,  H = 45 mm  \u21d2  D_eq = \u221a(40\u00b2 + 45\u00b2) = 60.2 mm\n'
        '  C_sab = 1.5 mm  \u21d2  2\u00b7C_sab = 3.0 mm\n'
        '  D_barrel,nom = 52 mm,  tolerance = \u00b10.3 mm\n'
        '  \u21d2  D_barrel,min = 51.7 mm\n'
        '\n'
        'Check:\n'
        '  D_eq + 2\u00b7C_sab = 60.2 + 3.0 = 63.2 mm\n'
        '  63.2 mm  >  51.7 mm  \u21d2  INTERFERENCE if payload is misaligned in barrel'
    )

    complete_doc.add_heading('Interpretation', level=2)
    complete_doc.add_paragraph(
        'The payload does not satisfy the worst-case diagonal envelope constraint. '
        'Unconstrained rotation inside the barrel will result in interference (jamming). '
        'A sabot or alignment feature is mandatory to constrain the payload orientation '
        'and ensure the presented envelope does not exceed D_barrel,min.'
    )

    complete_doc.add_heading('Design Requirements', level=2)
    req_para = complete_doc.add_paragraph()
    req_para.add_run('Requirement G-01:\n').bold = True
    req_para.add_run(
        'The sabot shall enforce axial alignment such that payload rotation is constrained '
        'and the effective envelope presented to the barrel remains within D_barrel,min.\n\n'
    )
    req_para.add_run('Requirement G-02:\n').bold = True
    req_para.add_run(
        'Total radial clearance (including sabot) shall be limited to 1.0\u20131.5 mm per side '
        'to prevent tilt-induced interference while maintaining acceptable friction and ease of loading.'
    )

    # ODE system documentation for report
    complete_doc.add_heading('Governing ODE System for Launcher Simulation', level=1)
    ode_text = (
        'The launcher’s internal ballistics are modeled as a coupled system of ordinary differential equations (ODEs), solved numerically at each timestep. The state vector is:\n'
        '\n'
        '    s(t) = [x, v, P, m]\n'
        '\n'
        'where:\n'
        '  x = projectile position\n'
        '  v = projectile velocity\n'
        '  P = chamber pressure\n'
        '  m = mass of gas in chamber\n'
        '\n'
        'The system:\n'
        '1. Projectile motion (Newton’s law):\n'
        '   dv/dt = (P * A_bore - F_friction) / m_payload\n'
        '2. Kinematics:\n'
        '   dx/dt = v\n'
        '3. Gas mass balance:\n'
        '   dm/dt = -m_dot_out\n'
        '4. Pressure evolution (ideal gas, real-gas correction applied in code):\n'
        '   P = m * R * T / V(t)\n'
        '   dP/dt = (R * T / V) * dm/dt - (m * R * T / V^2) * dV/dt\n'
        '5. Chamber volume change (moving projectile):\n'
        '   V(t) = V0 + A_bore * x(t)\n'
        '   dV/dt = A_bore * v\n'
        '6. Valve mass flow (critical):\n'
        '   Choked: m_dot_out = Cd * A_orifice * P * sqrt(gamma / (R * T)) * (2/(gamma+1))^((gamma+1)/(2*(gamma-1)))\n'
        '   Subsonic: m_dot_out = f(Cv, P_up, P_down)\n'
        '\n'
        'Key insight: There is no single closed-form velocity equation. The exit velocity is obtained by integrating this ODE system over time.\n'
        '\n'
        'This system is implemented in simulate_transient() in scripts/gen_doc.py.'
    )
    complete_doc.add_paragraph(ode_text)

    complete_path = os.path.join(
        DOCS_DIR, 'pneumatic_launcher_analysis_complete.docx')
    try:
        complete_doc.save(complete_path)
    except PermissionError:
        # fallback: save to temp and attempt atomic replace
        tmp_path = complete_path + '.tmp'
        try:
            complete_doc.save(tmp_path)
            os.replace(tmp_path, complete_path)
        except Exception:
            # last resort: skip overwrite
            pass

    # Remove any intermediate document files in DOCS_DIR, keep only the master
    try:
        for fname in os.listdir(DOCS_DIR):
            # remove any .docx that is not the master, and any temp files
            if (fname.lower().endswith('.docx') and fname != os.path.basename(complete_path)) or fname.lower().endswith('.tmp') or fname.startswith(os.path.basename(complete_path)) and fname != os.path.basename(complete_path):
                try:
                    os.remove(os.path.join(DOCS_DIR, fname))
                except Exception:
                    pass
    except Exception:
        pass
except Exception:
    import traceback
    traceback.print_exc()
    complete_path = None

complete_path
