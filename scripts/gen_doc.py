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
# Working pressure shown on accumulator: 10 bar (gauge) â€” matches EDD nominal WP
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
        # Real-gas pressure: P = Z * rho * R_spec * T = Z * (m/V) * R_u * T / M
        # Z is evaluated at the ideal-gas pressure estimate (first-order approximation)
        Pc_ideal = (m_c / Vc) * R_u * T / M_co2 if Vc > 0 else P_atm
        Zc = compressibility_Z_RK(max(P_atm, Pc_ideal), T)
        Pc = Pc_ideal * Zc if Vc > 0 else P_atm
        Pb_ideal = (m_b / Vb) * R_u * T / M_co2
        Zb = compressibility_Z_RK(max(P_atm, Pb_ideal), T)
        Pb = Pb_ideal * Zb

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

        # pressures update â€” use ideal-gas estimate for Z lookup (first-order real-gas correction)
        Pc_ideal_new = (m_c / Vc) * R_u * T / M_co2 if m_c > 0 else P_atm
        Zc = compressibility_Z_RK(max(P_atm, Pc_ideal_new), T)
        Pc = Pc_ideal_new * Zc
        Vb = A_bore * x + 1e-6
        Pb_ideal_new = (m_b / Vb) * R_u * T / M_co2
        Zb = compressibility_Z_RK(max(P_atm, Pb_ideal_new), T)
        Pb = Pb_ideal_new * Zb

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
    plt.ylabel('Impulse (NÂ·s)')
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
# Bolt check uses static endcap load = P0 * A_bore (correct load case).
# worst_peak is the peak force on the PROJECTILE during transit â€” not the endcap load.
F_endcap_static = P0_abs * barrel_area  # N
flange_result = flange_bolt_check(F_endcap_static, n_bolts=flange_assumptions['n_bolts'], pcd=flange_assumptions[
                                  'pcd_m'], bolt_dia=flange_assumptions['bolt_dia_m'], mat_shear=flange_assumptions['bolt_material_shear'])
flange_summary_path = os.path.join(OUTPUT_DIR, 'flange_check.json')
with open(flange_summary_path, 'w') as ff:
    json.dump({
        'assumptions': flange_assumptions,
        'endcap_static_F_N': F_endcap_static,
        'endcap_static_formula': 'F = P0_abs * A_bore = P0_abs * pi*(D/2)^2',
        'endcap_flange_result': flange_result,
        'worst_peak_barrel_F_N': worst_peak,
        'note_worst_peak': 'Peak force on projectile during transit (not endcap bolt load)',
        'worst_case_sweep': worst
    }, ff, indent=2)

# Final summary doc
final_doc_path = None

