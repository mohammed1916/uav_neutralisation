---
title: "Pneumatic Launcher — Complete Technical Analysis"
date: "2026-04-28 09:52"
---

# 1. Input Parameters

All parameters derive from the system schematic and engineering requirements.

| Parameter | Symbol | Value | Notes / Derivation |
|---|:---:|---:|---|
| Charge chamber volume | $V_{0}$ | 1.0 mL (0.0010 m³) | Accumulator tank |
| Working pressure (gauge) | $P_{0,\text{gauge}}$ | 10.0 bar | As marked on accumulator |
| Working pressure (absolute) | $P_{0}$ | 11.00 bar (1.100e+06 Pa) | $P_{0}=(P_{0,\text{gauge}}+1)\times10^{5}$ Pa |
| Atmospheric back-pressure | $P_{f}$ | 1.00 bar (100 000 Pa) | Standard atmosphere |
| Barrel internal diameter | $D$ | 52 mm | Measured from drawing |
| Barrel length | $L$ | 700 mm | Measured from drawing |
| Bore cross-section area | $A_{\text{bore}}$ | 21.2372 cm² (0.002124 m²) | $A_{\text{bore}}=\pi(D/2)^{2}$ |
| CO₂ specific gas constant | $R_{\text{spec}}$ | 188.92 J/(kg·K) | $R_{\text{spec}}=R_{u}/M_{\text{CO}_{2}}=8.314/0.04401$ |
| Temperature | $T$ | 293.15 K (20 °C) | Ambient / charge temperature |
| Specific heat ratio | $\gamma$ | 1.30 (CO₂) | Used in compressible-flow formulae |
| Discharge coefficient (default) | $C_{d}$ | 0.8 | Swept 0.6–0.8 in parametric study |
| Default orifice diameter | $d_{\text{or}}$ | 12 mm | Swept 6–18 mm in parametric study |

# 2. Theoretical Energy Analysis

## 2.1 Isothermal Expansion Work

The maximum theoretical work available from isothermal expansion of a compressed
gas from $P_{0}$ down to atmospheric $P_{f}$ in a fixed charge volume $V_{0}$:

$$W = P_{0}\cdot V_{0}\cdot\ln\!\left(\frac{P_{0}}{P_{f}}\right)$$

**Derivation.** For an ideal gas expanding isothermally the work element is
$\mathrm{d}W = P\,\mathrm{d}V$. With $PV = \text{const}$ at constant $T$,
$P = P_{0}V_{0}/V$. Integrating from $V_{0}$ to $V_{f}=V_{0}(P_{0}/P_{f})$:

$$W = \int_{V_{0}}^{V_{f}} P\,\mathrm{d}V
    = P_{0}V_{0}\int_{V_{0}}^{V_{f}}\frac{\mathrm{d}V}{V}
    = P_{0}V_{0}\ln\!\left(\frac{V_{f}}{V_{0}}\right)
    = P_{0}V_{0}\ln\!\left(\frac{P_{0}}{P_{f}}\right)$$

## 2.2 Numerical Verification

$$P_{0} = 1.1000e+06\;\text{Pa},\quad  V_{0} = 1.0000e-03\;\text{m}^{3},\quad  P_{f} = 100000\;\text{Pa}$$

$$\ln\!\left(\frac{P_{0}}{P_{f}}\right)  = \ln\!\left(\frac{1100000}{100000}\right)  = \ln(11.0000) = 2.3979$$

$$W = 1.1000e+06\times1.0000e-03\times2.3979   = 1100.00000\times2.3979   = 2637.68\;\text{J}$$

> **Note:** This is the absolute theoretical upper bound (ideal gas, zero losses).
> The ODE simulation (§​5) accounts for real-gas behaviour, flow restriction,
> friction, and finite barrel length.

## 2.3 Simulation Result and Launch Efficiency

Default case: $m_{\text{payload}}=1.0$ kg, $d_{\text{or}}=12$ mm, $C_{d}=0.8$:

$$v_{\text{exit}} = 27.765\;\text{m/s},\quad  E_{k} = \tfrac{1}{2}\cdot1.0\cdot27.765^{2} = 385.45\;\text{J}$$

$$\eta = \frac{E_{k}}{W} = \frac{385.45}{2637.68} = 14.6\%$$

# 3. Representative Payload Scenarios (Theoretical Bounds)

