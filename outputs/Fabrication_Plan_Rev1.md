# UAV Neutralisation Launcher — Fabrication Plan
**Revision**: 1.0  
**Date**: April 28, 2026  
**Status**: Ready for Implementation

---

## 1. Executive Summary

This Fabrication Plan outlines the step-by-step procurement, assembly, and testing sequence for the **UAV Neutralisation Launcher + Interceptor UAV system** as defined in EDD-UAV-001 Rev 3. All component substitutions (PTFE seals, honed barrel, precision charge chamber) are documented with supplier recommendations and lead times.

**Target configuration**: Launcher + UAV basic (ESP32-S3 telemetry, no on-board vision) for first prototype.  
**Estimated total cost**: ₹26,735–₹42,385 (minimum–maximum with all contingencies).  
**Estimated lead time**: 4–6 weeks (6 weeks with honing + hydrostatic test buffer).

---

## 2. Procurement Schedule & Supplier Contact List

### Phase 1: URGENT (Week 1) — Confirm Component Availability

| Component | Vendor | Lead Time | Action | Contact |
|-----------|--------|-----------|--------|---------|
| **SMC AQ2110A-N02 QEV (PTFE seals)** | Moglix.com or SMC India Bengaluru | 3–5 days | Search Moglix: "SMC AQ2110A-N02"; request datasheet confirming PTFE diaphragm | https://moglix.com/ or smcworld.com/in |
| **Airmax Pressure Regulator (−20°C rated)** | Amazon.in or Airmax direct | In stock | Verify seal rating on product page; confirm −20°C cold-temp rating before checkout | amazon.in (₹2,615) or airmaxindia.com |
| **OpenMV H7 Plus** | openmv.io distributor OR Robu.in | 2–4 weeks (uncertain) | Contact official openmv.io distributor for India delivery timeline; if >3 weeks, commit to **ESP32-S3 fallback** | openmv.io or robu.in |
| **ESP32-S3 dev board (FALLBACK)** | Amazon.in or Robu.in | 2–3 days (in stock) | If OpenMV delay >2 weeks, order ESP32-S3-DevKitC-1 immediately | amazon.in or robu.in (₹600–700) |
| **PTFE O-ring assortment** | Amazon.in (Aasons brand) or IndiaMART | 2–4 days | Search "PTFE o-ring assortment metric"; verify 200+ piece count and −60°C rating | amazon.in (~₹450–550) |

**Decision Gate**: By end of Week 1, confirm OpenMV status. If unavailable within 2 weeks, **commit to ESP32-S3 fallback and adjust UAV cost to ₹7,825–₹14,225**.

---

### Phase 2: MECHANICAL PROCUREMENT (Week 1–2) — Honing & Charge Chamber

| Component | Vendor | Lead Time | Action | Contact |
|-----------|--------|-----------|--------|---------|
| **6061-T6 Al tube, 56 mm OD × 700 mm** | Prince Metal Industries (IndiaMART) or Hindalco Chennai | 2–3 days | Order: 56 mm OD, 3 mm wall, 700 mm length, raw (unhooned). Confirm delivery address. | Prince Metal: https://www.indiamart.com/proddetail/aluminum-tubes-21949662962.html |
| **Barrel Honing (52 mm ID ±0.3 mm)** | Precision machine shops, Saidapet/Ambattur (Chennai) | 3–5 business days (after tube arrival) | **PRIORITY**: Request quotes from 3 machine shops. Template: "6061-T6 Al tube 56 mm OD × 700 mm, bore honing to 52 mm ID ±0.3 mm (±0.1 preferred), Ra < 0.8 μm finish, dimensional cert required. Turnaround? Cost?" | **Recommended contacts**: Saidapet Industrial Area machine shops (search: "CNC honing Chennai" or visit local area). Alternative: Hindalco distributor (Chennai) — ask for precision-honed tubes directly. |
| **50 mm bore × 500 mm hydraulic cylinder** | Moglix.com or IndiaMART industrial hydraulics | 3–5 days | Search: "50mm bore hydraulic cylinder 500mm length". Verify bore diameter and wall thickness (3 mm ideal). Budget ₹800–1,500. | https://dir.indiamart.com/impcat/hydraulic-cylinders.html or moglix.com |
| **Al 6061-T6 end caps (custom machining)** | Local machine shop (Saidapet/Ambattur) OR Hindalco distributor | 3–5 days (after cylinder received) | Provide CAD sketch (Section 3.2 below). Request 2× caps: M20×1.5 or 1/4" NPT ports, threads clean, surface finish Ra < 1.6 μm. Cost: ₹400–500 for pair. | Same machine shop as honing, or Hindalco distributor. |

