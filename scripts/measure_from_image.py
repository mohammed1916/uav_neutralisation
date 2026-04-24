import os
import sys
import math
import csv
import json
from datetime import datetime

try:
    import cv2
    import numpy as np
except Exception as e:
    print('ERROR: OpenCV (cv2) and numpy are required. Install with: pip install opencv-python numpy')
    raise

from docx import Document

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
DOCS_DIR = os.path.join(REPO_ROOT, 'docs')
OUTPUTS_DIR = os.path.join(REPO_ROOT, 'outputs')
IMAGE_PATH = os.path.join(OUTPUTS_DIR, 'top_view_and_side_view.png')
MASTER_DOC = os.path.join(
    DOCS_DIR, 'pneumatic_launcher_analysis_complete.docx')

# Known reference: barrel length in mm
BARREL_LENGTH_MM = 700.0

DEFAULT_ENVELOPE = {
    'length_mm': 1100.0,
    'height_mm': 180.0,
    'width_mm': 80.0,
    'clearance_mm': 10.0
}


def longest_hough_line_length(img_gray):
    edges = cv2.Canny(img_gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, math.pi/180.0,
                            threshold=100, minLineLength=50, maxLineGap=20)
    if lines is None:
        return None, None
    longest = None
    maxlen = 0
    for l in lines:
        x1, y1, x2, y2 = l[0]
        L = math.hypot(x2-x1, y2-y1)
        if L > maxlen:
            maxlen = L
            longest = (x1, y1, x2, y2)
    return longest, maxlen


