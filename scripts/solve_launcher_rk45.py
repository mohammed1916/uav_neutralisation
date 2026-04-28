import json
import math
import os
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp


BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'outputs'))
os.makedirs(OUTPUT_DIR, exist_ok=True)


@dataclass
class Params:
    V_chamber: float = 0.001
    P0_gauge_bar: float = 10.0
    T: float = 293.15
    D_barrel: float = 0.052
    L_barrel: float = 0.700
    m_payload: float = 1.0
    D_orifice: float = 0.012
    Cd: float = 0.8
    mu_friction: float = 0.10
    gamma: float = 1.30
    P_atm: float = 1.0e5


R_U = 8.31446261815324
M_CO2 = 0.04401
R_SPEC = R_U / M_CO2
TC_CO2 = 304.1282
PC_CO2 = 7.3773e6
A_RK = 0.42748 * R_U * R_U * TC_CO2 * TC_CO2 / PC_CO2
B_RK = 0.08664 * R_U * TC_CO2 / PC_CO2


def z_rk_newton(P: float, T: float, z0: float = 1.0) -> float:
    P = max(P, 1.0)
    Z = max(z0, 0.05)
    for _ in range(80):
        Vm = max(Z * R_U * T / P, 1e-9)
        f = P - R_U * T / (Vm - B_RK) + A_RK / (Vm * (Vm + B_RK) * math.sqrt(T))
        df = (R_U * T) / ((Vm - B_RK) ** 2) - A_RK * (2 * Vm + B_RK) / ((Vm * (Vm + B_RK)) ** 2 * math.sqrt(T))
        if abs(df) < 1e-20:
            break
        Vm_new = Vm - f / df
        Vm_new = max(Vm_new, 1e-9)
        Z_new = max(min(P * Vm_new / (R_U * T), 20.0), 0.05)
        if abs(Z_new - Z) < 1e-8:
            Z = Z_new
            break
        Z = Z_new
    return Z


def pressure_from_mass_volume_rk(m_gas: float, V: float, T: float, p_guess: float) -> float:
    if m_gas <= 0.0 or V <= 0.0:
        return 1.0e5

    p = max(p_guess, 1.0e5)
    for _ in range(8):
        Z = z_rk_newton(p, T, z0=1.0)
        p_new = Z * (m_gas / V) * R_U * T / M_CO2
        if abs(p_new - p) / max(p, 1.0) < 1e-6:
            p = p_new
            break
        p = p_new
    return max(p, 1.0)


def critical_pressure_ratio(gamma: float) -> float:
    return (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))


def mass_flow_rate(Pc: float, Pb: float, T: float, A_or: float, Cd: float, gamma: float) -> float:
    if Pc <= Pb or Pc <= 0.0:
        return 0.0

    pr = max(min(Pb / Pc, 1.0), 0.0)
    r_crit = critical_pressure_ratio(gamma)

    if pr <= r_crit:
        factor = (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (2.0 * (gamma - 1.0)))
        return Cd * A_or * Pc * math.sqrt(gamma / (R_SPEC * T)) * factor

    bracket = (2.0 * gamma / (gamma - 1.0)) * (pr ** (2.0 / gamma) - pr ** ((gamma + 1.0) / gamma))
    if bracket <= 0.0:
        return 0.0
    return Cd * A_or * Pc / math.sqrt(R_SPEC * T) * math.sqrt(bracket)