**Parallel action**: While waiting for honing + cap machining, proceed to Phase 3 (pneumatic components).

---

### Phase 3: PNEUMATIC & ELECTRICAL (Week 2–3)

| Component | Vendor | Lead Time | Action | Contact |
|-----------|--------|-----------|--------|---------|
| **Pressure regulator, PRV, solenoid, brass fittings** | Moglix.com / Robu.in / Airmax distributor | 2–4 days | Order from Moglix (one-stop shop for all pneumatic items) for faster consolidated delivery. Verify part numbers + specifications against BOM. | moglix.com (search: "pneumatic regulator", "PRV 18 bar", "solenoid valve 12V DC") |
| **Arduino Nano (CH340G clone) + relay module** | Robu.in or Campus Components | In stock | Order: ATmega328P CH340G Nano clone (₹150–200) + SRD-05VDC relay (₹80–120). Verify USB cable included. | robu.in (SKU 975725 or similar) |
| **3S LiPo 1000–1500 mAh + XT30 connector** | Robu.in or Tattu distributor | 2–3 days | Order: 3S 1000 mAh 30C+ from Robu.in (~₹700–900). Check connector type matches Arduino relay setup. | robu.in or quadkart.in |
| **22 AWG silicone wire, XT30 connectors, key switch** | Robu.in | 2–3 days | Bundle order: 4 m silicone wire (2R+2B) + XT30 connectors + panel-mount key switch (₹50–100 total). | robu.in |

---

### Phase 4: UAV COMPONENTS (Week 2–3)

| Component | Vendor | Lead Time | Action | Contact |
|-----------|--------|-----------|--------|---------|
| **CF frame 3-inch folding** | Robu.in or Quadkopters.com | 3–7 days | Search: "3-inch folding frame"; budget ₹1,200–1,800. Confirm 140–160 mm wheelbase. | robu.in or quadkopters.com (shipping Pan-India) |
| **AIO FC F4/F7 + 4-in-1 20A ESC** | Robu.in or ElectroPi | 3–5 days | Order: SpeedyBee F405 Mini AIO (~₹3,500) or similar 20×20 mm stack. Verify SPI/UART pins for OpenMV/ESP32-S3 connection. | robu.in or electropi.in |
| **1103/1204 motors (×4)** | Robu.in or ElectroPi | 2–3 days | Order: BetaFPV 1103 6000KV (~₹500–600 ea, ₹2,000–2,400 set of 4) + 2 spare motors. Confirm shaft size (2mm) matches prop adapter. | robu.in |
| **3" propellers (2 sets CW/CCW)** | Robu.in or Uav Marketplace | 2–3 days | Order: Gemfan 3016 or HQProp 3×1.5; 2 full sets (8 total props) + 4 spares. | robu.in (~₹150–200/set) |
| **RunCam Nano 4 FPV camera** | ElectroPi or Robu.in | 2–3 days | Order: ~₹1,500–2,000. Include TPU damped mount (can print locally if needed). | electropi.in or robu.in |
| **3S LiPo 300–450 mAh (UAV)** | Robu.in or Quadkart | 2–3 days | Order: Strip format 300 mAh 3S 30C+ (~₹600–700). Verify XT30 connector. | quadkart.in or robu.in |
| **M2 nylon standoffs + vibration grommets** | IndianRoboStore or Robu.in | 2–3 days | Order: M2 hex spacer kit (~₹100) + silicone anti-vibration grommets (~₹100–200). Critical for IMU reliability under 30g launch shock. | indianrobostore.com |

---

