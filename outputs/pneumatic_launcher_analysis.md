# Pneumatic Launcher Analysis
Generated: 2026-04-24 17:26
## Formulas and Calculations
Key calculations used in the analysis (LaTeX math is supported by pandoc). Numeric substitutions are shown where data is available.
### Isothermal expansion work
Symbolic: $W = P_0 V_0 \ln\left(\frac{P_0}{P_f}\right)$
Numeric: $P_0=1600000\;\mathrm{Pa},\; V_0=1.0000e-03\;\mathrm{m^3},\; P_f=100000\;\mathrm{Pa}$\
Display: $$W = 1600000\times 1.0000e-03 \times \ln\left(\frac{1600000}{100000}\right) = 4436.14\ \mathrm{J}$$\n### Kinetic energy (example)
Symbolic: $E = \tfrac{1}{2} m v^2$
Numeric (m=1.00 kg, v=38.308 m/s): $E = 0.5 \times 1.00 \times 38.308^2 = 733.74\;\mathrm{J}$\n### Thin-wall hoop stress and required thickness
Symbolic: $\sigma_{hoop} = \frac{P r}{t}$ ; therefore $t = \frac{P r}{\sigma_{allowable}}$
Numeric: barrel area=2.123717e-03 m^2 → r=26.00 mm; using allowable=92.0 MPa → t_required=0.452 mm\n## Summary
### Analysis Summary
| Parameter | Value |
|---|---:|
| W_ideal_J | 4436.14195558365 |
| P0_abs_Pa | 1600000.0 |
| barrel_area_m2 | 0.0021237166338267 |
| transient_report | None |
| structural_report | None |
| parametric_csv | C:\Users\BBBS-AI-01\d\uav_neutralisation\outputs\parametric_sweep.csv |
| parametric_json | C:\Users\BBBS-AI-01\d\uav_neutralisation\outputs\parametric_sweep_summary.json |
### Parametric Sweep (full table)
| orifice_d_m | Vc_m3 | Cd | muzzle_v | impulse | t_end_s | peak_F |
|---:|---:|---:|---:|---:|---:|---:|
| 0.0060 | 0.0005 | 0.6000 | 9.2176 | 9.2176 | 0.0811 | 3118 |
| 0.0060 | 0.0005 | 0.7000 | 10.7605 | 10.7605 | 0.0712 | 3259 |
| 0.0060 | 0.0005 | 0.8000 | 12.3176 | 12.3176 | 0.0640 | 3384 |
| 0.0060 | 0.0008 | 0.6000 | 9.1941 | 9.1941 | 0.0812 | 3120 |
| 0.0060 | 0.0008 | 0.7000 | 10.7247 | 10.7247 | 0.0713 | 3262 |
| 0.0060 | 0.0008 | 0.8000 | 12.2698 | 12.2698 | 0.0641 | 3387 |
| 0.0060 | 0.0010 | 0.6000 | 9.1859 | 9.1859 | 0.0812 | 3120 |
| 0.0060 | 0.0010 | 0.7000 | 10.7117 | 10.7117 | 0.0713 | 3263 |
| 0.0060 | 0.0010 | 0.8000 | 12.2511 | 12.2511 | 0.0641 | 3388 |
| 0.0060 | 0.0012 | 0.6000 | 9.1803 | 9.1803 | 0.0813 | 3121 |
| 0.0060 | 0.0012 | 0.7000 | 10.7028 | 10.7028 | 0.0714 | 3263 |
| 0.0060 | 0.0012 | 0.8000 | 12.2381 | 12.2381 | 0.0641 | 3388 |
| 0.0080 | 0.0005 | 0.6000 | 16.2765 | 16.2765 | 0.0526 | 3641 |
| 0.0080 | 0.0005 | 0.7000 | 18.4284 | 18.4284 | 0.0481 | 3648 |
| 0.0080 | 0.0005 | 0.8000 | 20.2719 | 20.2719 | 0.0448 | 3951 |
| 0.0080 | 0.0008 | 0.6000 | 16.2861 | 16.2861 | 0.0524 | 3644 |
| 0.0080 | 0.0008 | 0.7000 | 18.5156 | 18.5156 | 0.0479 | 3652 |
| 0.0080 | 0.0008 | 0.8000 | 20.4358 | 20.4358 | 0.0446 | 3953 |
| 0.0080 | 0.0010 | 0.6000 | 16.2799 | 16.2799 | 0.0524 | 3645 |
| 0.0080 | 0.0010 | 0.7000 | 18.5327 | 18.5327 | 0.0478 | 3653 |
| 0.0080 | 0.0010 | 0.8000 | 20.4777 | 20.4777 | 0.0445 | 3953 |
| 0.0080 | 0.0012 | 0.6000 | 16.2723 | 16.2723 | 0.0524 | 3646 |
| 0.0080 | 0.0012 | 0.7000 | 18.5442 | 18.5442 | 0.0478 | 3654 |
| 0.0080 | 0.0012 | 0.8000 | 20.5000 | 20.5000 | 0.0444 | 3954 |
| 0.0100 | 0.0005 | 0.6000 | 22.4434 | 22.4434 | 0.0415 | 4381 |
| 0.0100 | 0.0005 | 0.7000 | 24.5318 | 24.5318 | 0.0388 | 4541 |
| 0.0100 | 0.0005 | 0.8000 | 26.3350 | 26.3350 | 0.0369 | 4194 |
| 0.0100 | 0.0008 | 0.6000 | 22.6998 | 22.6998 | 0.0412 | 4383 |
| 0.0100 | 0.0008 | 0.7000 | 24.9035 | 24.9035 | 0.0385 | 4546 |
| 0.0100 | 0.0008 | 0.8000 | 26.8043 | 26.8043 | 0.0365 | 4184 |
| 0.0100 | 0.0010 | 0.6000 | 22.7758 | 22.7758 | 0.0411 | 4384 |
| 0.0100 | 0.0010 | 0.7000 | 25.0186 | 25.0186 | 0.0384 | 4548 |
| 0.0100 | 0.0010 | 0.8000 | 26.9593 | 26.9593 | 0.0364 | 4181 |
| 0.0100 | 0.0012 | 0.6000 | 22.8318 | 22.8318 | 0.0411 | 4385 |
| 0.0100 | 0.0012 | 0.7000 | 25.0868 | 25.0868 | 0.0383 | 4549 |
| 0.0100 | 0.0012 | 0.8000 | 27.0528 | 27.0528 | 0.0363 | 4178 |
| 0.0120 | 0.0005 | 0.6000 | 27.3416 | 27.3416 | 0.0358 | 4341 |
| 0.0120 | 0.0005 | 0.7000 | 29.3583 | 29.3583 | 0.0340 | 4536 |
| 0.0120 | 0.0005 | 0.8000 | 31.0333 | 31.0333 | 0.0326 | 4753 |
| 0.0120 | 0.0008 | 0.6000 | 27.8835 | 27.8835 | 0.0354 | 4351 |
| 0.0120 | 0.0008 | 0.7000 | 30.0437 | 30.0437 | 0.0335 | 4544 |
| 0.0120 | 0.0008 | 0.8000 | 31.8941 | 31.8941 | 0.0321 | 4753 |
| 0.0120 | 0.0010 | 0.6000 | 28.0643 | 28.0643 | 0.0353 | 4354 |
| 0.0120 | 0.0010 | 0.7000 | 30.2846 | 30.2846 | 0.0334 | 4547 |
| 0.0120 | 0.0010 | 0.8000 | 32.1622 | 32.1622 | 0.0319 | 4753 |
| 0.0120 | 0.0012 | 0.6000 | 28.1742 | 28.1742 | 0.0352 | 4357 |
| 0.0120 | 0.0012 | 0.7000 | 30.4330 | 30.4330 | 0.0333 | 4548 |
| 0.0120 | 0.0012 | 0.8000 | 32.3506 | 32.3506 | 0.0318 | 4753 |
| 0.0150 | 0.0005 | 0.6000 | 32.9032 | 32.9032 | 0.0311 | 5570 |
| 0.0150 | 0.0005 | 0.7000 | 34.5740 | 34.5740 | 0.0300 | 6498 |
| 0.0150 | 0.0005 | 0.8000 | 35.8326 | 35.8326 | 0.0292 | 7426 |
| 0.0150 | 0.0008 | 0.6000 | 34.0231 | 34.0231 | 0.0306 | 5570 |
| 0.0150 | 0.0008 | 0.7000 | 35.9613 | 35.9613 | 0.0293 | 6498 |
| 0.0150 | 0.0008 | 0.8000 | 37.5559 | 37.5559 | 0.0284 | 7426 |
| 0.0150 | 0.0010 | 0.6000 | 34.3757 | 34.3757 | 0.0304 | 5570 |
| 0.0150 | 0.0010 | 0.7000 | 36.4192 | 36.4192 | 0.0291 | 6498 |
| 0.0150 | 0.0010 | 0.8000 | 38.1370 | 38.1370 | 0.0282 | 7426 |
| 0.0150 | 0.0012 | 0.6000 | 34.6232 | 34.6232 | 0.0303 | 5570 |
| 0.0150 | 0.0012 | 0.7000 | 36.7391 | 36.7391 | 0.0290 | 6498 |
| 0.0150 | 0.0012 | 0.8000 | 38.4787 | 38.4787 | 0.0280 | 7426 |
| 0.0180 | 0.0005 | 0.6000 | 36.4385 | 36.4385 | 0.0287 | 8020 |
| 0.0180 | 0.0005 | 0.7000 | 37.5580 | 37.5580 | 0.0280 | 9357 |
| 0.0180 | 0.0005 | 0.8000 | 38.3076 | 38.3076 | 0.0274 | 1.069e+04 |
| 0.0180 | 0.0008 | 0.6000 | 38.3928 | 38.3928 | 0.0279 | 8020 |
| 0.0180 | 0.0008 | 0.7000 | 39.9578 | 39.9578 | 0.0271 | 9357 |
| 0.0180 | 0.0008 | 0.8000 | 41.1333 | 41.1333 | 0.0265 | 1.069e+04 |
| 0.0180 | 0.0010 | 0.6000 | 39.0595 | 39.0595 | 0.0277 | 8020 |
| 0.0180 | 0.0010 | 0.7000 | 40.7481 | 40.7481 | 0.0268 | 9357 |
| 0.0180 | 0.0010 | 0.8000 | 42.0973 | 42.0973 | 0.0262 | 1.069e+04 |
| 0.0180 | 0.0012 | 0.6000 | 39.4538 | 39.4538 | 0.0275 | 8020 |
| 0.0180 | 0.0012 | 0.7000 | 41.2672 | 41.2672 | 0.0266 | 9357 |
| 0.0180 | 0.0012 | 0.8000 | 42.6597 | 42.6597 | 0.0259 | 1.069e+04 |
### Flange Check
| Assumption | Value |
|---|---:|
| n_bolts | 6 |
| pcd_m | 0.08 |
| bolt_dia_m | 0.008 |
| bolt_material_shear | 240000000.0 |

