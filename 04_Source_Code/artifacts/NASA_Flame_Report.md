# NASA Microgravity Combustion — Analytical Ranking Report

## 1. Scoring Methodology & Weight Distribution
| Component Metric | Weight | Description |
| :--- | :---: | :--- |
| `flame_stability_score` | 0.25 | Spherical flame symmetry and steady state |
| `fire_safety_score` | 0.25 | Spacecraft material safety & quenching behavior |
| `data_completeness_score` | 0.15 | Diagnostic resolution and sensor completeness |
| `norm_burn_rate` | 0.15 | Min-Max normalized burn/regression rate (`mm/s`) |
| `norm_burn_duration` | 0.10 | Min-Max normalized combustion duration (`s`) |
| `norm_oxygen_margin` | 0.10 | Min-Max normalized oxygen concentration (`%`) |

## 2. Executive Ranking Table
| Rank | Experiment ID | Fuel / Material | Pressure (kPa) | O2 (%) | Burn Rate (mm/s) | Duration (s) | Penalty | Final Score |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | `EXP_FLEX_01` | n-Heptane | 101.33 | 20.00 | 1.200 | 20.00 | -0.00 | **94.70** |

## 3. Detailed Experiment Breakdown & Citations

### Rank #1: `EXP_FLEX_01` (Score: 94.70 / 100)
- **Fuel / Material**: n-Heptane | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `99.56` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.15` | Spacesuit (`29.65 kPa, 100% O2`): `44.59`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `95.0`, Safety `88.0`, Completeness `93.0`
- **Confidence Penalty**: `-0.00` (Missing fields: `None`)
- **Key Findings**: Free-floating n-Heptane droplet burned in 20.0% O2 at 101.325 kPa and 298.15 K with a burn rate of 1.2 mm/s for 20.0 s inside CIR/MDCA.
- **Verified Citations**: [SOURCE: JASMAC-33 FLEX w video.pdf | LOC: page_14]; [SOURCE: 20150023456.pdf | LOC: page_230]; [SOURCE: 20150023456.pdf | LOC: page_76]; [SOURCE: 20150023456.pdf | LOC: page_182]; [SOURCE: 20150023456.pdf | LOC: page_8]; [SOURCE: 20150023456.pdf | LOC: page_229]
