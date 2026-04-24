from docx import Document
import math
import os

# Directories: scripts live in `scripts/`, runtime outputs go to `outputs/`, documents to `docs/`.
# `BASE_DIR` is the directory containing this script (scripts/ after reorganization).
BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'outputs'))
DOCS_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'docs'))
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

# Parameters inferred from the schematic image (labels on the figure)
# Charge chamber: 1.0 L accumulator
V0 = 1.0e-3  # m^3
# Working pressure shown on accumulator: 15 bar (gauge)
P0_gauge_bar = 15.0  # bar (gauge)
BAR = 1.0e5  # Pa per bar
P0_abs = (P0_gauge_bar + 1.0) * BAR  # convert to absolute Pa
Pf = 1.0e5  # atmospheric pressure (Pa)

# Barrel geometry from figure: 52 mm ID, 700 mm length
barrel_id = 0.052  # m
barrel_length = 0.700  # m
barrel_area = math.pi * (barrel_id / 2.0) ** 2

def isothermal_work(P0, V, Pf=Pf):
	"""Return theoretical isothermal work available from expansion from P0 to Pf."""
	return P0 * V * math.log(P0 / Pf)

def required_P0_for_work(W_target, V, Pf=Pf, Pmin=None, Pmax=None):
	"""Find P0 (absolute Pa) such that isothermal_work(P0,V) = W_target using bisection."""
	if Pmin is None:
		Pmin = Pf * 1.000001
	if Pmax is None:
		Pmax = 300 * BAR

	def f(P):
		return isothermal_work(P, V, Pf) - W_target

	if f(Pmin) >= 0:
		return Pmin
	if f(Pmax) < 0:
		raise ValueError("Pmax too low to reach target work")

	for _ in range(100):
		mid = 0.5 * (Pmin + Pmax)
		if f(mid) > 0:
			Pmax = mid
		else:
			Pmin = mid
	return 0.5 * (Pmin + Pmax)


doc = Document()

doc.add_heading('Pneumatic Launcher Feasibility Analysis (Detailed Calculations)', 0)

doc.add_paragraph(
	"This document expands the high-level analysis with numeric examples derived from the provided schematic (chamber 1.0 L, 15 bar working pressure, 52 mm barrel ID, 700 mm barrel length)."
)

doc.add_heading('1. Input Parameters (from image)', level=1)
doc.add_paragraph(f"Charge chamber volume: {V0*1e3:.1f} mL (1.0 L label)")
doc.add_paragraph(f"Working pressure: {P0_gauge_bar:.1f} bar (gauge) → {P0_abs/1e5:.2f} bar absolute")
doc.add_paragraph(f"Barrel: ID = {barrel_id*1000:.0f} mm, Length = {barrel_length*1000:.0f} mm")

doc.add_heading('2. Theoretical Isothermal Work from Chamber', level=1)
W_ideal = isothermal_work(P0_abs, V0)
doc.add_paragraph(f"Isothermal work (ideal) from {P0_gauge_bar:.1f} bar gauge in {V0*1e3:.1f} mL: {W_ideal:.0f} J")

doc.add_heading('3. Representative Payload Scenarios', level=1)
doc.add_paragraph("We evaluate 3 representative payload masses and a range of effective energy transfer efficiencies to capture flow and thermodynamic losses.")

masses = [0.2, 0.5, 1.0]  # kg (typical small interceptor payloads)
efficiencies = [0.25, 0.5, 0.75]

for m in masses:
	doc.add_heading(f'Mass = {m:.2f} kg', level=2)
	# ideal velocity if all ideal energy converted
	v_ideal = math.sqrt(2.0 * W_ideal / m)
	doc.add_paragraph(f'Ideal (no losses) muzzle velocity: {v_ideal:.1f} m/s')

	# table-like lines for different efficiencies
	for eff in efficiencies:
		W_eff = W_ideal * eff
		v_eff = math.sqrt(2.0 * W_eff / m)
		F_peak = P0_abs * barrel_area
		F_avg = W_eff / barrel_length
		a_peak = F_peak / m
		a_avg = F_avg / m
		doc.add_paragraph(
			f'Efficiency {eff*100:.0f}%: energy={W_eff:.0f} J, v={v_eff:.1f} m/s, '
			f'avg accel={a_avg/9.81:.1f} g, peak accel~{a_peak/9.81:.0f} g'
		)