def measure_from_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise SystemExit('Image not found: ' + image_path)
    h, w = img.shape[:2]
    # split into top and side halves
    top = img[0:h//2, :].copy()
    side = img[h//2:, :].copy()

    top_gray = cv2.cvtColor(top, cv2.COLOR_BGR2GRAY)
    side_gray = cv2.cvtColor(side, cv2.COLOR_BGR2GRAY)

    top_line, top_len_px = longest_hough_line_length(top_gray)
    side_line, side_len_px = longest_hough_line_length(side_gray)

    # prefer top_line for scale, fallback to side_line
    scale_px = None
    scale_mm_per_px = None
    used_region = None
    if top_len_px and top_len_px > 10:
        scale_px = top_len_px
        used_region = 'top'
    elif side_len_px and side_len_px > 10:
        scale_px = side_len_px
        used_region = 'side'
    else:
        raise SystemExit(
            'Unable to detect barrel line automatically. Please provide manual scale.')

    scale_mm_per_px = BARREL_LENGTH_MM / scale_px

    # Measurements: overall length (top): measure non-white horizontal extents
    top_bw = cv2.threshold(top_gray, 250, 255, cv2.THRESH_BINARY_INV)[1]
    coords = cv2.findNonZero(top_bw)
    if coords is not None:
        xs = coords[:, 0, 0]
        overall_left = int(xs.min())
        overall_right = int(xs.max())
        overall_length_px = overall_right - overall_left
    else:
        overall_length_px = int(w)

    # Chamber: find largest blob left of barrel midpoint
    barrel_mid_x = None
    if top_line is not None:
        x1, y1, x2, y2 = top_line
        barrel_mid_x = int((x1+x2)/2)
    else:
        barrel_mid_x = overall_left + int(overall_length_px*0.5)

    # find contours and select largest contour left of barrel_mid_x
    contours, _ = cv2.findContours(
        top_bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    chamber_bbox = None
    max_area = 0
    for c in contours:
        x, y, ww, hh = cv2.boundingRect(c)
        if x+ww < barrel_mid_x + 10:  # left of barrel
            area = ww*hh
            if area > max_area:
                max_area = area
                chamber_bbox = (x, y, ww, hh)

    # Frame width: detect two long vertical rails (approx) using side projection
    top_proj = np.mean(top_bw, axis=0)
    nonzero = np.where(top_proj > 10)[0]
    if nonzero.size > 0:
        frame_left = int(nonzero.min())
        frame_right = int(nonzero.max())
        frame_width_px = frame_right - frame_left
    else:
        frame_width_px = int(w*0.08)

    # Side view height measurement
    side_bw = cv2.threshold(side_gray, 250, 255, cv2.THRESH_BINARY_INV)[1]
    coords_s = cv2.findNonZero(side_bw)
    if coords_s is not None:
        ys = coords_s[:, 0, 1]
        top_y = int(ys.min())
        bottom_y = int(ys.max())
        overall_height_px = bottom_y - top_y
    else:
        overall_height_px = int(h*0.25)

    # Convert to mm
    overall_length_mm = overall_length_px * scale_mm_per_px
    chamber_length_mm = (
        chamber_bbox[2] if chamber_bbox else 0) * scale_mm_per_px
    frame_width_mm = frame_width_px * scale_mm_per_px
    overall_height_mm = overall_height_px * scale_mm_per_px

    measured = {
        'scale_mm_per_px': scale_mm_per_px,
        'scale_px': scale_px,
        'used_region_for_scale': used_region,
        'overall_length_mm': overall_length_mm,
        'chamber_length_mm': chamber_length_mm,
        'frame_width_mm': frame_width_mm,
        'overall_height_mm': overall_height_mm,
        'barrel_length_mm': BARREL_LENGTH_MM
    }

    # Annotate and save image
    annotated = top.copy()
    if top_line is not None:
        x1, y1, x2, y2 = top_line
        cv2.line(annotated, (x1, y1), (x2, y2), (0, 0, 255), 3)
    if chamber_bbox:
        x, y, ww, hh = chamber_bbox
        cv2.rectangle(annotated, (x, y), (x+ww, y+hh), (0, 255, 0), 2)
    # draw overall extents
    try:
        cv2.line(annotated, (overall_left, 10),
                 (overall_right, 10), (255, 0, 0), 3)
        cv2.putText(annotated, f"Overall {overall_length_mm:.0f} mm", (
            overall_left, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    except Exception:
        pass
    out_annot = os.path.join(OUTPUTS_DIR, 'top_view_measured.png')
    cv2.imwrite(out_annot, annotated)

    # Write CSV
    csv_path = os.path.join(OUTPUTS_DIR, 'dimensions_measured.csv')
    with open(csv_path, 'w', newline='') as cf:
        wcsv = csv.writer(cf)
        wcsv.writerow(['parameter', 'value_mm'])
        for k, v in measured.items():
            if isinstance(v, float):
                wcsv.writerow([k, f"{v:.3f}"])
            else:
                wcsv.writerow([k, str(v)])

    # Append fit check to master doc
    doc = Document(MASTER_DOC)
    doc.add_page_break()
    doc.add_heading('Fit Check — Automated Measurements', level=1)
    doc.add_paragraph(f'Generated: {datetime.utcnow().isoformat()} UTC')
    table = doc.add_table(rows=1, cols=3)
    table.rows[0].cells[0].text = 'Measurement'
    table.rows[0].cells[1].text = 'Value (mm)'
    table.rows[0].cells[2].text = 'Pass/Fail (vs default envelope)'

    def passfail(name, val):
        if name == 'overall_length_mm':
            ok = val <= DEFAULT_ENVELOPE['length_mm']
        elif name == 'overall_height_mm':
            ok = val <= DEFAULT_ENVELOPE['height_mm']
        elif name == 'frame_width_mm':
            ok = val <= DEFAULT_ENVELOPE['width_mm']
        else:
            ok = True
        return 'PASS' if ok else 'FAIL'

    for k in ['overall_length_mm', 'chamber_length_mm', 'frame_width_mm', 'overall_height_mm']:
        row = table.add_row().cells
        row[0].text = k
        row[1].text = f"{measured[k]:.1f}"
        row[2].text = passfail(k, measured[k])

    doc.add_paragraph(
        'Notes: scale computed from detected barrel length (700 mm). If detection failed or measurement seems off, provide manual scaling coordinates.')
    doc.save(MASTER_DOC)

    return {'csv': csv_path, 'annotated_png': out_annot, 'measured': measured}


if __name__ == '__main__':
    out = measure_from_image(IMAGE_PATH)
    print('Wrote:', out)
