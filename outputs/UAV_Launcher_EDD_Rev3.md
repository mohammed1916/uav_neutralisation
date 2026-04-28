**ENGINEERING DESIGN DOCUMENT**

**CO₂-Based Pneumatic Launcher System**

Autonomous / Semi-Manual Pneumatic Accelerator Platform

| **Document ID** | **EDD-UAV-001**                               |
|-----------------|-----------------------------------------------|
| Revision        | Rev 3 — Physics-Corrected (Coupled ODE Model) |
| Date            | April 2026                                    |
| Status          | Engineering Review Draft                      |
| Replaces        | Rev 2 — Updated BOM (Closed-form model)       |

> Rev 3 Change Summary: Section 4 (Physics & Modeling) has been fully rewritten. The prior closed-form velocity formula and geometric-only pressure decay equation have been replaced with a coupled three-layer ODE model (gas supply / valve flow / projectile dynamics). The BOM has been expanded with specific sourcing notes, tolerance requirements, and sub-zero rated components. All other sections are carried forward from Rev 2 with minor editorial corrections.

# Table of Contents

[Table of Contents](#table-of-contents)

[1. System Overview](#system-overview)

[1.1 Purpose](#purpose)

[1.2 Key Performance Requirements](#key-performance-requirements)

[1.3 Scope Limitations](#scope-limitations)

[2. System Architecture](#system-architecture)

[2.2 Component Interaction](#component-interaction)

[2.3 Signal & Control Flow](#signal-control-flow)

[3. Component-Level Design](#component-level-design)

[3.1 Gas Source](#gas-source)

[CO₂ Cartridge](#co₂-cartridge)

[CO₂ vs Compressed Air Trade-off](#co₂-vs-compressed-air-trade-off)

[3.2 Pressure Regulation](#pressure-regulation)

[3.3 Charge Chamber](#charge-chamber)

[Volume Estimation](#volume-estimation)

[Material and Pressure Rating](#material-and-pressure-rating)

[3.4 Valve System](#valve-system)

[Recommended Configuration: QEV + Pilot Solenoid](#recommended-configuration-qev-pilot-solenoid)

[Cv Role in the Model (IMPORTANT CORRECTION)](#cv-role-in-the-model-important-correction)

[3.5 Trigger System](#trigger-system)

[3.6 Barrel Design](#barrel-design)

[4. Physics & Modeling (Rev 3 — Coupled ODE Model)](#physics-modeling-rev-3-coupled-ode-model)

[4.0 Modeling Assumptions (Explicit)](#modeling-assumptions-explicit)

[4.1 Layer A: Gas Supply Thermodynamics](#layer-a-gas-supply-thermodynamics)

[4.2 Layer B: Valve Mass Flow Model](#layer-b-valve-mass-flow-model)

[Choked Flow Condition](#choked-flow-condition)

[Choked mass flow (sonic throat)](#choked-mass-flow-sonic-throat)

[Subsonic mass flow](#subsonic-mass-flow)

[4.3 Layer C: Projectile Dynamics (Coupled ODE)](#layer-c-projectile-dynamics-coupled-ode)

[ODE System (Correct Primary Model)](#ode-system-correct-primary-model)

[Friction Model](#friction-model)

[4.4 Parametric Results (ODE Numerical Sweeps)](#parametric-results-ode-numerical-sweeps)

[4.5 Model Limitations](#model-limitations)

[5. Simulation Approach](#simulation-approach)

[5.1 MATLAB / Simulink (Recommended First Step)](#matlab-simulink-recommended-first-step)

[5.2 CFD — ANSYS Fluent / OpenFOAM (Advanced Only)](#cfd-ansys-fluent-openfoam-advanced-only)

[5.3 Why Simulation Alone is Insufficient](#why-simulation-alone-is-insufficient)

[6. Testing & Validation](#testing-validation)

[6.1 Test Infrastructure](#test-infrastructure)

[6.2 Test Procedures](#test-procedures)

[T1: Pressure Containment Test (Hydrostatic)](#t1-pressure-containment-test-hydrostatic)

[T2: Valve Response Time Test](#t2-valve-response-time-test)

[T3: Muzzle Velocity Test](#t3-muzzle-velocity-test)

[7. Safety Considerations](#safety-considerations)

[7.1 Pressure Containment](#pressure-containment)

[7.2 Valve Failure Modes](#valve-failure-modes)

[7.3 CO₂ Thermal Effects](#co₂-thermal-effects)

[7.4 Structural Integrity](#structural-integrity)

[8. Bill of Materials (BOM) — Revised](#bill-of-materials-bom-revised)

[8.1 Launcher System BOM](#launcher-system-bom)

[8.2 Interceptor UAV Payload BOM (Appendix B)](#interceptor-uav-payload-bom-appendix-b)

[9. Design Trade-offs](#design-trade-offs)

[9.1 Barrel-Payload Compatibility](#barrel-payload-compatibility)

[9.2 Cost vs Performance](#cost-vs-performance)

[9.3 CO₂ vs Compressed Air](#co₂-vs-compressed-air)

[9.4 Manual vs Autonomous Triggering](#manual-vs-autonomous-triggering)

[10. Conclusion](#conclusion)

[10.1 Optimal Configuration Summary](#optimal-configuration-summary)

[10.2 Priority Design Risks](#priority-design-risks)

[10.3 Next Steps](#some-points-to-consider)

[11. References](#_Toc228192151)

[11.1 Technical Standards](#_Toc228192152)

[11.2 Pneumatic Components](#_Toc228192153)

[11.3 Engineering & Physics References](#_Toc228192154)

[11.4 Simulation Resources](#_Toc228192155)

[Appendix A — Revision History](#_Toc228192156)

[Appendix B — Interceptor UAV Payload Design Review](#appendix-a-interceptor-uav-payload-design-review)

[B.1 Proposed 3-inch Foldable Quadcopter](#a.1-proposed-3-inch-foldable-quadcopter)

[B.2 Proposed Specification Summary](#a.2-proposed-specification-summary)

[B.3 Technical Assessment — Correct Choices](#a.3-technical-assessment-correct-choices)

[B.4 Technical Assessment — Issues and Corrections](#a.4-technical-assessment-issues-and-corrections)

[B.5 Interceptor UAV BOM](#a.5-interceptor-uav-bom)

# 1. System Overview

This document defines the engineering design for a CO₂-based pneumatic launcher intended to accelerate a ~1 kg payload to 15–25 m/s using stored compressed CO₂ gas released through a high-flow valve-barrel assembly. The system is designed for field-portable, rapid-recharge operation.

## 1.1 Purpose

- Provide rapid, repeatable launch of a ~1 kg payload.

- Operate autonomously (solenoid trigger) or semi-manually (mechanical trigger).

- Deploy in field environments without external power infrastructure.

## 1.2 Key Performance Requirements

| **Parameter**          | **Value**          | **Notes**                |
|------------------------|--------------------|--------------------------|
| Launch velocity        | 15–25 m/s          | At barrel exit           |
| Payload mass           | ~1 kg              | With sabot               |
| Operational pressure   | 50–60 bar (source) | Regulated to 8–15 bar WP |
| System mass (launcher) | \< 5 kg            | Field portable           |
| Actuation type         | Manual + solenoid  | Dual-mode                |
| Cost target            | \< USD 300         | Prototype unit           |
| Recharge time          | \< 30 s            | Cartridge swap           |

## 1.3 Scope Limitations

- This document covers the launcher only — not the interceptor UAV payload design (see Appendix B).

- Flight trajectory, terminal guidance, and payload integration are out of scope.

- Structural mounting hardware design is indicative only.

# 2. System Architecture

The launcher consists of six functional subsystems arranged in a linear pneumatic train:

> 
> ``` math
> \mathbf{Gas\ Source\  \rightarrow \ Regulator\  \rightarrow \ Charge\ Chamber\  \rightarrow \ Pilot\ Valve\  \rightarrow \ Quick\ Exhaust\ Valve\ (QEV)\  \rightarrow \ Barrel}
> ```

## 2.2 Component Interaction

The CO₂ cartridge supplies high-pressure gas (50–60 bar) which passes through a pressure regulator set to 8–15 bar working pressure. This charges a sealed accumulator chamber of 0.5–1.0 L. The pilot valve (solenoid or mechanical trigger) releases a small control signal that actuates the Quick Exhaust Valve. The QEV dumps chamber pressure directly into the barrel, accelerating the payload down the bore.

## 2.3 Signal & Control Flow

| **Stage** | **Action** | **Component** |
|----|----|----|
| 1 — Pre-fire | Chamber charged to set pressure | Regulator + Chamber |
| 2 — Command | Trigger signal sent (manual or electrical) | Pilot valve |
| 3 — Actuation | Pilot pressure opens QEV main poppet | QEV |
| 4 — Discharge | High-flow gas released into barrel | Barrel |
| 5 — Launch | Payload exits barrel at 15–25 m/s | — |
| 6 — Reset | CO₂ cartridge recharges chamber | Regulator |

# 3. Component-Level Design

## 3.1 Gas Source

### CO₂ Cartridge

- Standard 12 g or 88 g CO₂ cylinders (paintball/SodaStream format).

- Storage pressure: 50–60 bar at 20°C (saturated liquid/vapour phase).

- Energy density is high relative to cost — ideal for intermittent use.

- 88 g cylinder provides ~45 L of gas at atmospheric pressure; sufficient for multiple launches.

### CO₂ vs Compressed Air Trade-off

| **Criterion** | **CO₂ Cartridge** | **Compressed Air Tank** |
|----|----|----|
| Working pressure | 50–60 bar (fixed) | Adjustable, 10–300 bar |
| Cost | Low (~USD 1–3/cartridge) | Moderate (~USD 50–150 tank) |
| Recharge method | Swap cartridge (\< 30 s) | Pump/compressor required |
| Thermal effects | Gas cools on expansion (Joule-Thomson) | Minimal |
| Field portability | Excellent | Moderate — tank bulk |
| Recommendation | ✔ Preferred for prototype | Preferred for sustained ops |

> CO₂ expansion causes significant barrel cooling (~−10°C to −20°C at orifice). Valve seats must tolerate this. PTFE or Buna-N seals rated to −60°C are required; standard O-rings at sub-zero temperatures will fail.

#### Verification: **Cartridge Size Justification**

Each shot consumes all gas in the charge chamber (QEV dumps it to atmosphere). The CO₂ mass required to fill the 1.0 L chamber to 10 bar gauge (11 bar absolute) at 20 °C is:

``` math
m = \frac{P_{abs} \cdot V}{R_{spec} \cdot T} = \frac{(11 \times 10^{5}) \times 0.001}{188.92 \times 293.15} = \frac{1100}{55,397} \approx 19.9\text{ g}
```

where $R_{spec}=\frac{R_u}{M_{CO_2}}=\frac{8.314}{0.04401}=188.92\,\mathrm{J\,kg^{-1}\,K^{-1}}$ for CO₂.

Real-gas correction (Z ≈ 0.97 at Tr = 0.964, Pr = 0.149 from Redlich-Kwong EOS): actual mass ≈ **20.48 g**. Ideal-gas mass (19.86 g) is lower by about **3.1%**, which is acceptable for first-pass cartridge sizing.

| Cartridge | CO₂ mass | Can fill 1.0 L chamber to 10 bar? | Full shots             |
|-----------|----------|-----------------------------------|------------------------|
| 12 g      | 12 g     | **No** — 12 g \< 20 g required    | 0                      |
| 88 g      | 88 g     | Yes                               | ~4 (with ~8 g reserve) |

Conclusion is correct: **12 g \< 20 g → insufficient. 88 g → ~4 shots.** The 12 g cartridge cannot produce even one full charge. 88 g cartridges are required. The 12 g size is only viable for chambers ≤ 0.5 L at ≤ 6 bar.

## 3.2 Pressure Regulation

- A two-stage regulator reduces 50–60 bar source to a stable 8–15 bar working pressure.

- Eliminates pressure variability between shots (cartridge depletion effect).

- Recommended: Clippard R32 or Parker R12 series. Set to 10 bar for nominal operations.

- Cracking pressure must be above ambient by at least 2× safety margin.

## 3.3 Charge Chamber

### Volume Estimation

Using the ODE-based energy balance (Section 4), the minimum chamber volume required to achieve 20 m/s exit velocity at 10 bar and 40% system efficiency is 0.5 L. The recommended design point is 1.0 L to provide margin and account for mass flow losses through the valve.

### Material and Pressure Rating

| **Property**          | **Specification**                             |
|-----------------------|-----------------------------------------------|
| Material              | 6061-T6 Aluminium or Schedule 80 steel pipe   |
| Working pressure      | 15 bar                                        |
| Test pressure         | 22.5 bar (1.5× safety factor, per ASME B31.3) |
| Burst pressure rating | 45+ bar (3× WP minimum)                       |
| Wall thickness        | Min 5 mm for aluminium at this pressure       |
| End caps              | Threaded or welded; no press-fit only         |

## 3.4 Valve System

Valve selection is the most critical design decision. The valve must pass sufficient mass flow (high Cv) to sustain barrel pressure during the payload's dwell time (~20–40 ms). Critically: Cv determines mass flow rate capacity, not exit velocity directly. Velocity is an emergent result of the full coupled ODE system (Section 4).

| **Valve Type** | **Cv** | **Response Time** | **Cost** | **Suitability** |
|----|----|----|----|----|
| Quick Exhaust Valve (QEV) | 1.5–4.0 | \< 5 ms | \$8–20 | Recommended |
| Poppet valve (direct-act) | 0.5–1.5 | 5–20 ms | \$15–35 | Acceptable |
| Globe solenoid valve | 0.1–0.5 | 10–50 ms | \$25+ | Not recommended alone |
| Diaphragm valve | 2.0–5.0 | \< 10 ms | \$30–60 | Alternative to QEV |

### Recommended Configuration: QEV + Pilot Solenoid

- QEV (e.g., SMC AQ-series, Parker, or Camozzi) is pilot-operated.

- A small solenoid valve (or manual pushbutton) acts as the pilot, sending a brief pressure pulse to actuate the QEV poppet.

- Cv requirement: Cv ≥ 1.5 for a 52 mm bore barrel at 10 bar.

- The QEV exhaust port faces the barrel inlet for maximum flow efficiency.

### Cv Role in the Model (IMPORTANT CORRECTION)

> Cv defines valve flow capacity only. It does not determine exit velocity directly. The correct causal chain is: Cv → mass flow rate → chamber pressure evolution → force on payload → acceleration → exit velocity. The full chain must be resolved by numerical integration (Section 4). A low Cv valve is flow-limiting; a high Cv valve shifts the bottleneck to chamber volume and barrel length.

## 3.5 Trigger System

| **Parameter**   | **Manual Trigger**     | **Solenoid Trigger**          |
|-----------------|------------------------|-------------------------------|
| Latency         | ~150–300 ms (human RT) | ~5–15 ms (electrical)         |
| Reliability     | High (no electronics)  | Moderate (requires power)     |
| Cost            | \$10–20                | \$15–30                       |
| Recommended for | Prototype / semi-auto  | Autonomous / timed deployment |

## 3.6 Barrel Design

- Bore diameter: 52 mm ID (fits 1 kg payload with 3D-printed sabot at ±0.5 mm tolerance).

- Length: 700 mm nominal. Longer barrel increases dwell time and final velocity, but adds mass and bulk.

- Material: 6061-T6 aluminium tube, 3 mm wall minimum at 15 bar WP.

- Barrel length vs velocity trade-off is swept numerically in the ODE model (Section 5.1).

# 4. Physics & Modeling (Rev 3 — Coupled ODE Model)

This section has been fully rewritten for Rev 3. The previous closed-form velocity equation and purely geometric pressure decay formula have been replaced with a physically consistent three-layer coupled ODE framework. The three layers are:

> Correct causal chain: Gas thermodynamics (Layer A) → Mass flow through valve (Layer B) → Projectile dynamics (Layer C) → Exit velocity
>
> The closed-form formula v = sqrt(2 P A L / m) used in Rev 1/2 is REMOVED as a primary model. It is retained only as a rough order-of-magnitude sanity check, not as a design tool. It omits valve flow constraints, pressure decay during transit, and friction coupling.

## 4.0 Modeling Assumptions (Explicit)

The following assumptions apply to all sub-models in this section:

| **Assumption** | **Justification / Limitation** |
|----|----|
| 1D flow only (lumped model) | Valid for barrel L/D ≥ 5; neglects radial pressure gradients |
| Uniform pressure in chamber at each timestep | Valid when sound transit time ≪ timestep (satisfied here) |
| No shock waves in barrel | Mach \< 0.3 for 20 m/s in 52 mm bore; subsonic regime holds |
| Adiabatic expansion (isentropic baseline) | Valid for fast events (≤30 ms dwell); add 10–20% heat loss correction factor |
| Valve modelled as compressible orifice | Cv-based ISA flow equation; choked flow condition checked explicitly |
| CO₂ modelled with Redlich-Kwong EOS ($T_{c}$ = 304.13 K, $P_{c}$ = 7.377 MPa) | already implemented in simulation. Ideal gas with γ = 1.3 retained as a cross-check only. |
| Friction lumped as empirical coefficient | Must be measured from hardware; 0.10 is initial estimate only |
| Valve response modelled as first-order lag (τ = 3–10 ms) | Based on QEV manufacturer specs; verify from T2 test |

## 4.1 Layer A: Gas Supply Thermodynamics

The charge chamber is modelled as a closed control volume. Before valve opening, the gas is at initial state P₀, T₀, V₀. After valve opening, gas escapes and the remaining gas expands.

The pressure of gas remaining in the chamber after mass m_gas has escaped is governed by the energy equation for an open system. For the adiabatic (isentropic) baseline:

> $P(t)\cdot V(t)^{\gamma}=P_{0}\cdot V_{0}^{\gamma}$ \[valid for single-phase ideal gas only\]

However, this geometric isentropic relation is NOT applied directly as P(x). Instead, pressure is updated at each timestep by the combined effect of:

- Volume increase due to payload displacement: $\Delta V = A_{bore} \times \Delta x$

- Mass loss due to outflow through the valve: $\Delta m_{out} = \dot{m}(C_v, P_{chamber}, P_{downstream}, T)\cdot\Delta t$

- Combined via ideal gas law: $P(t + \Delta t) = \dfrac{m(t + \Delta t)\,R\,T}{V(t + \Delta t)}$

> The naive form $P(x) = P^{0} \times \left( \dfrac{V^{0}}{V^{0} + A\,x} \right)^{\gamma}$ is only correct for a closed, fixed-mass chamber with no outflow. In this system the valve is open, and mass is leaving the chamber during transit, so the volume-only isentropic relation overestimates retained pressure by 15–30%. The correct update accounts for both volume change and mass loss simultaneously.

## 4.2 Layer B: Valve Mass Flow Model

The valve is modelled as a compressible orifice using the ISA/IEC 60534 standard flow equation. Mass flow rate depends on whether flow is choked (sonic at throat) or subsonic.

### Choked Flow Condition

> $\text{Choked if: }\dfrac{P_{downstream}}{P_{upstream}} < \left(\dfrac{2}{\gamma+1}\right)^{\gamma/(\gamma-1)}$

For CO₂ (γ = 1.30): choked if P₂/P₁ \< 0.546

At initial conditions (P₁ = 10 bar, P₂ = 1 bar atmospheric): P₂/P₁ = 0.10 ➡ flow is choked at valve opening. Flow transitions to subsonic when $P_{chamber}$ drops below ~5.5 bar.

### Choked mass flow (sonic throat)

> $$\dot{m}_{choked}=C_d\,A_{orifice}\,P_1\,\sqrt{\frac{\gamma}{R\,T_1}}\left(\frac{2}{\gamma+1}\right)^{\frac{\gamma+1}{2(\gamma-1)}}$$

### Subsonic mass flow

> $$\dot{m}_{subsonic}=C_d\,A_{orifice}\,P_1\,\sqrt{\frac{2\gamma}{R\,T_1\,(\gamma-1)}\left[\left(\frac{P_2}{P_1}\right)^{2/\gamma}-\left(\frac{P_2}{P_1}\right)^{(\gamma+1)/\gamma}\right]}$$

The valve $C_{v}$ is used to determine the orifice effective area for substitution into the choked-flow formula. This is the correct bridge between the $C_{v}$ datasheet value and the thermodynamic mass flow rate.

> $C_{v}$ alone does NOT predict exit velocity. It constrains the maximum available mass flow. Whether the system is flow-limited or pressure-limited depends on the ratio of valve $C_{v}$ to chamber volume to barrel dwell time. This ratio must be evaluated numerically.

## 4.3 Layer C: Projectile Dynamics (Coupled ODE)

The payload motion is governed by Newton's second law. The net force is the gas pressure acting on the bore area minus friction losses.

### ODE System (Correct Primary Model)

> $$\frac{dv}{dt}=\frac{P(t)\,A_{bore}-F_{friction}(v)}{m}$$
>
> $$\frac{dx}{dt}=v$$
>
> $$\frac{dP}{dt}=f\!\left(m_{gas}(t),V(t),\text{valve flow},\gamma\right)\quad\text{(from Layers A and B)}$$

These three equations are solved simultaneously at each timestep. The state vector is $[v,x,P,m_{gas}]$. Standard numerical integration (RK4 or similar) converges with $\Delta t = 0.1$ ms.

### Friction Model

> $$F_{friction}(v)=\mu_r\,P(t)\,A_{bore}\quad\text{(velocity-independent, pressure-scaled baseline)}$$

Where $\mu_{r}$ is the rolling/sliding resistance coefficient of the sabot in the bore. Initial estimate: $\mu_{r}\, = \, 0.10$ (i.e., 10% of driving force lost to friction). Must be empirically calibrated in T3 testing.

## 4.4 Parametric Results (ODE Numerical Sweeps)

The following table summarizes muzzle velocity predictions from the ODE model, corroborated by the parametric sweep in the analysis document. Design target is 15–25 m/s at 10 bar.

| Orifice (mm) | $v_{exit}$ (m/s) @ 10 bar | Status |
|---:|---:|---|
| 6 | 15.7 | Below target |
| 8 | 21.3 | Within target ✓ |
| 10 | 25.8 | Within target ✓ |
| 12 | 29.4 | Above target |

> Verified RK45 sweep results support an effective orifice recommendation of **8–10 mm** at 10 bar gauge with a 1.0 L chamber. The 6 mm case is below target, while 12 mm exceeds the upper target velocity band.

## 4.5 Model Limitations

- Isentropic assumption overestimates performance by ~10–20% due to heat transfer and real-gas behavior of CO₂ near saturation. Apply a 0.80–0.90 correction factor to final velocity predictions.

- Valve response time modelled as first-order lag (τ = 5 ms); real QEV onset causes brief pressure dip at barrel start. This reduces effective initial force by ~8–12%.

- Friction coefficient $\mu_{r}$= 0.10 is an estimate. Must be measured by instrumented barrel test (T3) before final model calibration.

- CO₂ at high flow rates exhibits real-gas deviation from ideal gas. Redlich-Kwong or Peng-Robinson EOS improves accuracy for P \> 8 bar. γ = 1.30 is a useful first approximation.

- Lumped model assumes uniform chamber pressure. Valid for chamber $L/D < 3$. If chamber is elongated, 1D distributed model may be needed.

> This ODE model provides a first-order design estimate with ±15% accuracy. Empirical calibration from T2 (valve timing) and T3 (muzzle velocity) tests is mandatory before field deployment. Correlate model predictions with measured data and update friction and Cd empirical parameters.

# 5. Simulation Approach

## 5.1 MATLAB / Simulink (Recommended First Step)

- Implement the coupled ODE system: $dv/dt,\ dx/dt,\ dP/dt$ as three state variables.

- Simulate valve response as a first-order lag (τ = 3–10 ms) using a transfer function block.

- Use Simscape Fluids compressed gas library for valve and pipe blocks.

- Parametric sweep: orifice diameter (6–12 mm) × chamber volume (0.5–1.5 L) × barrel length (400–800 mm).

- Expected simulation time per run: \< 1 s. Sweep of 100 configurations: \< 2 min.

## 5.2 CFD — ANSYS Fluent / OpenFOAM (Advanced Only)

- Use only if internal flow dynamics around the QEV orifice are critical.

- 2D axisymmetric model of barrel bore + projectile interface to assess blowby.

- Compressible Navier-Stokes with $k - \omega$ SST turbulence model.

- NOT recommended for initial design iteration — high computational cost for marginal benefit at this velocity regime.

## 5.3 Why Simulation Alone is Insufficient

- CO₂ phase change behavior (liquid-to-vapor at nozzle) is difficult to simulate without specialized EOS.

- Valve $C_{v}$ specifications from datasheets have ±15–25% tolerance in practice.

- Seal friction and barrel bore dimensional tolerances are not captured in 1D models.

- Empirical validation is always the ground truth — simulation guides the design space but does not replace physical testing.

# 6. Testing & Validation

## 6.1 Test Infrastructure

| **Instrument** | **Model / Spec** | **Purpose** |
|----|----|----|
| Pressure transducer | 0–20 bar, 4–20 mA, 1 kHz BW | Chamber P(t) measurement |
| DAQ system | 10 kHz sample rate minimum | Capture pressure transient |
| Optical gates (x2) | 1 mm beam, 0.1 ms resolution | Muzzle velocity |
| High-speed camera | 1000 fps minimum | Optional sabot behavior |
| Blast shield | 12 mm polycarbonate | Downrange safety |
| Pressure relief valve | Set 18 bar, ASME rated | Overpressure protection |

## 6.2 Test Procedures

### T1: Pressure Containment Test (Hydrostatic)

- Fill chamber with water to 22.5 bar (1.5× WP). Hold for 5 minutes.

- Inspect for leaks, deformation. Do not use gas for this test.

- Pass criteria: zero visible leakage, no permanent deformation.

### T2: Valve Response Time Test

- Connect pilot solenoid to signal generator with 50 ms pulse.

- Monitor chamber pressure decay with 10 kHz DAQ.

- Pass criteria: QEV response \< 10 ms from electrical signal to 10% pressure drop.

### T3: Muzzle Velocity Test

- Load dummy payload (1 kg mass with known sabot) into barrel.

- Set chamber to 8, 10, 12, 15 bar — four test conditions.

- Fire and capture optical gate timing for each. Repeat 3 shots per condition.

- Record mean and standard deviation. Compare to ODE model predictions.

- Pass criteria: $v_{exit}$ ≥ 15 m/s at 10 bar; ≤ 25 m/s at 15 bar.

- If model prediction deviates \> 15% from measured, update Cd and$\mu_{r}$ empirically.

![Figure 1 - Testing cases: The first input mentioned as "Model Prediction" refers to physics constraints mentioned above, which we must test. T1, T2, T3 are as defined in this section](UAV_Launcher_EDD_Rev3_media/media/image1.png)

# 7. Safety Considerations

## 7.1 Pressure Containment

- All pressure-carrying components must be rated to 3× maximum working pressure.

- Use pressure relief valves (PRV) set at 1.2× WP on the chamber. PRV must be downstream of the regulator.

- Never use PVC for chambers above 8 bar — catastrophic brittle failure risk.

- Inspect all threaded fittings for correct engagement (minimum 5 full threads).

- Mark all pressure-rated components with working pressure and inspection date.

## 7.2 Valve Failure Modes

| **Failure Mode** | **Effect** | **Mitigation** |
|----|----|----|
| QEV poppet stuck open | Uncontrolled discharge | PRV upstream; blast shield |
| Pilot solenoid coil short | Unintended fire | Arm/safe circuit; arming key |
| Regulator failure (open) | Overpressure in chamber | PRV rated to 1.2× WP |
| O-ring failure at fitting | Slow gas leak | Regular inspection; PTFE seals |
| Cartridge neck fracture | Rapid gas release | Containment housing over cartridge |

## 7.3 CO₂ Thermal Effects

- CO₂ exits as a cold jet (~−20°C at the regulator outlet under high flow). Exposed skin contact causes cold burns.

- Thermal contraction of aluminum at −20°C is ~0.46 mm/m — design clearances accordingly.

- All seals downstream of the regulator must be PTFE, rated for sub-zero temperatures.

- Allow 30 s warm-up time between rapid successive shots to prevent seal failure.

## 7.4 Structural Integrity

- Barrel exit must be directed in a safe zone; use a launch cage or ballistic backstop during ground testing.

- Launcher body must be rigidly mounted. Recoil impulse estimate: $F_{recoil}$ ≈ m × v / $t_{dwell}$ ≈ 1 × 20 / 0.03 ≈ 667 N. Structural mounts must account for this.

- Personnel must wear eye protection and hearing protection during all live firing tests. Minimum 5 m exclusion zone downrange.

# 8. Bill of Materials (BOM) — Revised

The following BOM has been updated for Rev 3 to include tolerance and thermal rating requirements driven by the physics model. All components below are for one complete launcher prototype.

## 8.1 Launcher System BOM

Refer [Initial BOM.docx](https://bigbangboom-my.sharepoint.com/:w:/p/mohammed_a/IQDJJww1bM5SRL-KjZQQ3bRLAT_NncloefbEUZM8DRAIYYI?e=oyDtB7)

**TOTAL (prototype unit): ~USD 249–438** (within USD 300 target at low end; high end includes test instrumentation)

> Key BOM changes vs Rev 2: (1) Pressure regulator now explicitly requires −40°C rating. (2) QEV minimum orifice ID added as ≥ 8 mm (from ODE model — 6 mm is flow-limited). (3) Barrel bore tolerance tightened to ±0.3 mm (vs ±0.5 mm). (4) O-ring kit now specifies PTFE explicitly. (5) Wiring harness upgraded to silicone-insulated. All changes driven by Section 4 ODE model outputs and CO₂ thermal requirements.

## 8.2 Interceptor UAV Payload BOM (Appendix B)

See Appendix B for the interceptor UAV sub-BOM. Combined system total is approximately USD 380–649 including the UAV payload.

# 9. Design Trade-offs

## 9.1 Barrel-Payload Compatibility

The 40×45 mm payload diagonal (60.2 mm) exceeds the 52 mm bore (51.7 mm minimum) by 11.5 mm. A close-fitting sabot is mandatory to prevent jamming.

## 9.2 Cost vs Performance

| **Decision** | **Low-Cost Option** | **High-Performance Option** | **Recommendation** |
|----|----|----|----|
| Valve | Airmax QEV (≥8 mm orifice, ~₹400) | SMC / Parker QEV (~₹3k–5k) | Use Airmax if effective orifice ≥ 8 mm |
| Chamber | Hydraulic cylinder (~₹800–1500) | Machined Al chamber (~₹2k–5k) | Hydraulic for prototype |
| Barrel | Local 6061 Al tube (~₹800–1500) | Honed precision tube (~₹3k+) | Local, verify ID tolerance |
| Trigger | Manual 3/2 valve (~₹840) | Solenoid-triggered (~₹1k–2k total) | **Manual for first prototype** |

## 9.3 CO₂ vs Compressed Air

CO₂ is optimal for a first prototype due to availability and simplicity. Compressed air is preferred if:

- More than 10 launches per operational period are required.

- Precise velocity control is required shot-to-shot.

- Operating temperature is below 5°C where CO₂ vapour pressure drops below 40 bar.

## 9.4 Manual vs Autonomous Triggering

Both modes can coexist using a simple relay: the solenoid is driven by either the fire control output OR a manual pushbutton. Autonomous triggering is required when reaction time \< 100 ms is needed (human RT is 150–300 ms).

# 10. Conclusion

## 10.1 Optimal Configuration Summary

| **Parameter** | **Selected Design Point** |
|----|----|
| Gas source | 88 g CO₂ cartridge with 2-stage regulator (10 bar WP) |
| Chamber volume | 1.0 L; 6061-T6 aluminium; 22.5 bar test pressure |
| QEV orifice | ≥ 8 mm effective orifice ID; Cv ≥ 1.5 |
| Valve type | Quick Exhaust Valve + manual pushbutton pilot |
| Barrel | 52 mm ID ±0.3 mm; 700 mm length; 6061-T6 Al |
| Predicted $v_{exit}$ | 21–26 m/s at 10 bar (ODE model; ±15%) |
| System mass | \< 4 kg assembled |
| Unit cost (prototype) | ~USD 250–300 |

## 10.2 Priority Design Risks

- Risk 1 — QEV orifice undersized: Verify effective orifice diameter ≥ 8 mm from datasheet before procurement. 6 mm orifice is flow-limited and cannot achieve \> 12 m/s per ODE model.

- Risk 2 — CO₂ seal degradation at low temperature: Use PTFE seals exclusively downstream of regulator.

- Risk 3 — Chamber overpressure: Install PRV; never bypass the regulator.

- Risk 4 — Blowby in barrel: Machine barrel bore to ±0.3 mm tolerance on payload sabot. Tighter than Rev 2 (±0.5 mm) is based on friction model sensitivity.

- Risk 5 — Model vs reality gap: ODE model has ±15% accuracy. T3 testing must confirm before field use. Update Cd and $\mu_{r}$ if deviation \> 15%.

## 10.3 Some points to consider

- By Procuring QEV and measuring actual orifice ID; we can verify $C_{v}$ from datasheet and confirm ≥ 1.5.

- Implement MATLAB ODE model: sweep orifice diameter (6–12 mm) × chamber volume (0.5–1.5 L) × barrel length (400–800 mm) at 10 bar.

- Fabricate charge chamber from hydraulic cylinder or machined Al; perform T1 hydrostatic test.

- Conduct T2 (valve response timing) and T3 (muzzle velocity) tests with 4 pressure conditions.

- Correlate ODE model with measured data; update empirical parameters Cd and $\mu_{r}$.

- Document test results and revise design if $v_{exit}$ deviates \> 15% from prediction.

# Appendix A — Interceptor UAV Payload Design Review

## A.1 Proposed 3-inch Foldable Quadcopter

This appendix covers the interceptor UAV payload that the launcher accelerates. The launcher BOM (Section 8) covers the launch system only.

## A.2 Proposed Specification Summary

Folded envelope: 60 × 40 × 32 mm. Unfolded wheelbase: 140–160 mm. Target weight: 120–180 g. 20×20 mm AIO F4/F7 flight controller with integrated 20A 4-in-1 ESC, ESP32-S3 for vision processing, 1103–1204 motors, 3-inch bi-blade props, RunCam Nano FPV camera, 2S Li-ion strip battery (300–600 mAh).

## A.3 Technical Assessment — Correct Choices

- 20×20 mm AIO FC+ESC stack is the established standard for sub-150 g craft. 1103–1204 motors are appropriate for 3-inch props.

- RunCam Nano or equivalent micro-FPV camera; 140–160° FOV is standard. 5–10° camera tilt is correct for loiter/intercept.

- TPU-damped camera mount is essential at 3-inch prop frequencies (8,000–15,000 RPM).

- Inline battery placement is correct for CG management.

## A.4 Technical Assessment — Issues and Corrections

- ESP32-S3 as primary vision board is questionable. It cannot run real-time object detection at useful frame rates (80–200 ms latency). Use OpenMV H7 (5–15 ms inference) if on-board vision is required. ESP32-S3 is acceptable for comms relay only.

- 2S Li-ion strip battery may be underpowered. Thrust-to-weight ~2:1–2.7:1 is marginal for aggressive maneuvers. Recommend 3S LiPo (300–450 mAh) for 3:1+ thrust headroom and higher C-rating.

- 32 mm folded height is not achievable with real hardware. Expect 38–45 mm. The 52 mm barrel ID provides adequate clearance for a 40–45 mm high sabot.

- Launch survivability not addressed. Peak acceleration ~20–40 g during barrel transit. All electronics must be mechanically secured with foam padding and locked connectors.

## A.5 Interceptor UAV BOM

Refer: [Initial BOM.docx](https://bigbangboom-my.sharepoint.com/:w:/p/mohammed_a/IQDJJww1bM5SRL-KjZQQ3bRLAT_NncloefbEUZM8DRAIYYI?e=oyDtB7)

> Note: The 32 mm folded height stated in the source design is not achievable with real hardware tolerances. Plan for 38–45 mm and confirm barrel bore adequacy (52 mm ID provides sufficient clearance). All electronic components must be vibration-isolated and secured against the ~20–40 g launch acceleration impulse.

**— END OF DOCUMENT —**
