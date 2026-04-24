#!/usr/bin/env python
"""Render a DXF to a PNG preview using ezdxf + matplotlib.

Usage:
    python scripts/view_dxf.py [INPUT_DXF] [OUTPUT_PNG] [--open]

Defaults:
    INPUT_DXF  -> outputs/launcher_drawing.dxf
    OUTPUT_PNG -> outputs/launcher_drawing_preview.png

Requires: ezdxf, matplotlib
    pip install ezdxf matplotlib
"""
from __future__ import annotations
import os
import sys
import argparse

DEFAULT_DXF = os.path.join('outputs', 'launcher_drawing.dxf')
DEFAULT_PNG = os.path.join('outputs', 'launcher_drawing_preview.png')


def main():
    parser = argparse.ArgumentParser(description='Render DXF to PNG preview')
    parser.add_argument('dxf', nargs='?', default=DEFAULT_DXF, help='Input DXF path')
    parser.add_argument('out', nargs='?', default=DEFAULT_PNG, help='Output PNG path')
    parser.add_argument('--open', action='store_true', help='Open the PNG after render (Windows only)')
    args = parser.parse_args()

    dxf_path = args.dxf
    out_png = args.out

    # ensure output dir exists
    os.makedirs(os.path.dirname(out_png) or '.', exist_ok=True)

    try:
        import ezdxf
        from ezdxf.addons.drawing import RenderContext, Frontend
        # Matplotlib backend helper
        try:
            from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
        except Exception:
            MatplotlibBackend = None
    except Exception as e:
        print('Missing Python package: ezdxf (and drawing addons).')
        print('Install with: pip install ezdxf matplotlib')
        sys.exit(2)

    try:
        import matplotlib.pyplot as plt
    except Exception:
        print('Missing matplotlib. Install with: pip install matplotlib')
        sys.exit(2)

    if not os.path.exists(dxf_path):
        print(f'Input DXF not found: {dxf_path}')
        sys.exit(3)

    try:
        doc = ezdxf.readfile(dxf_path)
    except Exception as e:
        print('Failed to read DXF:', e)
        sys.exit(4)

    msp = doc.modelspace()

    # Create figure and axis
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_axes([0, 0, 1, 1])

    ctx = RenderContext(doc)
    if MatplotlibBackend is None:
        # fallback: attempt to import helper path
        try:
            from ezdxf.addons.drawing import matplotlib as ezmat
            Backend = getattr(ezmat, 'MatplotlibBackend', None)
        except Exception:
            Backend = None
    else:
        Backend = MatplotlibBackend

    if Backend is None:
        print('ezdxf matplotlib backend not available in this environment.')
        print('You can still view the DXF with FreeCAD, AutoCAD TrueView, LibreCAD, or other DXF viewers.')
        sys.exit(5)

    out = Backend(ax)
    frontend = Frontend(ctx, out)

    try:
        frontend.draw_layout(msp, finalize=True)
    except Exception as e:
        print('Rendering failed:', e)
        sys.exit(6)

    ax.set_axis_off()
    ax.autoscale()
    ax.set_aspect('equal')

    try:
        plt.savefig(out_png, dpi=200, bbox_inches='tight', pad_inches=0.02)
        plt.close(fig)
        print('Wrote preview:', out_png)
    except Exception as e:
        print('Failed to save PNG:', e)
        sys.exit(7)

    if args.open and sys.platform.startswith('win'):
        try:
            os.startfile(os.path.abspath(out_png))
        except Exception:
            print('Could not open file automatically; open it manually in Explorer.')


if __name__ == '__main__':
    main()
