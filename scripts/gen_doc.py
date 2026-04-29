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
    'V0_m3': V0,
    'barrel_area_m2': barrel_area,
    'barrel_length_m': barrel_length,
    'sim_muzzle_v_ms': sim['muzzle_v'],
    'sim_impulse_Ns': sim['impulse'],
    'sim_t_end_s': sim['t_end'],
    'sim_peak_F_N': sim['peak_F'],
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

# ---- Generate complete analysis document via pandoc ----
try:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        'gen_doc_pandoc', os.path.join(BASE_DIR, 'gen_doc_pandoc.py'))
    _pandoc = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_pandoc)
    _pandoc.main()
    complete_path = _pandoc.DOCX_OUT
except Exception:
    import traceback
    traceback.print_exc()
    complete_path = None