doc.add_heading('4. Barrel Acceleration & g-Loads (consistency with schematic)', level=1)
doc.add_paragraph(
	'The schematic annotation lists peak acceleration ≈ 20–40 g. Solving for muzzle velocity achievable at those g levels over a 0.7 m barrel gives:'
)

for g_target in [20.0, 40.0]:
	a_target = g_target * 9.81
	v = math.sqrt(2.0 * a_target * barrel_length)
	doc.add_paragraph(f'{g_target:.0f} g (peak) → muzzle velocity ≈ {v:.1f} m/s')

doc.add_heading('5. Required Charge Pressure For Given Target Velocity', level=1)
doc.add_paragraph('Compute required P0 to deliver Ek (neglecting losses) for a few target velocities:')
for v_target in [15.0, 20.0, 25.0, 30.0]:
	Ek_per_mass_examples = []
	# show results for a 0.5 kg baseline
	m_ref = 0.5
	Ek = 0.5 * m_ref * v_target ** 2
	# require ideal work W = Ek -> solve for P0
	try:
		P_needed = required_P0_for_work(Ek, V0)
		P_needed_gauge_bar = P_needed / BAR - 1.0
		doc.add_paragraph(
			f'For m={m_ref:.2f} kg and v={v_target:.0f} m/s: Ek={Ek:.0f} J → required P0 ≈ {P_needed_gauge_bar:.1f} bar (gauge)'
		)
	except ValueError:
		doc.add_paragraph(f'For v={v_target:.0f} m/s: required pressure exceeds solver maximum (>{300} bar)')

doc.add_heading('6. Notes on Flow & Real-World Losses', level=1)
doc.add_paragraph(
	'Practical delivered energy is significantly less than the ideal isothermal work due to valve flow limits, choked flow, piping losses, and rapid expansion (adiabatic cooling). Typical overall transfer efficiencies for short, fast discharges are in the 20–50% range; our examples used 25–75% to bracket possibilities.'
)

doc.add_heading('7. Quick Summary (numbers)', level=1)
doc.add_paragraph(f'Barrel cross-sectional area: {barrel_area:.6f} m^2')
doc.add_paragraph(f'Ideal isothermal work at {P0_gauge_bar:.1f} bar (gauge): {W_ideal:.0f} J')

out_path = os.path.join(DOCS_DIR, 'pneumatic_launcher_analysis.docx')
doc.save(out_path)

out_path

# ---- Additional structural and thrust calculations ----
doc2 = Document()
doc2.add_heading('Supplementary: Thrust, Impulse, and Aluminum Structural Checks', 0)

# Material: 6061-T6 typical properties (conservative)
mat_yield = 276e6  # Pa (approx for 6061-T6)
mat_ultimate = 310e6  # Pa
safety_factor = 3.0
allowable = mat_yield / safety_factor

doc2.add_paragraph(f'Material: 6061-T6 (assumed). Yield ≈ {mat_yield/1e6:.0f} MPa; using SF={safety_factor:.1f} → allowable = {allowable/1e6:.1f} MPa')

# Thrust & impulse estimates
doc2.add_heading('Thrust & Impulse Estimates', level=1)
doc2.add_paragraph(f'Peak theoretical force (instant opening) at P0={P0_gauge_bar:.1f} bar gauge: F_peak = P0_abs * A = {P0_abs*barrel_area:.1f} N')

for m in masses:
	for eff in efficiencies:
		W_eff = W_ideal * eff
		v_eff = math.sqrt(2.0 * W_eff / m)
		impulse = m * v_eff
		# estimate discharge time as barrel_length / v_eff (crude)
		t_est = barrel_length / v_eff if v_eff > 0 else float('inf')
		F_avg = W_eff / barrel_length
		doc2.add_paragraph(
			f'm={m:.2f} kg, eff={eff*100:.0f}% → v={v_eff:.1f} m/s, impulse={impulse:.1f} N·s, t~{t_est*1e3:.1f} ms, avg F={F_avg:.0f} N'
		)

