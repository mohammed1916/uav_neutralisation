"""Fine-tune: exact orifice for 12 m/s and pressure trade-off."""
from scipy.optimize import brentq
import math
import sys
sys.path.insert(0, 'scripts')

# Load helper functions from recalc script
ns = {}
src = open('scripts/recalc_12ms_120mm.py').read()
# Only exec the function definitions, up to the parameters block
exec('\n'.join(src.split('# ── Parameters')[0].splitlines()), ns)
run_case = ns['run_case']
z_rk = ns['z_rk']
M_CO2 = ns['M_CO2']
R_U = ns['R_U']


D_barrel = 0.120
m_payload = 1.0
T = 293.15
P_atm = 1e5

print("── Fine orifice sweep (V=1.0 L, L=700 mm, P=10 bar gauge) ──────────────")
for d_tenth in range(100, 130):
    d = d_tenth / 1000.0
    r = run_case(d, 0.001, 10.0, D_barrel, 0.700, m_payload)
    mark = "  ***" if 11.8 <= r['v'] <= 12.2 else ""
    if 11.0 <= r['v'] <= 13.5:
        print(f"  d={d*1000:.1f} mm  ->  {r['v']:.3f} m/s{mark}")

print()
print("── Pressure vs required orifice for exactly 12 m/s (V=1.0 L, L=700 mm) ─")
print(f"  {'P_gauge':>8}  {'d_or_mm':>8}  {'F_end_kN':>10}  {'m_fill_g':>10}  {'shots/88g':>10}")


def v_at_d(d_mm, P_g):
    return run_case(d_mm/1000.0, 0.001, P_g, D_barrel, 0.700, m_payload)['v']


for P_g in [4.0, 5.0, 6.0, 7.0, 8.0, 10.0]:
    P_abs = (P_g + 1.0) * 1e5
    try:
        d_opt = brentq(lambda d: v_at_d(d, P_g) - 12.0, 8.0, 50.0)
        F_ec = P_abs * math.pi * 0.06**2
        Z0 = z_rk(P_abs, T)
        mfill = P_abs * M_CO2 / (Z0 * R_U * T) * 0.001 * 1000
        shots = 88.0 / mfill
        print(
            f"  {P_g:>6.1f} bar  {d_opt:>8.2f}  {F_ec/1000:>10.2f}  {mfill:>10.1f}  {shots:>10.1f}")
    except Exception as ex:
        print(f"  {P_g:>6.1f} bar  no solution ({ex})")
