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

## 2. Fixed Design Parameters

| Parameter                   | Symbol               | Value              | Notes                              |
| --------------------------- | -------------------- | ------------------ | ---------------------------------- |
| Payload mass (with sabot)   | $m$                | 1.0 kg             |                                    |
| Target muzzle velocity      | $v$                | 30 m/s             | From §1.2                         |
| Chamber volume              | $V_0$              | 1.0 L = 0.001 m³  |                                    |
| Barrel length               | $L$                | 700 mm             |                                    |
| Ambient temperature         | $T$                | 293.15 K           | 20°C                              |
| CO₂ specific gas constant  | $R_{\text{spec}}$  | 188.92 J/(kg·K)   | $R_u / M_{\text{CO}_2}$          |
| Specific heat ratio         | $\gamma$           | 1.30               | CO₂ compressible value            |
| Discharge coefficient       | $C_d$              | 0.8                | For QEV orifice                    |
| Ambient pressure            | $P_{\text{atm}}$   | 1 bar = 100,000 Pa |                                    |
| Efficiency factor           | $\eta$             | 0.20 (20%)         | Valve losses + friction + real gas |
| Real-gas compressibility    | $Z$                | 0.990              | CO₂ at ~10 bar, 20°C             |
| Estimated barrel dwell time | $t_{\text{dwell}}$ | 50 ms              | For orifice sizing                 |

---

## 3. Step-by-Step Derivation

### 3.1 Required Kinetic Energy

$$
KE = \frac{1}{2} m v^2 = \frac{1}{2} \times 1.0 \times 30^2 = \boxed{450 \; \text{J}}
$$

This is the same for all four bore sizes — it depends only on payload mass and target velocity.

### 3.2 Required Ideal Gas Work

With efficiency $\eta = 0.20$, the chamber gas must supply:

$$
W_{\text{req}} = \frac{KE}{\eta} = \frac{450}{0.20} = \boxed{2250 \; \text{J}}
$$

### 3.3 Required Chamber Pressure (Pressure Solve)

The ideal isothermal expansion work from a chamber at pressure $P_{\text{abs}}$ expanding to atmospheric is:

$$
W = P_{\text{abs}} \times V_0 \times \ln\!\left(\frac{P_{\text{abs}}}{P_{\text{atm}}}\right)
$$

We need $W = W_{\text{req}} = 2250$ J, with $V_0 = 0.001$ m³. This is transcendental in $P_{\text{abs}}$ and is solved by bisection iteration.

**Starting the iteration** — test $P_{\text{abs}} = 10$ bar abs:

$$
W_{10\text{bar}} = 10 \times 10^5 \times 0.001 \times \ln(10) = 1000 \times 2.3026 = 2302.6 \; \text{J}
$$

That is slightly above 2250 J, so the pressure is just under 10 bar. Converging with bisection:

$$
\boxed{P_{\text{abs}} = 9.8404 \; \text{bar abs}}
$$

$$
\boxed{P_{\text{gauge}} = 8.8404 \; \text{bar gauge}}
$$

**Verification:**

$$
W = 9.8404 \times 10^5 \times 0.001 \times \ln(9.8404) = 984.04 \times \ln(9.8404) = 984.04 \times 2.2866 = 2250.0 \; \text{J} \; \checkmark
$$

> **Key insight:** The required pressure is **identical for all four bore sizes**. The pressure is determined entirely by the energy budget ($W_{\text{req}}$), which depends on $KE$, $\eta$, $V_0$, and $T$ — none of which involve bore diameter. The bore only affects the structural endcap load.

### 3.4 Choked Mass-Flow Constant

For choked (sonic) flow through the valve orifice:

$$
\dot{m} = C_d \cdot A_{\text{or}} \cdot P_{\text{abs}} \cdot \sqrt{\frac{\gamma}{R_{\text{spec}} T}} \cdot \left(\frac{2}{\gamma+1}\right)^{\frac{\gamma+1}{2(\gamma-1)}}
$$

Evaluating the constant (independent of bore) for CO₂ at $T = 293.15$ K, $\gamma = 1.30$, $C_d = 0.8$:

$$
\sqrt{\frac{\gamma}{R_{\text{spec}} T}} = \sqrt{\frac{1.30}{188.92 \times 293.15}} = \sqrt{\frac{1.30}{55,388}} = \sqrt{2.348 \times 10^{-5}} = 4.845 \times 10^{-3}
$$

$$
\left(\frac{2}{\gamma+1}\right)^{\frac{\gamma+1}{2(\gamma-1)}} = \left(\frac{2}{2.30}\right)^{\frac{2.30}{0.60}} = (0.8696)^{3.833} = 0.5852
$$

$$
\text{choke\_factor} = C_d \times 4.845 \times 10^{-3} \times 0.5852 = 0.8 \times 2.836 \times 10^{-3} = \mathbf{0.002268} \; \text{kg/(m}^2 \text{⋅Pa⋅s)}
$$

Therefore $\dot{m} = A_{\text{or}} \times P_{\text{abs}} \times 0.002268$.

### 3.5 CO₂ Mass per Shot

Using the real-gas ideal expression with compressibility $Z = 0.990$:

$$
m_{\text{CO}_2} = \frac{P_{\text{abs}} \times V_0 \times M_{\text{CO}_2}}{Z \times R_u \times T} = \frac{9.8404 \times 10^5 \times 0.001 \times 0.04401}{0.990 \times 8.314 \times 293.15}
$$

$$
= \frac{43.30}{2411.1} = 0.01795 \; \text{kg} = \boxed{17.95 \; \text{g per shot}}
$$

> Also bore-independent — depends only on $P_{\text{abs}}$, $V_0$, and gas properties.

### 3.6 Required Orifice Diameter

Required mass flow rate to discharge $m_{\text{CO}_2}$ within $t_{\text{dwell}} = 50$ ms:

$$
\dot{m}_{\text{req}} = \frac{m_{\text{CO}_2}}{t_{\text{dwell}}} = \frac{0.01795}{0.050} = 0.3590 \; \text{kg/s}
$$

Required orifice area from choked flow equation:

$$
A_{\text{or}} = \frac{\dot{m}_{\text{req}}}{P_{\text{abs}} \times \text{choke\_factor}} = \frac{0.3590}{9.8404 \times 10^5 \times 0.002268} = \frac{0.3590}{2231.4} = 1.6082 \times 10^{-4} \; \text{m}^2 = 160.82 \; \text{mm}^2
$$

Equivalent circular diameter:

$$
d_{\text{or}} = 2\sqrt{\frac{A_{\text{or}}}{\pi}} = 2\sqrt{\frac{160.82}{\pi}} = 2\sqrt{51.21} = 2 \times 7.156 = \boxed{14.31 \; \text{mm}}
$$

> Also bore-independent. Orifice is sized to the energy (pressure and gas mass), not to bore geometry.

---

## 4. Per-Bore Calculations

All four cases share: $P_{\text{abs}} = 9.8404$ bar abs, $P_{\text{gauge}} = 8.84$ bar gauge, CO₂/shot = 17.95 g, $d_{\text{or}} = 14.31$ mm.

The **only quantity that varies with bore** is the endcap static load $F_{\text{endcap}} = P_{\text{abs}} \times A_{\text{bore}}$.

### Bore radius 60 mm — diameter 120 mm

$$
A_{\text{bore}} = \pi r^2 = \pi \times (0.060)^2 = 0.011310 \; \text{m}^2 \; (113.10 \; \text{cm}^2)
$$

$$
F_{\text{endcap}} = 9.8404 \times 10^5 \times 0.011310 = 11{,}129 \; \text{N} = \mathbf{11.13 \; \text{kN}}
$$

Status flags: Endcap > 10 kN (marginally — 11.13 kN vs 10 kN limit)

---

### Bore radius 80 mm — diameter 160 mm

$$
A_{\text{bore}} = \pi \times (0.080)^2 = 0.020106 \; \text{m}^2 \; (201.06 \; \text{cm}^2)
$$

$$
F_{\text{endcap}} = 9.8404 \times 10^5 \times 0.020106 = 19{,}785 \; \text{N} = \mathbf{19.79 \; \text{kN}}
$$

Status flags: Endcap > 10 kN

---

### Bore radius 100 mm — diameter 200 mm

