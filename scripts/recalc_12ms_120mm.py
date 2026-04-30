"""
Recalculation: 12 m/s target, 120 mm bore (radius 60 mm), 100 m operational range.
"""
import math
from scipy.integrate import solve_ivp

R_U = 8.31446261815324
M_CO2 = 0.04401
R_SPEC = R_U / M_CO2
TC_CO2 = 304.1282
PC_CO2 = 7.3773e6
A_RK = 0.42748 * R_U**2 * TC_CO2**2 / PC_CO2
B_RK = 0.08664 * R_U * TC_CO2 / PC_CO2


def z_rk(P, T, z0=1.0):
    P = max(P, 1.0)
    Z = max(z0, 0.05)
    for _ in range(80):
        Vm = max(Z * R_U * T / P, 1e-9)
        f = P - R_U*T/(Vm - B_RK) + A_RK/(Vm*(Vm + B_RK)*math.sqrt(T))
        df = R_U*T/(Vm - B_RK)**2 - A_RK*(2*Vm + B_RK) / \
            ((Vm*(Vm + B_RK))**2*math.sqrt(T))
        if abs(df) < 1e-20:
            break
        Vm = max(Vm - f/df, 1e-9)
        Z_new = max(min(P*Vm/(R_U*T), 20.0), 0.05)
        if abs(Z_new - Z) < 1e-8:
            Z = Z_new
            break
        Z = Z_new
    return Z


def pressure_from_mass(m, V, T, p_guess):
    if m <= 0 or V <= 0:
        return 1e5
    p = max(p_guess, 1e5)
    for _ in range(8):
        Z = z_rk(p, T)
        p_new = Z * (m / V) * R_U * T / M_CO2
        if abs(p_new - p) / max(p, 1.0) < 1e-6:
            p = p_new
            break
        p = p_new
    return max(p, 1.0)


def mass_flow(Pc, Pb, T, A_or, Cd, gamma):
    if Pc <= Pb or Pc <= 0:
        return 0.0
    pr = max(min(Pb / Pc, 1.0), 0.0)
    cpr = (2.0 / (gamma + 1.0))**(gamma / (gamma - 1.0))
    if pr <= cpr:
        f = (2.0 / (gamma + 1.0))**((gamma + 1.0) / (2.0*(gamma - 1.0)))
        return Cd * A_or * Pc * math.sqrt(gamma / (R_SPEC * T)) * f
    b = (2.0*gamma / (gamma - 1.0)) * \
        (pr**(2.0/gamma) - pr**((gamma+1.0)/gamma))
    return Cd * A_or * Pc / math.sqrt(R_SPEC * T) * math.sqrt(max(b, 0.0))


def run_case(d_orifice, V_chamber, P0_gauge_bar, D_barrel, L_barrel,
             m_payload, Cd=0.8, mu=0.10, gamma=1.30, T=293.15, P_atm=1e5):
    A_bore = math.pi * (D_barrel / 2)**2
    A_or = math.pi * (d_orifice / 2)**2
    P0_abs = (P0_gauge_bar + 1.0) * 1e5
    V_dead = 1e-6

    Z0 = z_rk(P0_abs, T)
    rho0 = P0_abs * M_CO2 / (Z0 * R_U * T)
    m_c0 = rho0 * V_chamber

    rho_b0 = P_atm * M_CO2 / (z_rk(P_atm, T) * R_U * T)
    m_b0 = rho_b0 * V_dead

    def ode(t, y):
        x, v, m_c = y
        xc = min(max(x, 0.0), L_barrel)
        V_b = A_bore * xc + V_dead
        mce = max(m_c, 0.0)
        m_b = max(m_b0 + (m_c0 - mce), 1e-12)
        Pc = pressure_from_mass(mce, V_chamber, T, P0_abs)
        Pb = pressure_from_mass(m_b, V_b,       T, P_atm)
        md = mass_flow(Pc, Pb, T, A_or, Cd, gamma)
        md = min(md, max(mce, 0.0) / 1e-4)
        F_p = max((Pb - P_atm) * A_bore, 0.0)
        F_f = mu * max(Pb * A_bore, 0.0)
        a = max(F_p - F_f, 0.0) / m_payload
        return [v, a, -md]

    def ev_exit(t, y): return y[0] - L_barrel
    ev_exit.terminal = True
    ev_exit.direction = 1

    def ev_empty(t, y): return y[2] - 1e-10
    ev_empty.terminal = True
    ev_empty.direction = -1

    sol = solve_ivp(ode, (0.0, 0.6), [0.0, 0.0, m_c0], method='RK45',
                    rtol=1e-6, atol=1e-9, max_step=2e-4,
                    events=[ev_exit, ev_empty])
    v_exit = float(sol.y[1, -1])
    t_end = float(sol.t[-1])
    forces = []
    for i in range(len(sol.t)):
        xc = min(max(sol.y[0, i], 0.0), L_barrel)
        V_b = A_bore * xc + V_dead
        m_b = max(m_b0 + (m_c0 - max(sol.y[2, i], 0.0)), 1e-12)
        Pb = pressure_from_mass(m_b, V_b, T, P_atm)
        forces.append(max((Pb - P_atm) * A_bore, 0.0))
    KE = 0.5 * m_payload * v_exit**2
    W_ideal = P0_abs * V_chamber * math.log(P0_abs / P_atm)
    return dict(v=v_exit, t_ms=t_end*1000, peak_F=max(forces) if forces else 0.0,
                KE=KE, eta=100.0*KE/W_ideal, m_fill=m_c0)


