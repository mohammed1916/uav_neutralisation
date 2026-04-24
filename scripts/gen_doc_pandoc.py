#!/usr/bin/env python3
import os
import json
import csv
import argparse
import subprocess
from datetime import datetime

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

    components = []
    if geom:
        for name in ['co2_cartridge', 'chamber', 'flange', 'barrel', 'sabot']:
            comp = geom.get(name, {})
            if comp:
                # determine nominal widths/heights
                nominal_w = comp.get('w') or comp.get('od') or comp.get('id')
                comp_row = {
                    'component': name,
                    'field': 'width_mm',
                    'nominal': nominal_w,
                    'measured': None
                }
                components.append(comp_row)

    # overall assembly
    nominal_overall = geom.get('overall_length') if geom else params.get('overall_length_mm')
    measured_overall = None
    if 'overall_length_mm' in measures_dict:
        measured_overall = measures_dict.get('overall_length_mm')

    # per-component measured: try to find specific keys in measures_dict
    for r in components:
        name = r['component']
        key_map = {
            'co2_cartridge': ['co2_cartridge_w', 'co2_cartridge_w_mm'],
            'chamber': ['chamber_length_mm', 'chamber_w_mm', 'chamber_length'],
            'flange': ['flange_w_mm', 'flange_width_mm'],
            'barrel': ['barrel_length_mm', 'barrel_w_mm'],
            'sabot': ['sabot_od_mm', 'sabot_w_mm']
        }
        for k in key_map.get(name, []):
            if k in measures_dict:
                r['measured'] = measures_dict.get(k)
                break

    # assemble results rows
    tol = tol_pct / 100.0
    # overall row
    overall_pass = True
    if nominal_overall is not None and measured_overall is not None:
        delta = measured_overall - nominal_overall
        pass_flag = abs(delta) <= abs(nominal_overall) * tol
        overall_pass = pass_flag
    else:
        delta = None
        pass_flag = None

    results.append({'parameter': 'Overall length (mm)', 'nominal': nominal_overall, 'measured': measured_overall, 'delta': delta, 'tolerance_pct': tol_pct, 'pass': pass_flag})

    for r in components:
        nom = r['nominal']
        meas = r['measured']
        if nom is not None and meas is not None:
            d = meas - nom
            pf = abs(d) <= abs(nom) * tol
        else:
            d = None
            pf = None
        results.append({'parameter': f"{r['component']} {r['field']}", 'nominal': nom, 'measured': meas, 'delta': d, 'tolerance_pct': tol_pct, 'pass': pf})

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
    md.append('Key calculations used in the analysis (LaTeX math is supported by pandoc):\n')
    md.append('Kinetic energy of projectile: $E = \\tfrac{1}{2} m v^2$\n')
    md.append('Pressure-volume work (idealised): $W = \\int p\\,dV$\n')

    md.append('## Summary\n')
    if analysis:
        md.append('### Analysis Summary\n')
        md.append('```json\n' + json.dumps(analysis, indent=2) + '\n```\n')
    else:
        md.append('_No analysis_summary.json found_\n')

    if sweep:
        md.append('### Parametric Sweep Summary\n')
        md.append('```json\n' + json.dumps(sweep, indent=2) + '\n```\n')

    if flange:
        md.append('### Flange Check\n')
        md.append('```json\n' + json.dumps(flange, indent=2) + '\n```\n')

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
        md.append('| Parameter | Nominal | Measured | Delta | Tolerance (%) | Pass |\n')
        md.append('|---|---:|---:|---:|---:|---:|\n')
        for fr in fit_rows:
            nom = f"{fr['nominal']:.2f}" if isinstance(fr['nominal'], (int, float)) else ''
            meas = f"{fr['measured']:.2f}" if isinstance(fr['measured'], (int, float)) else ''
            delta = f"{fr['delta']:.2f}" if isinstance(fr['delta'], (int, float)) else ''
            pass_mark = 'PASS' if fr['pass'] else ('FAIL' if fr['pass'] is False else '')
            md.append(f"| {fr['parameter']} | {nom} | {meas} | {delta} | {fr['tolerance_pct']:.1f} | {pass_mark} |\n")
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

    if include_artifacts:
        md.append('\n## Appendix: Raw outputs\n')
        for p in [ANALYSIS_JSON, SWEEP_JSON, FLANGE_JSON, MEASURE_CSV]:
            if os.path.exists(p):
                name = os.path.basename(p)
                md.append(f'### {name}\n')
                if p.lower().endswith('.json'):
                    try:
                        with open(p, 'r', encoding='utf-8') as f:
                            md.append('```json\n' + f.read() + '\n```\n')
                    except Exception:
                        md.append('_unable to read file_\n')
                else:
                    try:
                        with open(p, 'r', encoding='utf-8') as f:
                            md.append('```\n' + f.read() + '\n```\n')
                    except Exception:
                        md.append('_unable to read file_\n')

    return ''.join(md)


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
    parser = argparse.ArgumentParser(description='Build analysis markdown and convert with pandoc')
    parser.add_argument('--include-artifacts', action='store_true', help='Append raw output files in an appendix')
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