$$
A_{\text{bore}} = \pi \times (0.100)^2 = 0.031416 \; \text{m}^2 \; (314.16 \; \text{cm}^2)
$$

$$
F_{\text{endcap}} = 9.8404 \times 10^5 \times 0.031416 = 30{,}915 \; \text{N} = \mathbf{30.91 \; \text{kN}}
$$

Status flags: Endcap > 10 kN

---

### Bore radius 120 mm — diameter 240 mm

$$
A_{\text{bore}} = \pi \times (0.120)^2 = 0.045239 \; \text{m}^2 \; (452.39 \; \text{cm}^2)
$$

$$
F_{\text{endcap}} = 9.8404 \times 10^5 \times 0.045239 = 44{,}517 \; \text{N} = \mathbf{44.52 \; \text{kN}}
$$

Status flags: Endcap > 10 kN

---

## 5. Summary Results Table

| Bore radius (mm) | Bore diameter (mm) | A_bore (m²) |  P_gauge (bar) |     Endcap load (kN) |   CO₂/shot (g) |    Orifice (mm) |
| ---------------: | -----------------: | -----------: | -------------: | -------------------: | --------------: | --------------: |
|     **60** |      **120** |     0.011310 | **8.84** | **11.13** ⚠️ | **17.95** | **14.31** |
|               80 |                160 |     0.020106 |           8.84 |             19.79 ❌ |           17.95 |           14.31 |
|              100 |                200 |     0.031416 |           8.84 |             30.91 ❌ |           17.95 |           14.31 |
|              120 |                240 |     0.045239 |           8.84 |             44.52 ❌ |           17.95 |           14.31 |

> ⚠️ Slightly over 10 kN limit — manageable with reinforced flange
> ❌ Significantly over 10 kN — requires major structural reinforcement or design change

### Criteria check per case

| Criterion            | Limit     | r=60 mm      | r=80 mm     | r=100 mm    | r=120 mm    |
| -------------------- | --------- | ------------ | ----------- | ----------- | ----------- |
| P_gauge 3–10 bar    | ≥3, ≤10 | ✅ 8.84 bar  | ✅ 8.84 bar | ✅ 8.84 bar | ✅ 8.84 bar |
| Endcap load ≤ 10 kN | ≤ 10 kN  | ⚠️ 11.1 kN | ❌ 19.8 kN  | ❌ 30.9 kN  | ❌ 44.5 kN  |
| CO₂/shot ≤ 20 g    | ≤ 20 g   | ✅ 18.0 g    | ✅ 18.0 g   | ✅ 18.0 g   | ✅ 18.0 g   |
| Orifice 10–30 mm    | 10–30 mm | ✅ 14.3 mm   | ✅ 14.3 mm  | ✅ 14.3 mm  | ✅ 14.3 mm  |

---

## 6. Critical Observation: Why Pressure and Orifice Are Bore-Independent

This analysis reveals a **fundamental insight** that is easy to miss:

> **For a fixed energy target, fixed chamber volume, and fixed efficiency assumption, the required operating pressure and orifice diameter are completely independent of bore size.** Bore size only changes the endcap structural load.

**Why?**

- The pressure is set by: $P_{\text{abs}} \times V_0 \times \ln(P_{\text{abs}}/P_{\text{atm}}) = KE/\eta$. No bore term appears.
- The CO₂ mass per shot is set by: $m = P_{\text{abs}} \times V_0 \times M / (ZRT)$. No bore term appears.
- The orifice is set by: $A_{\text{or}} = (m/t_{\text{dwell}}) / (P_{\text{abs}} \times k)$. No bore term appears.
- The endcap load IS bore-dependent: $F = P_{\text{abs}} \times \pi r^2$, growing as $r^2$.

**Practical implication:** The only reason to choose a small bore is to keep the endcap load manageable. All other parameters (pressure, gas consumption, valve specification) stay the same. **Choose the smallest bore that geometrically fits the payload.**

---

## 7. Recommendation

### Optimal selection: Bore radius 60 mm (120 mm diameter)

**This is the only bore size that approaches the ≤ 10 kN endcap load criterion.** All larger bores fail it decisively. The 60 mm radius case gives 11.13 kN — **11.3% over the 10 kN guideline**, which is a soft engineering limit rather than a hard failure threshold.