# ---- Now assemble the single comprehensive document (after plots & checks exist) ----
try:
    complete_doc = Document()
    complete_doc.add_heading('Pneumatic Launcher \u2014 Complete Technical Analysis', 0)

    # â”€â”€ 1. INPUT PARAMETERS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    complete_doc.add_heading('1. Input Parameters', level=1)
    complete_doc.add_paragraph(
        'All parameters are derived from the system schematic and engineering requirements.'
    )
    params_table = complete_doc.add_table(rows=1, cols=3)
    ph = params_table.rows[0].cells
    ph[0].text = 'Parameter'; ph[1].text = 'Value'; ph[2].text = 'Notes / Derivation'
    R_spec_co2 = 8.31446 / 0.04401
    param_rows_data = [
        ('Charge chamber volume, V\u2080', f'{V0*1e3:.1f} mL  ({V0:.4f} m\u00b3)', 'Accumulator tank'),
        ('Working pressure (gauge), P\u2080', f'{P0_gauge_bar:.1f} bar gauge', 'As marked on accumulator'),
        ('Working pressure (absolute)', f'{P0_abs/1e5:.2f} bar  ({P0_abs:.3e} Pa)',
         f'P\u2080_abs = (P\u2080_gauge + 1) \u00d7 10\u2075 = ({P0_gauge_bar:.0f}+1)\u00d710\u2075'),
        ('Atmospheric back-pressure, Pf', f'{Pf/1e5:.2f} bar  ({Pf:.0f} Pa)', 'Standard atmosphere'),
        ('Barrel internal diameter, D', f'{barrel_id*1e3:.0f} mm', 'Measured from drawing'),
        ('Barrel length, L', f'{barrel_length*1e3:.0f} mm', 'Measured from drawing'),
        ('Bore area, A_bore', f'{barrel_area*1e4:.4f} cm\u00b2  ({barrel_area:.6f} m\u00b2)',
         f'A = \u03c0(D/2)\u00b2 = \u03c0\u00d70.026\u00b2 = {barrel_area:.6f} m\u00b2'),
        ('CO\u2082 specific gas constant, R_spec', f'{R_spec_co2:.2f} J/(kg\u00b7K)',
         'R_spec = R_u/M_CO\u2082 = 8.314/0.04401'),
        ('Temperature, T', '293.15 K (20 \u00b0C)', 'Ambient / charge temperature'),
        ('Specific heat ratio, \u03b3', '1.30  (CO\u2082)', 'Used in compressible flow formulae'),
        ('Discharge coefficient, Cd', '0.8 (default)', 'Swept 0.6\u20130.8 in parametric study'),
        ('Default orifice diameter, d_or', '12 mm', 'Swept 6\u201318 mm in parametric study'),
    ]
    for pr in param_rows_data:
        rc = params_table.add_row().cells
        rc[0].text = pr[0]; rc[1].text = pr[1]; rc[2].text = pr[2]

    # â”€â”€ 2. THEORETICAL ENERGY ANALYSIS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    complete_doc.add_heading('2. Theoretical Energy Analysis', level=1)
    complete_doc.add_paragraph(
        'The maximum theoretical work available from isothermal expansion of a compressed '
        'gas from pressure P\u2080 down to atmospheric Pf in a fixed charge volume V\u2080 is:'
    )
    p_eq = complete_doc.add_paragraph('    W = P\u2080 \u00b7 V\u2080 \u00b7 ln(P\u2080 / Pf)')
    p_eq.runs[0].bold = True
    complete_doc.add_paragraph(
        'Derivation:\n'
        'For an ideal gas expanding isothermally, the work element is dW = P dV.\n'
        'With PV = const at constant T, we have P = P\u2080V\u2080/V.\n'
        'Integrating from the initial volume V\u2080 to the final volume Vf = V\u2080\u00b7(P\u2080/Pf):\n\n'
        '    W = \u222b\u1d6a\u1d64\u1d5c  P dV  =  P\u2080V\u2080 \u222b dV/V  =  P\u2080V\u2080 \u00b7 ln(Vf/V\u2080)\n'
        '      = P\u2080V\u2080 \u00b7 ln(P\u2080/Pf)\n\n'
        'Numerical verification:\n'
        f'  P\u2080 = {P0_abs:.4e} Pa\n'
        f'  V\u2080 = {V0:.4f} m\u00b3\n'
        f'  ln(P\u2080/Pf) = ln({P0_abs:.4e}/{Pf:.0f}) = ln({P0_abs/Pf:.4f}) = {math.log(P0_abs/Pf):.4f}\n'
        f'  W = {P0_abs:.4e} \u00d7 {V0:.4f} \u00d7 {math.log(P0_abs/Pf):.4f}\n'
        f'    = {P0_abs*V0:.4f} \u00d7 {math.log(P0_abs/Pf):.4f}\n'
        f'    = {W_ideal:.2f} J\n\n'
        'Note: This is the absolute theoretical upper bound (ideal gas, zero losses).\n'
        'The ODE simulation (Section 5) accounts for real-gas behaviour, flow restriction,\n'
        'friction, and finite barrel length, giving the physically realistic muzzle velocity.'
    )
    sim_ke = 0.5 * 1.0 * sim['muzzle_v'] ** 2
    complete_doc.add_paragraph(
        f'ODE simulation result (1 kg payload, 12 mm orifice, Cd=0.8):\n'
        f'  v_exit = {sim["muzzle_v"]:.2f} m/s  \u2192  KE = \u00bd\u00d71.0\u00d7{sim["muzzle_v"]:.2f}\u00b2 = {sim_ke:.1f} J\n'
        f'  Launch efficiency \u03b7 = {sim_ke:.1f} / {W_ideal:.1f} = {sim_ke/W_ideal*100:.1f} %'
    )

    # â”€â”€ 3. REPRESENTATIVE PAYLOAD SCENARIOS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    complete_doc.add_heading('3. Representative Payload Scenarios (Theoretical Bounds)', level=1)
    complete_doc.add_paragraph(
        'Converting available expansion work to muzzle velocity at a given mechanical '
        'efficiency \u03b7 (accounts for friction, heat loss, sealing losses):\n\n'
        '    KE = \u03b7 \u00b7 W  \u21d2  \u00bdmv\u00b2 = \u03b7W  \u21d2  v = \u221a(2\u03b7W / m)\n\n'
        'These are theoretical upper bounds only. Actual velocity from ODE simulation is\n'
        f'lower ({sim["muzzle_v"]:.1f} m/s for 1 kg) due to valve flow restriction and friction.'
    )
    scen_table = complete_doc.add_table(rows=1, cols=5)
    sh = scen_table.rows[0].cells
    sh[0].text = 'Mass m (kg)'
    sh[1].text = 'Efficiency \u03b7 (%)'
    sh[2].text = 'W_eff = \u03b7\u00b7W (J)'
    sh[3].text = 'v = \u221a(2W_eff/m)  (m/s)'
    sh[4].text = 'Numeric check'
    for m_sc in masses:
        for eff in efficiencies:
            W_eff = W_ideal * eff
            v_eff = math.sqrt(2.0 * W_eff / m_sc)
            sr = scen_table.add_row().cells
            sr[0].text = f'{m_sc:.2f}'
            sr[1].text = f'{eff*100:.0f}'
            sr[2].text = f'{W_eff:.0f}'
            sr[3].text = f'{v_eff:.1f}'
            sr[4].text = f'\u221a(2\u00d7{W_eff:.0f}/{m_sc:.2f}) = {v_eff:.1f}'

    # â”€â”€ 4. STRUCTURAL ANALYSIS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    complete_doc.add_heading('4. Structural Analysis \u2014 Barrel Wall and Endcap', level=1)
    complete_doc.add_heading('4.1 Barrel Thin-Wall Hoop Stress', level=2)
    complete_doc.add_paragraph(
        'Applicable for thin-walled cylinder (D/t > 20). The two principal stresses are:\n\n'
        '    Hoop (circumferential):  \u03c3_hoop  = P \u00b7 r / t\n'
        '    Axial (longitudinal):    \u03c3_axial = P \u00b7 r / (2t)  =  \u00bd \u03c3_hoop\n\n'
        'where  r = D/2 = inner radius,  t = wall thickness,  P = internal pressure.\n'
        'Hoop stress governs; setting \u03c3_hoop = \u03c3_yield / SF gives minimum wall thickness:\n\n'
        '    t_min = P \u00b7 r \u00b7 SF / \u03c3_yield\n\n'
        'Numerical check:\n'
        f'  P = {P0_abs:.3e} Pa\n'
        f'  r = {r_barrel*1e3:.1f} mm = {r_barrel:.4f} m\n'
        f'  \u03c3_yield = {mat_yield/1e6:.0f} MPa  (6061-T6 aluminium)\n'
        f'  SF = {safety_factor:.0f}  (design safety factor)\n'
        f'  \u03c3_allowable = {mat_yield/1e6:.0f} / {safety_factor:.0f} = {mat_yield/safety_factor/1e6:.1f} MPa\n\n'
        f'  t_min = {P0_abs:.3e} \u00d7 {r_barrel:.4f} / ({mat_yield/1e6:.0f}\u00d710\u2076 / {safety_factor:.0f})\n'
        f'        = {P0_abs*r_barrel:.4f} / {mat_yield/safety_factor:.0f}\n'
        f'        = {t_req_hoop*1e3:.4f} mm\n\n'
        f'  Axial t_min = {t_req_axial*1e3:.4f} mm (non-governing)\n\n'
        'Thin-wall check at 3 mm:  D/t = 52/3 = 17.3 \u2192 borderline; '
        'use thick-wall (Lam\u00e9) if t > D/20. At these stresses the difference is negligible.'
    )
    complete_doc.add_heading('4.2 Wall Thickness Comparison Table', level=2)
    t_table = complete_doc.add_table(rows=1, cols=5)
    th_cells = t_table.rows[0].cells
    th_cells[0].text = 'Thickness t (mm)'
    th_cells[1].text = '\u03c3_hoop (MPa)'
    th_cells[2].text = 'SF vs yield'
    th_cells[3].text = 'SF vs ultimate'
    th_cells[4].text = 'Formula: P\u00b7r/t'
    for t_w in common_thicknesses:
        sigma_h = P0_abs * r_barrel / t_w
        sf_y = mat_yield / sigma_h
        sf_u = mat_ultimate / sigma_h
        tr = t_table.add_row().cells
        tr[0].text = f'{t_w*1e3:.1f}'
        tr[1].text = f'{sigma_h/1e6:.2f}'
        tr[2].text = f'{sf_y:.1f}'
        tr[3].text = f'{sf_u:.1f}'
        tr[4].text = f'{P0_abs/1e6:.2f}\u00d710\u2076\u00d7{r_barrel*1e3:.0f}e-3/{t_w*1e3:.0f}e-3'
    complete_doc.add_paragraph(
        f'Minimum required hoop thickness (SF={safety_factor:.0f}): {t_req_hoop*1e3:.3f} mm.\n'
        f'Standard 3 mm wall gives SF = {mat_yield/(P0_abs*r_barrel/0.003):.1f} vs yield '
        f'({mat_ultimate/(P0_abs*r_barrel/0.003):.1f} vs ultimate) \u2014 acceptable.'
    )

    # â”€â”€ 5. 1D TRANSIENT SIMULATION â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    complete_doc.add_heading('5. 1D Transient Simulation (ODE Model)', level=1)
    complete_doc.add_heading('5.1 Governing ODE System', level=2)
    complete_doc.add_paragraph(
        'Internal ballistics are modelled as a coupled ODE system, integrated with '
        'a fixed time step dt = 0.1 ms using forward Euler.\n\n'
        'State variables:\n'
        '  x    = projectile position along bore  (m)\n'
        '  v    = projectile velocity              (m/s)\n'
        '  Pc   = charge chamber pressure          (Pa)\n'
        '  Pb   = barrel (bore) pressure           (Pa)\n'
        '  m_c  = gas mass in charge chamber       (kg)\n'
        '  m_b  = gas mass in barrel volume        (kg)\n\n'
        'Equations of motion:\n\n'
        '  (1)  dx/dt = v\n\n'
        '  (2)  dv/dt = F_net / m_payload\n'
        '         F_net = max(0,  (Pb \u2212 Patm)\u00b7A_bore  \u2212  \u03bc\u00b7Pb\u00b7A_bore)\n'
        '         where \u03bc = 0.10 is the bore friction coefficient\n\n'
        '  (3)  dm_c/dt = \u2212\u1e41\n'
        '       dm_b/dt = +\u1e41\n'
        '         \u1e41 = mass flow rate through valve orifice (see Section 5.2)\n\n'
        '  (4)  Barrel volume (moves with projectile):\n'
        '         V_b(t) = A_bore\u00b7x(t) + V_clearance   (V_clearance = 10\u207b\u2076 m\u00b3)\n\n'
        '  (5)  Real-gas pressure (Redlich\u2013Kwong EOS, first-order iteration):\n'
        '         P_ideal = (m/V)\u00b7R_u\u00b7T / M_CO\u2082          (ideal gas estimate)\n'
        '         Z = Z_RK(P_ideal, T)                   (compressibility factor)\n'
        '         P_real  = Z\u00b7P_ideal                      (since P = Z\u00b7\u03c1\u00b7R_spec\u00b7T)\n\n'
        '  (6)  Termination: loop exits when x \u2265 L (muzzle) or Pc \u2264 1.01\u00b7Patm'
    )
    complete_doc.add_heading('5.2 Real-Gas Correction (Redlich\u2013Kwong EOS)', level=2)
    Tc_co2 = 304.1282; Pc_rk = 7.3773e6; Ru = 8.31446
    a_rk = 0.42748 * Ru * Ru * Tc_co2 * Tc_co2 / Pc_rk
    b_rk = 0.08664 * Ru * Tc_co2 / Pc_rk
    complete_doc.add_paragraph(
        'The Redlich\u2013Kwong equation of state for CO\u2082:\n\n'
        '    P = R_u\u00b7T / (V_m \u2212 b)  \u2212  a / (V_m\u00b7(V_m + b)\u00b7\u221aT)\n\n'
        'CO\u2082 critical constants:  Tc = 304.13 K,  Pc = 7.377 MPa\n\n'
        'RK constants:\n'
        f'    a = 0.42748\u00b7R\u00b2\u00b7Tc\u00b2/Pc = {a_rk:.4f}  (J\u00b7m\u00b3\u00b7K^0.5 / mol\u00b2)\n'
        f'    b = 0.08664\u00b7R\u00b7Tc/Pc  = {b_rk:.6f}  (m\u00b3/mol)\n\n'
        'Compressibility Z is solved iteratively via Newton\u2013Raphson on the cubic\n'
        '(tolerance 10\u207b\u2076, max 60 iterations). For CO\u2082 at 11 bar, 293 K: Z \u2248 0.97.\n\n'
        'Pressure from mass and volume: P_real = Z\u00b7(m/V)\u00b7R_u\u00b7T / M_CO\u2082\n'
        '  where Z is evaluated at P_ideal = (m/V)\u00b7R_u\u00b7T/M_CO\u2082 (first-order approximation).'
    )
    complete_doc.add_heading('5.3 Valve Mass Flow Rate Formulas', level=2)
    gamma_co2 = 1.3
    critical_ratio = (2.0 / (gamma_co2 + 1.0)) ** (gamma_co2 / (gamma_co2 - 1.0))
    choked_factor = (2.0 / (gamma_co2 + 1.0)) ** ((gamma_co2 + 1.0) / (2.0 * (gamma_co2 - 1.0)))
    A_or_default = math.pi * (0.006) ** 2
    mdot_choked_t0 = 0.8 * A_or_default * P0_abs / math.sqrt(R_spec_co2 * 293.15) * math.sqrt(gamma_co2) * choked_factor
    complete_doc.add_paragraph(
        'Mass flow through the valve orifice uses compressible orifice theory.\n\n'
        'Critical pressure ratio \u2014 flow chokes when Pb/Pc \u2264 r_crit:\n\n'
        f'    r_crit = (2/(\u03b3+1))^(\u03b3/(\u03b3\u22121))\n'
        f'           = (2/{gamma_co2+1:.1f})^({gamma_co2:.1f}/{gamma_co2-1:.1f})\n'
        f'           = {critical_ratio:.4f}   (\u03b3 = {gamma_co2})\n\n'
        'CHOKED FLOW  (Pb/Pc \u2264 r_crit; governs the majority of the discharge cycle):\n\n'
        '    \u1e41 = Cd \u00b7 A_or \u00b7 Pc \u00b7 \u221a(\u03b3/(R_spec\u00b7T)) \u00b7 (2/(\u03b3+1))^((\u03b3+1)/(2(\u03b3\u22121)))\n\n'
        f'    Numerically at t=0  (Pc = {P0_abs/1e5:.1f} bar, Cd = 0.8, d_or = 12 mm, T = 293 K):\n'
        f'      A_or = \u03c0\u00d7(0.006)\u00b2 = {A_or_default:.4e} m\u00b2\n'
        f'      \u221a(\u03b3/(R\u00b7T)) = \u221a({gamma_co2}/{R_spec_co2:.1f}\u00d7293) = {math.sqrt(gamma_co2/(R_spec_co2*293.15)):.5f}\n'
        f'      factor = (2/{gamma_co2+1:.1f})^(({gamma_co2+1:.1f})/(2\u00d7{gamma_co2-1:.1f})) = {choked_factor:.4f}\n'
        f'      \u1e41\u2080 = 0.8 \u00d7 {A_or_default:.4e} \u00d7 {P0_abs:.3e} \u00d7 {math.sqrt(gamma_co2/(R_spec_co2*293.15)):.5f} \u00d7 {choked_factor:.4f}\n'
        f'         = {mdot_choked_t0:.4f} kg/s\n\n'
        'UNCHOKED FLOW  (Pb/Pc > r_crit; late in the discharge cycle when pressures equalise):\n\n'
        '    \u1e41 = Cd\u00b7A_or\u00b7Pc/\u221a(R\u00b7T) \u00b7 \u221a[ 2\u03b3/(\u03b3\u22121) \u00b7 ((Pb/Pc)^(2/\u03b3) \u2212 (Pb/Pc)^((\u03b3+1)/\u03b3)) ]\n\n'
        '    This is the standard isentropic compressible orifice formula (Anderson 2003);\n'
        '    it converges to zero as Pb \u2192 Pc (pressure equalisation).'
    )
    complete_doc.add_heading('5.4 Default Case Results', level=2)
    complete_doc.add_paragraph(
        f'Simulation parameters: m_payload = 1.0 kg | d_or = 12 mm | Cd = 0.8 | T = 293 K\n'
        f'Barrel: D = {barrel_id*1e3:.0f} mm, L = {barrel_length*1e3:.0f} mm | '
        f'Chamber: V\u2080 = {V0*1e3:.0f} mL @ {P0_gauge_bar:.0f} bar gauge'
    )
    sim_table = complete_doc.add_table(rows=1, cols=3)
    sim_h = sim_table.rows[0].cells
    sim_h[0].text = 'Output'
    sim_h[1].text = 'Value'
    sim_h[2].text = 'Formula / Notes'
    sim_rows_data = [
        ('Muzzle velocity', f"{sim['muzzle_v']:.3f} m/s",
         'v(t) at x = L (ODE integration endpoint)'),
        ('Impulse', f"{sim['impulse']:.3f} N\u00b7s",
         'I = m_payload \u00d7 v_exit = \u0394(momentum)  [v_init = 0]'),
        ('KE at muzzle', f"{sim_ke:.2f} J",
         f'\u00bd\u00d71.0\u00d7{sim["muzzle_v"]:.3f}\u00b2'),
        ('Launch efficiency',
         f"{sim_ke/W_ideal*100:.2f} %",
         f'KE / W_ideal = {sim_ke:.2f} / {W_ideal:.1f}'),
        ('Discharge time', f"{sim['t_end']*1e3:.2f} ms",
         'Time for projectile to traverse full barrel'),
        ('Peak barrel force', f"{sim['peak_F']:.1f} N",
         'max[(Pb(t)\u2212Patm)\u00b7A_bore]; force on projectile'),
        ('Average propulsion force', f"{sim['avg_F']:.1f} N",
         'F_avg = Impulse / t_discharge'),
        ('Static endcap bolt load', f"{P0_abs*barrel_area:.1f} N",
         'P\u2080_abs \u00d7 A_bore (see Section 8)'),
    ]
    for sr in sim_rows_data:
        rc = sim_table.add_row().cells
        rc[0].text = sr[0]; rc[1].text = sr[1]; rc[2].text = sr[2]

    # â”€â”€ 6. PARAMETRIC SWEEP â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    complete_doc.add_heading('6. Parametric Sweep', level=1)
    complete_doc.add_paragraph(
        'The ODE model was run over a 3-D grid to characterise performance sensitivity.\n'
        f'Fixed: m_payload = 1.0 kg, T = 293 K, P\u2080 = {P0_gauge_bar:.0f} bar gauge, '
        f'D = {barrel_id*1e3:.0f} mm, L = {barrel_length*1e3:.0f} mm.\n\n'
        'Swept variables:\n'
        '  \u2022 Orifice diameter  d_or \u2208 {6, 8, 10, 12, 15, 18} mm  '
        '(A_or = \u03c0(d/2)\u00b2 ranges {28.3, 50.3, 78.5, 113.1, 176.7, 254.5} mm\u00b2)\n'
        '  \u2022 Chamber volume    Vc  \u2208 {500, 800, 1000, 1200} mL\n'
        '  \u2022 Discharge coeff.  Cd  \u2208 {0.6, 0.7, 0.8}\n\n'
        'Total: 6 \u00d7 4 \u00d7 3 = 72 ODE runs.\n\n'
        'Recorded outputs per run:\n'
        '  v_exit  \u2014 muzzle velocity at x = L  (m/s)\n'
        '  I       \u2014 impulse = m\u00b7v_exit  (N\u00b7s)\n'
        '  t_end   \u2014 projectile transit time  (s)\n'
        '  F_peak  \u2014 max[(Pb\u2212Patm)\u00b7A_bore] during stroke  (N)'
    )
    complete_doc.add_heading('6.1 Sweep Data Table (first 30 of 72 runs)', level=2)
    with open(json_path, 'r') as jf:
        ps_data = json.load(jf)
    sample_data = ps_data[:30]
    sweep_headers = ['d_or (mm)', 'Vc (mL)', 'Cd', 'v_exit (m/s)', 'Impulse (N\u00b7s)', 't_end (ms)', 'F_peak (N)']
    sweep_keys_list = ['orifice_d_m', 'Vc_m3', 'Cd', 'muzzle_v', 'impulse', 't_end_s', 'peak_F']
    sweep_scale_list = [1e3, 1e6, 1.0, 1.0, 1.0, 1e3, 1.0]
    if sample_data:
        sw_table = complete_doc.add_table(rows=1, cols=len(sweep_headers))
        for i, h in enumerate(sweep_headers):
            sw_table.rows[0].cells[i].text = h
        for row_d in sample_data:
            rc = sw_table.add_row().cells
            for i, k in enumerate(sweep_keys_list):
                val = row_d.get(k, '')
                if isinstance(val, float):
                    scaled = val * sweep_scale_list[i]
                    rc[i].text = f'{scaled:.2f}' if abs(scaled) < 100 else f'{scaled:.1f}'
                else:
                    rc[i].text = str(val)

    # â”€â”€ 7. PARAMETRIC SWEEP PLOTS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    complete_doc.add_heading('7. Parametric Sweep Plots', level=1)
    complete_doc.add_paragraph(
        'Each data point is the endpoint of one full ODE integration run (72 total).\n'
        'X-axis: orifice diameter d_or. Each curve: one value of discharge coefficient Cd.\n'
        'Each figure: one fixed chamber volume Vc.\n\n'
        'How each plot was computed:\n'
        '  Muzzle velocity plots: v_exit = v(t) when x(t) first reaches L = 700 mm\n'
        '  Peak force plot:       F_peak = max_t[ (Pb(t)\u2212Patm) \u00d7 A_bore ]\n'
        '  Impulse plot:          I = m_payload \u00d7 v_exit  (= \u222bF_net dt for m_init=0)'
    )
    plot_captions_map = {
        'vel_vs_orifice_Vc_500uL.png': (
            'Figure 1 \u2014 Muzzle velocity vs orifice diameter  (Vc = 500 mL)\n'
            'Formula: v_exit from ODE integration, x integrated until x = 700 mm.\n'
            'Observation: velocity rises steeply up to ~10 mm orifice; plateau beyond '
            '12 mm indicates barrel-length limits the energy extraction at this volume.'
        ),
        'vel_vs_orifice_Vc_800uL.png': (
            'Figure 2 \u2014 Muzzle velocity vs orifice diameter  (Vc = 800 mL)\n'
            'Larger chamber maintains higher Pc longer, raising exit velocity especially '
            'at large orifice diameters where flow duration matters.'
        ),
        'vel_vs_orifice_Vc_1000uL.png': (
            'Figure 3 \u2014 Muzzle velocity vs orifice diameter  (Vc = 1000 mL) \u2014 NOMINAL CASE\n'
            f'Reference: V\u2080 = {V0*1e3:.0f} mL at P\u2080 = {P0_gauge_bar:.0f} bar gauge.\n'
            f'At d_or = 12 mm, Cd = 0.8: v_exit = {sim["muzzle_v"]:.1f} m/s.'
        ),
        'vel_vs_orifice_Vc_1200uL.png': (
            'Figure 4 \u2014 Muzzle velocity vs orifice diameter  (Vc = 1200 mL)\n'
            'Over-volume case; diminishing returns vs 1000 mL due to barrel-length limit '
            'at this pressure.'
        ),
        'peakF_vs_orifice_Vc_1000uL.png': (
            'Figure 5 \u2014 Peak barrel force vs orifice diameter  (Vc = 1000 mL)\n'
            'Formula: F_peak = max_t[ (Pb(t) \u2212 Patm) \u00d7 A_bore ]\n'
            'This is the maximum force accelerating the PROJECTILE during the firing stroke.\n'
            'It is NOT the endcap bolt load (endcap sees static P\u2080\u00d7A_bore; see Section 8).\n'
            'Large orifices allow rapid barrel pressure build-up \u2192 higher peak projectile force.'
        ),
        'impulse_vs_orifice_Vc_1000uL.png': (
            'Figure 6 \u2014 Impulse vs orifice diameter  (Vc = 1000 mL)\n'
            'Formula: I = m_payload \u00d7 v_exit = \u0394p = \u222bF_net dt  (m_payload = 1 kg)\n'
            'For 1 kg payload: impulse (N\u00b7s) = velocity (m/s) numerically.\n'
            'Plateau at large d_or confirms barrel-length limited regime: additional valve '
            'area cannot increase the velocity further once gas transit time < projectile '
            'transit time.'
        ),
    }
    for pf in plot_files:
        basename = os.path.basename(pf)
        caption = plot_captions_map.get(basename, f'Plot: {basename}')
        complete_doc.add_paragraph(caption)
        try:
            complete_doc.add_picture(pf)
        except Exception:
            complete_doc.add_paragraph(f'[Image: {basename}]')
        complete_doc.add_paragraph('')

    # Engineering drawing
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
            complete_doc.add_paragraph('No drawing file found in outputs/.')
    except Exception:
        pass

    # â”€â”€ 8. FLANGE AND BOLT CHECK â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    complete_doc.add_heading('8. Flange and Bolt Check', level=1)
    F_endcap = P0_abs * barrel_area
    complete_doc.add_heading('8.1 Load Cases', level=2)
    complete_doc.add_paragraph(
        'LOAD CASE A \u2014 Static endcap bolt load (governs fastener design):\n'
        '  The endcap must resist the maximum chamber pressure acting on the bore area.\n\n'
        f'    F_endcap = P\u2080_abs \u00d7 A_bore\n'
        f'             = {P0_abs:.3e} Pa \u00d7 {barrel_area:.6f} m\u00b2\n'
        f'             = {P0_abs:.3e} \u00d7 \u03c0 \u00d7 ({r_barrel*1e3:.0f}e\u207b\u00b3)\u00b2\n'
        f'             = {F_endcap:.1f} N   ({F_endcap/1e3:.3f} kN)\n\n'
        'LOAD CASE B \u2014 Peak barrel transit force (informational only, not endcap load):\n'
        '  Maximum force propelling the projectile during firing stroke.\n'
        '  This acts on the projectile, NOT on the endcap or chamber bolts.\n\n'
        f'    F_peak_barrel = {worst_peak:.1f} N\n'
        f'    (Worst sweep case: d_or={worst["orifice_d_m"]*1e3:.0f} mm, '
        f'Vc={worst["Vc_m3"]*1e6:.0f} mL, Cd={worst["Cd"]:.1f})\n\n'
        'Bolt design uses Load Case A only.'
    )
    complete_doc.add_heading('8.2 Bolt Shear Capacity Formula', level=2)
    A_M8 = math.pi * (0.004) ** 2
    F_cap_M8 = A_M8 * 240e6
    n_M8 = math.ceil(F_endcap / F_cap_M8)
    SF_6xM8 = 6 * F_cap_M8 / F_endcap
    complete_doc.add_paragraph(
        'Each bolt resists the endcap axial load in direct shear:\n\n'
        '    A_bolt = \u03c0 \u00d7 (d_bolt/2)\u00b2\n'
        '    F_cap  = A_bolt \u00d7 \u03c4_shear\n'
        '    n_req  = \u2308 F_endcap / F_cap \u2309  (ceiling)\n\n'
        f'For M8 bolts (d = 8 mm, \u03c4_shear = 240 MPa):\n'
        f'    A_bolt = \u03c0\u00d7(0.004)\u00b2 = {A_M8:.4e} m\u00b2  ({A_M8*1e6:.2f} mm\u00b2)\n'
        f'    F_cap  = {A_M8:.4e} \u00d7 240\u00d710\u2076 = {F_cap_M8:.1f} N\n'
        f'    n_req  = \u2308 {F_endcap:.1f} / {F_cap_M8:.1f} \u2309 = {n_M8}\n\n'
        f'With {flange_assumptions["n_bolts"]} M8 bolts provided:\n'
        f'    SF = {flange_assumptions["n_bolts"]} \u00d7 {F_cap_M8:.1f} / {F_endcap:.1f} = {SF_6xM8:.1f}\n\n'
        'Safety factor of ' + f'{SF_6xM8:.1f} gives substantial margin; 4 M6 bolts would also suffice.'
    )
    complete_doc.add_heading('8.3 Bolt Shear Check Table', level=2)
    b_table = complete_doc.add_table(rows=1, cols=5)
    bh = b_table.rows[0].cells
    bh[0].text = 'Bolt size'
    bh[1].text = 'A_bolt (mm\u00b2)'
    bh[2].text = 'F_cap per bolt (N)'
    bh[3].text = 'n_req (Load A)'
    bh[4].text = 'SF with 6 bolts'
    bolt_areas = {'M6': 20e-6, 'M8': 36.6e-6, 'M10': 58e-6}
    for bname, info in bolt_check.items():
        A_b = bolt_areas.get(bname, 0)
        rc = b_table.add_row().cells
        rc[0].text = bname
        rc[1].text = f'{A_b*1e6:.1f}'
        rc[2].text = f"{info['cap_N']:.1f}"
        rc[3].text = str(math.ceil(F_endcap / info['cap_N']))
        rc[4].text = f"{6 * info['cap_N'] / F_endcap:.1f}"

    # â”€â”€ 9. BARREL\u2013PAYLOAD GEOMETRIC COMPATIBILITY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    complete_doc.add_heading('9. Barrel\u2013Payload Geometric Compatibility Constraint', level=1)
    complete_doc.add_paragraph(
        'The payload\u2013sabot assembly shall fit within the barrel bore under all operating '
        'conditions without interference.'
    )
    complete_doc.add_heading('9.1 Core Constraint', level=2)
    complete_doc.add_paragraph(
        'For a rectangular payload (W \u00d7 H) inside a circular bore (diameter D_barrel),\n'
        'the worst-case envelope occurs when the payload diagonal aligns with the bore:\n\n'
        '    D_eq = \u221a(W\u00b2 + H\u00b2)    (worst-case diagonal envelope)\n\n'
        'Including sabot radial clearance C_sab per side, the no-interference condition is:\n\n'
        '    D_eq + 2\u00b7C_sab  \u2264  D_barrel,min\n\n'
        'where  D_barrel,min = D_barrel,nom \u2212 machining tolerance.'
    )
    complete_doc.add_heading('9.2 Numerical Check', level=2)
    W_p, H_p = 40.0, 45.0
    D_eq_val = math.sqrt(W_p ** 2 + H_p ** 2)
    C_sab_val = 1.5
    D_barrel_nom_val = 52.0
    D_barrel_tol_val = 0.3
    D_barrel_min_val = D_barrel_nom_val - D_barrel_tol_val
    clearance_total = D_eq_val + 2 * C_sab_val
    complete_doc.add_paragraph(
        f'Payload dimensions:  W = {W_p:.0f} mm,  H = {H_p:.0f} mm\n'
        f'  D_eq = \u221a({W_p:.0f}\u00b2 + {H_p:.0f}\u00b2) = \u221a{W_p**2 + H_p**2:.0f} = {D_eq_val:.2f} mm\n\n'
        f'Sabot clearance:  C_sab = {C_sab_val:.1f} mm per side  \u21d2  2\u00b7C_sab = {2*C_sab_val:.1f} mm\n\n'
        f'Barrel bore:  D_nom = {D_barrel_nom_val:.0f} mm,  tolerance = \u00b1{D_barrel_tol_val} mm\n'
        f'  D_barrel,min = {D_barrel_nom_val:.0f} \u2212 {D_barrel_tol_val} = {D_barrel_min_val:.1f} mm\n\n'
        f'Check:\n'
        f'  D_eq + 2\u00b7C_sab = {D_eq_val:.2f} + {2*C_sab_val:.1f} = {clearance_total:.2f} mm\n'
        f'  {clearance_total:.2f} mm  >  {D_barrel_min_val:.1f} mm\n'
        f'  \u21d2  INTERFERENCE by {clearance_total - D_barrel_min_val:.2f} mm if payload is free to rotate\n\n'
        f'The constraint FAILS without a sabot enforcing axial orientation.'
    )
    complete_doc.add_heading('9.3 Interpretation', level=2)
    complete_doc.add_paragraph(
        f'The payload diagonal ({D_eq_val:.2f} mm) exceeds the minimum bore ({D_barrel_min_val:.1f} mm) '
        f'by {clearance_total - D_barrel_min_val:.2f} mm. Unrestricted yaw or roll during '
        'loading or the firing stroke will cause the payload to jam. '
        'A close-fitting sabot that locks the payload in axial alignment is mandatory.'
    )
    complete_doc.add_heading('9.4 Design Requirements', level=2)
    req_p = complete_doc.add_paragraph()
    req_p.add_run('Requirement G-01:\n').bold = True
    req_p.add_run(
        'The sabot shall enforce axial alignment such that the effective payload envelope '
        'presented to the bore remains \u2264 D_barrel,min under all loading and firing conditions.\n\n'
    )
    req_p.add_run('Requirement G-02:\n').bold = True
    req_p.add_run(
        f'Total radial clearance (sabot OD to barrel ID) shall be 1.0\u20131.5 mm per side '
        'to prevent tilt-induced interference while maintaining acceptable bore friction '
        'and ease of manual loading.'
    )

    # â”€â”€ 10. FORMULA REFERENCE SUMMARY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    complete_doc.add_heading('10. Formula Reference Summary', level=1)
    formula_table_data = [
        ('Isothermal expansion work',
         'W = P\u2080\u00b7V\u2080\u00b7ln(P\u2080/Pf)',
         f'W = {W_ideal:.1f} J'),
        ('Bore cross-section area',
         'A = \u03c0(D/2)\u00b2',
         f'A = {barrel_area:.6f} m\u00b2  ({barrel_area*1e4:.4f} cm\u00b2)'),
        ('Ideal muzzle velocity (theoretical)',
         'v = \u221a(2\u03b7W/m)',
         f'e.g. \u03b7=50%, m=1 kg \u21d2 {math.sqrt(2*0.5*W_ideal/1.0):.1f} m/s'),
        ('Real-gas pressure (RK EOS)',
         'P = Z(P,T)\u00b7(m/V)\u00b7R_u\u00b7T/M',
         f'Z \u2248 0.97 for CO\u2082 at 11 bar, 20 \u00b0C'),
        ('Hoop stress (thin-wall)',
         '\u03c3_hoop = P\u00b7r/t',
         f't=3 mm \u21d2 \u03c3 = {P0_abs*r_barrel/0.003/1e6:.1f} MPa'),
        ('Minimum wall thickness',
         't_min = P\u00b7r\u00b7SF/\u03c3_yield',
         f't_min = {t_req_hoop*1e3:.3f} mm  (SF={safety_factor:.0f})'),
        ('Axial stress (thin-wall)',
         '\u03c3_axial = P\u00b7r/(2t)  =  \u00bd\u03c3_hoop',
         'Non-governing'),
        ('Endcap axial bolt load',
         'F_endcap = P\u2080\u00b7A_bore',
         f'F = {P0_abs*barrel_area:.1f} N'),
        ('Bolt shear capacity',
         'F_cap = \u03c0(d/2)\u00b2\u00b7\u03c4_shear',
         f'M8: {F_cap_M8:.1f} N per bolt'),
        ('Critical pressure ratio',
         'r_crit = (2/(\u03b3+1))^(\u03b3/(\u03b3\u22121))',
         f'{critical_ratio:.4f}  (\u03b3=1.3)'),
        ('Choked mass flow rate',
         '\u1e41 = Cd\u00b7A\u00b7Pc\u00b7\u221a(\u03b3/(R\u00b7T))\u00b7(2/(\u03b3+1))^((\u03b3+1)/(2(\u03b3-1)))',
         f'\u1e41\u2080 = {mdot_choked_t0:.4f} kg/s at t=0'),
        ('Impulse',
         'I = m\u00b7v_exit = \u222bF_net dt',
         f'{sim["impulse"]:.3f} N\u00b7s'),
        ('Average propulsion force',
         'F_avg = I / t_discharge',
         f'{sim["avg_F"]:.1f} N'),
        ('Diagonal payload envelope',
         'D_eq = \u221a(W\u00b2 + H\u00b2)',
         f'{D_eq_val:.2f} mm  (W=40, H=45 mm)'),
        ('Launch efficiency',
         '\u03b7 = \u00bdmv\u00b2 / W_ideal',
         f'{sim_ke/W_ideal*100:.2f}%  (1 kg payload, ODE sim)'),
    ]
    f_table = complete_doc.add_table(rows=1, cols=3)
    fh_cells = f_table.rows[0].cells
    fh_cells[0].text = 'Quantity'
    fh_cells[1].text = 'Formula'
    fh_cells[2].text = 'Numerical result'
    for fr_row in formula_table_data:
        rc = f_table.add_row().cells
        rc[0].text = fr_row[0]; rc[1].text = fr_row[1]; rc[2].text = fr_row[2]

    complete_doc.add_paragraph(
        f'\nConclusion:\n'
        f'The 52 mm \u00d7 700 mm pneumatic launcher charged to {P0_gauge_bar:.0f} bar gauge '
        f'with {V0*1e3:.0f} mL of CO\u2082 can accelerate a 1 kg payload to '
        f'{sim["muzzle_v"]:.1f} m/s in {sim["t_end"]*1e3:.0f} ms (launch efficiency '
        f'{sim_ke/W_ideal*100:.1f}%). '
        f'A 3 mm 6061-T6 barrel wall gives SF = '
        f'{mat_yield/(P0_abs*r_barrel/0.003):.1f} vs yield. '
        f'Six M8 flange bolts give SF = {SF_6xM8:.1f} on the static endcap load. '
        f'The 40\u00d745 mm rectangular payload requires a sabot to prevent bore interference '
        f'(diagonal envelope 60.2 mm exceeds 52 mm bore by 8.2 mm when misaligned).'
    )

    complete_path = os.path.join(DOCS_DIR, 'pneumatic_launcher_analysis_complete.docx')
    try:
        complete_doc.save(complete_path)
    except PermissionError:
        tmp_path = complete_path + '.tmp'
        try:
            complete_doc.save(tmp_path)
            os.replace(tmp_path, complete_path)
        except Exception:
            pass

    # Remove intermediate doc files
    try:
        for fname in os.listdir(DOCS_DIR):
            if ((fname.lower().endswith('.docx') and fname != os.path.basename(complete_path))
                    or fname.lower().endswith('.tmp')):
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