doc2.add_heading('Aluminum Structural Checks (thin-wall cylinder formulas)', level=1)
doc2.add_paragraph('We compute required wall thickness for a thin-walled cylinder under internal pressure using hoop stress allowables.')

# Barrel thin-wall hoop stress: sigma_hoop = P * r / t  -> t = P * r / sigma_allowable
r_barrel = barrel_id / 2.0
t_req_hoop = P0_abs * r_barrel / allowable
t_req_axial = P0_abs * r_barrel / (2.0 * allowable)
doc2.add_paragraph(f'Barrel inner radius = {r_barrel*1e3:.1f} mm')
doc2.add_paragraph(f'Required thickness (hoop) at P0: {t_req_hoop*1e3:.2f} mm; (axial controls: {t_req_axial*1e3:.2f} mm)')

# Compare to common wall thicknesses
common_thicknesses = [0.002, 0.003, 0.005, 0.008]
for t in common_thicknesses:
	sigma_hoop = P0_abs * r_barrel / t
	sf = mat_yield / sigma_hoop
	doc2.add_paragraph(f'Thickness {t*1e3:.1f} mm → hoop stress {sigma_hoop/1e6:.1f} MPa, implied SF vs yield ≈ {sf:.2f}')

doc2.add_paragraph('For the charge chamber (1.0 L), geometry not specified. We compute required thickness for a range of assumed diameters (0.04–0.12 m) to illustrate sensitivity:')
for D in [0.04, 0.06, 0.08, 0.10, 0.12]:
	r = D / 2.0
	t_req = P0_abs * r / allowable
	doc2.add_paragraph(f'Assumed chamber diameter {D*1e3:.0f} mm → required t ≈ {t_req*1e3:.2f} mm')

doc2.add_heading('Conclusions and Recommendations', level=1)
doc2.add_paragraph(
	'1) Peak theoretical forces are large — structural checks must use actual component geometries.\n'
	'2) Barrel thin-wall calculations show required thickness on order shown above; choose a thickness that gives SF≥3 against yield.\n'
	'3) Charge chamber thickness depends strongly on diameter; use measured geometry and apply pressure-vessel formulas or standard fittings rated for the working pressure.\n'
	'4) Add valves and piping flow analysis (mass flow, choked flow) to predict realistic time-history, peak pressure drop and resulting thrust impulse more accurately.'
)

out_path2 = os.path.join(DOCS_DIR, 'pneumatic_launcher_analysis_structural.docx')
doc2.save(out_path2)

out_path2