| Flange Metric | Value |
|---|---:|
| n_bolts | 6 |
| cap_per_bolt_N | 12063.715789784805 |
| bolts_needed | 1 |

| Worst-case param | Value |
|---|---:|
| orifice_d_m | 0.018 |
| Vc_m3 | 0.0005 |
| Cd | 0.8 |
| muzzle_v | 38.307600282677335 |
| impulse | 38.307600282677335 |
| t_end_s | 0.02739999999999989 |
| peak_F | 10694.11419802843 |
## Final Measurements
| Parameter | Value |
|---|---:|
| scale_mm_per_px | 0.709 |
| scale_px | 987.000 |
| used_region_for_scale | top |
| overall_length_mm | 701.418 |
| chamber_length_mm | 39.716 |
| frame_width_mm | 697.872 |
| overall_height_mm | 263.121 |
| barrel_length_mm | 700.000 |

## Fit Verification
| Parameter | Nominal | Measured | Units | Delta | Tolerance (%) | Pass |
|---|---:|---:|---:|---:|---:|---:|
| Overall length | 999.72 | 701.42 | mm | -298.30 | 5.0 | FAIL |
| co2_cartridge width | 120.00 | 120.00 | mm | 0.00 | 5.0 | PASS |
| chamber width | 39.72 | 39.72 | mm | 0.00 | 5.0 | PASS |
| flange width | 20.00 | 20.00 | mm | 0.00 | 5.0 | PASS |
| barrel width | 700.00 | 700.00 | mm | 0.00 | 5.0 | PASS |
| sabot width | 60.00 | 60.00 | mm | 0.00 | 5.0 | PASS |
## Diagrams
### Top view
![Top view](outputs\launcher_top_view.png)
### Side view
![Side view](outputs\launcher_side_view.png)

