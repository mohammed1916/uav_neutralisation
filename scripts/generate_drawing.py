import os
import csv
import json
import shutil
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
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            next(reader)
        except StopIteration:
            return vals
        for row in reader:
            if not row:
                continue
            key = row[0].strip()
            try:
                val = float(row[1])
            except Exception:
                val = row[1]
            vals[key] = val
    return vals


def build_geometry(params):
    x = 20.0
    geom = {}
    geom['co2_cartridge'] = {'x': x, 'w': 120.0, 'h': 30.0, 'label': 'CO2 Cartridge'}
    x += geom['co2_cartridge']['w'] + 20.0
    geom['chamber'] = {'x': x, 'w': params['chamber_length_mm'], 'h': params['barrel_id_mm'] * 1.6, 'label': 'Chamber'}
    x += geom['chamber']['w']
    geom['flange'] = {'x': x, 'w': 20.0, 'h': geom['chamber']['h'], 'label': 'Flange'}
    x += geom['flange']['w']
    geom['barrel'] = {'x': x, 'w': params['barrel_length_mm'], 'id': params['barrel_id_mm'], 'label': 'Barrel'}
    x += geom['barrel']['w']
    geom['sabot'] = {'x': x, 'w': 60.0, 'od': params['sabot_od_mm'], 'label': 'Sabot'}
    x += geom['sabot']['w'] + 20.0
    geom['overall_length'] = x
    geom['y_center'] = 200
    return geom


def _ensure_outdir():
    os.makedirs(OUTPUTS_DIR, exist_ok=True)