# ---- Transient 1D launcher simulation (compressible orifice + projectile motion) ----
def simulate_transient(m_payload=1.0,
					   Vc=V0,
					   P0=P0_abs,
					   A_bore=barrel_area,
					   L=barrel_length,
					   orifice_d=0.012,
					   C_d=0.8,
					   friction_coeff=0.10,
					   T=293.15,
					   gamma=1.3,
					   dt=1e-4,
					   t_max=0.2):
	"""Simulate discharge and projectile motion until exit or t_max.
	Returns summary dict and time histories.
	"""
	R_u = 8.31446261815324
	M_co2 = 0.04401  # kg/mol
	R_spec = R_u / M_co2

	# --- Real-gas compressibility using Redlich-Kwong EOS ---
	Tc = 304.1282  # K
	Pc_RK = 7.3773e6  # Pa
	a_RK = 0.42748 * R_u * R_u * Tc * Tc / Pc_RK
	b_RK = 0.08664 * R_u * Tc / Pc_RK

	def compressibility_Z_RK(P, T):
		# solve cubic for Z using RK in terms of Z; use simple Newton on molar volume
		# initial guess ideal Z=1
		Z = 1.0
		for _ in range(60):
			Vm = Z * R_u * T / P
			# f(Vm) = P - R*T/(Vm - b) + a/(Vm*(Vm + b)*math.sqrt(T))
			f = P - R_u * T / (Vm - b_RK) + a_RK / (Vm * (Vm + b_RK) * math.sqrt(T))
			# df/dVm (approx)
			df = (R_u * T) / ((Vm - b_RK) ** 2) - a_RK * ( (2*Vm + b_RK) ) / ( (Vm * (Vm + b_RK))**2 * math.sqrt(T) )
			if df == 0:
				break
			dVm = -f / df
			Vm += dVm
			if Vm <= 0:
				Vm = 1e-6
			Z_new = P * Vm / (R_u * T)
			if abs(Z_new - Z) < 1e-6:
				Z = Z_new
				break
			Z = Z_new
		return max(0.1, min(10.0, Z))

	# compute initial compressibilities and densities
	Zc = compressibility_Z_RK(P0, T)
	rho_c0 = P0 * M_co2 / (Zc * R_u * T)
	m_c = rho_c0 * Vc
	# small initial barrel volume (clearance) to avoid zero
	Vb = 1e-6
	P_atm = Pf
	Zb0 = compressibility_Z_RK(P_atm, T)
	rho_b0 = P_atm * M_co2 / (Zb0 * R_u * T)
	m_b = rho_b0 * Vb

	# geometry
	r_or = orifice_d / 2.0
	A_or = math.pi * r_or * r_or

	x = 0.0
	v = 0.0
	t = 0.0

	times = []
	xs = []
	vs = []
	Pcs = []
	Pbs = []
	mdots = []

	def critical_pratio(gamma):
		return (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))

	pr_crit = critical_pratio(gamma)

	while t < t_max and x < L:
		Vb = A_bore * x + 1e-6
		Zc = compressibility_Z_RK(max(P_atm, P0 * 1e-12), T)
		Pc = (m_c / Vc) * R_u * T / M_co2 * (1.0 / Zc) if Vc > 0 else P_atm
		Zb = compressibility_Z_RK(max(P_atm, P0 * 1e-12), T)
		Pb = (m_b / Vb) * R_u * T / M_co2 * (1.0 / Zb)

		# compute mass flow from chamber to barrel
		p_ratio = Pb / Pc if Pc > 0 else 1.0
		if p_ratio <= pr_crit:
			# choked flow
			factor = (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (2.0 * (gamma - 1.0)))
			mdot = C_d * A_or * Pc / math.sqrt(R_spec * T) * math.sqrt(gamma) * factor
		else:
			# unchoked isentropic mass flow formula (from compressible orifice relations)
			term = (2.0 * gamma / (gamma - 1.0)) * ( (p_ratio) ** (2.0/gamma) - (p_ratio) ** ((gamma+1.0)/gamma) )
			if term < 0:
				mdot = 0.0
			else:
				mdot = C_d * A_or * Pc / math.sqrt(R_spec * T) * math.sqrt(term)

		# limit mdot to available mass in chamber
		mdot = min(mdot, m_c / dt)

		# update masses
		m_c -= mdot * dt
		m_b += mdot * dt

		# pressures update (use RK compressibility for chamber and barrel)
		Zc = compressibility_Z_RK(max(P0 * 1e-12, (m_c>0 and (m_c*R_u*T/(M_co2*(Vc))) or P_atm) ), T)
		Pc = (m_c / Vc) * R_u * T / M_co2 * (1.0 / Zc)
		Vb = A_bore * x + 1e-6
		Zb = compressibility_Z_RK(max(Pb if 'Pb' in locals() else P_atm, P_atm), T)
		Pb = (m_b / Vb) * R_u * T / M_co2 * (1.0 / Zb)

		# force on projectile
		F_friction = friction_coeff * (Pc * A_bore)
		F_net = max(0.0, (Pb - P_atm) * A_bore - F_friction)

		# integrate projectile motion
		a = F_net / m_payload
		v += a * dt
		x += v * dt

		times.append(t)
		xs.append(x)
		vs.append(v)
		Pcs.append(Pc)
		Pbs.append(Pb)
		mdots.append(mdot)

		t += dt

		# if chamber empty or pressure close to atm, break
		if Pc <= P_atm * 1.01:
			# allow some residual movement then stop
			if x >= L or v < 0.001:
				break

	# summaries
	impulse = m_payload * vs[-1]
	muzzle_v = vs[-1]
	peak_F = max([(Pbs[i]-P_atm)*A_bore for i in range(len(Pbs))]) if Pbs else 0.0
	avg_F = impulse / t if t>0 else 0.0

	return {
		'time': times,
		'x': xs,
		'v': vs,
		'Pc': Pcs,
		'Pb': Pbs,
		'mdot': mdots,
		'impulse': impulse,
		'muzzle_v': muzzle_v,
		'peak_F': peak_F,
		'avg_F': avg_F,
		't_end': t,
	}