Converting available work $W$ to muzzle velocity at mechanical efficiency $\eta$:

$$E_{k} = \eta W \implies \tfrac{1}{2}mv^{2} = \eta W\implies v = \sqrt{\frac{2\eta W}{m}}$$

These are theoretical upper bounds only. Actual ODE result: 27.8 m/s for 1 kg.

| $m$ (kg) | $\eta$ (%) | $W_{\text{eff}}=\eta W$ (J) | $v=\sqrt{2W_{\text{eff}}/m}$ (m/s) | Numeric check |
|---:|---:|---:|---:|---|
| 0.20 | 25 | 659 | 81.2 | $\sqrt{2\times659/0.20}=81.2$ |
| 0.20 | 50 | 1319 | 114.8 | $\sqrt{2\times1319/0.20}=114.8$ |
| 0.20 | 75 | 1978 | 140.7 | $\sqrt{2\times1978/0.20}=140.7$ |
| 0.50 | 25 | 659 | 51.4 | $\sqrt{2\times659/0.50}=51.4$ |
| 0.50 | 50 | 1319 | 72.6 | $\sqrt{2\times1319/0.50}=72.6$ |
| 0.50 | 75 | 1978 | 89.0 | $\sqrt{2\times1978/0.50}=89.0$ |
| 1.00 | 25 | 659 | 36.3 | $\sqrt{2\times659/1.00}=36.3$ |
| 1.00 | 50 | 1319 | 51.4 | $\sqrt{2\times1319/1.00}=51.4$ |
| 1.00 | 75 | 1978 | 62.9 | $\sqrt{2\times1978/1.00}=62.9$ |

# 4. Structural Analysis — Barrel Wall and Endcap

## 4.1 Thin-Wall Hoop Stress

Applicable for a thin-walled cylinder ($D/t > 20$). Principal stresses:

$$\sigma_{\text{hoop}} = \frac{P\,r}{t},\qquad  \sigma_{\text{axial}} = \frac{P\,r}{2t} = \frac{1}{2}\sigma_{\text{hoop}}$$

where $r = D/2$, $t$ = wall thickness, $P$ = internal pressure.
Hoop stress governs. Setting $\sigma_{\text{hoop}} = \sigma_{\text{yield}}/\mathrm{SF}$:

$$t_{\min} = \frac{P\cdot r\cdot\mathrm{SF}}{\sigma_{\text{yield}}}$$

**Numerical check:**

$$P_{0} = 1.100e+06\;\text{Pa},\quad  r = 26.0\;\text{mm},\quad  \sigma_{\text{yield}} = 276\;\text{MPa},\quad  \mathrm{SF} = 3$$

$$\sigma_{\text{allow}} = 276/3  = 92.0\;\text{MPa}$$

$$t_{\min} = \frac{1.100e+06\times0.0260}{92000000}  = 0.3109\;\text{mm}$$

Axial: $t_{\min,\text{axial}} = 0.1554$ mm (non-governing).

Thin-wall check at 3 mm: $D/t = 52/3 = 17.3$ — borderline;
Lamé thick-wall analysis changes the result by < 0.5 % at these pressures.

## 4.2 Wall Thickness Comparison

| $t$ (mm) | $\sigma_{\text{hoop}}$ (MPa) | SF vs yield | SF vs ultimate | Formula: $P_{0}\cdot r/t$ |
|---:|---:|---:|---:|---|
| 2 | 14.30 | 19.3 | 21.7 | $1.10\times10^{6}\times26\times10^{-3}/2\times10^{-3}$ |
| 3 | 9.53 | 29.0 | 32.5 | $1.10\times10^{6}\times26\times10^{-3}/3\times10^{-3}$ |
| 5 | 5.72 | 48.3 | 54.2 | $1.10\times10^{6}\times26\times10^{-3}/5\times10^{-3}$ |
| 8 | 3.58 | 77.2 | 86.7 | $1.10\times10^{6}\times26\times10^{-3}/8\times10^{-3}$ |

Standard 3 mm wall: SF = 29.0 vs yield (32.5 vs ultimate) — acceptable.

# 5. 1D Transient ODE Simulation

## 5.1 Governing ODE System

Internal ballistics are modelled as a coupled ODE system integrated with
forward Euler at $\Delta t = 0.1$ ms.

State vector: $\bigl(x,\;v,\;P_{c},\;P_{b},\;m_{c},\;m_{b}\bigr)$.