def write_top_svg(geom, params, out_svg):
    try:
        import svgwrite
    except Exception:
        svgwrite = None

    width = int(geom['overall_length'] + 60)
    height = 420
    y_center = geom['y_center']

    if svgwrite:
        dwg = svgwrite.Drawing(out_svg, size=(f'{width}mm', f'{height}mm'))
        def rect(x, y, w, h, stroke='black', fill='none'):
            dwg.add(dwg.rect(insert=(f'{x}mm', f'{y}mm'), size=(f'{w}mm', f'{h}mm'), fill=fill, stroke=stroke))
        # draw parts
        rect(geom['co2_cartridge']['x'], y_center - 15, geom['co2_cartridge']['w'], geom['co2_cartridge']['h'])
        rect(geom['chamber']['x'], y_center - geom['chamber']['h'] / 2, geom['chamber']['w'], geom['chamber']['h'])
        rect(geom['flange']['x'], y_center - geom['flange']['h'] / 2, geom['flange']['w'], geom['flange']['h'])
        rect(geom['barrel']['x'], y_center - geom['barrel']['id'] * 0.8, geom['barrel']['w'], geom['barrel']['id'] * 1.6)
        # inner bore
        bore_w = geom['barrel']['id']
        rect(geom['barrel']['x'] + (geom['barrel']['w'] - bore_w) / 2, y_center - bore_w / 2, bore_w, bore_w, stroke='red')
        rect(geom['sabot']['x'], y_center - 20, geom['sabot']['w'], 40)

        # labels
        for k in ['co2_cartridge', 'chamber', 'flange', 'barrel', 'sabot']:
            g = geom[k]
            lx = g['x'] + g['w'] / 2
            ly = y_center - (g.get('h', 40) / 2) - 10
            dwg.add(dwg.text(g.get('label', k), insert=(f'{lx}mm', f'{ly}mm'), text_anchor='middle', font_size='10pt'))

        # simple overall dimension
        start_x = geom['co2_cartridge']['x']
        end_x = geom['barrel']['x'] + geom['barrel']['w']
        dim_y = y_center + 110
        dwg.add(dwg.line(start=(f'{start_x}mm', f'{dim_y}mm'), end=(f'{end_x}mm', f'{dim_y}mm'), stroke='black'))
        dwg.add(dwg.text(f"Overall {int(geom['overall_length'])} mm", insert=(f'{(start_x + 10)}mm', f'{dim_y + 12}mm'), font_size='10pt'))

        # title block (bottom-right)
        tb_w = 220
        tb_h = 56
        tb_x = max(10, width - tb_w - 10)
        tb_y = height - tb_h - 10
        rect(tb_x, tb_y, tb_w, tb_h)
        tb_lines = [
            f"Title: Launcher Top View",
            f"Date: {datetime.utcnow().date().isoformat()}",
            f"Scale: 1:1 (mm)",
            f"Author: automated"
        ]
        for i, line in enumerate(tb_lines):
            dwg.add(dwg.text(line, insert=(f'{tb_x + 6}mm', f'{tb_y + 14 + i*12}mm'), font_size='8pt'))

        dwg.save()
    else:
        with open(out_svg, 'w', encoding='utf-8') as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}">\n')
            def r(x, y, w, h, stroke='black', fill='none'):
                f.write(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" />\n')
            r(geom['co2_cartridge']['x'], y_center - 15, geom['co2_cartridge']['w'], geom['co2_cartridge']['h'])
            r(geom['chamber']['x'], y_center - geom['chamber']['h'] / 2, geom['chamber']['w'], geom['chamber']['h'])
            r(geom['flange']['x'], y_center - geom['flange']['h'] / 2, geom['flange']['w'], geom['flange']['h'])
            r(geom['barrel']['x'], y_center - geom['barrel']['id'] * 0.8, geom['barrel']['w'], geom['barrel']['id'] * 1.6)
            bore_w = geom['barrel']['id']
            r(geom['barrel']['x'] + (geom['barrel']['w'] - bore_w) / 2, y_center - bore_w / 2, bore_w, bore_w)
            r(geom['sabot']['x'], y_center - 20, geom['sabot']['w'], 40)
            # labels
            for k in ['co2_cartridge', 'chamber', 'flange', 'barrel', 'sabot']:
                g = geom[k]
                lx = g['x'] + g['w'] / 2
                ly = y_center - (g.get('h', 40) / 2) - 10
                f.write(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="10">{g.get("label", k)}</text>\n')
            f.write(f'<line x1="{geom["co2_cartridge"]["x"]}" y1="{y_center+110}" x2="{geom["barrel"]["x"]+geom["barrel"]["w"]}" y2="{y_center+110}" stroke="black"/>\n')
            f.write(f'<text x="{10}" y="{y_center+124}" font-size="10">Overall {int(geom["overall_length"])} mm</text>\n')
            # title block
            tb_w = 220
            tb_h = 56
            tb_x = max(10, width - tb_w - 10)
            tb_y = height - tb_h - 10
            r(tb_x, tb_y, tb_w, tb_h)
            tb_lines = [
                f"Title: Launcher Top View",
                f"Date: {datetime.utcnow().date().isoformat()}",
                f"Scale: 1:1 (mm)",
                f"Author: automated"
            ]
            for i, line in enumerate(tb_lines):
                f.write(f'<text x="{tb_x+6}" y="{tb_y+14+i*12}" font-size="8">{line}</text>\n')
            f.write('</svg>\n')


def write_top_png(geom, params, out_png):
    try:
        import cv2
        import numpy as np
    except Exception:
        print('OpenCV required to create PNG preview. Install with: pip install opencv-python numpy')
        return

    width = int(geom['overall_length'] + 120)
    height = 420
    img = 255 * np.ones((height, width, 3), dtype=np.uint8)
    y_center = height//2

    def draw_rect(x, y, w, h, color=(0, 0, 0)):
        x1 = int(x)
        y1 = int(y)
        x2 = int(x + w)
        y2 = int(y + h)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

    draw_rect(int(geom['co2_cartridge']['x']), int(y_center - 15), int(geom['co2_cartridge']['w']), int(geom['co2_cartridge']['h']))
    draw_rect(int(geom['chamber']['x']), int(y_center - geom['chamber']['h'] / 2), int(geom['chamber']['w']), int(geom['chamber']['h']))
    draw_rect(int(geom['flange']['x']), int(y_center - geom['flange']['h'] / 2), int(geom['flange']['w']), int(geom['flange']['h']))
    draw_rect(int(geom['barrel']['x']), int(y_center - geom['barrel']['id'] * 0.8), int(geom['barrel']['w']), int(geom['barrel']['id'] * 1.6))
    bore_w = geom['barrel']['id']
    draw_rect(int(geom['barrel']['x'] + (geom['barrel']['w'] - bore_w) / 2), int(y_center - bore_w / 2), int(bore_w), int(bore_w))
    draw_rect(int(geom['sabot']['x']), int(y_center - 20), int(geom['sabot']['w']), 40)

    # labels
    for k in ['co2_cartridge', 'chamber', 'flange', 'barrel', 'sabot']:
        g = geom[k]
        lx = int(g['x'] + g['w'] / 2)
        ly = int(y_center - (g.get('h', 40) / 2) - 12)
        cv2.putText(img, g.get('label', k), (lx - 40, ly), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    cv2.putText(img, f'Overall {int(geom["overall_length"])} mm', (10, y_center + 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    # title block bottom-right
    tb_w = 220
    tb_h = 56
    tb_x = max(10, width - tb_w - 10)
    tb_y = height - tb_h - 10
    cv2.rectangle(img, (tb_x, tb_y), (tb_x + tb_w, tb_y + tb_h), (0, 0, 0), 2)
    tb_lines = [
        f"Title: Launcher Top View",
        f"Date: {datetime.utcnow().date().isoformat()}",
        f"Scale: 1:1 (mm)",
        f"Author: automated"
    ]
    for i, line in enumerate(tb_lines):
        cv2.putText(img, line, (tb_x + 6, tb_y + 16 + i*12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)

    cv2.imwrite(out_png, img)


def write_side_svg(geom, params, out_svg):
    try:
        import svgwrite
    except Exception:
        svgwrite = None

    width = int(max(geom['overall_length'], 300) + 60)
    height = 300
    y_base = 220

    if svgwrite:
        dwg = svgwrite.Drawing(out_svg, size=(f'{width}mm', f'{height}mm'))
        def rect(x, y, w, h, stroke='black', fill='none'):
            dwg.add(dwg.rect(insert=(f'{x}mm', f'{y}mm'), size=(f'{w}mm', f'{h}mm'), fill=fill, stroke=stroke))

        frame_h = params.get('overall_height_mm', 180)
        rect(10, y_base - frame_h, geom['overall_length'] - 20, frame_h)

        ch = geom['chamber']
        rect(ch['x'], y_base - ch.get('h', 40) - 10, ch['w'], ch.get('h', 40))
        br = geom['barrel']
        rect(br['x'], y_base - br.get('id', 40) - 10, br['w'], br.get('id', 40))

        dwg.add(dwg.text('Side view (elevation)', insert=(f'10mm', f'14mm'), font_size='12pt'))
        dwg.save()
    else:
        with open(out_svg, 'w', encoding='utf-8') as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}">\n')
            def r(x, y, w, h, stroke='black', fill='none'):
                f.write(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" />\n')
            frame_h = params.get('overall_height_mm', 180)
            r(10, y_base - frame_h, geom['overall_length'] - 20, frame_h)
            ch = geom['chamber']
            r(ch['x'], y_base - ch.get('h', 40) - 10, ch['w'], ch.get('h', 40))
            br = geom['barrel']
            r(br['x'], y_base - br.get('id', 40) - 10, br['w'], br.get('id', 40))
            f.write(f'<text x="10" y="14" font-size="12">Side view (elevation)</text>\n')
            f.write('</svg>\n')


def write_side_png(geom, params, out_png):
    try:
        import cv2
        import numpy as np
    except Exception:
        print('OpenCV required to create PNG preview. Install with: pip install opencv-python numpy')
        return

    width = int(max(geom['overall_length'], 300) + 120)
    height = 300
    img = 255 * np.ones((height, width, 3), dtype=np.uint8)
    y_base = 220

    def draw_rect(x, y, w, h, color=(0, 0, 0)):
        x1 = int(x)
        y1 = int(y)
        x2 = int(x + w)
        y2 = int(y + h)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

    frame_h = int(params.get('overall_height_mm', 180))
    draw_rect(10, y_base - frame_h, int(geom['overall_length'] - 20), frame_h)
    ch = geom['chamber']
    draw_rect(int(ch['x']), int(y_base - ch.get('h', 40) - 10), int(ch['w']), int(ch.get('h', 40)))
    br = geom['barrel']
    draw_rect(int(br['x']), int(y_base - br.get('id', 40) - 10), int(br['w']), int(br.get('id', 40)))

    cv2.putText(img, 'Side view (elevation)', (10, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    cv2.imwrite(out_png, img)


def try_write_dxf(geom, params, out_dxf):
    try:
        import ezdxf
    except Exception:
        return False
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()

    def rect(x, y, w, h):
        msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)])

    y_center = 0
    rect(geom['co2_cartridge']['x'], y_center - 15, geom['co2_cartridge']['w'], geom['co2_cartridge']['h'])
    rect(geom['chamber']['x'], y_center - geom['chamber']['h'] / 2, geom['chamber']['w'], geom['chamber']['h'])
    rect(geom['flange']['x'], y_center - geom['flange']['h'] / 2, geom['flange']['w'], geom['flange']['h'])
    bar_x = geom['barrel']['x']
    bar_h = geom['barrel']['id'] * 1.6
    rect(bar_x, y_center - bar_h / 2, geom['barrel']['w'], bar_h)
    bore_w = geom['barrel']['id']
    rect(bar_x + (geom['barrel']['w'] - bore_w) / 2, y_center - bore_w / 2, bore_w, bore_w)
    rect(geom['sabot']['x'], y_center - 20, geom['sabot']['w'], 40)
    try:
        msp.add_text("Launcher Top View", dxfattribs={'height': 2}).set_pos((geom['overall_length'] - 200, -60))
    except Exception:
        pass

    doc.saveas(out_dxf)
    return True


def main():
    _ensure_outdir()
    measured = read_measured(MEASURE_CSV)
    params = DEFAULTS.copy()
    # override with measured where sensible
    for k in ['barrel_length_mm', 'overall_length_mm', 'overall_height_mm', 'frame_width_mm', 'barrel_id_mm', 'chamber_length_mm', 'sabot_od_mm']:
        if k in measured and isinstance(measured[k], (int, float)) and measured[k] > 0:
            params[k] = float(measured[k])

    geom = build_geometry(params)
    out_top_svg = os.path.join(OUTPUTS_DIR, 'launcher_top_view.svg')
    out_top_png = os.path.join(OUTPUTS_DIR, 'launcher_top_view.png')
    out_side_svg = os.path.join(OUTPUTS_DIR, 'launcher_side_view.svg')
    out_side_png = os.path.join(OUTPUTS_DIR, 'launcher_side_view.png')
    out_dxf = os.path.join(OUTPUTS_DIR, 'launcher_drawing.dxf')

    # top view
    write_top_svg(geom, params, out_top_svg)
    write_top_png(geom, params, out_top_png)

    # side view
    write_side_svg(geom, params, out_side_svg)
    write_side_png(geom, params, out_side_png)

    # write geometry summary for downstream tools
    try:
        geo_out = os.path.join(OUTPUTS_DIR, 'launcher_geometry.json')
        summary = {'params': params, 'geom': geom}
        with open(geo_out, 'w', encoding='utf-8') as gf:
            json.dump(summary, gf, indent=2)
    except Exception:
        geo_out = None

    # also write legacy filenames for compatibility
    try:
        legacy_png = os.path.join(OUTPUTS_DIR, 'launcher_drawing.png')
        shutil.copyfile(out_top_png, legacy_png)
    except Exception:
        pass

    wrote_dxf = try_write_dxf(geom, params, out_dxf)

    print('Wrote:', out_top_svg, out_top_png, out_side_svg, out_side_png, geo_out if geo_out else '(geo json skipped)', out_dxf if wrote_dxf else '(dxf skipped)')


if __name__ == '__main__':
    main()