# Run a default transient simulation and write results
sim = simulate_transient(m_payload=1.0, orifice_d=0.012, C_d=0.8)

doc3 = Document()
doc3.add_heading('Transient Simulation Results (1D)', 0)
doc3.add_paragraph(f"Muzzle velocity (simulated): {sim['muzzle_v']:.2f} m/s")
doc3.add_paragraph(f"Impulse delivered: {sim['impulse']:.2f} N·s")
doc3.add_paragraph(f"Simulated discharge time: {sim['t_end']*1e3:.1f} ms")
doc3.add_paragraph(f"Peak force on projectile (sim): {sim['peak_F']:.0f} N; average force: {sim['avg_F']:.0f} N")

# Endcap bolt check
doc3.add_heading('Endcap / Bolt Shear Check', level=1)
F_axial = P0_abs * math.pi * (r_barrel ** 2)
doc3.add_paragraph(f'Approx axial force on endcap at P0: {F_axial:.0f} N')
# bolt capacities (approx tensile stress area)
bolt_sizes = {'M6': 20e-6, 'M8': 36.6e-6, 'M10': 58e-6}  # area m^2 (tensile stress area approximate)
shear_strength = 240e6  # Pa (conservative shear capacity)
for name, A_bolt in bolt_sizes.items():
	cap = A_bolt * shear_strength
	n_needed = math.ceil(F_axial / cap)
	doc3.add_paragraph(f'{name}: bolt shear cap ≈ {cap:.0f} N → bolts required ≈ {n_needed}')

out_path3 = os.path.join(DOCS_DIR, 'pneumatic_launcher_analysis_transient.docx')
doc3.save(out_path3)

out_path3

# ---- Parametric sweep and detailed flange checks ----
import csv
import json

def flange_bolt_check(F_axial, n_bolts=6, pcd=0.08, bolt_dia=0.008, mat_shear=240e6):
	# simple check: dividing axial into n_bolts shear
	A_bolt = math.pi * (bolt_dia/2.0)**2
	cap_per_bolt = A_bolt * mat_shear
	bolts_needed = math.ceil(F_axial / cap_per_bolt)
	return {'n_bolts': n_bolts, 'cap_per_bolt_N': cap_per_bolt, 'bolts_needed': bolts_needed}

def run_parametric_sweep():
	orifice_ds = [0.006, 0.008, 0.010, 0.012, 0.015, 0.018]
	Vcs = [0.5e-3, 0.8e-3, 1.0e-3, 1.2e-3]
	Cds = [0.6, 0.7, 0.8]
	rows = []
	for d in orifice_ds:
		for Vc_test in Vcs:
			for Cd in Cds:
				simr = simulate_transient(m_payload=1.0, Vc=Vc_test, orifice_d=d, C_d=Cd)
				rows.append({
					'orifice_d_m': d,
					'Vc_m3': Vc_test,
					'Cd': Cd,
					'muzzle_v': simr['muzzle_v'],
					'impulse': simr['impulse'],
					't_end_s': simr['t_end'],
					'peak_F': simr['peak_F']
				})
	csv_path = os.path.join(OUTPUT_DIR, 'parametric_sweep.csv')
	with open(csv_path, 'w', newline='') as f:
		writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
		writer.writeheader()
		writer.writerows(rows)

	json_path = os.path.join(OUTPUT_DIR, 'parametric_sweep_summary.json')
	with open(json_path, 'w') as jf:
		json.dump(rows, jf, indent=2)

	return csv_path, json_path

csv_path, json_path = run_parametric_sweep()