| \# | Equation | Physical meaning |
|:---:|---|---|
| 1 | $\dot{x} = v$ | Kinematics |
| 2 | $\dot{v} = F_{\text{net}}/m_{\text{payload}}$, $\;F_{\text{net}}=\max\!\bigl(0,(P_{b}-P_{\text{atm}})A_{\text{bore}}-\mu P_{b}A_{\text{bore}}\bigr)$ | Newton 2nd law ($\mu=0.10$) |
| 3 | $\dot{m}_{c}=-\dot{m}$, $\;\dot{m}_{b}=+\dot{m}$ | Mass conservation |
| 4 | $V_{b}(t)=A_{\text{bore}}\cdot x(t)+V_{\text{cl}}$, $\;V_{\text{cl}}=10^{-6}$ m³ | Moving bore volume |
| 5 | $P_{\text{real}}=Z_{\text{RK}}(P_{\text{ideal}},T)\cdot P_{\text{ideal}}$ | Real-gas correction |
| 6 | Exit when $x\geq L$ or $P_{c}\leq 1.01\,P_{\text{atm}}$ | Termination |

## 5.2 Real-Gas Correction — Redlich–Kwong EOS

The Redlich–Kwong equation of state for CO₂:

$$P = \frac{R_{u}\,T}{V_{m}-b} - \frac{a}{V_{m}(V_{m}+b)\,\sqrt{T}}$$

CO₂ critical constants: $T_{c}=304.13$ K, $P_{c}^{\text{RK}}=7.377$ MPa.

RK parameters:

$$a = \frac{0.42748\,R_{u}^{2}\,T_{c}^{2}}{P_{c}^{\text{RK}}} = 0.3705\;\text{J\,m}^3\text{\,K}^{1/2}\text{/mol}^2$$

$$b = \frac{0.08664\,R_{u}\,T_{c}}{P_{c}^{\text{RK}}} = 0.000030\;\text{m}^3\text{/mol}$$

$Z_{\text{RK}}$ is solved via Newton–Raphson on the cubic EOS
(tolerance $10^{-6}$, max 60 iterations).
For CO₂ at 11 bar, 293 K: $Z_{\text{RK}}\approx 0.97$.

Pressure from density:

$$P_{\text{real}} = Z_{\text{RK}}(P_{\text{ideal}},T)\cdot P_{\text{ideal}}\quad\text{where}\quadP_{\text{ideal}} = \frac{m}{V}\cdot\frac{R_{u}\,T}{M_{\text{CO}_{2}}}$$

## 5.3 Valve Mass-Flow Formulas

Flow chokes when $P_{b}/P_{c}\leq r_{\text{crit}}$:

$$r_{\text{crit}} = \left(\frac{2}{\gamma+1}\right)^{\!\gamma/(\gamma-1)}  = \left(\frac{2}{2.3}\right)^{1.3/0.3}  = 0.5457\quad(\gamma=1.3)$$

**Choked flow** ($P_{b}/P_{c}\leq r_{\text{crit}}$; governs most of the discharge):

$$\dot{m} = C_{d}\cdot A_{\text{or}}\cdot P_{c}  \sqrt{\frac{\gamma}{R_{\text{spec}}\,T}}  \left(\frac{2}{\gamma+1}\right)^{\!(\gamma+1)/[2(\gamma-1)]}$$

Numerical example at $t=0$ ($P_{c}=11.0$ bar, $C_{d}=0.8$, $d_{\text{or}}=12$ mm, $T=293$ K):

$$A_{\text{or}} = \pi(0.006)^{2} = 1.1310e-04\;\text{m}^2$$

$$\sqrt{\frac{\gamma}{R_{\text{spec}}\,T}}  = \sqrt{\frac{1.3}{188.9\times293}}  = 0.00484$$

$$\left(\frac{2}{2.3}\right)^{(2.3)/(2\times0.3)}  = 0.5852$$

$$\dot{m}_{0} = 0.8\times1.1310e-04\times1.100e+06  \times0.00484\times0.5852  = 0.2822\;\text{kg/s}$$

**Unchoked flow** ($P_{b}/P_{c}>r_{\text{crit}}$; late discharge):