## 3. Assembly Sequence & Test Gates

### Stage T0: Component Verification (Pre-Assembly)
**Timeline**: Week 2–3 (parallel with procurement)

1. **Barrel bore measurement**: Once honing supplier returns barrel, measure bore at 3 points (start/mid/end) with dial caliper:
   - All readings must be **52.0 mm ±0.3 mm** (i.e., 51.7–52.3 mm)
   - If **any reading outside tolerance**, reject and reorder honing
   - **Pass**: Proceed to T1

2. **Chamber volume check**: Hydraulic cylinder + endcaps:
   - Measure inner diameter (should be ~50 mm), length (should be ~500 mm), endcap lengths
   - Estimate volume = π × (0.025 m)² × 0.5 m = 0.00098 m³ ≈ **1.0 L ✓**
   - **Pass**: Proceed to T1

3. **Sabot OD verification**: 3D-printed sabots must fit loosely in barrel (52 mm ID):
   - Measure actual printed OD with calipers at 3 points
   - Target: **52.0 mm ±0.2 mm** (slightly looser than barrel to allow loading)
   - If **<51.8 mm or >52.2 mm**, reprint or hand-hone sabot

4. **QEV datasheet confirmation**:
   - Request PDF datasheet from SMC before payment
   - Confirm: **Diaphragm material = PTFE**, operating temp **≥−40°C**, **Cv ≥ 1.5**
   - If NBR or lower Cv, reject and escalate to supplier

---

### Stage T1: Hydrostatic Pressure Test (Charge Chamber)
**Timeline**: Week 3 (immediately after honing + endcap machining complete)

**Procedure**: Perform before ANY pneumatic pressurization.

1. **Assembly**:
   - Install 2× endcaps onto hydraulic cylinder with M20×1.5 threads (or NPT threads with sealant)
   - Hand-tighten, then wrench to ~50 N⋅m torque (gentle, do not over-torque)
   - Leave one NPT port open for water fill + pump connection

2. **Test setup**:
   - Fill chamber completely with water (remove air bubbles)
   - Connect low-pressure hand pump (bicycle or manual) to open port
   - Place chamber in containment basin (in case of failure)
   - Attach pressure gauge to second port (0–100 bar rated)

3. **Test execution**:
   - Pressurize slowly to **22.5 bar** (1.5× safety factor per ASME B31.3)
   - Hold **5 minutes** with no visible leaks at threads or welds
   - Slowly depressurize over 2–3 minutes
   - **Pass**: No leaks, no permanent deformation → Proceed to assembly
   - **Fail** (leak at threads, swelling, deformation): Reject chamber; source replacement

4. **Test certificate**:
   - Document: Date, chamber ID, pressure gauge reading, test duration, result (PASS/FAIL)
   - Photograph pressure gauge reading at 22.5 bar for records
   - Keep certificate with launcher for future inspections

---

### Stage T2: Launcher Assembly & Component Integration
**Timeline**: Week 4

**System diagram** (pressure flow):
```
CO₂ Cartridge → Regulator (0–42 bar) → PRV (18 bar set) → Pressure gauge → [Chamber @ 10 bar] 
                                                                    ↓
                                                          QEV (pilot-operated)
                                                          ↓
                                                    Barrel (52 mm ID) → Payload
```

1. **Charge chamber mounting**:
   - Mount chamber to rigid Al frame using 2× M8 U-bolts + rubber damping pads
   - Ensure threaded ports face forward (convenient for plumbing)