# ── Parameters ──────────────────────────────────────────────────────────────
D_barrel = 0.120   # 12 cm bore (radius 6 cm)
R_bore = 0.060
A_bore = math.pi * R_bore**2
P0_gauge = 10.0    # bar gauge
P_atm = 1e5
m_payload = 1.0     # kg
gamma = 1.30
T = 293.15

P0_abs = (P0_gauge + 1.0) * 1e5
cpr = (2.0/(gamma+1.0))**(gamma/(gamma-1.0))
KE_req = 0.5 * m_payload * 12.0**2
W_ideal = P0_abs * 0.001 * math.log(P0_abs / P_atm)   # 1 L chamber ref

print("=" * 68)
print("RECALCULATION — 12 m/s target | 120 mm bore | 100 m operational range")
print("=" * 68)
print()
print("── Geometry & thermodynamics ──────────────────────────────────────────")
print(f"  Bore diameter             : 120 mm  (radius 60 mm)")
print(
    f"  Bore area A_bore          : {A_bore*1e4:.4f} cm²  =  {A_bore:.6f} m²")
print(f"  (Old 52 mm bore area      : {math.pi*0.026**2*1e4:.4f} cm²)")
print(f"  Area ratio new/old        : {A_bore / (math.pi*0.026**2):.2f}×")
print(f"  Working pressure (gauge)  : {P0_gauge:.1f} bar")
print(f"  Working pressure (abs)    : {P0_abs/1e5:.2f} bar")
print(
    f"  Critical pressure ratio   : {cpr:.4f}  (choked if P2/P1 < {cpr:.4f})")
print(
    f"  Choked transition pressure: {P_atm/cpr/1e5:.3f} bar abs  (P_atm÷CPR)")
print(f"  Initial P2/P1             : {P_atm/P0_abs:.4f}  → choked ✓")
print()
print("── Energy ─────────────────────────────────────────────────────────────")
print(f"  KE required @ 12 m/s, 1 kg: {KE_req:.1f} J")
print(f"  Ideal work (1 L, 10 bar)  : {W_ideal:.1f} J")
print(
    f"  Min efficiency needed     : {100*KE_req/W_ideal:.2f}%  (at 1 L chamber)")
print()
print("── Static structural loads ─────────────────────────────────────────────")
F_endcap = P0_abs * A_bore
print(
    f"  Endcap static load @ {P0_abs/1e5:.1f} bar abs: {F_endcap:.0f} N  ({F_endcap/1000:.2f} kN)")
print(
    f"  (Old 52 mm bore endcap load: {(P0_gauge+1)*1e5*math.pi*0.026**2:.0f} N)")
print()

# CO2 fill mass
Z0 = z_rk(P0_abs, T)
rho0 = P0_abs * M_CO2 / (Z0 * R_U * T)
Z_rk_val = Z0
for V_mL, label in [(1000, "1.0 L"), (2000, "2.0 L"), (3000, "3.0 L")]:
    m_fill = rho0 * V_mL/1e6 * 1000  # grams
    print(
        f"  CO2 fill mass ({label} chamber): {m_fill:.1f} g  (ideal-gas; Z={Z0:.4f})")
print()

# ── Sweep 1: orifice diameter at V=1 L, L=700 mm ──────────────────────────
print("── Orifice sweep  (V_chamber=1.0 L,  L_barrel=700 mm,  P=10 bar gauge) ─")
print(f"  {'d_or':>6}  {'v_exit':>8}  {'t_ms':>8}  {'KE_J':>7}  {'eta%':>6}  {'peakF_kN':>9}")
for d_mm in [10, 12, 15, 18, 20, 25, 30]:
    r = run_case(d_mm/1000, 0.001, P0_gauge, D_barrel, 0.700, m_payload)
    flag = " << low" if r['v'] < 10 else (
        " ✓ OK" if 11 <= r['v'] <= 13 else "")
    print(
        f"  {d_mm:>4} mm  {r['v']:>8.2f}  {r['t_ms']:>8.2f}  {r['KE']:>7.1f}  {r['eta']:>6.2f}  {r['peak_F']/1000:>9.2f}{flag}")