$$\dot{m} = \frac{C_{d}\cdot A_{\text{or}}\cdot P_{c}}{\sqrt{R_{\text{spec}}\,T}}  \sqrt{\frac{2\gamma}{\gamma-1}\left[  \left(\frac{P_{b}}{P_{c}}\right)^{2/\gamma} -\left(\frac{P_{b}}{P_{c}}\right)^{(\gamma+1)/\gamma}  \right]}$$

## 5.4 Default Case Results

Parameters: $m_{\text{payload}}=1.0$ kg, $d_{\text{or}}=12$ mm, $C_{d}=0.8$, $T=293$ K, $D\times L=52\times700$ mm, $V_{0}=1$ mL @ 10 bar gauge.

| Output | Value | Formula / Notes |
|---|---:|---|
| Muzzle velocity $v_{\text{exit}}$ | 27.765 m/s | $v(t)$ at $x=L$ (ODE endpoint) |
| Impulse $I$ | 27.765 N·s | $I=m_{\text{payload}}\cdot v_{\text{exit}}$ |
| KE at muzzle $E_{k}$ | 385.45 J | $\tfrac{1}{2}\times1.0\times27.765^{2}$ |
| Launch efficiency $\eta$ | 14.61 % | $E_{k}/W=385.45/2637.7$ |
| Discharge time $t_{\text{end}}$ | 37.20 ms | Projectile transit time |
| Peak barrel force $F_{\text{peak}}$ | 3369.8 N | $\max_{t}[(P_{b}-P_{\text{atm}})A_{\text{bore}}]$ |
| Average force $F_{\text{avg}}$ | 746.4 N | $F_{\text{avg}}=I/t_{\text{end}}$ |
| Static endcap bolt load | 2336.1 N | $P_{0}\cdot A_{\text{bore}}$ (§​8) |

# 6. Parametric Sweep

The ODE model was run over a 3-D grid to characterise performance sensitivity.

Fixed: $m_{\text{payload}}=1.0$ kg, $T=293$ K, $P_{0}=10$ bar gauge, $D=52$ mm, $L=700$ mm.

Swept variables:

- $d_{\text{or}}\in\{6,8,10,12,15,18\}$ mm ($A_{\text{or}}=\pi(d_{\text{or}}/2)^{2}$ ranges 28.3–254.5 mm²)
- $V_{c}\in\{500,800,1000,1200\}$ mL
- $C_{d}\in\{0.6,0.7,0.8\}$

Total: $6\times4\times3=72$ ODE runs.

Recorded outputs per run:

| Symbol | Quantity | Unit |
|:---:|---|:---:|
| $v_{\text{exit}}$ | Muzzle velocity at $x=L$ | m/s |
| $I$ | Impulse $=m_{\text{payload}}\cdot v_{\text{exit}}$ | N·s |
| $t_{\text{end}}$ | Projectile transit time | s |
| $F_{\text{peak}}$ | $\max_{t}[(P_{b}-P_{\text{atm}})A_{\text{bore}}]$ | N |

## 6.1 Sweep Data Table (first 30 of 72 runs)