# write a small verification summary file
summary = {
	'W_ideal_J': W_ideal,
	'P0_abs_Pa': P0_abs,
	'barrel_area_m2': barrel_area,
	'transient_report': out_path3,
	'structural_report': out_path2,
	'parametric_csv': csv_path,
	'parametric_json': json_path
}
summary_path = os.path.join(OUTPUT_DIR, 'analysis_summary.json')
with open(summary_path, 'w') as sf:
	json.dump(summary, sf, indent=2)

summary_path

# ---- Generate plots from parametric sweep and final flange checks ----
try:
	import matplotlib.pyplot as plt
	with open(json_path, 'r') as jf:
		param = json.load(jf)

	orifices = sorted(list(set([round(p['orifice_d_m'],6) for p in param])))
	Vcs_list = sorted(list(set([p['Vc_m3'] for p in param])))
	Cds_list = sorted(list(set([p['Cd'] for p in param])))

	plot_files = []
	for Vc_plot in Vcs_list:
		plt.figure()
		for Cd_plot in Cds_list:
			xs = []
			ys = []
			for o in orifices:
				match = [p for p in param if abs(p['orifice_d_m']-o)<1e-9 and abs(p['Vc_m3']-Vc_plot)<1e-12 and abs(p['Cd']-Cd_plot)<1e-12]
				if match:
					xs.append(o*1e3)
					ys.append(match[0]['muzzle_v'])
			if xs:
				plt.plot(xs, ys, marker='o', label=f'Cd={Cd_plot}')
		plt.xlabel('Orifice diameter (mm)')
		plt.ylabel('Muzzle velocity (m/s)')
		plt.title(f'Muzzle velocity vs orifice (Vc={Vc_plot*1e3:.1f} mL)')
		plt.legend()
		plt.grid(True)
		fp = os.path.join(OUTPUT_DIR, f'vel_vs_orifice_Vc_{int(Vc_plot*1e6)}uL.png')
		plt.savefig(fp)
		plt.close()
		plot_files.append(fp)

	# Peak force plot for Vc=1.0L
	plt.figure()
	for Cd_plot in Cds_list:
		xs = []
		ys = []
		for o in orifices:
			match = [p for p in param if abs(p['orifice_d_m']-o)<1e-9 and abs(p['Vc_m3']-1.0e-3)<1e-12 and abs(p['Cd']-Cd_plot)<1e-12]
			if match:
				xs.append(o*1e3)
				ys.append(match[0]['peak_F'])
		if xs:
			plt.plot(xs, ys, marker='x', label=f'Cd={Cd_plot}')
	plt.xlabel('Orifice diameter (mm)')
	plt.ylabel('Peak Force (N)')
	plt.title('Peak Force vs Orifice (Vc=1.0 L)')
	plt.legend()
	plt.grid(True)
	fp2 = os.path.join(OUTPUT_DIR, 'peakF_vs_orifice_Vc_1000uL.png')
	plt.savefig(fp2)
	plt.close()
	plot_files.append(fp2)

	# Impulse plot example
	plt.figure()
	for Cd_plot in Cds_list:
		xs = []
		ys = []
		for o in orifices:
			match = [p for p in param if abs(p['orifice_d_m']-o)<1e-9 and abs(p['Vc_m3']-1.0e-3)<1e-12 and abs(p['Cd']-Cd_plot)<1e-12]
			if match:
				xs.append(o*1e3)
				ys.append(match[0]['impulse'])
		if xs:
			plt.plot(xs, ys, marker='s', label=f'Cd={Cd_plot}')
	plt.xlabel('Orifice diameter (mm)')
	plt.ylabel('Impulse (N·s)')
	plt.title('Impulse vs Orifice (Vc=1.0 L)')
	plt.legend()
	plt.grid(True)
	fp3 = os.path.join(OUTPUT_DIR, 'impulse_vs_orifice_Vc_1000uL.png')
	plt.savefig(fp3)
	plt.close()
	plot_files.append(fp3)
except Exception:
	plot_files = []

# Detailed flange/bolt checks (assumed geometry)
flange_assumptions = {
	'n_bolts': 6,
	'pcd_m': 0.08,
	'bolt_dia_m': 0.008,
	'bolt_material_shear': 240e6
}
with open(json_path, 'r') as jf:
	param = json.load(jf)