print()
# ── Sweep 2: chamber volume at d=20 mm, L=700 mm ─────────────────────────
print("── Volume sweep  (d_or=20 mm,  L_barrel=700 mm,  P=10 bar gauge) ──────")
print(f"  {'V_ch':>8}  {'v_exit':>8}  {'t_ms':>8}  {'KE_J':>7}  {'eta%':>6}  {'mfill_g':>8}")
for V_mL in [500, 750, 1000, 1500, 2000, 3000]:
    r = run_case(0.020, V_mL/1e6, P0_gauge, D_barrel, 0.700, m_payload)
    Zv = z_rk(P0_abs, T)
    mfg = (P0_abs*M_CO2/(Zv*R_U*T)) * V_mL/1e6 * 1000
    flag = " ✓" if 11 <= r['v'] <= 13 else ""
    print(
        f"  {V_mL:>6} mL  {r['v']:>8.2f}  {r['t_ms']:>8.2f}  {r['KE']:>7.1f}  {r['eta']:>6.2f}  {mfg:>8.1f}{flag}")

print()
# ── Sweep 3: barrel length at d=20 mm, V=1.5 L ───────────────────────────
print("── Barrel length sweep  (d_or=20 mm,  V=1.5 L,  P=10 bar gauge) ───────")
print(f"  {'L_mm':>6}  {'v_exit':>8}  {'t_ms':>8}  {'KE_J':>7}")
for L_mm in [400, 500, 600, 700, 800, 1000, 1200]:
    r = run_case(0.020, 0.0015, P0_gauge, D_barrel, L_mm/1000, m_payload)
    flag = " ✓" if 11 <= r['v'] <= 13 else ""
    print(
        f"  {L_mm:>4} mm  {r['v']:>8.2f}  {r['t_ms']:>8.2f}  {r['KE']:>7.1f}{flag}")

print()
# ── Ballistics: post-exit flight ─────────────────────────────────────────
print("── Post-exit ballistics (purely ballistic, 1 kg, 12 m/s, no drag) ─────")
g = 9.81
for ang in [15, 30, 45]:
    th = math.radians(ang)
    R = 12**2 * math.sin(2*th) / g
    H = 12**2 * math.sin(th)**2 / (2*g)
    Tf = 2*12*math.sin(th) / g
    print(
        f"  θ={ang:2d}°: range={R:.1f} m,  height={H:.1f} m,  flight_time={Tf:.2f} s")
print(f"  Max ballistic range (45°): {12**2/g:.1f} m")
print(
    f"  → 100 m operational range: UAV self-propulsion covers remaining ~{100 - 12**2/g:.0f} m")
print()

# ── Recommended design point ─────────────────────────────────────────────
print("── Recommended design point (nominal) ──────────────────────────────────")
r_nom = run_case(0.020, 0.0015, P0_gauge, D_barrel, 0.700, m_payload)
print(f"  d_orifice   = 20 mm")
print(f"  V_chamber   = 1.5 L")
print(f"  L_barrel    = 700 mm")
print(f"  D_bore      = 120 mm")
print(f"  P_working   = 10 bar gauge  (11 bar abs)")
print(f"  v_exit      = {r_nom['v']:.2f} m/s")
print(f"  KE          = {r_nom['KE']:.1f} J")
print(f"  dwell_time  = {r_nom['t_ms']:.1f} ms")
print(f"  peak_force  = {r_nom['peak_F']/1000:.2f} kN")
print(f"  efficiency  = {r_nom['eta']:.2f}%")
CO2_fill_g = (P0_abs*M_CO2/(z_rk(P0_abs, T)*R_U*T)) * 0.0015 * 1000
print(
    f"  CO2/shot    = {CO2_fill_g:.1f} g  (88 g cartridge → {88/CO2_fill_g:.1f} shots)")
print()
print("── Endcap fastener check (new bore) ────────────────────────────────────")
F_ec = P0_abs * A_bore
tau = 240e6  # MPa shear
for d_bolt, A_bolt in [("M6", 28.27e-6), ("M8", 50.27e-6), ("M10", 78.54e-6)]:
    cap1 = tau * A_bolt
    n_req = math.ceil(F_ec / cap1)
    sf6 = 6 * cap1 / F_ec
    print(f"  {d_bolt}: single-bolt shear {cap1/1000:.1f} kN | need ≥{n_req} bolt | SF×6 bolts = {sf6:.1f}")