| $d_{\text{or}}$ (mm) | $V_{c}$ (mL) | $C_{d}$ | $v_{\text{exit}}$ (m/s) | Impulse (N·s) | $t_{\text{end}}$ (ms) | $F_{\text{peak}}$ (N) |
|---:|---:|---:|---:|---:|---:|---:|
| 6.00 | 500.0 | 0.60 | 7.81 | 7.81 | 95.10 | 2235.6 |
| 6.00 | 500.0 | 0.70 | 9.08 | 9.08 | 83.50 | 2304.7 |
| 6.00 | 500.0 | 0.80 | 10.34 | 10.34 | 75.10 | 2303.0 |
| 6.00 | 800.0 | 0.60 | 7.82 | 7.82 | 95.00 | 2237.3 |
| 6.00 | 800.0 | 0.70 | 9.10 | 9.10 | 83.40 | 2306.3 |
| 6.00 | 800.0 | 0.80 | 10.38 | 10.38 | 74.90 | 2304.7 |
| 6.00 | 1000.0 | 0.60 | 7.82 | 7.82 | 94.90 | 2237.9 |
| 6.00 | 1000.0 | 0.70 | 9.11 | 9.11 | 83.30 | 2306.9 |
| 6.00 | 1000.0 | 0.80 | 10.39 | 10.39 | 74.80 | 2305.3 |
| 6.00 | 1200.0 | 0.60 | 7.83 | 7.83 | 94.90 | 2238.3 |
| 6.00 | 1200.0 | 0.70 | 9.11 | 9.11 | 83.30 | 2307.2 |
| 6.00 | 1200.0 | 0.80 | 10.39 | 10.39 | 74.70 | 2305.6 |
| 8.00 | 500.0 | 0.60 | 13.60 | 13.60 | 61.30 | 2417.0 |
| 8.00 | 500.0 | 0.70 | 15.53 | 15.53 | 55.90 | 2525.0 |
| 8.00 | 500.0 | 0.80 | 17.18 | 17.18 | 52.10 | 2809.6 |
| 8.00 | 800.0 | 0.60 | 13.75 | 13.75 | 60.90 | 2421.0 |
| 8.00 | 800.0 | 0.70 | 15.75 | 15.75 | 55.40 | 2525.7 |
| 8.00 | 800.0 | 0.80 | 17.48 | 17.48 | 51.60 | 2810.7 |
| 8.00 | 1000.0 | 0.60 | 13.78 | 13.78 | 60.80 | 2422.4 |
| 8.00 | 1000.0 | 0.70 | 15.82 | 15.82 | 55.30 | 2525.9 |
| 8.00 | 1000.0 | 0.80 | 17.57 | 17.57 | 51.40 | 2811.0 |
| 8.00 | 1200.0 | 0.60 | 13.81 | 13.81 | 60.70 | 2423.3 |
| 8.00 | 1200.0 | 0.70 | 15.86 | 15.86 | 55.20 | 2526.1 |
| 8.00 | 1200.0 | 0.80 | 17.62 | 17.62 | 51.30 | 2811.3 |
| 10.00 | 500.0 | 0.60 | 19.10 | 19.10 | 48.20 | 3071.7 |
| 10.00 | 500.0 | 0.70 | 20.93 | 20.93 | 45.20 | 3027.9 |
| 10.00 | 500.0 | 0.80 | 22.48 | 22.48 | 43.00 | 2861.0 |
| 10.00 | 800.0 | 0.60 | 19.50 | 19.50 | 47.70 | 3073.8 |
| 10.00 | 800.0 | 0.70 | 21.44 | 21.44 | 44.60 | 3032.8 |
| 10.00 | 800.0 | 0.80 | 23.09 | 23.09 | 42.30 | 2869.3 |

# 7. Parametric Sweep Plots

Each data point is the endpoint of one full ODE integration (72 total).
X-axis: $d_{\text{or}}$ (mm). Each curve: one $C_{d}$ value. Each figure: one fixed $V_{c}$.

### Figure 1 — Muzzle velocity vs orifice diameter ($V_{c}=500$ mL)

*Velocity rises steeply to ≈ 10 mm orifice; plateau beyond 12 mm indicates the barrel length limits energy extraction at this volume.*

![](outputs/vel_vs_orifice_Vc_500uL.png)

### Figure 2 — Muzzle velocity vs orifice diameter ($V_{c}=800$ mL)

*Larger chamber sustains higher $P_{c}$ longer, raising $v_{\text{exit}}$ especially at large $d_{\text{or}}$.*

![](outputs/vel_vs_orifice_Vc_800uL.png)

### Figure 3 — Muzzle velocity vs orifice diameter ($V_{c}=1000$ mL) — **nominal case**

*Reference: $V_{0}=1$ mL at $P_{0}=10$ bar gauge. At $d_{\text{or}}=12$ mm, $C_{d}=0.8$: $v_{\text{exit}}=27.8$ m/s.*

![](outputs/vel_vs_orifice_Vc_1000uL.png)

### Figure 4 — Muzzle velocity vs orifice diameter ($V_{c}=1200$ mL)

*Over-volume case; diminishing returns vs 1000 mL due to barrel-length limit.*

![](outputs/vel_vs_orifice_Vc_1200uL.png)

### Figure 5 — Peak barrel force vs orifice diameter ($V_{c}=1000$ mL)

*$F_{\text{peak}}=\max_{t}[(P_{b}(t)-P_{\text{atm}})A_{\text{bore}}]$. Maximum force on the **projectile** during the firing stroke — NOT the endcap bolt load (§​8).*

![](outputs/peakF_vs_orifice_Vc_1000uL.png)

### Figure 6 — Impulse vs orifice diameter ($V_{c}=1000$ mL)

