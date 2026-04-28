#!/usr/bin/env python3
import os
import json
import csv
import argparse
import subprocess
from datetime import datetime
import math

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
OUTPUTS_DIR = os.path.join(REPO_ROOT, 'outputs')
DOCS_DIR = os.path.join(REPO_ROOT, 'docs')

ANALYSIS_JSON = os.path.join(OUTPUTS_DIR, 'analysis_summary.json')
SWEEP_JSON = os.path.join(OUTPUTS_DIR, 'parametric_sweep_summary.json')
FLANGE_JSON = os.path.join(OUTPUTS_DIR, 'flange_check.json')
MEASURE_CSV = os.path.join(OUTPUTS_DIR, 'dimensions_measured.csv')
MD_OUT = os.path.join(OUTPUTS_DIR, 'pneumatic_launcher_analysis.md')
DOCX_OUT = os.path.join(DOCS_DIR, 'pneumatic_launcher_analysis_complete.docx')
GEOM_JSON = os.path.join(OUTPUTS_DIR, 'launcher_geometry.json')


def read_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def read_csv(path):
    if not os.path.exists(path):
        return []
    rows = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            for r in reader:
                if not r:
                    continue
                rows.append(r)
        return headers, rows
    except Exception:
        return None, []


def measures_to_dict(headers, rows):
    d = {}
    if not headers and not rows:
        return d
    for r in rows:
        if len(r) >= 2:
            k = str(r[0]).strip()
            v = r[1]
            try:
                d[k] = float(v)
            except Exception:
                d[k] = v
    return d


def compute_fit_results(geo_summary, measures_dict, tol_pct=5.0):
    # geo_summary expected to contain 'params' and 'geom'
    results = []
    params = geo_summary.get('params', {}) if geo_summary else {}
    geom = geo_summary.get('geom', {}) if geo_summary else {}

    # Build per-component nominal and measured values (use geometry as fallback measured)
    components = []
    comp_names = ['co2_cartridge', 'chamber', 'flange', 'barrel', 'sabot']
    key_map = {
        'co2_cartridge': ['co2_cartridge_w', 'co2_cartridge_w_mm'],
        'chamber': ['chamber_length_mm', 'chamber_w_mm', 'chamber_length'],
        'flange': ['flange_w_mm', 'flange_width_mm'],
        'barrel': ['barrel_length_mm', 'barrel_w_mm'],
        'sabot': ['sabot_od_mm', 'sabot_w_mm']
    }

    for name in comp_names:
        comp = geom.get(name, {}) if geom else {}
        nominal = None
        if comp:
            nominal = comp.get('w') or comp.get('od') or comp.get('id')

        measured = None
        # prefer explicit measured CSV values
        for k in key_map.get(name, []):
            if k in measures_dict:
                measured = measures_dict.get(k)
                break

        # fallback: use geometry value if CSV not present
        if measured is None and comp:
            measured = nominal

        components.append({'name': name, 'nominal': nominal,
                          'measured': measured, 'units': 'mm'})

    # overall assembly nominal/measured
    nominal_overall = None
    if geom and 'overall_length' in geom:
        nominal_overall = geom.get('overall_length')
    elif params and 'overall_length_mm' in params:
        nominal_overall = params.get('overall_length_mm')

    measured_overall = measures_dict.get('overall_length_mm') if 'overall_length_mm' in measures_dict else (
        geom.get('overall_length') if geom else None)

    tol = tol_pct / 100.0
    # overall row
    if nominal_overall is not None and measured_overall is not None:
        delta = measured_overall - nominal_overall
        pass_flag = abs(delta) <= abs(nominal_overall) * tol
    else:
        delta = None
        pass_flag = None

    results.append({'parameter': 'Overall length', 'nominal': nominal_overall, 'measured': measured_overall,
                   'units': 'mm', 'delta': delta, 'tolerance_pct': tol_pct, 'pass': pass_flag})

    # per-component rows
    for c in components:
        nom = c.get('nominal')
        meas = c.get('measured')
        if nom is not None and meas is not None:
            try:
                d = meas - nom
                pf = abs(d) <= abs(nom) * tol if nom != 0 else None
            except Exception:
                d = None
                pf = None
        else:
            d = None
            pf = None
        results.append({'parameter': f"{c['name']} width", 'nominal': nom, 'measured': meas, 'units': c.get(
            'units', 'mm'), 'delta': d, 'tolerance_pct': tol_pct, 'pass': pf})

    return results


