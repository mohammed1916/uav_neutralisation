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


def build_markdown(include_artifacts=False):
    analysis = read_json(ANALYSIS_JSON)
    sweep = read_json(SWEEP_JSON)
    flange = read_json(FLANGE_JSON)
    headers, measures = read_csv(MEASURE_CSV)
    measures_dict = measures_to_dict(headers, measures)
    geo_summary = read_json(GEOM_JSON)

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    md = []
    md.append(f'# Pneumatic Launcher Analysis\n')
    md.append(f'Generated: {now}\n')

    md.append('## Formulas and Calculations\n')
    md.append('Key calculations used in the analysis (LaTeX math is supported by pandoc). Numeric substitutions are shown where data is available.\n')
    # Isothermal work formula and numeric substitution (use V0 default if not present)
    md.append('### Isothermal expansion work\n')
    md.append('Symbolic: $W = P_0 V_0 \\ln\\left(\\frac{P_0}{P_f}\\right)$\n')
    P0 = None
    V0 = 1.0e-3
    Pf = 1.0e5
    if analysis and isinstance(analysis, dict):
        P0 = analysis.get('P0_abs_Pa')
        # support optional stored V0 key
        if 'V0_m3' in analysis:
            try:
                V0 = float(analysis.get('V0_m3'))
            except Exception:
                pass

    if P0:
        try:
            W_calc = P0 * V0 * math.log(P0 / Pf)
            md.append(
                f'Numeric: $P_0={P0:.0f}\\;\\mathrm{{Pa}},\\; V_0={V0:.4e}\\;\\mathrm{{m^3}},\\; P_f={Pf:.0f}\\;\\mathrm{{Pa}}$\\\n')
            md.append(
                f'Display: $$W = {P0:.0f}\\times {V0:.4e} \\times \\ln\\left(\\frac{{{P0:.0f}}}{{{Pf:.0f}}}\\right) = {W_calc:.2f}\\ \mathrm{{J}}$$\\n')
        except Exception:
            md.append('_Numeric evaluation failed_\n')
    else:
        md.append(
            '_P0 not available in analysis summary; numeric evaluation skipped_\n')

    # Kinetic energy example using worst-case muzzle velocity when available
    md.append('### Kinetic energy (example)\n')
    md.append('Symbolic: $E = \\tfrac{1}{2} m v^2$\n')
    m_example = 1.0
    v_example = None
    if flange and isinstance(flange, dict):
        worst = flange.get('worst_case') or {}
        v_example = worst.get('muzzle_v') if worst else None
    # fallback: try to use first entry in sweep
    if v_example is None and sweep and isinstance(sweep, list) and len(sweep) > 0:
        try:
            v_example = float(sweep[0].get('muzzle_v'))
        except Exception:
            v_example = None

    if v_example is not None:
        Ekin = 0.5 * m_example * (v_example ** 2)
        md.append(
            f'Numeric (m={m_example:.2f} kg, v={v_example:.3f} m/s): $E = 0.5 \\times {m_example:.2f} \\times {v_example:.3f}^2 = {Ekin:.2f}\\;\\mathrm{{J}}$\\n')
    else:
        md.append('_No muzzle velocity available for numeric KE example_\n')

    # Hoop stress / required thickness (thin-wall) example
    md.append('### Thin-wall hoop stress and required thickness\n')
    md.append(
        'Symbolic: $\\sigma_{hoop} = \\frac{P r}{t}$ ; therefore $t = \\frac{P r}{\\sigma_{allowable}}$\n')
    try:
        barrel_area = analysis.get('barrel_area_m2') if analysis else None
    except Exception:
        barrel_area = None
    if barrel_area:
        r_barrel = math.sqrt(barrel_area / math.pi)
        # material assumptions (match gen_doc.py defaults)
        mat_yield = 276e6
        safety_factor = 3.0
        allowable = mat_yield / safety_factor
        if P0:
            t_req = P0 * r_barrel / allowable
            md.append(
                f'Numeric: barrel area={barrel_area:.6e} m^2 → r={r_barrel*1e3:.2f} mm; using allowable={allowable/1e6:.1f} MPa → t_required={t_req*1e3:.3f} mm\\n')
        else:
            md.append('_P0 not available; cannot compute numeric thickness_\n')
    else:
        md.append('_Barrel area not available; numeric hoop thickness skipped_\n')

    md.append('## Summary\n')
    if analysis and isinstance(analysis, dict):
        md.append('### Analysis Summary\n')
        md.append('| Parameter | Value |\n')
        md.append('|---|---:|\n')
        for k, v in analysis.items():
            md.append(f'| {k} | {v} |\n')
    else:
        md.append('_No analysis_summary.json found_\n')

    if sweep and isinstance(sweep, list) and len(sweep) > 0:
        md.append('### Parametric Sweep (full table)\n')
        # build header from keys of first element
        keys = list(sweep[0].keys())
        md.append('| ' + ' | '.join(keys) + ' |\n')
        md.append('|' + '|'.join(['---:' for _ in keys]) + '|\n')
        for row in sweep:
            vals = []
            for k in keys:
                v = row.get(k, '')
                if isinstance(v, float):
                    # format floats compactly
                    if abs(v) >= 1000 or abs(v) < 0.001:
                        vals.append(f'{v:.4g}')
                    else:
                        vals.append(f'{v:.4f}')
                else:
                    vals.append(str(v))
            md.append('| ' + ' | '.join(vals) + ' |\n')

    if flange and isinstance(flange, dict):
        md.append('### Flange Check\n')
        assumptions = flange.get('assumptions', {})
        if assumptions:
            md.append('| Assumption | Value |\n')
            md.append('|---|---:|\n')
            for k, v in assumptions.items():
                md.append(f'| {k} | {v} |\n')
        md.append('\n')
        fr = flange.get('flange_result', {})
        if fr:
            md.append('| Flange Metric | Value |\n')
            md.append('|---|---:|\n')
            for k, v in fr.items():
                md.append(f'| {k} | {v} |\n')
        worst = flange.get('worst_case')
        if worst:
            md.append('\n')
            md.append('| Worst-case param | Value |\n')
            md.append('|---|---:|\n')
            for k, v in worst.items():
                md.append(f'| {k} | {v} |\n')

    md.append('## Final Measurements\n')
    if headers and measures:
        # Expecting two-column key,value_mm style CSV
        md.append('| Parameter | Value |\n')
        md.append('|---|---:|\n')
        for r in measures:
            if len(r) >= 2:
                md.append(f'| {r[0]} | {r[1]} |\n')
            else:
                md.append(f'| {r[0]} | |\n')
    else:
        md.append('_No measurements found_\n')

    # Fit verification using geometry JSON (if available)
    md.append('\n## Fit Verification\n')
    fit_rows = compute_fit_results(geo_summary, measures_dict, tol_pct=5.0)
    if fit_rows:
        md.append(
            '| Parameter | Nominal | Measured | Units | Delta | Tolerance (%) | Pass |\n')
        md.append('|---|---:|---:|---:|---:|---:|---:|\n')
        for fr in fit_rows:
            nom = f"{fr['nominal']:.2f}" if isinstance(
                fr.get('nominal'), (int, float)) else ''
            meas = f"{fr['measured']:.2f}" if isinstance(
                fr.get('measured'), (int, float)) else ''
            delta = f"{fr['delta']:.2f}" if isinstance(
                fr.get('delta'), (int, float)) else ''
            units = fr.get('units', '')
            pass_mark = 'PASS' if fr['pass'] else (
                'FAIL' if fr['pass'] is False else '')
            md.append(
                f"| {fr['parameter']} | {nom} | {meas} | {units} | {delta} | {fr['tolerance_pct']:.1f} | {pass_mark} |\n")
    else:
        md.append('_Fit verification data not available_\n')

    md.append('## Diagrams\n')
    # include top and side views if present
    top_png = os.path.join('outputs', 'launcher_top_view.png')
    side_png = os.path.join('outputs', 'launcher_side_view.png')
    if os.path.exists(os.path.join(REPO_ROOT, top_png)):
        md.append('### Top view\n')
        md.append(f'![Top view]({top_png})\n')
    if os.path.exists(os.path.join(REPO_ROOT, side_png)):
        md.append('### Side view\n')
        md.append(f'![Side view]({side_png})\n')
    # fallback legacy drawing
    legacy = os.path.join('outputs', 'launcher_drawing.png')
    if os.path.exists(os.path.join(REPO_ROOT, legacy)) and not (os.path.exists(os.path.join(REPO_ROOT, top_png)) or os.path.exists(os.path.join(REPO_ROOT, side_png))):
        md.append(f'![Launcher drawing]({legacy})\n')

    # Include all PNG plots from outputs/
    md.append('\n## Plots\n')
    try:
        files = sorted([f for f in os.listdir(OUTPUTS_DIR)
                       if f.lower().endswith('.png')])
        for f in files:
            rel = os.path.join('outputs', f)
            md.append(f'### {f}\n')
            md.append(f'![{f}]({rel})\n')
    except Exception:
        pass

    # Appendix of raw outputs removed to keep document focused and compact

    # join with explicit newlines to preserve paragraph separation for pandoc
    return '\n'.join(md) + '\n'


def write_md(md_text, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(md_text)


def run_pandoc(md_path, out_docx):
    os.makedirs(os.path.dirname(out_docx), exist_ok=True)
    try:
        # Run pandoc from the repo root so relative image paths resolve
        proc = subprocess.run(['pandoc', md_path, '-o', out_docx, '--standalone'],
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