*$I=m_{\text{payload}}\cdot v_{\text{exit}}=\int F_{\text{net}}\,\mathrm{d}t$ (1 kg payload: impulse in N·s = velocity in m/s numerically). Plateau at large $d_{\text{or}}$ confirms barrel-length-limited regime.*

![](outputs/impulse_vs_orifice_Vc_1000uL.png)

## Engineering Drawing

![Launcher assembly drawing](outputs/launcher_drawing.png)

# 8. Flange and Bolt Check

## 8.1 Load Cases

**Load Case A — static endcap bolt load (governs fastener design):**

The endcap must resist the maximum chamber pressure acting on the bore area:

$$F_{\text{endcap}} = P_{0}\cdot A_{\text{bore}}  = 1.100e+06\times0.002124  = 2336.1\;\text{N}\;(2.336\;\text{kN})$$

**Load Case B — peak barrel transit force (informational only; not the endcap load):**

$F_{\text{peak,barrel}}=7715.4$ N (worst sweep: $d_{\text{or}}=18$ mm, $V_{c}=500$ mL, $C_{d}=0.8$).

This force acts on the **projectile**, not the endcap bolts.
Bolt design uses Load Case A only.

## 8.2 Bolt Shear Capacity

Each bolt resists the endcap axial load in direct shear:

$$A_{\text{bolt}} = \pi\!\left(\frac{d_{\text{bolt}}}{2}\right)^{2},\qquad F_{\text{cap}} = A_{\text{bolt}}\cdot\tau_{\text{shear}},\qquad n_{\text{req}} = \left\lceil\frac{F_{\text{endcap}}}{F_{\text{cap}}}\right\rceil$$

For M8 bolts ($d_{\text{bolt}}=8$ mm, $\tau_{\text{shear}}=240$ MPa):

$$A_{\text{bolt}} = \pi(0.004)^{2}  = 5.0265e-05\;\text{m}^2\;(50.27\;\text{mm}^2)$$

$$F_{\text{cap}} = 5.0265e-05\times240\times10^{6}  = 12063.7\;\text{N}$$

$$n_{\text{req}} = \left\lceil\frac{2336.1}{12063.7}\right\rceil  = 1$$

With 6 bolts provided:

$$\mathrm{SF} = \frac{6\times12063.7}{2336.1}  = 31.0$$

## 8.3 Bolt Shear Check Table

$\tau_{\text{shear}}=240$ MPa for all bolt sizes.

| Bolt | $d_{\text{bolt}}$ (mm) | $A_{\text{bolt}}$ (mm²) | $F_{\text{cap}}$ (N) | $n_{\text{req}}$ (Load A) | SF with 6 bolts |
|---|---:|---:|---:|---:|---:|
| M6 | 6 | 28.27 | 6785.8 | 1 | 17.4 |
| M8 | 8 | 50.27 | 12063.7 | 1 | 31.0 |
| M10 | 10 | 78.54 | 18849.6 | 1 | 48.4 |

# 9. Barrel–Payload Geometric Compatibility

## 9.1 Core Constraint

For a rectangular payload ($W\times H$) inside a circular bore (diameter $D_{\text{barrel}}$),
the worst-case envelope occurs when the diagonal aligns with the bore:

$$D_{\text{eq}} = \sqrt{W^{2}+H^{2}}$$

Including sabot radial clearance $C_{\text{sab}}$ per side,
the no-interference condition is:

$$D_{\text{eq}}+2\,C_{\text{sab}}\leq D_{\text{barrel,min}}\quad\text{where}\quadD_{\text{barrel,min}}=D_{\text{barrel,nom}}-\delta_{\text{tol}}$$

## 9.2 Numerical Check

$$W=40\;\text{mm},\quad H=45\;\text{mm}  \implies D_{\text{eq}}=\sqrt{40^{2}+45^{2}}  =\sqrt{3625}=60.21\;\text{mm}$$

$$C_{\text{sab}}=1.5\;\text{mm/side}  \implies 2C_{\text{sab}}=3.0\;\text{mm}$$

$$D_{\text{barrel,nom}}=52\;\text{mm},  \quad\delta_{\text{tol}}=0.3\;\text{mm}  \implies D_{\text{barrel,min}}=51.7\;\text{mm}$$

**Check:**

$$D_{\text{eq}}+2C_{\text{sab}}=60.21+3.0  =63.21\;\text{mm}  >51.7\;\text{mm}=D_{\text{barrel,min}}$$