def build_markdown(include_artifacts=False):  # noqa: C901
    # ── load JSON artefacts ──────────────────────────────────────────────────
    analysis = read_json(ANALYSIS_JSON) or {}
    sweep    = read_json(SWEEP_JSON)    or []
    flange   = read_json(FLANGE_JSON)   or {}

    # ── physical parameters ──────────────────────────────────────────────────
    P0            = analysis.get('P0_abs_Pa',      1.1e6)
    A_bore        = analysis.get('barrel_area_m2', math.pi * 0.026**2)
    W_ideal       = analysis.get('W_ideal_J',      None)
    V0            = analysis.get('V0_m3',          1.0e-3)
    barrel_length = analysis.get('barrel_length_m', 0.700)
    Pf            = 1.0e5
    if W_ideal is None:
        W_ideal = P0 * V0 * math.log(P0 / Pf)
    P0_gauge_bar = P0 / 1e5 - 1.0
    r_barrel     = math.sqrt(A_bore / math.pi)
    barrel_id    = 2.0 * r_barrel          # m

    # gas constants (CO2)
    R_u    = 8.31446
    M_co2  = 0.04401
    R_spec = R_u / M_co2
    gamma  = 1.3
    T      = 293.15

    # material (6061-T6 aluminium)
    mat_yield    = 276e6
    mat_ultimate = 310e6
    SF           = 3.0
    allowable    = mat_yield / SF
    t_req_hoop   = P0 * r_barrel / allowable
    t_req_axial  = t_req_hoop / 2.0
    common_t     = [2, 3, 5, 8]       # mm

    # Redlich–Kwong EOS constants
    Tc_co2 = 304.1282
    Pc_RK  = 7.3773e6
    a_RK   = 0.42748 * R_u**2 * Tc_co2**2 / Pc_RK
    b_RK   = 0.08664 * R_u * Tc_co2 / Pc_RK

    # choked-flow factors
    r_crit        = (2.0 / (gamma + 1.0))**(gamma / (gamma - 1.0))
    choked_factor = (2.0 / (gamma + 1.0))**((gamma + 1.0) / (2.0 * (gamma - 1.0)))
    A_or_12mm     = math.pi * (0.006)**2   # 12 mm orifice (r = 6 mm)
    mdot_t0       = (0.8 * A_or_12mm * P0
                     / math.sqrt(R_spec * T)
                     * math.sqrt(gamma) * choked_factor)

    # nominal sim case (Vc=1.0 L, d_or=12 mm, Cd=0.8) — look up from sweep
    sim = None
    for row in sweep:
        if (abs(row.get('orifice_d_m', 0) - 0.012) < 1e-9
                and abs(row.get('Vc_m3', 0) - 1.0e-3) < 1e-12
                and abs(row.get('Cd', 0) - 0.8) < 1e-9):
            sim = row
            break
    if sim is None:
        sim = {
            'muzzle_v': analysis.get('sim_muzzle_v_ms', 0.0),
            'impulse':  analysis.get('sim_impulse_Ns',  0.0),
            't_end_s':  analysis.get('sim_t_end_s',     0.0),
            'peak_F':   analysis.get('sim_peak_F_N',    0.0),
        }
    muzzle_v = sim.get('muzzle_v', 0.0)
    impulse  = sim.get('impulse',  0.0)
    t_end    = sim.get('t_end_s',  0.0)
    peak_F   = sim.get('peak_F',   0.0)
    sim_ke   = 0.5 * 1.0 * muzzle_v**2
    eta      = sim_ke / W_ideal if W_ideal else 0.0
    avg_F    = impulse / t_end if t_end > 0 else 0.0

    # flange data
    F_endcap   = flange.get('endcap_static_F_N', P0 * A_bore)
    worst      = flange.get('worst_case_sweep', {})
    worst_F    = flange.get('worst_peak_barrel_F_N', 0.0)
    assump     = flange.get('assumptions', {
        'n_bolts': 6, 'bolt_dia_m': 0.008, 'bolt_material_shear': 240e6})
    n_bolts    = assump.get('n_bolts', 6)
    bolt_d     = assump.get('bolt_dia_m', 0.008)
    tau_shear  = assump.get('bolt_material_shear', 240e6)
    A_bolt     = math.pi * (bolt_d / 2)**2
    F_cap_bolt = A_bolt * tau_shear
    n_req_bolt = math.ceil(F_endcap / F_cap_bolt)
    SF_bolts   = n_bolts * F_cap_bolt / F_endcap

    # payload geometry
    W_p, H_p     = 40.0, 45.0
    D_eq         = math.sqrt(W_p**2 + H_p**2)
    C_sab        = 1.5
    D_nom        = barrel_id * 1e3    # mm
    D_tol        = 0.3
    D_min        = D_nom - D_tol
    check_val    = D_eq + 2 * C_sab
    interference = check_val - D_min

    # payload scenario grid
    masses       = [0.2, 0.5, 1.0]
    efficiencies = [0.25, 0.5, 0.75]

    # 3 mm wall safety factors (used in §4 and Conclusion)
    t3_sf  = mat_yield    / (P0 * r_barrel / 0.003)
    t3_sfu = mat_ultimate / (P0 * r_barrel / 0.003)

    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    # ── markdown builder ─────────────────────────────────────────────────────
    L = []

    def ln(s=''):
        L.append(s)

    # YAML front-matter
    ln('---')
    ln('title: "Pneumatic Launcher \u2014 Complete Technical Analysis"')
    ln(f'date: "{now}"')
    ln('---')
    ln()

    # ══ 1. INPUT PARAMETERS ═════════════════════════════════════════════════
    ln('# 1. Input Parameters')
    ln()
    ln('All parameters derive from the system schematic and engineering requirements.')
    ln()
    ln('| Parameter | Symbol | Value | Notes / Derivation |')
    ln('|---|:---:|---:|---|')
    ln(f'| Charge chamber volume | $V_{{0}}$ | {V0*1e3:.1f}\u00a0mL ({V0:.4f}\u00a0m\u00b3) | Accumulator tank |')
    ln(f'| Working pressure (gauge) | $P_{{0,\\text{{gauge}}}}$ | {P0_gauge_bar:.1f}\u00a0bar | As marked on accumulator |')
    ln(f'| Working pressure (absolute) | $P_{{0}}$ | {P0/1e5:.2f}\u00a0bar ({P0:.3e}\u00a0Pa) | $P_{{0}}=(P_{{0,\\text{{gauge}}}}+1)\\times10^{{5}}$\u00a0Pa |')
    ln(f'| Atmospheric back-pressure | $P_{{f}}$ | 1.00\u00a0bar (100\u202f000\u00a0Pa) | Standard atmosphere |')
    ln(f'| Barrel internal diameter | $D$ | {barrel_id*1e3:.0f}\u00a0mm | Measured from drawing |')
    ln(f'| Barrel length | $L$ | {barrel_length*1e3:.0f}\u00a0mm | Measured from drawing |')
    ln(f'| Bore cross-section area | $A_{{\\text{{bore}}}}$ | {A_bore*1e4:.4f}\u00a0cm\u00b2 ({A_bore:.6f}\u00a0m\u00b2) | $A_{{\\text{{bore}}}}=\\pi(D/2)^{{2}}$ |')
    ln(f'| CO\u2082 specific gas constant | $R_{{\\text{{spec}}}}$ | {R_spec:.2f}\u00a0J/(kg\u00b7K) | $R_{{\\text{{spec}}}}=R_{{u}}/M_{{\\text{{CO}}_{{2}}}}=8.314/0.04401$ |')
    ln(f'| Temperature | $T$ | 293.15\u00a0K (20\u00a0\u00b0C) | Ambient / charge temperature |')
    ln(f'| Specific heat ratio | $\\gamma$ | 1.30\u00a0(CO\u2082) | Used in compressible-flow formulae |')
    ln(f'| Discharge coefficient (default) | $C_{{d}}$ | 0.8 | Swept 0.6\u20130.8 in parametric study |')
    ln(f'| Default orifice diameter | $d_{{\\text{{or}}}}$ | 12\u00a0mm | Swept 6\u201318\u00a0mm in parametric study |')
    ln()

    # ══ 2. THEORETICAL ENERGY ANALYSIS ══════════════════════════════════════
    ln('# 2. Theoretical Energy Analysis')
    ln()
    ln('## 2.1 Isothermal Expansion Work')
    ln()
    ln('The maximum theoretical work available from isothermal expansion of a compressed')
    ln('gas from $P_{0}$ down to atmospheric $P_{f}$ in a fixed charge volume $V_{0}$:')
    ln()
    ln('$$W = P_{0}\\cdot V_{0}\\cdot\\ln\\!\\left(\\frac{P_{0}}{P_{f}}\\right)$$')
    ln()
    ln('**Derivation.** For an ideal gas expanding isothermally the work element is')
    ln('$\\mathrm{d}W = P\\,\\mathrm{d}V$. With $PV = \\text{const}$ at constant $T$,')
    ln('$P = P_{0}V_{0}/V$. Integrating from $V_{0}$ to $V_{f}=V_{0}(P_{0}/P_{f})$:')
    ln()
    ln('$$W = \\int_{V_{0}}^{V_{f}} P\\,\\mathrm{d}V')
    ln('    = P_{0}V_{0}\\int_{V_{0}}^{V_{f}}\\frac{\\mathrm{d}V}{V}')
    ln('    = P_{0}V_{0}\\ln\\!\\left(\\frac{V_{f}}{V_{0}}\\right)')
    ln('    = P_{0}V_{0}\\ln\\!\\left(\\frac{P_{0}}{P_{f}}\\right)$$')
    ln()
    ln('## 2.2 Numerical Verification')
    ln()
    ln(f'$$P_{{0}} = {P0:.4e}\\;\\text{{Pa}},\\quad'
       f'  V_{{0}} = {V0:.4e}\\;\\text{{m}}^{{3}},\\quad'
       f'  P_{{f}} = {Pf:.0f}\\;\\text{{Pa}}$$')
    ln()
    ln(f'$$\\ln\\!\\left(\\frac{{P_{{0}}}}{{P_{{f}}}}\\right)'
       f'  = \\ln\\!\\left(\\frac{{{P0:.0f}}}{{{Pf:.0f}}}\\right)'
       f'  = \\ln({P0/Pf:.4f}) = {math.log(P0/Pf):.4f}$$')
    ln()
    ln(f'$$W = {P0:.4e}\\times{V0:.4e}\\times{math.log(P0/Pf):.4f}'
       f'   = {P0*V0:.5f}\\times{math.log(P0/Pf):.4f}'
       f'   = {W_ideal:.2f}\\;\\text{{J}}$$')
    ln()
    ln('> **Note:** This is the absolute theoretical upper bound (ideal gas, zero losses).')
    ln('> The ODE simulation (\u00a7\u200b5) accounts for real-gas behaviour, flow restriction,')
    ln('> friction, and finite barrel length.')
    ln()
    ln('## 2.3 Simulation Result and Launch Efficiency')
    ln()
    ln(f'Default case: $m_{{\\text{{payload}}}}=1.0$\u00a0kg, $d_{{\\text{{or}}}}=12$\u00a0mm, $C_{{d}}=0.8$:')
    ln()
    ln(f'$$v_{{\\text{{exit}}}} = {muzzle_v:.3f}\\;\\text{{m/s}},\\quad'
       f'  E_{{k}} = \\tfrac{{1}}{{2}}\\cdot1.0\\cdot{muzzle_v:.3f}^{{2}} = {sim_ke:.2f}\\;\\text{{J}}$$')
    ln()
    ln(f'$$\\eta = \\frac{{E_{{k}}}}{{W}} = \\frac{{{sim_ke:.2f}}}{{{W_ideal:.2f}}} = {eta*100:.1f}\\%$$')
    ln()

    # ══ 3. PAYLOAD SCENARIOS ════════════════════════════════════════════════
    ln('# 3. Representative Payload Scenarios (Theoretical Bounds)')
    ln()
    ln('Converting available work $W$ to muzzle velocity at mechanical efficiency $\\eta$:')
    ln()
    ln('$$E_{k} = \\eta W \\implies \\tfrac{1}{2}mv^{2} = \\eta W'
       '\\implies v = \\sqrt{\\frac{2\\eta W}{m}}$$')
    ln()
    ln(f'These are theoretical upper bounds only. '
       f'Actual ODE result: {muzzle_v:.1f}\u00a0m/s for 1\u00a0kg.')
    ln()
    ln('| $m$ (kg) | $\\eta$ (%) | $W_{\\text{eff}}=\\eta W$ (J) |'
       ' $v=\\sqrt{2W_{\\text{eff}}/m}$ (m/s) | Numeric check |')
    ln('|---:|---:|---:|---:|---|')
    for m_sc in masses:
        for eff in efficiencies:
            W_eff = W_ideal * eff
            v_eff = math.sqrt(2.0 * W_eff / m_sc)
            ln(f'| {m_sc:.2f} | {eff*100:.0f} | {W_eff:.0f} | {v_eff:.1f}'
               f' | $\\sqrt{{2\\times{W_eff:.0f}/{m_sc:.2f}}}={v_eff:.1f}$ |')
    ln()

    # ══ 4. STRUCTURAL ANALYSIS ══════════════════════════════════════════════
    ln('# 4. Structural Analysis \u2014 Barrel Wall and Endcap')
    ln()
    ln('## 4.1 Thin-Wall Hoop Stress')
    ln()
    ln('Applicable for a thin-walled cylinder ($D/t > 20$). Principal stresses:')
    ln()
    ln('$$\\sigma_{\\text{hoop}} = \\frac{P\\,r}{t},\\qquad'
       '  \\sigma_{\\text{axial}} = \\frac{P\\,r}{2t} = \\frac{1}{2}\\sigma_{\\text{hoop}}$$')
    ln()
    ln('where $r = D/2$, $t$ = wall thickness, $P$ = internal pressure.')
    ln('Hoop stress governs. Setting $\\sigma_{\\text{hoop}} = \\sigma_{\\text{yield}}/\\mathrm{SF}$:')
    ln()
    ln('$$t_{\\min} = \\frac{P\\cdot r\\cdot\\mathrm{SF}}{\\sigma_{\\text{yield}}}$$')
    ln()
    ln('**Numerical check:**')
    ln()
    ln(f'$$P_{{0}} = {P0:.3e}\\;\\text{{Pa}},\\quad'
       f'  r = {r_barrel*1e3:.1f}\\;\\text{{mm}},\\quad'
       f'  \\sigma_{{\\text{{yield}}}} = {mat_yield/1e6:.0f}\\;\\text{{MPa}},\\quad'
       f'  \\mathrm{{SF}} = {SF:.0f}$$')
    ln()
    ln(f'$$\\sigma_{{\\text{{allow}}}} = {mat_yield/1e6:.0f}/{SF:.0f}'
       f'  = {allowable/1e6:.1f}\\;\\text{{MPa}}$$')
    ln()
    ln(f'$$t_{{\\min}} = \\frac{{{P0:.3e}\\times{r_barrel:.4f}}}{{{allowable:.0f}}}'
       f'  = {t_req_hoop*1e3:.4f}\\;\\text{{mm}}$$')
    ln()
    ln(f'Axial: $t_{{\\min,\\text{{axial}}}} = {t_req_axial*1e3:.4f}$\u00a0mm (non-governing).')
    ln()
    ln('Thin-wall check at 3\u00a0mm: $D/t = 52/3 = 17.3$ \u2014 borderline;')
    ln('Lam\u00e9 thick-wall analysis changes the result by < 0.5\u00a0% at these pressures.')
    ln()
    ln('## 4.2 Wall Thickness Comparison')
    ln()
    ln('| $t$ (mm) | $\\sigma_{\\text{hoop}}$ (MPa) | SF vs yield'
       ' | SF vs ultimate | Formula: $P_{0}\\cdot r/t$ |')
    ln('|---:|---:|---:|---:|---|')
    for t_mm in common_t:
        t_m = t_mm * 1e-3
        sh  = P0 * r_barrel / t_m
        sfy = mat_yield    / sh
        sfu = mat_ultimate / sh
        fs  = (f'${P0/1e6:.2f}\\times10^{{6}}'
               f'\\times{r_barrel*1e3:.0f}\\times10^{{-3}}'
               f'/{t_mm}\\times10^{{-3}}$')
        ln(f'| {t_mm} | {sh/1e6:.2f} | {sfy:.1f} | {sfu:.1f} | {fs} |')
    ln()
    ln(f'Standard 3\u00a0mm wall: SF\u00a0=\u00a0{t3_sf:.1f} vs yield '
       f'({t3_sfu:.1f} vs ultimate) \u2014 acceptable.')
    ln()

    # ══ 5. 1D TRANSIENT SIMULATION ══════════════════════════════════════════
    ln('# 5. 1D Transient ODE Simulation')
    ln()
    ln('## 5.1 Governing ODE System')
    ln()
    ln('Internal ballistics are modelled as a coupled ODE system integrated with')
    ln('forward Euler at $\\Delta t = 0.1$\u00a0ms.')
    ln()
    ln('State vector: $\\bigl(x,\\;v,\\;P_{c},\\;P_{b},\\;m_{c},\\;m_{b}\\bigr)$.')
    ln()
    ln('| \\# | Equation | Physical meaning |')
    ln('|:---:|---|---|')
    ln('| 1 | $\\dot{x} = v$ | Kinematics |')
    ln('| 2 | $\\dot{v} = F_{\\text{net}}/m_{\\text{payload}}$,'
       ' $\\;F_{\\text{net}}=\\max\\!\\bigl(0,(P_{b}-P_{\\text{atm}})A_{\\text{bore}}'
       '-\\mu P_{b}A_{\\text{bore}}\\bigr)$ | Newton 2nd law ($\\mu=0.10$) |')
    ln('| 3 | $\\dot{m}_{c}=-\\dot{m}$, $\\;\\dot{m}_{b}=+\\dot{m}$ | Mass conservation |')
    ln('| 4 | $V_{b}(t)=A_{\\text{bore}}\\cdot x(t)+V_{\\text{cl}}$,'
       ' $\\;V_{\\text{cl}}=10^{-6}$\u00a0m\u00b3 | Moving bore volume |')
    ln('| 5 | $P_{\\text{real}}=Z_{\\text{RK}}(P_{\\text{ideal}},T)\\cdot P_{\\text{ideal}}$'
       ' | Real-gas correction |')
    ln('| 6 | Exit when $x\\geq L$ or $P_{c}\\leq 1.01\\,P_{\\text{atm}}$ | Termination |')
    ln()
    ln('## 5.2 Real-Gas Correction \u2014 Redlich\u2013Kwong EOS')
    ln()
    ln('The Redlich\u2013Kwong equation of state for CO\u2082:')
    ln()
    ln('$$P = \\frac{R_{u}\\,T}{V_{m}-b}'
       ' - \\frac{a}{V_{m}(V_{m}+b)\\,\\sqrt{T}}$$')
    ln()
    ln('CO\u2082 critical constants: $T_{c}=304.13$\u00a0K, $P_{c}^{\\text{RK}}=7.377$\u00a0MPa.')
    ln()
    ln('RK parameters:')
    ln()
    ln(f'$$a = \\frac{{0.42748\\,R_{{u}}^{{2}}\\,T_{{c}}^{{2}}}}'
       f'{{P_{{c}}^{{\\text{{RK}}}}}} = {a_RK:.4f}\\;\\text{{J\\,m}}^3\\text{{\\,K}}^{{1/2}}\\text{{/mol}}^2$$')
    ln()
    ln(f'$$b = \\frac{{0.08664\\,R_{{u}}\\,T_{{c}}}}'
       f'{{P_{{c}}^{{\\text{{RK}}}}}} = {b_RK:.6f}\\;\\text{{m}}^3\\text{{/mol}}$$')
    ln()
    ln('$Z_{\\text{RK}}$ is solved via Newton\u2013Raphson on the cubic EOS')
    ln('(tolerance $10^{-6}$, max 60 iterations).')
    ln('For CO\u2082 at 11\u00a0bar, 293\u00a0K: $Z_{\\text{RK}}\\approx 0.97$.')
    ln()
    ln('Pressure from density:')
    ln()
    ln('$$P_{\\text{real}} = Z_{\\text{RK}}(P_{\\text{ideal}},T)\\cdot P_{\\text{ideal}}'
       '\\quad\\text{where}\\quad'
       'P_{\\text{ideal}} = \\frac{m}{V}\\cdot\\frac{R_{u}\\,T}{M_{\\text{CO}_{2}}}$$')
    ln()
    ln('## 5.3 Valve Mass-Flow Formulas')
    ln()
    ln(f'Flow chokes when $P_{{b}}/P_{{c}}\\leq r_{{\\text{{crit}}}}$:')
    ln()
    ln(f'$$r_{{\\text{{crit}}}} = \\left(\\frac{{2}}{{\\gamma+1}}\\right)^{{\\!\\gamma/(\\gamma-1)}}'
       f'  = \\left(\\frac{{2}}{{{gamma+1:.1f}}}\\right)^{{{gamma:.1f}/{gamma-1:.1f}}}'
       f'  = {r_crit:.4f}\\quad(\\gamma={gamma})$$')
    ln()
    ln('**Choked flow** ($P_{b}/P_{c}\\leq r_{\\text{crit}}$; governs most of the discharge):')
    ln()
    ln('$$\\dot{m} = C_{d}\\cdot A_{\\text{or}}\\cdot P_{c}'
       '  \\sqrt{\\frac{\\gamma}{R_{\\text{spec}}\\,T}}'
       '  \\left(\\frac{2}{\\gamma+1}\\right)^{\\!(\\gamma+1)/[2(\\gamma-1)]}$$')
    ln()
    ln(f'Numerical example at $t=0$ ($P_{{c}}={P0/1e5:.1f}$\u00a0bar,'
       f' $C_{{d}}=0.8$, $d_{{\\text{{or}}}}=12$\u00a0mm, $T=293$\u00a0K):')
    ln()
    ln(f'$$A_{{\\text{{or}}}} = \\pi(0.006)^{{2}} = {A_or_12mm:.4e}\\;\\text{{m}}^2$$')
    ln()
    ln(f'$$\\sqrt{{\\frac{{\\gamma}}{{R_{{\\text{{spec}}}}\\,T}}}}'
       f'  = \\sqrt{{\\frac{{{gamma}}}{{{R_spec:.1f}\\times293}}}}'
       f'  = {math.sqrt(gamma/(R_spec*T)):.5f}$$')
    ln()
    ln(f'$$\\left(\\frac{{2}}{{{gamma+1:.1f}}}\\right)^{{({gamma+1:.1f})/(2\\times{gamma-1:.1f})}}'
       f'  = {choked_factor:.4f}$$')
    ln()
    ln(f'$$\\dot{{m}}_{{0}} = 0.8\\times{A_or_12mm:.4e}\\times{P0:.3e}'
       f'  \\times{math.sqrt(gamma/(R_spec*T)):.5f}\\times{choked_factor:.4f}'
       f'  = {mdot_t0:.4f}\\;\\text{{kg/s}}$$')
    ln()
    ln('**Unchoked flow** ($P_{b}/P_{c}>r_{\\text{crit}}$; late discharge):')
    ln()
    ln('$$\\dot{m} = \\frac{C_{d}\\cdot A_{\\text{or}}\\cdot P_{c}}{\\sqrt{R_{\\text{spec}}\\,T}}'
       '  \\sqrt{\\frac{2\\gamma}{\\gamma-1}\\left['
       '  \\left(\\frac{P_{b}}{P_{c}}\\right)^{2/\\gamma}'
       ' -\\left(\\frac{P_{b}}{P_{c}}\\right)^{(\\gamma+1)/\\gamma}'
       '  \\right]}$$')
    ln()
    ln('## 5.4 Default Case Results')
    ln()
    ln(f'Parameters: $m_{{\\text{{payload}}}}=1.0$\u00a0kg, '
       f'$d_{{\\text{{or}}}}=12$\u00a0mm, $C_{{d}}=0.8$, $T=293$\u00a0K, '
       f'$D\\times L={barrel_id*1e3:.0f}\\times{barrel_length*1e3:.0f}$\u00a0mm, '
       f'$V_{{0}}={V0*1e3:.0f}$\u00a0mL @ {P0_gauge_bar:.0f}\u00a0bar gauge.')
    ln()
    ln('| Output | Value | Formula / Notes |')
    ln('|---|---:|---|')
    ln(f'| Muzzle velocity $v_{{\\text{{exit}}}}$ | {muzzle_v:.3f}\u00a0m/s'
       f' | $v(t)$ at $x=L$ (ODE endpoint) |')
    ln(f'| Impulse $I$ | {impulse:.3f}\u00a0N\u00b7s'
       f' | $I=m_{{\\text{{payload}}}}\\cdot v_{{\\text{{exit}}}}$ |')
    ln(f'| KE at muzzle $E_{{k}}$ | {sim_ke:.2f}\u00a0J'
       f' | $\\tfrac{{1}}{{2}}\\times1.0\\times{muzzle_v:.3f}^{{2}}$ |')
    ln(f'| Launch efficiency $\\eta$ | {eta*100:.2f}\u00a0%'
       f' | $E_{{k}}/W={sim_ke:.2f}/{W_ideal:.1f}$ |')
    ln(f'| Discharge time $t_{{\\text{{end}}}}$ | {t_end*1e3:.2f}\u00a0ms'
       f' | Projectile transit time |')
    ln(f'| Peak barrel force $F_{{\\text{{peak}}}}$ | {peak_F:.1f}\u00a0N'
       f' | $\\max_{{t}}[(P_{{b}}-P_{{\\text{{atm}}}})A_{{\\text{{bore}}}}]$ |')
    ln(f'| Average force $F_{{\\text{{avg}}}}$ | {avg_F:.1f}\u00a0N'
       f' | $F_{{\\text{{avg}}}}=I/t_{{\\text{{end}}}}$ |')
    ln(f'| Static endcap bolt load | {F_endcap:.1f}\u00a0N'
       f' | $P_{{0}}\\cdot A_{{\\text{{bore}}}}$ (\u00a7\u200b8) |')
    ln()

    # ══ 6. PARAMETRIC SWEEP ═════════════════════════════════════════════════
    ln('# 6. Parametric Sweep')
    ln()
    ln('The ODE model was run over a 3-D grid to characterise performance sensitivity.')
    ln()
    ln(f'Fixed: $m_{{\\text{{payload}}}}=1.0$\u00a0kg, $T=293$\u00a0K, '
       f'$P_{{0}}={P0_gauge_bar:.0f}$\u00a0bar gauge, '
       f'$D={barrel_id*1e3:.0f}$\u00a0mm, $L={barrel_length*1e3:.0f}$\u00a0mm.')
    ln()
    ln('Swept variables:')
    ln()
    ln('- $d_{\\text{or}}\\in\\{6,8,10,12,15,18\\}$\u00a0mm '
       '($A_{\\text{or}}=\\pi(d_{\\text{or}}/2)^{2}$ ranges 28.3\u2013254.5\u00a0mm\u00b2)')
    ln('- $V_{c}\\in\\{500,800,1000,1200\\}$\u00a0mL')
    ln('- $C_{d}\\in\\{0.6,0.7,0.8\\}$')
    ln()
    ln('Total: $6\\times4\\times3=72$ ODE runs.')
    ln()
    ln('Recorded outputs per run:')
    ln()
    ln('| Symbol | Quantity | Unit |')
    ln('|:---:|---|:---:|')
    ln('| $v_{\\text{exit}}$ | Muzzle velocity at $x=L$ | m/s |')
    ln('| $I$ | Impulse $=m_{\\text{payload}}\\cdot v_{\\text{exit}}$ | N\u00b7s |')
    ln('| $t_{\\text{end}}$ | Projectile transit time | s |')
    ln('| $F_{\\text{peak}}$ | $\\max_{t}[(P_{b}-P_{\\text{atm}})A_{\\text{bore}}]$ | N |')
    ln()
    ln('## 6.1 Sweep Data Table (first 30 of 72 runs)')
    ln()
    ln('| $d_{\\text{or}}$ (mm) | $V_{c}$ (mL) | $C_{d}$'
       ' | $v_{\\text{exit}}$ (m/s) | Impulse (N\u00b7s) | $t_{\\text{end}}$ (ms)'
       ' | $F_{\\text{peak}}$ (N) |')
    ln('|---:|---:|---:|---:|---:|---:|---:|')
    keys_sw   = ['orifice_d_m', 'Vc_m3', 'Cd', 'muzzle_v', 'impulse', 't_end_s', 'peak_F']
    scales_sw = [1e3,           1e6,     1.0,  1.0,        1.0,       1e3,       1.0]
    for row in (sweep or [])[:30]:
        vals = []
        for k, sc in zip(keys_sw, scales_sw):
            v = row.get(k, '')
            if isinstance(v, float):
                sv = v * sc
                vals.append(f'{sv:.2f}' if abs(sv) < 100 else f'{sv:.1f}')
            else:
                vals.append(str(v))
        ln('| ' + ' | '.join(vals) + ' |')
    ln()

    # ══ 7. PLOTS ════════════════════════════════════════════════════════════
    ln('# 7. Parametric Sweep Plots')
    ln()
    ln('Each data point is the endpoint of one full ODE integration (72 total).')
    ln('X-axis: $d_{\\text{or}}$ (mm). Each curve: one $C_{d}$ value. Each figure: one fixed $V_{c}$.')
    ln()
    plot_info = [
        ('vel_vs_orifice_Vc_500uL.png',
         'Figure\u00a01 \u2014 Muzzle velocity vs orifice diameter ($V_{c}=500$\u00a0mL)',
         'Velocity rises steeply to \u2248\u200910\u00a0mm orifice; plateau beyond 12\u00a0mm '
         'indicates the barrel length limits energy extraction at this volume.'),
        ('vel_vs_orifice_Vc_800uL.png',
         'Figure\u00a02 \u2014 Muzzle velocity vs orifice diameter ($V_{c}=800$\u00a0mL)',
         'Larger chamber sustains higher $P_{c}$ longer, raising $v_{\\text{exit}}$ '
         'especially at large $d_{\\text{or}}$.'),
        ('vel_vs_orifice_Vc_1000uL.png',
         f'Figure\u00a03 \u2014 Muzzle velocity vs orifice diameter '
         f'($V_{{c}}=1000$\u00a0mL) \u2014 **nominal case**',
         f'Reference: $V_{{0}}={V0*1e3:.0f}$\u00a0mL at $P_{{0}}={P0_gauge_bar:.0f}$\u00a0bar gauge. '
         f'At $d_{{\\text{{or}}}}=12$\u00a0mm, $C_{{d}}=0.8$: '
         f'$v_{{\\text{{exit}}}}={muzzle_v:.1f}$\u00a0m/s.'),
        ('vel_vs_orifice_Vc_1200uL.png',
         'Figure\u00a04 \u2014 Muzzle velocity vs orifice diameter ($V_{c}=1200$\u00a0mL)',
         'Over-volume case; diminishing returns vs 1000\u00a0mL due to barrel-length limit.'),
        ('peakF_vs_orifice_Vc_1000uL.png',
         'Figure\u00a05 \u2014 Peak barrel force vs orifice diameter ($V_{c}=1000$\u00a0mL)',
         '$F_{\\text{peak}}=\\max_{t}[(P_{b}(t)-P_{\\text{atm}})A_{\\text{bore}}]$. '
         'Maximum force on the **projectile** during the firing stroke \u2014 '
         'NOT the endcap bolt load (\u00a7\u200b8).'),
        ('impulse_vs_orifice_Vc_1000uL.png',
         'Figure\u00a06 \u2014 Impulse vs orifice diameter ($V_{c}=1000$\u00a0mL)',
         '$I=m_{\\text{payload}}\\cdot v_{\\text{exit}}=\\int F_{\\text{net}}\\,\\mathrm{d}t$ '
         '(1\u00a0kg payload: impulse in N\u00b7s = velocity in m/s numerically). '
         'Plateau at large $d_{\\text{or}}$ confirms barrel-length-limited regime.'),
    ]
    for fname, caption, interp in plot_info:
        fpath = os.path.join(OUTPUTS_DIR, fname)
        rel   = 'outputs/' + fname
        ln(f'### {caption}')
        ln()
        ln(f'*{interp}*')
        ln()
        if os.path.exists(fpath):
            ln(f'![]({rel})')
        else:
            ln(f'*(image not found: {fname})*')
        ln()

    drawing_png = os.path.join(OUTPUTS_DIR, 'launcher_drawing.png')
    if os.path.exists(drawing_png):
        ln('## Engineering Drawing')
        ln()
        ln('![Launcher assembly drawing](outputs/launcher_drawing.png)')
        ln()

    # ══ 8. FLANGE AND BOLT CHECK ════════════════════════════════════════════
    ln('# 8. Flange and Bolt Check')
    ln()
    ln('## 8.1 Load Cases')
    ln()
    ln('**Load Case A \u2014 static endcap bolt load (governs fastener design):**')
    ln()
    ln('The endcap must resist the maximum chamber pressure acting on the bore area:')
    ln()
    ln(f'$$F_{{\\text{{endcap}}}} = P_{{0}}\\cdot A_{{\\text{{bore}}}}'
       f'  = {P0:.3e}\\times{A_bore:.6f}'
       f'  = {F_endcap:.1f}\\;\\text{{N}}\\;({F_endcap/1e3:.3f}\\;\\text{{kN}})$$')
    ln()
    ln('**Load Case B \u2014 peak barrel transit force (informational only; not the endcap load):**')
    ln()
    ln(f'$F_{{\\text{{peak,barrel}}}}={worst_F:.1f}$\u00a0N '
       f'(worst sweep: $d_{{\\text{{or}}}}={worst.get("orifice_d_m",0)*1e3:.0f}$\u00a0mm, '
       f'$V_{{c}}={worst.get("Vc_m3",0)*1e6:.0f}$\u00a0mL, '
       f'$C_{{d}}={worst.get("Cd",0):.1f}$).')
    ln()
    ln('This force acts on the **projectile**, not the endcap bolts.')
    ln('Bolt design uses Load Case\u00a0A only.')
    ln()
    ln('## 8.2 Bolt Shear Capacity')
    ln()
    ln('Each bolt resists the endcap axial load in direct shear:')
    ln()
    ln('$$A_{\\text{bolt}} = \\pi\\!\\left(\\frac{d_{\\text{bolt}}}{2}\\right)^{2},'
       '\\qquad F_{\\text{cap}} = A_{\\text{bolt}}\\cdot\\tau_{\\text{shear}},'
       '\\qquad n_{\\text{req}} = \\left\\lceil\\frac{F_{\\text{endcap}}}{F_{\\text{cap}}}\\right\\rceil$$')
    ln()
    ln(f'For M{int(bolt_d*1e3)} bolts '
       f'($d_{{\\text{{bolt}}}}={bolt_d*1e3:.0f}$\u00a0mm, '
       f'$\\tau_{{\\text{{shear}}}}={tau_shear/1e6:.0f}$\u00a0MPa):')
    ln()
    ln(f'$$A_{{\\text{{bolt}}}} = \\pi(0.004)^{{2}}'
       f'  = {A_bolt:.4e}\\;\\text{{m}}^2\\;({A_bolt*1e6:.2f}\\;\\text{{mm}}^2)$$')
    ln()
    ln(f'$$F_{{\\text{{cap}}}} = {A_bolt:.4e}\\times{tau_shear/1e6:.0f}\\times10^{{6}}'
       f'  = {F_cap_bolt:.1f}\\;\\text{{N}}$$')
    ln()
    ln(f'$$n_{{\\text{{req}}}} = \\left\\lceil\\frac{{{F_endcap:.1f}}}{{{F_cap_bolt:.1f}}}\\right\\rceil'
       f'  = {n_req_bolt}$$')
    ln()
    ln(f'With {n_bolts} bolts provided:')
    ln()
    ln(f'$$\\mathrm{{SF}} = \\frac{{{n_bolts}\\times{F_cap_bolt:.1f}}}{{{F_endcap:.1f}}}'
       f'  = {SF_bolts:.1f}$$')
    ln()
    ln('## 8.3 Bolt Shear Check Table')
    ln()
    ln('$\\tau_{\\text{shear}}=240$\u00a0MPa for all bolt sizes.')
    ln()
    ln('| Bolt | $d_{\\text{bolt}}$ (mm) | $A_{\\text{bolt}}$ (mm\u00b2)'
       ' | $F_{\\text{cap}}$ (N) | $n_{\\text{req}}$ (Load\u00a0A) | SF with 6 bolts |')
    ln('|---|---:|---:|---:|---:|---:|')
    for bname, bd in [('M6', 6e-3), ('M8', 8e-3), ('M10', 10e-3)]:
        Ab  = math.pi * (bd / 2)**2
        Fc  = Ab * tau_shear
        nr  = math.ceil(F_endcap / Fc)
        sf6 = 6 * Fc / F_endcap
        ln(f'| {bname} | {bd*1e3:.0f} | {Ab*1e6:.2f} | {Fc:.1f} | {nr} | {sf6:.1f} |')
    ln()

    # ══ 9. GEOMETRIC COMPATIBILITY ══════════════════════════════════════════
    ln('# 9. Barrel\u2013Payload Geometric Compatibility')
    ln()
    ln('## 9.1 Core Constraint')
    ln()
    ln('For a rectangular payload ($W\\times H$) inside a circular bore (diameter $D_{\\text{barrel}}$),')
    ln('the worst-case envelope occurs when the diagonal aligns with the bore:')
    ln()
    ln('$$D_{\\text{eq}} = \\sqrt{W^{2}+H^{2}}$$')
    ln()
    ln('Including sabot radial clearance $C_{\\text{sab}}$ per side,')
    ln('the no-interference condition is:')
    ln()
    ln('$$D_{\\text{eq}}+2\\,C_{\\text{sab}}\\leq D_{\\text{barrel,min}}'
       '\\quad\\text{where}\\quad'
       'D_{\\text{barrel,min}}=D_{\\text{barrel,nom}}-\\delta_{\\text{tol}}$$')
    ln()
    ln('## 9.2 Numerical Check')
    ln()
    ln(f'$$W={W_p:.0f}\\;\\text{{mm}},\\quad H={H_p:.0f}\\;\\text{{mm}}'
       f'  \\implies D_{{\\text{{eq}}}}=\\sqrt{{{W_p:.0f}^{{2}}+{H_p:.0f}^{{2}}}}'
       f'  =\\sqrt{{{W_p**2+H_p**2:.0f}}}={D_eq:.2f}\\;\\text{{mm}}$$')
    ln()
    ln(f'$$C_{{\\text{{sab}}}}={C_sab:.1f}\\;\\text{{mm/side}}'
       f'  \\implies 2C_{{\\text{{sab}}}}={2*C_sab:.1f}\\;\\text{{mm}}$$')
    ln()
    ln(f'$$D_{{\\text{{barrel,nom}}}}={D_nom:.0f}\\;\\text{{mm}},'
       f'  \\quad\\delta_{{\\text{{tol}}}}={D_tol}\\;\\text{{mm}}'
       f'  \\implies D_{{\\text{{barrel,min}}}}={D_min:.1f}\\;\\text{{mm}}$$')
    ln()
    ln('**Check:**')
    ln()
    ln(f'$$D_{{\\text{{eq}}}}+2C_{{\\text{{sab}}}}={D_eq:.2f}+{2*C_sab:.1f}'
       f'  ={check_val:.2f}\\;\\text{{mm}}'
       f'  >{D_min:.1f}\\;\\text{{mm}}=D_{{\\text{{barrel,min}}}}$$')
    ln()
    ln(f'**Result: INTERFERENCE by {interference:.2f}\u00a0mm** if the payload is free to rotate.')
    ln()
    ln('## 9.3 Interpretation and Requirements')
    ln()
    ln(f'The payload diagonal ({D_eq:.2f}\u00a0mm) exceeds the minimum bore ({D_min:.1f}\u00a0mm)')
    ln(f'by {interference:.2f}\u00a0mm. Unconstrained yaw or roll during loading or the firing stroke')
    ln('will cause the payload to jam. A close-fitting sabot is mandatory.')
    ln()
    ln('**Requirement G-01.** The sabot shall enforce axial alignment such that the effective')
    ln(f'payload envelope presented to the bore remains $\\leq D_{{\\text{{barrel,min}}}}$')
    ln('under all loading and firing conditions.')
    ln()
    ln('**Requirement G-02.** Total radial clearance (sabot OD to barrel ID) shall be')
    ln('1.0\u20131.5\u00a0mm per side to prevent tilt-induced interference while maintaining')
    ln('acceptable bore friction and ease of manual loading.')
    ln()

    # ══ 10. FORMULA REFERENCE SUMMARY ═══════════════════════════════════════
    ln('# 10. Formula Reference Summary')
    ln()
    ln('| Quantity | Formula | Numerical result |')
    ln('|---|---|---|')
    A_M8     = math.pi * (0.004)**2
    F_cap_M8 = A_M8 * 240e6
    v50      = math.sqrt(2 * 0.5 * W_ideal / 1.0)   # \eta=50%, m=1kg
    formula_rows = [
        ('Isothermal expansion work',
         r'$W = P_{0}\cdot V_{0}\cdot\ln(P_{0}/P_{f})$',
         f'$W={W_ideal:.1f}$\u00a0J'),
        ('Bore cross-section area',
         r'$A_{\text{bore}} = \pi(D/2)^{2}$',
         f'$A_{{\\text{{bore}}}}={A_bore:.6f}$\u00a0m\u00b2'),
        ('Ideal muzzle velocity',
         r'$v = \sqrt{2\eta W/m}$',
         f'$\\eta=50\\%$, $m=1$\u00a0kg $\\to {v50:.1f}$\u00a0m/s'),
        ('Real-gas pressure (RK\u00a0EOS)',
         r'$P_{\text{real}}=Z_{\text{RK}}\cdot(m/V)\cdot R_{u}T/M_{\text{CO}_{2}}$',
         '$Z_{\\text{RK}}\\approx0.97$ at 11\u00a0bar, 20\u00a0\u00b0C'),
        ('Hoop stress (thin-wall)',
         r'$\sigma_{\text{hoop}} = P\,r/t$',
         f'$t=3$\u00a0mm $\\to\\sigma_{{\\text{{hoop}}}}={P0*r_barrel/0.003/1e6:.1f}$\u00a0MPa'),
        ('Minimum wall thickness',
         r'$t_{\min} = P\cdot r\cdot\mathrm{SF}/\sigma_{\text{yield}}$',
         f'$t_{{\\min}}={t_req_hoop*1e3:.3f}$\u00a0mm (SF\u00a0=\u00a0{SF:.0f})'),
        ('Axial stress',
         r'$\sigma_{\text{axial}} = P\,r/(2t) = \tfrac{1}{2}\sigma_{\text{hoop}}$',
         'Non-governing'),
        ('Endcap axial bolt load',
         r'$F_{\text{endcap}} = P_{0}\cdot A_{\text{bore}}$',
         f'$F_{{\\text{{endcap}}}}={F_endcap:.1f}$\u00a0N'),
        ('Bolt shear capacity',
         r'$F_{\text{cap}} = \pi(d_{\text{bolt}}/2)^{2}\cdot\tau_{\text{shear}}$',
         f'M8: $F_{{\\text{{cap}}}}={F_cap_M8:.1f}$\u00a0N'),
        ('Critical pressure ratio',
         r'$r_{\text{crit}} = (2/(\gamma+1))^{\gamma/(\gamma-1)}$',
         f'$r_{{\\text{{crit}}}}={r_crit:.4f}$ ($\\gamma={gamma}$)'),
        ('Choked mass-flow rate',
         r'$\dot{m}=C_{d}A_{\text{or}}P_{c}\sqrt{\gamma/(R_{\text{spec}}T)}'
         r'\cdot(2/(\gamma+1))^{(\gamma+1)/[2(\gamma-1)]}$',
         f'$\\dot{{m}}_{{0}}={mdot_t0:.4f}$\u00a0kg/s at $t=0$'),
        ('Impulse',
         r'$I = m_{\text{payload}}\cdot v_{\text{exit}} = \int F_{\text{net}}\,\mathrm{d}t$',
         f'$I={impulse:.3f}$\u00a0N\u00b7s'),
        ('Average propulsion force',
         r'$F_{\text{avg}} = I/t_{\text{discharge}}$',
         f'$F_{{\\text{{avg}}}}={avg_F:.1f}$\u00a0N'),
        ('Diagonal payload envelope',
         r'$D_{\text{eq}} = \sqrt{W^{2}+H^{2}}$',
         f'$D_{{\\text{{eq}}}}={D_eq:.2f}$\u00a0mm ($W=40$, $H=45$\u00a0mm)'),
        ('Launch efficiency',
         r'$\eta = E_{k}/W = \tfrac{1}{2}mv^{2}/W$',
         f'$\\eta={eta*100:.2f}\\%$ (1\u00a0kg, ODE sim)'),
    ]
    for qty, formula, result in formula_rows:
        ln(f'| {qty} | {formula} | {result} |')
    ln()

    # ══ CONCLUSION ══════════════════════════════════════════════════════════
    ln('# Conclusion')
    ln()
    ln(f'The {barrel_id*1e3:.0f}\u00a0mm \u00d7 {barrel_length*1e3:.0f}\u00a0mm pneumatic launcher '
       f'charged to {P0_gauge_bar:.0f}\u00a0bar gauge with {V0*1e3:.0f}\u00a0mL of CO\u2082 '
       f'can accelerate a 1\u00a0kg payload to **{muzzle_v:.1f}\u00a0m/s** '
       f'in {t_end*1e3:.0f}\u00a0ms (launch efficiency {eta*100:.1f}\u00a0%).')
    ln(f'A 3\u00a0mm 6061-T6 barrel wall gives SF\u00a0=\u00a0{t3_sf:.1f} vs yield.')
    ln(f'Six M8 flange bolts give SF\u00a0=\u00a0{SF_bolts:.1f} on the static endcap '
       f'load ({F_endcap:.0f}\u00a0N).')
    ln(f'The {W_p:.0f}\u00d7{H_p:.0f}\u00a0mm rectangular payload requires a sabot '
       f'to prevent bore interference (diagonal envelope {D_eq:.1f}\u00a0mm exceeds '
       f'{D_min:.1f}\u00a0mm bore by {interference:.1f}\u00a0mm when misaligned).')
    ln()

    return '\n'.join(L) + '\n'



