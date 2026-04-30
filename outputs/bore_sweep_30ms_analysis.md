# CO₂ Pneumatic Launcher — Bore Sweep Analysis for 30 m/s / 100 m Operational Range

**Date:** 2026-04-30
**Scope:** Design study for a CO₂ pneumatic launcher that gives a 1 kg self-propelled UAV payload an initial muzzle velocity of 30 m/s, enabling a 100 m operational range. Four bore sizes are compared: radius 60, 80, 100, 120 mm (diameters 120, 160, 200, 240 mm).

---

## 1. Operational Range → Minimum Muzzle Velocity

### 1.1 Purely Ballistic Baseline (no UAV propulsion)

The ballistic range formula for a projectile with no drag and no self-propulsion is:

$$
R = \frac{v^2 \sin(2\theta)}{g}
$$

The **worst-case (maximum range)** launch angle is $\theta = 45°$, giving $\sin(2 \times 45°) = \sin(90°) = 1$. Solving for the minimum muzzle velocity required to reach 100 m by ballistics alone:

$$
v_{\text{min,ballistic}} = \sqrt{R \times g} = \sqrt{100 \times 9.81} = \sqrt{981} \approx 31.3 \; \text{m/s}
$$

This is the **absolute minimum muzzle velocity if the payload had zero propulsion**. Any slower and a passive projectile cannot reach 100 m even at the optimal angle.

### 1.2 Corrected Minimum with UAV Self-Propulsion

The interceptor UAV has its own motors. After exiting the barrel it flies under its own power and contributes additional velocity. Assuming the UAV's propulsion contributes an effective **10 m/s** to the range budget (conservative — modern 3-inch quads can cruise at 15–25 m/s), the launcher only needs to supply the remainder.

Using energy-equivalent velocity subtraction:

$$
v_{\text{muzzle}} = \sqrt{v_{\text{min,ballistic}}^2 - v_{\text{UAV}}^2} = \sqrt{31.3^2 - 10^2} = \sqrt{980.7 - 100} = \sqrt{880.7} \approx 29.7 \; \text{m/s}
$$

Rounded up for margin: **target muzzle velocity = 30 m/s**.

---

## 2. Corrected Design Parameters

| Parameter | Symbol | Value | Notes |
| --- | --- | --- | --- |
| Payload mass (with sabot) | $m$ | 1.0 kg | |
| Target muzzle velocity | $v$ | 30 m/s | From §1.2 |
| Chamber volume | $V_1$ | 1.0 L = 0.001 m³ | Fixed for sweep |
| Barrel length | $L$ | 700 mm | Fixed for sweep |
| Ambient temperature | $T$ | 293.15 K | 20°C |
| CO₂ specific gas constant | $R_{\text{spec}}$ | 188.92 J/(kg·K) | $R_u / M_{\text{CO}_2}$ |
| Specific heat ratio | $\gamma$ | 1.30 | CO₂ compressible value |
| Discharge coefficient | $C_d$ | 0.80 | For QEV orifice |
| Ambient pressure | $P_{\text{atm}}$ | 1 bar = 100,000 Pa | |
| Real-gas compressibility | $Z$ | 0.990 | CO₂ near this pressure range |
| Baseline polytropic exponent | $n$ | 1.25 | Near-adiabatic fast discharge |
| Baseline launcher efficiency | $\eta$ | 0.50 | Recommended single loss term |
| Sensitivity band | $n, \eta$ | $n = 1.20$ to $1.30$, $\eta = 0.40$ to $0.60$ | Used to bound results |
| Reference dwell time | $t_{\text{dwell}}$ | 46.7 ms | Constant-acceleration reference $2L/v$ |
| Valve sizing band | $t_{\text{dwell}}$ | 25 to 50 ms | Used for orifice sensitivity |

---

## 3. Corrected Step-by-Step Derivation

### 3.1 Required Kinetic Energy

$$
KE = \frac{1}{2} m v^2 = \frac{1}{2} \times 1.0 \times 30^2 = \boxed{450 \; \text{J}}
$$

This remains the same for all bores.

### 3.2 Modeling Correction: Fast Expansion Is Not Isothermal

The original calculation used:

$$
W = P V \ln\!\left(\frac{P}{P_{\text{atm}}}\right)
$$

That is an isothermal expansion model. For a 10 to 50 ms discharge with negligible heat transfer, the chamber behavior is better represented as polytropic / near-adiabatic:

$$
P_1 V_1^n = P_2 V_2^n
$$

$$
W = \frac{P_1 V_1 - P_2 V_2}{n - 1}
$$

with $n \approx 1.2$ to $1.3$ for CO₂ in this regime.

There is a second bookkeeping issue: the original document combined an isothermal model with a very low lumped efficiency, $\eta = 0.20$. That risks counting the same losses twice.

This revision therefore uses two cases:

1. **Legacy-efficiency check:** keep $\eta = 0.20$ only to show what happens if the old loss factor is retained while the thermodynamics are corrected.
2. **Recommended baseline:** use polytropic expansion with a single lumped efficiency $\eta = 0.50$.

The corresponding gas-work targets are:

$$
W_{\text{req,legacy}} = \frac{450}{0.20} = \boxed{2250 \; \text{J}}
$$

$$
W_{\text{req,baseline}} = \frac{450}{0.50} = \boxed{900 \; \text{J}}
$$

### 3.3 Required Chamber Pressure With Polytropic Expansion

Using $n = 1.25$ and $P_2 = P_{\text{atm}}$, the final volume at atmospheric discharge is:

$$
V_2 = V_1 \left(\frac{P_1}{P_{\text{atm}}}\right)^{1/n}
$$

Substituting into the polytropic work expression gives a transcendental pressure solve:

$$
W = \frac{P_1 V_1 - P_{\text{atm}} V_1 \left(P_1 / P_{\text{atm}}\right)^{1/n}}{n - 1}
$$

Solved by bisection for $V_1 = 0.001$ m³:

| Case | $n$ | $\eta$ | $W_{\text{req}}$ (J) | $P_1$ (bar abs) | $P_g$ (bar gauge) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Legacy-efficiency check | 1.25 | 0.20 | 2250 | **13.779** | **12.779** |
| Recommended baseline | 1.25 | 0.50 | 900 | **6.985** | **5.985** |

So the old single-point result of 9.84 bar abs is **not a stable design conclusion**. Once the expansion model is corrected, the answer depends strongly on how losses are represented.

Pressure sensitivity across the realistic band is:

| $n$ | $\eta = 0.40$ | $\eta = 0.50$ | $\eta = 0.60$ |
| ---: | ---: | ---: | ---: |
| 1.20 | 7.772 bar abs | 6.648 bar abs | 5.871 bar abs |
| 1.25 | 8.191 bar abs | 6.985 bar abs | 6.154 bar abs |
| 1.30 | 8.617 bar abs | 7.328 bar abs | 6.440 bar abs |

**Corrected insight:** thermodynamic pressure remains bore-independent for a fixed energy target and chamber volume, but it is sensitive to the thermodynamic model and to how efficiency is defined.

### 3.4 Choked Mass-Flow Constant

For choked flow through the valve orifice:

$$
\dot{m} = C_d A_{\text{or}} P_1 \sqrt{\frac{\gamma}{R_{\text{spec}} T}} \left(\frac{2}{\gamma+1}\right)^{\frac{\gamma+1}{2(\gamma-1)}}
$$

Evaluating the constant at $T = 293.15$ K, $\gamma = 1.30$, $C_d = 0.8$:

$$
\sqrt{\frac{\gamma}{R_{\text{spec}} T}} = \sqrt{\frac{1.30}{188.92 \times 293.15}} = 4.845 \times 10^{-3}
$$

$$
\left(\frac{2}{\gamma+1}\right)^{\frac{\gamma+1}{2(\gamma-1)}} = 0.5852
$$

$$
k_c = 0.8 \times 4.845 \times 10^{-3} \times 0.5852 = \boxed{0.002268 \; \text{kg/(m}^2\text{·Pa·s)}}
$$

### 3.5 CO₂ Mass per Shot

Using the real-gas ideal expression:

$$
m_{\text{CO}_2} = \frac{P_1 V_1 M_{\text{CO}_2}}{Z R_u T}
$$

This remains bore-independent for a fixed pressure, but it changes when the pressure model changes.

| Case | $P_1$ (bar abs) | CO₂ per shot |
| --- | ---: | ---: |
| Legacy-efficiency check | 13.779 | **25.13 g** |
| Recommended baseline | 6.985 | **12.74 g** |

### 3.6 Valve Sizing: 14.3 mm Is Only a Lower Bound

With a fixed dwell time, the required mass flow rate is:

$$
\dot{m}_{\text{req}} = \frac{m_{\text{CO}_2}}{t_{\text{dwell}}}
$$

and the orifice area is:

$$
A_{\text{or}} = \frac{\dot{m}_{\text{req}}}{P_1 \times \text{choke\_factor}}
$$

If $t_{\text{dwell}} = 50$ ms is held fixed, the baseline case gives:

$$
d_{\text{or,50ms}} = \boxed{14.31 \; \text{mm}}
$$

That number is useful only as a **lower-bound sizing point under the explicit 50 ms dwell assumption**. It is not a proof that valve size is bore-independent.

The bore enters through barrel dynamics: larger bores produce larger instantaneous force, different pressure decay, and therefore different dwell times and peak flow demand. A simple sensitivity check using the corrected baseline gives:

| Dwell time | Required orifice diameter |
| ---: | ---: |
| 50 ms | 14.31 mm |
| 40 ms | 16.00 mm |
| 30 ms | 18.47 mm |
| 25 ms | 20.24 mm |

So the corrected statement is:

> **Pressure and CO₂ mass are thermodynamically bore-independent for fixed energy and chamber volume, but real valve sizing is not strictly bore-independent because dwell time and flow demand depend on launcher dynamics.**

For this reason the practical valve recommendation is no longer a fixed 14 mm part. A **16 to 20 mm effective orifice** is a more defensible design band until the dwell time is solved with a coupled chamber-barrel dynamic model.

---

## 4. Corrected Bore Comparison