## Plots
### impulse_vs_orifice_Vc_1000uL.png
![impulse_vs_orifice_Vc_1000uL.png](outputs\impulse_vs_orifice_Vc_1000uL.png)
### launcher_drawing.png
![launcher_drawing.png](outputs\launcher_drawing.png)
### launcher_drawing_preview.png
![launcher_drawing_preview.png](outputs\launcher_drawing_preview.png)
### launcher_side_view.png
![launcher_side_view.png](outputs\launcher_side_view.png)
### launcher_top_view.png
![launcher_top_view.png](outputs\launcher_top_view.png)
### peakF_vs_orifice_Vc_1000uL.png
![peakF_vs_orifice_Vc_1000uL.png](outputs\peakF_vs_orifice_Vc_1000uL.png)
### top_view_and_side_view.png
![top_view_and_side_view.png](outputs\top_view_and_side_view.png)
### top_view_measured.png
![top_view_measured.png](outputs\top_view_measured.png)
### vel_vs_orifice_Vc_1000uL.png
![vel_vs_orifice_Vc_1000uL.png](outputs\vel_vs_orifice_Vc_1000uL.png)
### vel_vs_orifice_Vc_1200uL.png
![vel_vs_orifice_Vc_1200uL.png](outputs\vel_vs_orifice_Vc_1200uL.png)
### vel_vs_orifice_Vc_500uL.png
![vel_vs_orifice_Vc_500uL.png](outputs\vel_vs_orifice_Vc_500uL.png)
### vel_vs_orifice_Vc_800uL.png
![vel_vs_orifice_Vc_800uL.png](outputs\vel_vs_orifice_Vc_800uL.png)