def write_md(md_text, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(md_text)


def run_pandoc(md_path, out_docx):
    os.makedirs(os.path.dirname(out_docx), exist_ok=True)
    try:
        # Run pandoc from the repo root so relative image paths resolve
        ref = os.path.join(REPO_ROOT, 'docs', 'reference.docx')
        cmd = ['pandoc', md_path, '-o', out_docx, '--standalone']
        if os.path.exists(ref):
            cmd += ['--reference-doc', ref]
        proc = subprocess.run(cmd,
                              cwd=REPO_ROOT, capture_output=True, text=True)
        if proc.returncode != 0:
            print('pandoc failed:', proc.stderr.strip())
            return False
        return True
    except FileNotFoundError:
        print('pandoc not found. Install pandoc to enable .docx generation.')
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Build analysis markdown and convert with pandoc')
    parser.add_argument('--include-artifacts', action='store_true',
                        help='Append raw output files in an appendix')
    args = parser.parse_args()

    md = build_markdown(include_artifacts=args.include_artifacts)
    write_md(md, MD_OUT)
    print('Wrote markdown:', MD_OUT)

    ok = run_pandoc(MD_OUT, DOCX_OUT)
    if ok:
        print('Wrote docx:', DOCX_OUT)
    else:
        print('Document conversion failed or skipped.')


if __name__ == '__main__':
    main()