def run_case(orifice_d: float, params: Params) -> dict:
    A_bore = math.pi * (params.D_barrel / 2.0) ** 2
    A_or = math.pi * (orifice_d / 2.0) ** 2
    P0_abs = (params.P0_gauge_bar + 1.0) * 1.0e5
    V_dead = 1.0e-6

    Z0 = z_rk_newton(P0_abs, params.T)
    rho0 = P0_abs * M_CO2 / (Z0 * R_U * params.T)
    m_c0 = rho0 * params.V_chamber

    rho_b0 = params.P_atm * M_CO2 / (z_rk_newton(params.P_atm, params.T) * R_U * params.T)
    m_b0 = rho_b0 * V_dead

    def ode(t, y):
        x, v, m_c = y
        x_clip = min(max(x, 0.0), params.L_barrel)
        V_b = A_bore * x_clip + V_dead

        m_c_eff = max(m_c, 0.0)
        m_b = max(m_b0 + (m_c0 - m_c_eff), 1e-12)

        Pc = pressure_from_mass_volume_rk(m_c_eff, params.V_chamber, params.T, p_guess=P0_abs)
        Pb = pressure_from_mass_volume_rk(m_b, V_b, params.T, p_guess=params.P_atm)

        mdot = mass_flow_rate(Pc, Pb, params.T, A_or, params.Cd, params.gamma)
        mdot = min(mdot, max(m_c_eff, 0.0) / 1e-4)

        F_pressure = max((Pb - params.P_atm) * A_bore, 0.0)
        F_friction = params.mu_friction * max(Pb * A_bore, 0.0)
        F_net = max(F_pressure - F_friction, 0.0)
        a = F_net / params.m_payload

        return [v, a, -mdot]

    def event_exit(t, y):
        return y[0] - params.L_barrel

    event_exit.terminal = True
    event_exit.direction = 1

    def event_empty(t, y):
        return y[2] - 1e-10

    event_empty.terminal = True
    event_empty.direction = -1

    y0 = [0.0, 0.0, m_c0]
    sol = solve_ivp(
        ode,
        t_span=(0.0, 0.25),
        y0=y0,
        method='RK45',
        rtol=1e-6,
        atol=1e-9,
        max_step=2e-4,
        events=[event_exit, event_empty],
        dense_output=False,
    )

    t = sol.t
    x = sol.y[0]
    v = sol.y[1]
    mc = sol.y[2]

    pb_hist = []
    f_hist = []
    for i in range(len(t)):
        V_b = A_bore * min(max(x[i], 0.0), params.L_barrel) + V_dead
        m_b = max(m_b0 + (m_c0 - max(mc[i], 0.0)), 1e-12)
        Pb = pressure_from_mass_volume_rk(m_b, V_b, params.T, p_guess=params.P_atm)
        pb_hist.append(Pb)
        f_hist.append(max((Pb - params.P_atm) * A_bore, 0.0))

    v_exit = float(v[-1]) if len(v) else 0.0
    t_end = float(t[-1]) if len(t) else 0.0
    peak_force = float(max(f_hist)) if f_hist else 0.0

    KE = 0.5 * params.m_payload * v_exit * v_exit
    W_ideal = P0_abs * params.V_chamber * math.log(P0_abs / params.P_atm)
    eta = 100.0 * KE / W_ideal if W_ideal > 0 else 0.0

    return {
        'orifice_d_m': orifice_d,
        'muzzle_velocity_ms': v_exit,
        'peak_barrel_force_N': peak_force,
        'dwell_time_ms': 1000.0 * t_end,
        'kinetic_energy_J': KE,
        'launch_efficiency_pct': eta,
    }


def main():
    params = Params()

    nominal = run_case(0.012, params)

    sweep_d = [0.006, 0.008, 0.010, 0.012, 0.015, 0.018]
    sweep = [run_case(d, params) for d in sweep_d]

    json_out = {
        'method': 'scipy.integrate.solve_ivp (RK45)',
        'states': ['x_m', 'v_ms', 'm_c_kg'],
        'nominal': nominal,
        'sweep': sweep,
    }

    json_path = os.path.join(OUTPUT_DIR, 'rk45_launcher_results.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_out, f, indent=2)

    csv_path = os.path.join(OUTPUT_DIR, 'rk45_velocity_vs_orifice.csv')
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write('orifice_d_mm,muzzle_velocity_ms\n')
        for row in sweep:
            f.write(f"{row['orifice_d_m']*1000:.1f},{row['muzzle_velocity_ms']:.6f}\n")

    x_mm = [r['orifice_d_m'] * 1000.0 for r in sweep]
    y_v = [r['muzzle_velocity_ms'] for r in sweep]

    plt.figure(figsize=(8, 5))
    plt.plot(x_mm, y_v, marker='o', linewidth=2)
    plt.xlabel('Orifice diameter (mm)')
    plt.ylabel('Muzzle velocity (m/s)')
    plt.title('CO2 launcher (RK45): velocity vs orifice diameter')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plot_path = os.path.join(OUTPUT_DIR, 'rk45_velocity_vs_orifice.png')
    plt.savefig(plot_path, dpi=160)
    plt.close()

    print('Nominal (12 mm):')
    print(json.dumps(nominal, indent=2))
    print(f'Wrote: {json_path}')
    print(f'Wrote: {csv_path}')
    print(f'Wrote: {plot_path}')


if __name__ == '__main__':
    main()