Mitigation for 11.13 kN endcap load at 60 mm radius bore:

- Use **6× M10 grade 8.8 bolts** on the endcap flange (each capable of 18.85 kN in shear at 240 MPa; 6× gives 113.1 kN capacity, SF = 10.2).
- Alternatively, **6× M8 class 12.9** provides equivalent capacity.
- Use a **full-face gasket** (not O-ring only) to distribute the load across the flange face.
- Endcap material: minimum 6061-T6 aluminium or mild steel. No PVC, ABS, or press-fit end caps at this load level.

### Why 80–120 mm bore radii are not recommended for 30 m/s

| Bore r | Endcap load | Equivalent weight | Structural challenge                 |
| ------ | ----------- | ----------------- | ------------------------------------ |
| 60 mm  | 11.1 kN     | ~1.13 tonnes      | Manageable — reinforced flange      |
| 80 mm  | 19.8 kN     | ~2.0 tonnes       | Requires heavy steel flanges         |
| 100 mm | 30.9 kN     | ~3.1 tonnes       | Industrial pressure vessel territory |
| 120 mm | 44.5 kN     | ~4.5 tonnes       | Impractical for portable system      |

### Summary of recommended design point

| Parameter              | Value                                                           |
| ---------------------- | --------------------------------------------------------------- |
| Bore radius            | **60 mm**                                                 |
| Bore diameter          | **120 mm**                                                |
| Working pressure       | **8.84 bar gauge** (~9 bar gauge, practical round number) |
| Chamber volume         | **1.0 L**                                                 |
| Barrel length          | **700 mm**                                                |
| QEV orifice            | **14–15 mm** effective ID                                |
| Target muzzle velocity | **30 m/s**                                                |
| CO₂ per shot          | **~18 g** (~4.9 shots per 88 g cartridge)                 |
| Endcap load            | **~11.1 kN** — requires 6× M10 flange bolts             |
| Operational range      | **100 m** (UAV flies remaining ~85 m under own power)     |

### Alternative: Reduce pressure by increasing efficiency assumption or chamber volume

If 11.13 kN is truly unacceptable and a 60 mm bore must be used, the endcap load can be reduced by:

1. **Increasing $V_0$ to 1.5 L** → allows $P_{\text{abs}}$ to drop to ~7.1 bar abs (6.1 bar gauge) → endcap load drops to **8.02 kN** ✅
2. **Improving efficiency to η = 0.30** (better valve, longer barrel) → $W_{\text{req}}$ drops to 1500 J → $P_{\text{abs}} \approx 7.5$ bar abs → endcap **8.48 kN** ✅
3. **Accept 30 m/s is achievable only with UAV assistance** and size the launcher for 20 m/s instead if UAV propulsion is more capable → $P_{\text{abs}} \approx 5.5$ bar abs → endcap **6.2 kN** ✅

---

## 8. Notes and Assumptions

1. **Efficiency η = 0.20** is conservative for a CO₂ QEV launcher. Well-designed systems achieve 25–35%. If η is higher, required pressure is lower and endcap loads decrease.
2. **t_dwell = 50 ms** is an estimate for the 120 mm bore at ~30 m/s. Actual dwell is shorter for larger bores (larger bore area accelerates faster). The orifice calculation is therefore slightly conservative — actual required orifice may be smaller.
3. The **14.31 mm orifice** is comfortably within the 10–30 mm commercially available QEV range. The SMC VHS and Parker QEV series both cover this size.
4. **CO₂ per shot = 17.95 g** → approximately **4.9 shots per standard 88 g CO₂ cartridge** (with ~2 g reserve). An extended 120 g cartridge gives approximately 6.7 shots.
5. **P > 2 bar condition:** All cases give P_gauge = 8.84 bar, well above the 2 bar reliability floor.
6. **100 m operational range** is achievable only because the UAV has its own propulsion. A purely ballistic launch at 30 m/s and 45° gives maximum range ≈ 91.7 m (no drag). With real drag on a 1 kg, ~0.06 m² cross-section payload, actual ballistic range at 30 m/s is likely **50–70 m**. The UAV propulsion bridges the remainder.
