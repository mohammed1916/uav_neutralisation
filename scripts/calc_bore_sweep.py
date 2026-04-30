import math

# Launcher constants
M_PAYLOAD = 1.0        # kg
V_TARGET = 30.0        # m/s
V_CHAMBER = 0.001      # m^3 (1.0 L)
BARREL_LENGTH = 0.700  # m
T_GAS = 293.15         # K
R_SPEC = 188.92        # J/(kg.K) for CO2
R_UNIV = 8.314         # J/(mol.K)
M_CO2 = 0.04401        # kg/mol
GAMMA = 1.30
CD = 0.80
P_ATM = 1.0e5          # Pa abs
Z_CO2 = 0.99

BORE_RADII_MM = [60, 80, 100, 120]
DWELL_TIMES_MS = [50, 40, 30, 25]
POLYTROPIC_EXPONENTS = [1.20, 1.25, 1.30]
EFFICIENCIES = [0.40, 0.50, 0.60]


def choke_factor() -> float:
    factor_inner = math.sqrt(GAMMA / (R_SPEC * T_GAS))
    exponent = (GAMMA + 1) / (2 * (GAMMA - 1))
    return CD * factor_inner * (2 / (GAMMA + 1)) ** exponent


def kinetic_energy() -> float:
    return 0.5 * M_PAYLOAD * V_TARGET**2


def required_gas_work(efficiency: float) -> float:
    return kinetic_energy() / efficiency


def polytropic_work(p1_abs_pa: float, exponent: float) -> float:
    v2 = V_CHAMBER * (p1_abs_pa / P_ATM) ** (1.0 / exponent)
    return (p1_abs_pa * V_CHAMBER - P_ATM * v2) / (exponent - 1.0)


def solve_pressure_for_work(work_target_j: float, exponent: float) -> float:
    lo = P_ATM * 1.0001
    hi = 200.0e5
    for _ in range(120):
        mid = 0.5 * (lo + hi)
        if polytropic_work(mid, exponent) < work_target_j:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def co2_mass_per_shot_g(p_abs_pa: float) -> float:
    mass_kg = (p_abs_pa * V_CHAMBER * M_CO2) / (Z_CO2 * R_UNIV * T_GAS)
    return mass_kg * 1000.0


def orifice_diameter_mm(mass_g: float, p_abs_pa: float, dwell_ms: float, flow_constant: float) -> float:
    mdot = (mass_g / 1000.0) / (dwell_ms / 1000.0)
    area_m2 = mdot / (p_abs_pa * flow_constant)
    return 2.0 * math.sqrt(area_m2 / math.pi) * 1000.0


def endcap_force_kn(p_abs_pa: float, radius_mm: float) -> float:
    area = math.pi * (radius_mm / 1000.0) ** 2
    return p_abs_pa * area / 1000.0


def print_pressure_sensitivity() -> None:
    print("=== POLYTROPIC PRESSURE SENSITIVITY ===")
    print("n is the polytropic exponent. eta is the lumped launcher efficiency.")
    print(f"{'n':>6}  {'eta':>6}  {'Wreq(J)':>10}  {'Pabs(bar)':>10}  {'Pg(bar)':>9}  {'CO2(g)':>8}")
    print("-" * 66)
    for exponent in POLYTROPIC_EXPONENTS:
        for efficiency in EFFICIENCIES:
            work_target = required_gas_work(efficiency)
            p_abs = solve_pressure_for_work(work_target, exponent)
            p_gauge = (p_abs - P_ATM) / 1e5
            mass_g = co2_mass_per_shot_g(p_abs)
            print(f"{exponent:>6.2f}  {efficiency:>6.2f}  {work_target:>10.1f}  {p_abs/1e5:>10.3f}  {p_gauge:>9.3f}  {mass_g:>8.2f}")
    print()


def print_case_summary(label: str, exponent: float, efficiency: float, flow_constant: float) -> tuple[float, float]:
    work_target = required_gas_work(efficiency)
    p_abs = solve_pressure_for_work(work_target, exponent)
    p_gauge = (p_abs - P_ATM) / 1e5
    mass_g = co2_mass_per_shot_g(p_abs)

    print(f"=== {label.upper()} ===")
    print(f"n = {exponent:.2f}, eta = {efficiency:.2f}")
    print(f"Required gas work = {work_target:.1f} J")
    print(f"Pressure = {p_abs/1e5:.3f} bar abs  ({p_gauge:.3f} bar gauge)")
    print(f"CO2 per shot = {mass_g:.2f} g")
    print(
        f"50 ms lower-bound orifice = {orifice_diameter_mm(mass_g, p_abs, 50.0, flow_constant):.2f} mm")
    print()
    return p_abs, mass_g


def print_bore_table(label: str, p_abs: float) -> None:
    print(f"=== BORE LOADS: {label.upper()} ===")
    print(f"{'r(mm)':>6}  {'D(mm)':>6}  {'Fstatic(kN)':>12}  {'SF2 design(kN)':>14}  {'SF3 design(kN)':>14}")
    print("-" * 62)
    for radius_mm in BORE_RADII_MM:
        static_force = endcap_force_kn(p_abs, radius_mm)
        print(f"{radius_mm:>6}  {2*radius_mm:>6}  {static_force:>12.2f}  {2*static_force:>14.2f}  {3*static_force:>14.2f}")
    print()


def print_orifice_sensitivity(label: str, p_abs: float, mass_g: float, flow_constant: float) -> None:
    print(f"=== ORIFICE VS DWELL: {label.upper()} ===")
    constant_accel_dwell_ms = 2.0 * BARREL_LENGTH / V_TARGET * 1000.0
    print(
        f"Constant-acceleration reference dwell for {BARREL_LENGTH:.3f} m and {V_TARGET:.1f} m/s: {constant_accel_dwell_ms:.1f} ms")
    print(f"{'dwell(ms)':>10}  {'d_or(mm)':>10}")
    print("-" * 24)
    for dwell_ms in DWELL_TIMES_MS:
        diameter = orifice_diameter_mm(mass_g, p_abs, dwell_ms, flow_constant)
        print(f"{dwell_ms:>10.1f}  {diameter:>10.2f}")
    print()


def main() -> None:
    flow_constant = choke_factor()
    print(f"Choked flow constant = {flow_constant:.6f} kg/(m^2.Pa.s)")
    print(f"Target kinetic energy = {kinetic_energy():.1f} J")
    print()

    print_pressure_sensitivity()

    p_abs_old_eta, mass_old_eta = print_case_summary(
        "Corrected thermodynamics with legacy eta",
        exponent=1.25,
        efficiency=0.20,
        flow_constant=flow_constant,
    )
    p_abs_baseline, mass_baseline = print_case_summary(
        "Recommended baseline",
        exponent=1.25,
        efficiency=0.50,
        flow_constant=flow_constant,
    )

    print_bore_table("corrected thermodynamics with legacy eta", p_abs_old_eta)
    print_bore_table("recommended baseline", p_abs_baseline)
    print_orifice_sensitivity("recommended baseline",
                              p_abs_baseline, mass_baseline, flow_constant)


if __name__ == "__main__":
    main()