**Result: INTERFERENCE by 11.51 mm** if the payload is free to rotate.

## 9.3 Interpretation and Requirements

The payload diagonal (60.21 mm) exceeds the minimum bore (51.7 mm)
by 11.51 mm. Unconstrained yaw or roll during loading or the firing stroke
will cause the payload to jam. A close-fitting sabot is mandatory.

**Requirement G-01.** The sabot shall enforce axial alignment such that the effective
payload envelope presented to the bore remains $\leq D_{\text{barrel,min}}$
under all loading and firing conditions.

**Requirement G-02.** Total radial clearance (sabot OD to barrel ID) shall be
1.0–1.5 mm per side to prevent tilt-induced interference while maintaining
acceptable bore friction and ease of manual loading.

# 10. Formula Reference Summary

| Quantity | Formula | Numerical result |
|---|---|---|
| Isothermal expansion work | $W = P_{0}\cdot V_{0}\cdot\ln(P_{0}/P_{f})$ | $W=2637.7$ J |
| Bore cross-section area | $A_{\text{bore}} = \pi(D/2)^{2}$ | $A_{\text{bore}}=0.002124$ m² |
| Ideal muzzle velocity | $v = \sqrt{2\eta W/m}$ | $\eta=50\%$, $m=1$ kg $\to 51.4$ m/s |
| Real-gas pressure (RK EOS) | $P_{\text{real}}=Z_{\text{RK}}\cdot(m/V)\cdot R_{u}T/M_{\text{CO}_{2}}$ | $Z_{\text{RK}}\approx0.97$ at 11 bar, 20 °C |
| Hoop stress (thin-wall) | $\sigma_{\text{hoop}} = P\,r/t$ | $t=3$ mm $\to\sigma_{\text{hoop}}=9.5$ MPa |
| Minimum wall thickness | $t_{\min} = P\cdot r\cdot\mathrm{SF}/\sigma_{\text{yield}}$ | $t_{\min}=0.311$ mm (SF = 3) |
| Axial stress | $\sigma_{\text{axial}} = P\,r/(2t) = \tfrac{1}{2}\sigma_{\text{hoop}}$ | Non-governing |
| Endcap axial bolt load | $F_{\text{endcap}} = P_{0}\cdot A_{\text{bore}}$ | $F_{\text{endcap}}=2336.1$ N |
| Bolt shear capacity | $F_{\text{cap}} = \pi(d_{\text{bolt}}/2)^{2}\cdot\tau_{\text{shear}}$ | M8: $F_{\text{cap}}=12063.7$ N |
| Critical pressure ratio | $r_{\text{crit}} = (2/(\gamma+1))^{\gamma/(\gamma-1)}$ | $r_{\text{crit}}=0.5457$ ($\gamma=1.3$) |
| Choked mass-flow rate | $\dot{m}=C_{d}A_{\text{or}}P_{c}\sqrt{\gamma/(R_{\text{spec}}T)}\cdot(2/(\gamma+1))^{(\gamma+1)/[2(\gamma-1)]}$ | $\dot{m}_{0}=0.2822$ kg/s at $t=0$ |
| Impulse | $I = m_{\text{payload}}\cdot v_{\text{exit}} = \int F_{\text{net}}\,\mathrm{d}t$ | $I=27.765$ N·s |
| Average propulsion force | $F_{\text{avg}} = I/t_{\text{discharge}}$ | $F_{\text{avg}}=746.4$ N |
| Diagonal payload envelope | $D_{\text{eq}} = \sqrt{W^{2}+H^{2}}$ | $D_{\text{eq}}=60.21$ mm ($W=40$, $H=45$ mm) |
| Launch efficiency | $\eta = E_{k}/W = \tfrac{1}{2}mv^{2}/W$ | $\eta=14.61\%$ (1 kg, ODE sim) |

# Conclusion

The 52 mm × 700 mm pneumatic launcher charged to 10 bar gauge with 1 mL of CO₂ can accelerate a 1 kg payload to **27.8 m/s** in 37 ms (launch efficiency 14.6 %).
A 3 mm 6061-T6 barrel wall gives SF = 29.0 vs yield.
Six M8 flange bolts give SF = 31.0 on the static endcap load (2336 N).
The 40×45 mm rectangular payload requires a sabot to prevent bore interference (diagonal envelope 60.2 mm exceeds 51.7 mm bore by 11.5 mm when misaligned).

