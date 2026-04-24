import os
import csv
import math
from datetime import datetime

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
OUTPUTS_DIR = os.path.join(REPO_ROOT, 'outputs')
DOCS_DIR = os.path.join(REPO_ROOT, 'docs')

MEASURE_CSV = os.path.join(OUTPUTS_DIR, 'dimensions_measured.csv')

# Nominal defaults (mm)
DEFAULTS = {
    'barrel_length_mm': 700.0,
    'overall_length_mm': 1100.0,
    'overall_height_mm': 180.0,
    'frame_width_mm': 80.0,
    'barrel_id_mm': 52.0,
    'chamber_length_mm': 200.0,
    'sabot_od_mm': 52.0
}


def read_measured(csv_path):
    vals = {}
    if not os.path.exists(csv_path):
        return vals
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            key = row[0].strip()
            try:
                val = float(row[1])
            except Exception:
                val = row[1]
            vals[key] = val
    return vals


def build_geometry(params):
    # simple 2D layout coordinates in mm
    # Top view: origin at leftmost, y=0 baseline
    x = 0.0
    geom = {}
    geom['co2_cartridge'] = {'x': x, 'w': 120.0, 'h': 30.0}
    x += geom['co2_cartridge']['w'] + 20.0
    geom['chamber'] = {'x': x, 'w': params['chamber_length_mm'], 'h': params['barrel_id_mm']*1.6}
    x += geom['chamber']['w']
    geom['flange'] = {'x': x, 'w': 20.0, 'h': geom['chamber']['h']}
    x += geom['flange']['w']
    geom['barrel'] = {'x': x, 'w': params['barrel_length_mm'], 'id': params['barrel_id_mm']}
    x += geom['barrel']['w']
    geom['sabot'] = {'x': x, 'w': 60.0, 'od': params['sabot_od_mm']}
    geom['overall_length'] = x + geom['sabot']['w']
    # frame rails
    geom['frame'] = {'y_offset': -30.0, 'rail_w': 25.0, 'rail_gap': params['frame_width_mm']}
    return geom