The smallest bore that fits the payload is still the preferred direction, but the corrected loads are different from the earlier draft.

Static endcap load remains:

$$
F_{\text{endcap}} = P_1 \times A_{\text{bore}} = P_1 \times \pi r^2
$$

The table below shows both the recommended baseline and the legacy-efficiency check, plus force design bands using structural safety factors of 2 and 3.

| Bore radius | Bore diameter | Static load at 5.985 bar g baseline | Static load at legacy 12.779 bar g | SF = 2 design load (baseline) | SF = 3 design load (baseline) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 60 mm | 120 mm | **7.90 kN** | **15.58 kN** | 15.80 kN | 23.70 kN |
| 80 mm | 160 mm | 14.04 kN | 27.70 kN | 28.09 kN | 42.13 kN |
| 100 mm | 200 mm | 21.95 kN | 43.29 kN | 43.89 kN | 65.84 kN |
| 120 mm | 240 mm | 31.60 kN | 62.34 kN | 63.20 kN | 94.80 kN |

### What this means structurally

- At the **recommended baseline**, only the 60 mm radius case remains below 10 kN static load.
- At the **legacy-efficiency check**, even the 60 mm radius case rises to 15.6 kN static and exceeds the 10 bar gauge envelope.
- With a structural force safety factor of 2 to 3, even the 60 mm radius case should be designed for **15.8 to 23.7 kN** in the baseline scenario.
- Larger bores move rapidly into a heavy flange / pressure-vessel class and are hard to justify for a portable launcher.

---

## 5. Corrected Conclusions

| Parameter | Earlier draft | Corrected interpretation |
| --- | --- | --- |
| Thermodynamic model | Isothermal | Fast discharge should be treated as polytropic / near-adiabatic |
| Pressure result | 9.84 bar abs | **6.99 bar abs baseline** with $n = 1.25$, $\eta = 0.50$; **13.78 bar abs** if the old $\eta = 0.20$ is retained |
| CO₂ per shot | 17.95 g | **12.74 g baseline** or **25.13 g** for the legacy-efficiency check |
| Orifice result | 14.31 mm fixed | **14.31 mm only at 50 ms dwell**; realistic valve band is **16 to 20 mm** if dwell is 25 to 40 ms |
| Bore effect | Endcap load only | Bore leaves the thermodynamic energy unchanged, but it strongly affects structural load, dwell time, flow demand, and therefore valve sizing |

The core design lesson still survives the correction:

> **Choose the smallest bore that geometrically fits the payload.**

That remains true because larger bores do not reduce the gas energy requirement, but they do increase endcap load dramatically and tend to make the flow problem harder rather than easier.

---

## 6. Recommendation

### Recommended interpretation of the 30 m/s scenario

The 120 mm diameter case is still the only credible option among the four bores studied, but the corrected document should no longer claim that the design is settled at 8.84 bar gauge with a 14 mm valve.

The more defensible baseline is:

| Parameter | Recommended baseline value |
| --- | --- |
| Bore radius | **60 mm** |
| Bore diameter | **120 mm** |
| Chamber model | **Polytropic, $n = 1.25$** |
| Pressure | **5.99 bar gauge** baseline, with **4.87 to 7.62 bar gauge** sensitivity over $n = 1.20$ to $1.30$, $\eta = 0.40$ to $0.60$ |
| Chamber volume | **1.0 L** |
| Barrel length | **700 mm** |
| Valve orifice | **16 to 20 mm effective ID recommended** until dwell is solved dynamically |
| CO₂ per shot | **~12.7 g baseline** |
| Static endcap load | **~7.9 kN baseline** |
| Structural design load | **15.8 to 23.7 kN** for SF = 2 to 3 |
| Operational concept | **30 m/s launch plus UAV self-propulsion** |

### Important caveat

If measured launcher efficiency is closer to the old 0.20 assumption, this 1.0 L chamber concept no longer sits inside a 10 bar gauge working envelope. In that case the corrected thermodynamics require:

- **12.78 bar gauge** chamber pressure
- **25.1 g CO₂ per shot**
- **15.6 kN** static endcap load even for the 120 mm diameter bore

That is a materially different system class.

---

## 7. Notes and Remaining Limits

1. The 120 to 240 mm bores studied here are much larger than the earlier 52 mm concept. They should be treated as a different launcher class, not as a direct scale-up.
2. The pressure solve is corrected, but valve sizing still needs a coupled chamber-barrel transient model if this document is to be used for procurement or detailed fabrication.
3. The constant-acceleration reference dwell is $2L/v = 46.7$ ms. Actual dwell can be shorter because acceleration is front-loaded, which is why the valve recommendation is given as a band rather than a single number.
4. A 14.3 mm valve is still mathematically consistent with a 50 ms dwell assumption. The correction is that this should be treated as a lower-bound estimate, not as the final answer.
5. The structural design should not use static force alone. A force safety factor of 2 to 3 is appropriate to cover valve-opening shock, non-uniform loading, and modeling uncertainty.
6. The 100 m operational range still depends on UAV self-propulsion. A purely ballistic 30 m/s launch is marginal even before aerodynamic drag is included.