2. **Valve plumbing** (use 1/4" NPT brass fittings + PTFE tape):
   - Regulator inlet ← CO₂ cartridge (verify M16×1.5 thread match before assembly)
   - Regulator outlet → PRV inlet
   - PRV outlet → Chamber top port (pressure fill line)
   - Chamber side/bottom port → QEV inlet
   - QEV outlet → Barrel chamber (52 mm ID, open to projectile)
   - QEV pilot port → Solenoid valve (12V DC) or manual pushbutton

3. **Pilot trigger assembly** (choose one):
   - **Manual option**: 3/2 pushbutton valve (Janatics) with lockable handle
   - **Autonomous option**: 12V DC solenoid valve + Arduino Nano relay trigger (with arming key switch)
   - Connect 1/4" NPT tubing from chosen pilot source to QEV pilot port

4. **Barrel assembly**:
   - Insert sabot + projectile into bore
   - Secure barrel to frame with 2× M10 clamps (mild steel or Al)
   - Align barrel bore concentrically with chamber exhaust (critical for sabot guidance)
   - Leave ~20 cm muzzle clearance for payload ejection

5. **Pressure gauge mounting**:
   - Install digital 0–25 bar gauge on chamber (preferably glycerin-filled for damping)
   - Route gauge needle/display for easy line-of-sight reading from operator position

6. **Safety interlocks** (autonomous mode only):
   - **Arming key switch**: Placed in visible, easily-accessible location (not near QEV)
   - **Pressure relief**: PRV must be **before** solenoid circuit (fail-safe: if solenoid fails, PRV bleeds excess)
   - **Manual override**: Ensure manual pushbutton can override solenoid at any time

---

### Stage T3: Launcher Functional Test (Pre-Flight)
**Timeline**: Week 4–5

**Objective**: Validate launch velocity, response time, and system reliability.

1. **No-fire checkout**:
   - Open key switch, disconnect solenoid
   - Fill chamber to 10 bar with CO₂ cartridge (using regulator)
   - Observe pressure gauge stabilization
   - Slowly open QEV pilot manually → listen for gas exhaust (confirming orifice is open)
   - **Expected**: Clean "pshhh" sound, no hissing leaks
   - **Pass**: Proceed to fired test

2. **Single sabot launch test** (manual mode):
   - Load sabot + projectile into barrel
   - Set regulator to 10 bar
   - Operator stands 3 m behind launcher, wearing eye protection + sound protection (hearing test ~140 dB SPL expected)
   - Manually open QEV pilot → sabot launches
   - Measure exit distance with measuring tape
   - **Expected velocity** (from RK45 model): 21.3–25.8 m/s depending on orifice size
   - **Expected dwell time**: 46–51 ms (total trigger-to-exit time)
   - **Acceptance**: Sabot travels ≥10 m in straight line (confirming bore concentricity + barrel alignment)

3. **Response-time DAQ measurement** (solenoid mode, if available):
   - If using solenoid + Arduino, measure electrical trigger-to-sabot-launch latency with high-speed oscilloscope or sound timer
   - **Expected**: <57 ms total (Section 6 of EDD Rev 3)
   - **Pass**: Latency <100 ms → Proceed to UAV integration test

4. **Repeated-fire reliability test**:
   - Load 5 sabots, fire at 10 bar pressure, measure consistency of exit distances
   - **Pass**: Standard deviation of exit distances **<1 m** (indicating reproducible chamber pressure decay + orifice consistency)

---

### Stage T4: UAV Assembly & Integration Test
**Timeline**: Week 4–5

**Assembly steps** (see separate UAV fabrication sub-plan):

1. **UAV frame + FC + ESC assembly**: Standard quadcopter assembly (4 motors, 4 props, FC on M2 nylon standoffs with vibration damping)

2. **Vision board installation**:
   - **If ESP32-S3 (telemetry)**: Connect to FC via UART (RX/TX pins) for telemetry data streaming
   - **If OpenMV H7 Plus (when available)**: Connect via I2C or UART for real-time object detection feedback
   - Mount with shock absorber to isolate from 30 g launch impulse

3. **Launch vibration tolerance test** (critical):
   - Place UAV in containment frame inside launcher sabot (separate sabot design needed)
   - Fire launcher with no external load (empty sabot test)
   - Recover UAV and check for:
     - Loose FC screws, motor shaft play, propeller cracks
     - Flight controller IMU calibration drift (compare pre/post accel readings)
   - **Pass**: UAV powers on, passes IMU self-test, motors spin up normally

4. **Flight test** (in open field):
   - Launch UAV from ground (not from launcher sabot yet)
   - Confirm stabilization in 30 sec hover
   - Verify telemetry link (FPV feed or ESP32 serial output)
   - **Pass**: UAV loiters for 5 min on battery

5. **Sabot ejection test**:
   - Design custom sabot that holds UAV (separate from projectile sabot design)
   - Fire launcher at ground level with UAV sabot
   - Capture ejection on camera
   - **Pass**: UAV exits sabot cleanly, immediately stabilizes in hover, RTL (return-to-launch) works

---

## 4. Charge Chamber CAD Sketch

**2D Profile (side view)**:

```
                M20×1.5 NPT (fill port)
                        |
                        v
              +---------+----------+
              |   ENDCAP (Al)      |
          +---+                    +---+
         /    |   CYLINDER BORE   |    \  
        |     |   (50 mm ID)       |    |
        |  /==+====================+==\ |  
        | |   |                    |    | |  
        |═|═══|════════════════════|════|═|  TARGET VOLUME: 1.0 L
        | |   |                    |    | |  (π × r² × h = π × 0.025² × 0.5 m³)
        |  \==+====================+==/ |  
        |     |                    |    |
         \    |                    |   /
          +---+                    +---+
              |                    |
              +---------+----------+
                        ^
                        |
              M20×1.5 NPT (exhaust to QEV)

DIMENSIONS:
- Bore (ID): 50 mm
- Wall thickness: 3 mm (OD ≈ 56 mm)
- Cylinder length: 500 mm
- Endcap face: ~50 mm wide, threaded on both faces
- Total chamber volume: ~1.0 L (verified in T0 pre-assembly check)

MATERIAL:
- Cylinder tube: 6061-T6 Aluminum or Schedule 80 Steel
- End caps: 6061-T6 Aluminum, threaded for M20×1.5 (or NPT equivalents)
- All wetted surfaces: passivated (for corrosion resistance in humid environment)

ASSEMBLY:
- Thread end caps onto cylinder body until hand-tight
- Wrench to ~50 N⋅m torque (do NOT over-torque; use torque wrench)
- Use PTFE tape (white, 12 mm) on all threads for air-tight seal
```

**Hydrostatic Test Parameters**:
- Test pressure: 22.5 bar (1.5× safety factor)
- Test fluid: Distilled water
- Test duration: 5 minutes at pressure
- Pass criterion: No visible leaks, no permanent deformation
- Cert: Signed test sheet with photo of pressure gauge at 22.5 bar

---

## 5. Pre-Launch Checklist (T0–T4 Gates)

| Gate | Criteria | Pass/Fail |
|------|----------|-----------|
| **T0: Bore tolerance** | Barrel ID 52.0±0.3 mm at 3 points | ☐ PASS |
| **T0: Sabot fit** | Sabot OD 52.0±0.2 mm, loads easily in barrel | ☐ PASS |
| **T0: QEV datasheet** | SMC AQ-series PTFE diaphragm confirmed, Cv ≥1.5 | ☐ PASS |
| **T1: Hydrostatic test** | Chamber holds 22.5 bar for 5 min, no leaks | ☐ PASS / **FAIL** → Replace |
| **T2: Plumbing integrity** | No visible leaks at fittings after 10 bar pressurization | ☐ PASS |
| **T2: Trigger responsiveness** | Manual QEV pilot opens cleanly; solenoid response <100 ms (if used) | ☐ PASS |
| **T3: Launch velocity** | Measured v_exit ≥ 20 m/s (within RK45 envelope 21.3–25.8 m/s) | ☐ PASS |
| **T3: Consistency** | 5 launches: std dev of exit distance <1 m | ☐ PASS |
| **T4: UAV vibration tolerance** | Post-launch: FC IMU drift <2%, no visible damage | ☐ PASS |
| **T4: Flight stabilization** | UAV hover stable for 30 sec after ejection | ☐ PASS |

---

## 6. Estimated Timeline & Critical Path

```
Week 1:  [Procurement phase; confirm QEV+OpenMV status]
         ├─ SMC AQ2110A-N02 QEV (3–5 days)
         ├─ PTFE O-ring kit (2–4 days)
         ├─ Regulator + PRV + solenoid (2–4 days)
         └─ Pressure gauge (2–3 days)

Week 2:  [Honing & chamber start; UAV components order]
         ├─ Barrel honing quote + order (spec to shop)
         ├─ Hydraulic cylinder + end caps (3–5 days)
         └─ UAV frame, FC, motors, props (staggered 2–4 days each)

Week 3:  [CRITICAL PATH: Honing completion]
         ├─ Barrel honing delivery + T0 bore check
         ├─ End cap machining + hydrostatic test (T1)
         └─ Arduino + relay + solenoid delivery

Week 4:  [T2 Launcher assembly; T4 UAV assembly]
         ├─ Plumbing + chamber integration
         ├─ Pilot trigger + safety interlocks
         ├─ UAV FC integration + vibration isolation
         └─ Single-sabot launch test (T3 start)

Week 5:  [T3 Launcher testing; T4 UAV flight test]
         ├─ 5 × repeated-fire reliability test
         ├─ Response-time measurement (solenoid)
         ├─ UAV hover & telemetry validation
         └─ Sabot ejection test (if UAV sabot designed)

**CRITICAL BOTTLENECK**: Barrel honing lead time (3–5 days after tube arrival).  
**Mitigation**: Order honing service immediately upon tube delivery (Week 2); get quotes from 3 shops in parallel.

**TOTAL LEAD TIME**: 5–6 weeks (including honing + hydrostatic test buffer).
```

---

## 7. Safety Warnings & Operational Constraints

⚠️ **HIGH-PRESSURE PNEUMATIC SYSTEM**
- Charge chamber operates at 10 bar absolute (~150 psi), test pressure 22.5 bar (337 psi)
- **Never approach open QEV port during pressurization** (high-velocity gas jet can cause injury)
- **Always perform hydrostatic test before gas pressurization** (chamber failure under pressure = explosion hazard)

⚠️ **CO₂ COLD DUTY**
- CO₂ expansion at orifice causes rapid barrel cooling (−10°C to −20°C)
- **Never touch barrel immediately after firing** (frostbite risk)
- **All seals must be PTFE** (Nitrile/NBR will harden and fail; hydrostatic test will leak at cold)

⚠️ **LAUNCH IMPULSE (30 g)**
- UAV experiences ~30 g peak acceleration during launch
- **All electronic components must be secured with vibration damping** (nylon standoffs + foam)
- **Flight controller IMU may require re-calibration post-launch**; check self-test before flight

⚠️ **REGULATORY CONSTRAINTS** (India-specific)
- This system is **not licensed under DGCA** for autonomous aerial deployment
- **Manual telemetry + recovery only** for first prototype
- Check local RTO (Regional Transport Office) regulations before outdoor testing
- Operate only in **open fields with minimum 100 m clearance radius** from buildings/people

---

## 8. References

- **EDD**: `outputs/UAV_Launcher_EDD_Rev3.md` (governing parameters, RK45 velocity sweep, response-time calculations)
- **BOM**: `docs/initail_BoM.txt` (component list, suppliers, current pricing)
- **RK45 Results**: `outputs/rk45_launcher_results.json` (numerical simulation for 8–12 mm orifice range)
- **Pressure transducer logs**: (To be generated during T3 testing, stored in `outputs/test_logs/`)

---

## 9. Post-Prototype Improvements (Rev 2)

- **Vision processing upgrade**: Replace ESP32-S3 with **OpenMV H7 Plus** (5–15 ms inference for real-time target detection)
- **Solenoid trigger timing**: Optimize dwell time with **dual-solenoid fast-switching pilot system** for sub-40 ms response
- **Barrel precision**: Upgrade to **±0.1 mm bore tolerance** (CNC honing) for improved sabot concentricity and velocity consistency
- **Charge chamber integration**: Design **custom machined 6061-T6 Al chamber** (cost ₹2,500–3,500) with integrated NPT ports + relief valve (eliminates need for separate PRV)
- **Flight controller**: Replace F4 AIO with **F7 AIO with integrated barometer** (for altitude hold during hover post-launch)

---

**Document prepared by**: GitHub Copilot (Agent)  
**Approval pending**: User review & field testing validation  
**Next review**: After T3 launcher testing complete (Week 5)