def write_svg(geom, params, out_svg):
    try:
        import svgwrite
    except Exception:
        svgwrite = None

    width = int(geom['overall_length'] + 100)
    height = 300

    if svgwrite:
        dwg = svgwrite.Drawing(out_svg, size=(f'{width}mm', f'{height}mm'))
        # draw chamber
        y_center = height//2
        def rect(x,y,w,h,stroke='black'):
            dwg.add(dwg.rect(insert=(f'{x}mm', f'{y}mm'), size=(f'{w}mm', f'{h}mm'), fill='none', stroke=stroke))

        rect(geom['co2_cartridge']['x'], y_center-10, geom['co2_cartridge']['w'], geom['co2_cartridge']['h'])
        rect(geom['chamber']['x'], y_center-geom['chamber']['h']/2, geom['chamber']['w'], geom['chamber']['h'])
        rect(geom['flange']['x'], y_center-geom['flange']['h']/2, geom['flange']['w'], geom['flange']['h'])
        # barrel as outer rectangle and inner hole
        bar_x = geom['barrel']['x']
        bar_h = geom['barrel']['id']*1.6
        rect(bar_x, y_center-bar_h/2, geom['barrel']['w'], bar_h)
        # inner bore
        bore_w = geom['barrel']['id']
        rect(bar_x+ (geom['barrel']['w']-bore_w)/2, y_center-bore_w/2, bore_w, bore_w, stroke='red')
        # sabot
        rect(geom['sabot']['x'], y_center-20, geom['sabot']['w'], 40)

        # dimension lines (simple)
        dwg.add(dwg.line(start=(f'{geom["co2_cartridge"]["x"]}mm', f'{y_center+80}mm'), end=(f'{geom["barrel"]["x"]+geom["barrel"]["w"]}mm', f'{y_center+80}mm'), stroke='black'))
        dwg.add(dwg.text(f"Overall {geom['overall_length']:.0f} mm", insert=(f'{10}mm', f'{y_center+95}mm'), fill='black'))
        dwg.save()
    else:
        # write a very simple SVG by hand
        with open(out_svg, 'w') as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}">\n')
            y_center = height//2
            def r(x,y,w,h,stroke='black'):
                f.write(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{stroke}"/>\n')
            r(geom['co2_cartridge']['x'], y_center-10, geom['co2_cartridge']['w'], geom['co2_cartridge']['h'])
            r(geom['chamber']['x'], y_center-geom['chamber']['h']/2, geom['chamber']['w'], geom['chamber']['h'])
            r(geom['flange']['x'], y_center-geom['flange']['h']/2, geom['flange']['w'], geom['flange']['h'])
            bar_x = geom['barrel']['x']
            bar_h = geom['barrel']['id']*1.6
            r(bar_x, y_center-bar_h/2, geom['barrel']['w'], bar_h)
            bore_w = geom['barrel']['id']
            r(bar_x+ (geom['barrel']['w']-bore_w)/2, y_center-bore_w/2, bore_w, bore_w)
            r(geom['sabot']['x'], y_center-20, geom['sabot']['w'], 40)
            f.write(f'<line x1="{geom["co2_cartridge"]["x"]}" y1="{y_center+80}" x2="{geom["barrel"]["x"]+geom["barrel"]["w"]}" y2="{y_center+80}" stroke="black"/>\n')
            f.write(f'<text x="10" y="{y_center+95}">Overall {geom["overall_length"]:.0f} mm</text>\n')
            f.write('</svg>')


def write_png(geom, params, out_png):
    try:
        import cv2
        import numpy as np
    except Exception:
        print('OpenCV required to create PNG preview. Install with: pip install opencv-python numpy')
        return

    width = int(geom['overall_length'] + 200)
    height = 400
    scale = 1.0  # 1 px per mm
    img = 255 * np.ones((height, width, 3), dtype=np.uint8)
    y_center = height//2

    def draw_rect(x,y,w,h,color=(0,0,0)):
        x1 = int(x*scale)
        y1 = int(y)
        x2 = int((x+w)*scale)
        y2 = int((y+h))
        cv2.rectangle(img, (x1,y1), (x2,y2), color, 2)

    draw_rect(geom['co2_cartridge']['x'], y_center-10, geom['co2_cartridge']['w'], geom['co2_cartridge']['h'])
    draw_rect(geom['chamber']['x'], y_center-geom['chamber']['h']/2, geom['chamber']['w'], geom['chamber']['h'])
    draw_rect(geom['flange']['x'], y_center-geom['flange']['h']/2, geom['flange']['w'], geom['flange']['h'])
    bar_x = geom['barrel']['x']
    bar_h = geom['barrel']['id']*1.6
    draw_rect(bar_x, y_center-bar_h/2, geom['barrel']['w'], bar_h)
    bore_w = geom['barrel']['id']
    draw_rect(bar_x+ (geom['barrel']['w']-bore_w)/2, y_center-bore_w/2, bore_w, bore_w)
    draw_rect(geom['sabot']['x'], y_center-20, geom['sabot']['w'], 40)
    cv2.putText(img, f'Overall {geom["overall_length"]:.0f} mm', (10, y_center+140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)
    cv2.imwrite(out_png, img)


def try_write_dxf(geom, params, out_dxf):
    try:
        import ezdxf
    except Exception:
        print('ezdxf not installed; skipping DXF output. Install with: pip install ezdxf')
        return False
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()
    y_center = 0
    def r(x,y,w,h):
        msp.add_lwpolyline([(x, y), (x+w, y), (x+w, y+h), (x, y+h), (x, y)])
    r(geom['co2_cartridge']['x'], y_center-10, geom['co2_cartridge']['w'], geom['co2_cartridge']['h'])
    r(geom['chamber']['x'], y_center-geom['chamber']['h']/2, geom['chamber']['w'], geom['chamber']['h'])
    r(geom['flange']['x'], y_center-geom['flange']['h']/2, geom['flange']['w'], geom['flange']['h'])
    bar_x = geom['barrel']['x']
    bar_h = geom['barrel']['id']*1.6
    r(bar_x, y_center-bar_h/2, geom['barrel']['w'], bar_h)
    bore_w = geom['barrel']['id']
    r(bar_x+ (geom['barrel']['w']-bore_w)/2, y_center-bore_w/2, bore_w, bore_w)
    r(geom['sabot']['x'], y_center-20, geom['sabot']['w'], 40)
    doc.saveas(out_dxf)
    return True


def main():
    measured = read_measured(MEASURE_CSV)
    params = DEFAULTS.copy()
    # override with measured where sensible
    for k in ['barrel_length_mm','overall_length_mm','overall_height_mm','frame_width_mm','barrel_id_mm','chamber_length_mm','sabot_od_mm']:
        if k in measured and isinstance(measured[k], (int,float)) and measured[k]>0:
            params[k] = float(measured[k])

    geom = build_geometry(params)
    out_svg = os.path.join(OUTPUTS_DIR, 'launcher_drawing.svg')
    out_png = os.path.join(OUTPUTS_DIR, 'launcher_drawing.png')
    out_dxf = os.path.join(OUTPUTS_DIR, 'launcher_drawing.dxf')

    write_svg(geom, params, out_svg)
    write_png(geom, params, out_png)
    wrote_dxf = try_write_dxf(geom, params, out_dxf)

    # append reference to master doc
    master = os.path.join(DOCS_DIR, 'pneumatic_launcher_analysis_complete.docx')
    try:
        from docx import Document
        doc = Document(master)
        doc.add_page_break()
        doc.add_heading('Engineering Drawing (automatically generated)', level=1)
        doc.add_paragraph(f'Files: {os.path.relpath(out_svg, REPO_ROOT)}, {os.path.relpath(out_png, REPO_ROOT)}' + (f', {os.path.relpath(out_dxf, REPO_ROOT)}' if wrote_dxf else ''))
        doc.save(master)
    except Exception:
        pass

    print('Wrote:', out_svg, out_png, out_dxf if wrote_dxf else '(dxf skipped)')


if __name__ == '__main__':
    main()