worst = max(param, key=lambda p: p['peak_F'])
worst_peak = worst['peak_F']
flange_result = flange_bolt_check(worst_peak, n_bolts=flange_assumptions['n_bolts'], pcd=flange_assumptions['pcd_m'], bolt_dia=flange_assumptions['bolt_dia_m'], mat_shear=flange_assumptions['bolt_material_shear'])
flange_summary_path = os.path.join(OUTPUT_DIR, 'flange_check.json')
with open(flange_summary_path, 'w') as ff:
	json.dump({'assumptions': flange_assumptions, 'worst_peak_F_N': worst_peak, 'flange_result': flange_result, 'worst_case': worst}, ff, indent=2)

# Final summary doc
doc_final = Document()
doc_final.add_heading('Final Analysis Summary', 0)
doc_final.add_paragraph('This file summarizes the parametric sweep, transient simulation, and flange checks.')
doc_final.add_paragraph(f"Ideal isothermal work: {W_ideal:.0f} J; P0 abs: {P0_abs:.0f} Pa")
doc_final.add_paragraph(f"Worst-case simulated peak force: {worst_peak:.0f} N (see flange_check.json)")
for pf in plot_files:
	try:
		doc_final.add_paragraph(os.path.basename(pf))
		doc_final.add_picture(pf)
	except Exception:
		pass
doc_final.add_heading('Flange / Bolt Check (assumed geometry)', level=1)
doc_final.add_paragraph(json.dumps({'assumptions': flange_assumptions, 'flange_result': flange_result}, indent=2))
final_doc_path = os.path.join(DOCS_DIR, 'pneumatic_launcher_analysis_final.docx')
doc_final.save(final_doc_path)

final_doc_path

# ---- Now assemble the single comprehensive document (after plots & checks exist) ----
try:
	complete_doc = Document()
	complete_doc.add_heading('Pneumatic Launcher — Complete Analysis', 0)

	# Inputs
	complete_doc.add_heading('Input Parameters', level=1)
	complete_doc.add_paragraph(f'Charge chamber volume: {V0*1e3:.1f} mL')
	complete_doc.add_paragraph(f'Working pressure (gauge): {P0_gauge_bar:.1f} bar')
	complete_doc.add_paragraph(f'Barrel ID: {barrel_id*1000:.0f} mm; Length: {barrel_length*1000:.0f} mm')

	# Theoretical
	complete_doc.add_heading('Theoretical Energy Estimates', level=1)
	complete_doc.add_paragraph(f'Ideal isothermal work: {W_ideal:.1f} J')
	complete_doc.add_paragraph('Isothermal formula: W = P0*V0*ln(P0/Pf)')

	# Representative scenarios
	complete_doc.add_heading('Representative Payload Scenarios', level=1)
	for m in masses:
		complete_doc.add_paragraph(f'Mass = {m:.2f} kg')
		v_ideal = math.sqrt(2.0 * W_ideal / m)
		complete_doc.add_paragraph(f'Ideal muzzle velocity (no losses): {v_ideal:.1f} m/s')
		for eff in efficiencies:
			W_eff = W_ideal * eff
			v_eff = math.sqrt(2.0 * W_eff / m)
			complete_doc.add_paragraph(f'  Efficiency {eff*100:.0f}%: v = {v_eff:.1f} m/s, energy = {W_eff:.0f} J')

	# Structural summary
	complete_doc.add_heading('Structural Checks (Summary)', level=1)
	complete_doc.add_paragraph(f'6061-T6 yield: {mat_yield/1e6:.0f} MPa; design SF used: {safety_factor:.1f}')
	complete_doc.add_paragraph(f'Calculated required hoop thickness at P0: {t_req_hoop*1e3:.2f} mm')
	t_table = complete_doc.add_table(rows=1, cols=3)
	hdr = t_table.rows[0].cells
	hdr[0].text = 'Thickness (mm)'
	hdr[1].text = 'Hoop stress (MPa)'
	hdr[2].text = 'SF vs yield'
	for t in common_thicknesses:
		r = t_table.add_row().cells
		r[0].text = f'{t*1e3:.1f}'
		sigma_hoop = P0_abs * r_barrel / t
		r[1].text = f'{sigma_hoop/1e6:.1f}'
		sf = mat_yield / sigma_hoop
		r[2].text = f'{sf:.2f}'

	# Transient results
	complete_doc.add_heading('Transient 1D Simulation Results', level=1)
	complete_doc.add_paragraph(f"Simulated muzzle velocity: {sim['muzzle_v']:.2f} m/s")
	complete_doc.add_paragraph(f"Impulse delivered: {sim['impulse']:.2f} N·s")
	complete_doc.add_paragraph(f"Discharge time: {sim['t_end']*1e3:.1f} ms")
	complete_doc.add_paragraph(f"Peak force (sim): {sim['peak_F']:.0f} N; Average force: {sim['avg_F']:.0f} N")

	# Parametric sweep table (first 30 rows)
	complete_doc.add_heading('Parametric Sweep Summary (sample)', level=1)
	with open(json_path, 'r') as jf:
		ps = json.load(jf)
	sample = ps[:30]
	if sample:
		keys = ['orifice_d_m','Vc_m3','Cd','muzzle_v','impulse','t_end_s','peak_F']
		table = complete_doc.add_table(rows=1, cols=len(keys))
		for i,k in enumerate(keys):
			table.rows[0].cells[i].text = k
		for row in sample:
			rc = table.add_row().cells
			for i,k in enumerate(keys):
				val = row.get(k,'')
				if isinstance(val, float):
					rc[i].text = f"{val:.4f}" if abs(val)<1000 else f"{val:.1f}"
				else:
					rc[i].text = str(val)

	# Plots
	complete_doc.add_heading('Plots', level=1)
	for pf in plot_files:
		try:
			complete_doc.add_paragraph(os.path.basename(pf))
			complete_doc.add_picture(pf)
		except Exception:
			pass

	# Flange and bolt check
	complete_doc.add_heading('Flange and Bolt Check', level=1)
	with open(flange_summary_path, 'r') as ff:
		flange_info = json.load(ff)
	complete_doc.add_paragraph(json.dumps(flange_info, indent=2))

	# Appendix: files
	complete_doc.add_heading('Appendix: Generated Files', level=1)
	for f in [out_path, out_path2, out_path3, final_doc_path, csv_path, json_path, flange_summary_path, summary_path]:
		complete_doc.add_paragraph(f)

	# Formulas and concise conclusion
	complete_doc.add_heading('Formulas and Conclusion', level=1)
	complete_doc.add_paragraph('Key formulas used in this analysis:')
	complete_doc.add_paragraph(' - Isothermal work: W = P0 * V0 * ln(P0 / Pf)')
	complete_doc.add_paragraph(' - Thin-wall hoop stress: sigma_hoop = P * r / t  (valid when t << r)')
	complete_doc.add_paragraph('   => required thickness (hoop): t = P * r / sigma_allowable')
	complete_doc.add_paragraph(' - Axial (longitudinal) stress for thin cylinder: sigma_axial = P * r / (2 * t)')
	complete_doc.add_paragraph(' - Impulse and average force: I = m * v;  F_avg ≈ I / t_discharge (crude estimate)')

	# Numerical recommendation for 6061-T6
	allowable = mat_yield / safety_factor
	recommended_t_mm = max(0.0, t_req_hoop * 1e3)
	complete_doc.add_paragraph(f'Using 6061-T6 (yield ≈ {mat_yield/1e6:.0f} MPa) and safety factor {safety_factor:.1f}, allowable stress ≈ {allowable/1e6:.1f} MPa.')
	complete_doc.add_paragraph(f'Calculated required hoop thickness at working pressure ({P0_gauge_bar:.1f} bar gauge) is ≈ {recommended_t_mm:.2f} mm.')
	complete_doc.add_paragraph('Recommendation: select a standard tube/wall thickness equal to or greater than the calculated required thickness, and verify endcap/flange/bolt margins separately. Use ASME/EN pressure-vessel rules or certified fittings for the chamber when safety is critical.')

	complete_path = os.path.join(DOCS_DIR, 'pneumatic_launcher_analysis_complete.docx')
	complete_doc.save(complete_path)
except Exception:
	import traceback
	traceback.print_exc()
	complete_path = None

complete_path