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
| **1** | `ACME-CFI-G` | Butane | 101.33 | 85.00 | N/A | 304.00 | -4.00 | **77.49** |
| **2** | `BASS` | Cotton | 101.35 | N/A | 500.000 | N/A | -8.00 | **76.25** |
| **3** | `SPICE` | Methane | 101.35 | 21.00 | 400.000 | N/A | -4.00 | **73.24** |
| **4** | `SLICE` | Methane | 101.35 | N/A | 350.000 | N/A | -8.00 | **69.25** |
| **5** | `SAFFIRE-III` | Cotton | 70.33 | N/A | 300.000 | N/A | -8.00 | **67.75** |
| **6** | `SAFFIRE-I` | Cotton | 103.33 | 21.00 | 200.000 | N/A | -4.00 | **64.94** |
| **7** | `FLEX-2` | n-Heptane | 103.45 | 30.00 | 150.000 | N/A | -4.00 | **64.50** |
| **8** | `PSI-98_SAFFIRE-I` | N/A | 101.33 | 21.60 | 20.000 | 420.00 | -4.00 | **64.42** |
| **9** | `FLEX` | Methanol and n-Heptane | 101.33 | 14.00 | 100.000 | 60.00 | -0.00 | **63.68** |
| **10** | `ACME-BRE` | Methane | 106.35 | 35.00 | 0.000 | N/A | -4.00 | **63.21** |
| **11** | `ACME-BRE_ACME-BRE` | Pmma | 104.00 | 21.00 | 1.200 | N/A | -4.00 | **62.17** |
| **12** | `PSI-107_SPICE` | N/A | N/A | N/A | 363.900 | 60.00 | -12.00 | **62.10** |
| **13** | `ACME-E-FIELD` | Methane/Ethylene | 102.35 | 18.00 | 150.000 | 0.00 | -0.00 | **61.81** |
| **14** | `ACME-E-FIELD_ACME-E-FIELD` | Methane | 104.00 | 21.00 | 0.160 | N/A | -4.00 | **61.69** |
| **15** | `SAFFIRE-II` | Hydrogen | 56.54 | N/A | N/A | 5.00 | -8.00 | **61.57** |
| **16** | `EXP_FLEX_01` | n-Heptane | 101.33 | 20.00 | 1.200 | 18.00 | -0.00 | **61.01** |
| **17** | `MSG-DAFT_DAFT_DAFT-2` | Lunar Dust Simulant / Cabin Aerosol | 103.34 | 21.00 | 3.800 | 10.00 | -0.00 | **60.59** |
| **18** | `COOL-FLAMES-MODEL` | N/A | 106.15 | 30.00 | 150.000 | N/A | -8.00 | **60.50** |
| **19** | `PSI-68_FLEX-2` | Octane | 50.66 | N/A | 1.000 | N/A | -8.00 | **58.78** |
| **20** | `PSI-10_ACME-FLAMEDESIGN` | N/A | 101.73 | N/A | N/A | N/A | -16.00 | **58.25** |
| **21** | `PSI-69_FLEX` | Methanol | 101.33 | 21.00 | 4.800 | 6.34 | -0.00 | **58.03** |
| **22** | `BASS-II` | Pmma | 101.33 | 21.00 | 2.200 | 2.00 | -0.00 | **57.85** |
| **23** | `PSI-100_SAFFIRE-III` | N/A | N/A | N/A | 300.000 | N/A | -16.00 | **57.25** |
| **24** | `ACME-FLAMEDESIGN` | Ethylene, Methane | 101.33 | 15.00 | 0.000 | 0.00 | -0.00 | **56.89** |
| **25** | `MSG-SLICE_SLICE` | Diluted Methane Jet | 106.39 | 21.00 | 15.000 | 0.00 | -0.00 | **56.44** |
| **26** | `PSI-159_ACME-CFI-G` | N/A | 94.44 | N/A | N/A | 44.80 | -12.00 | **56.32** |
| **27** | `FUTURE-LUCI-FM2_LUCI_FM2_UPCOMING` | Lunar Habitat Polymer (Bounding Estimate) | 70.00 | 34.00 | 5.800 | 0.00 | -0.00 | **56.04** |
| **28** | `SAME-R` | N/A | N/A | N/A | N/A | N/A | -20.00 | **56.00** |
| **29** | `PSI-25_BASS-II` | Pmma | 101.33 | 22.20 | 1.200 | 18.00 | -0.00 | **55.87** |
| **30** | `PSI-26_BASS` | Pmma | N/A | N/A | N/A | N/A | -16.00 | **55.75** |
| **31** | `SAME` | N/A | 103.43 | 21.00 | N/A | N/A | -12.00 | **55.74** |
| **32** | `DAFT_DAFT-2` | N/A | 101.35 | 21.00 | 100.000 | N/A | -8.00 | **55.24** |
| **33** | `00_ISS_REFERENCE_GUIDE` | Cotton | N/A | 17.00 | 100.000 | 90.00 | -4.00 | **54.32** |
| **34** | `PSI-142_COOL-FLAMES-MODEL` | N/A | N/A | N/A | N/A | N/A | -20.00 | **54.25** |
| **35** | `LUCI_FM2_UPCOMING` | N/A | 70.33 | 30.00 | N/A | N/A | -12.00 | **52.50** |
| **36** | `03_SUPPRESSION` | N/A | N/A | N/A | N/A | N/A | -20.00 | **51.75** |
| **37** | `PSI-101_SAME-R` | N/A | N/A | N/A | 81.000 | 60.00 | -12.00 | **51.61** |
| **38** | `PSI-99_SAFFIRE-II` | N/A | 101.33 | 21.50 | 1.200 | 0.00 | -4.00 | **51.34** |
| **39** | `PSI-102_SAME` | N/A | N/A | N/A | 50.000 | 60.00 | -12.00 | **50.18** |
| **40** | `PAPERS` | N/A | N/A | N/A | 2.200 | 2.00 | -12.00 | **47.06** |

## 3. Detailed Experiment Breakdown & Citations

### Rank #1: `ACME-CFI-G` (Score: 77.49 / 100)
- **Fuel / Material**: Butane | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `41.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `89.48` | Spacesuit (`29.65 kPa, 100% O2`): `62.46`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `85.0`, Completeness `90.0`
- **Confidence Penalty**: `-4.00` (Missing fields: `burn_rate_mm_s`)
- **Key Findings**: Experiment ACME-CFI-G investigated gaseous fuels (Propane, n-Butane, n-Pentane) under high oxygen concentrations (21.0% to 85.0%) and pressure of 14.7 psi (101.325 kPa). Normal and inverse flames were observed with burn times ranging from 0 to 304 seconds. The experiment simulated microgravity conditions and utilized a spherical porous burner.
- **Verified Citations**: [SOURCE: PSI-159_Experimental table_CFI-G_Inverse Flames.csv | LOC: sheet_csv]; [SOURCE: PSI-159_Experimental table_CFI-G_Normal Flames.csv | LOC: sheet_csv]; [SOURCE: ACME-CFI-G_metadata.csv | LOC: sheet_csv]

### Rank #2: `BASS` (Score: 76.25 / 100)
- **Fuel / Material**: Cotton | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.97` | Spacesuit (`29.65 kPa, 100% O2`): `44.86`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `92.0`, Completeness `95.0`
- **Confidence Penalty**: `-8.00` (Missing fields: `oxygen_pct, burn_duration_s`)
- **Key Findings**: Experiment BASS investigates flame spread rates in both counterflow and forced airflow directions, as well as fire suppression using nitrogen gas in the MSG (SPICE Flow Duct) environment. The experiment uses solid polymer rods, thin films, and cotton-fiberglass as fuels. The oxygen concentration ranges from 16.0% to 21.0%, the pressure is 14.7 psi, and the maximum airflow speed is 50.0 cm/s.
- **Verified Citations**: [SOURCE: BASS_metadata.csv | LOC: sheet_csv]

### Rank #3: `SPICE` (Score: 73.24 / 100)
- **Fuel / Material**: Methane | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.97` | Spacesuit (`29.65 kPa, 100% O2`): `44.86`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `92.0`, Completeness `95.0`
- **Confidence Penalty**: `-4.00` (Missing fields: `burn_duration_s`)
- **Key Findings**: Experiment SPICE investigates the smoke point of gaseous fuels (Ethylene, Propane, Methane, Propylene) in co-flowing air within the MSG Flow Duct. The experiment operates at 21.0% O2, 14.7 psi pressure, and an airflow of 40.0 cm/s. The study aims to determine when the flame begins to emit soot in the duct.
- **Verified Citations**: [SOURCE: SPICE_metadata.csv | LOC: sheet_csv]

### Rank #4: `SLICE` (Score: 69.25 / 100)
- **Fuel / Material**: Methane | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.97` | Spacesuit (`29.65 kPa, 100% O2`): `44.86`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `85.0`, Completeness `90.0`
- **Confidence Penalty**: `-8.00` (Missing fields: `oxygen_pct, burn_duration_s`)
- **Key Findings**: Experiment uses a shared SPICE duct with BASS in the MSG rack to measure flame structure and liftoff phenomena until extinguishment. The experiment simulates microgravity conditions (0g) and involves methane co-flow laminar jet flames. The oxygen concentration ranges from 15.0% to 21.0%, the pressure is 14.7 psi, and the maximum airflow is 35.0 cm/s.
- **Verified Citations**: [SOURCE: SLICE_metadata.csv | LOC: sheet_csv]

### Rank #5: `SAFFIRE-III` (Score: 67.75 / 100)
- **Fuel / Material**: Cotton | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `91.82` | Lunar Base (`<=70.33 kPa, >=30% O2`): `93.00` | Spacesuit (`29.65 kPa, 100% O2`): `51.74`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `85.0`, Completeness `90.0`
- **Confidence Penalty**: `-8.00` (Missing fields: `oxygen_pct, burn_duration_s`)
- **Key Findings**: Large Sibal cotton-fiberglass panel burned in a simulated lunar/mission atmosphere with oxygen concentration ranging from 21.0% to 34.0%, pressure at 10.2 psi, and airflow up to 30.0 cm/s. The experiment simulates microgravity conditions and investigates fire behavior in a partial gravity environment.
- **Verified Citations**: [SOURCE: SAFFIRE-III_metadata.csv | LOC: sheet_csv]

### Rank #6: `SAFFIRE-I` (Score: 64.94 / 100)
- **Fuel / Material**: Cotton | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.27` | Spacesuit (`29.65 kPa, 100% O2`): `44.42`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `90.0`, Completeness `88.0`
- **Confidence Penalty**: `-4.00` (Missing fields: `burn_duration_s`)
- **Key Findings**: Large Sibal cloth (0.4 m x 0.94 m, 75% cotton / 25% fiberglass) burned in 21.0% O2 at 103.329 kPa with an airflow of 20.0 cm/s. The experiment was conducted in microgravity conditions to measure fire propagation limits.
- **Verified Citations**: [SOURCE: SAFFIRE-I_metadata.csv | LOC: sheet_csv]

### Rank #7: `FLEX-2` (Score: 64.50 / 100)
- **Fuel / Material**: n-Heptane | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `87.52` | Lunar Base (`<=70.33 kPa, >=30% O2`): `88.73` | Spacesuit (`29.65 kPa, 100% O2`): `46.87`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `85.0`, Completeness `90.0`
- **Confidence Penalty**: `-4.00` (Missing fields: `burn_duration_s`)
- **Key Findings**: Flame Extinguishment Experiment - 2 & Cool Flames (CFI) with n-Heptane, n-Octane, n-Decane, Iso-octane droplets & arrays burned in 15.0% to 30.0% O2 at 103.45 kPa with airflow of 15.0 cm/s. Cool flames were observed after flame extinction in microgravity conditions.
- **Verified Citations**: [SOURCE: FLEX-2_metadata.csv | LOC: sheet_csv]

### Rank #8: `PSI-98_SAFFIRE-I` (Score: 64.42 / 100)
- **Fuel / Material**: N/A | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `82.48` | Spacesuit (`29.65 kPa, 100% O2`): `45.03`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `85.0`, Completeness `90.0`
- **Confidence Penalty**: `-4.00` (Missing fields: `fuel_or_material`)
- **Key Findings**: SIBAL Fabric burned in 21.6% O2 at 101.325 kPa and 298.15 K with a burn rate of 20.0 mm/s for 420.0 s.
- **Verified Citations**: [SOURCE: PSI-98_Experimental_Table_2.csv | LOC: sheet_csv]; [SOURCE: PSI-98_Experimental_Table_2.xlsx | LOC: sheet_Sheet1]

### Rank #9: `FLEX` (Score: 63.68 / 100)
- **Fuel / Material**: Methanol and n-Heptane | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `90.99` | Lunar Base (`<=70.33 kPa, >=30% O2`): `76.15` | Spacesuit (`29.65 kPa, 100% O2`): `42.94`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `92.0`, Completeness `95.0`
- **Confidence Penalty**: `-0.00` (Missing fields: `None`)
- **Key Findings**: Flame Extinguishment Experiment conducted with liquid droplets of Methanol and n-Heptane (1.5 - 4.0 mm) in the MDCA (CIR rack) under 14.7 psi pressure, with oxygen concentration ranging from 14.0% to 30.0%, and airflow up to 10.0 cm/s. The experiment aimed to measure minimum CO2 and Helium concentrations required to extinguish flames in microgravity.
- **Verified Citations**: [SOURCE: FLEX_metadata.csv | LOC: sheet_csv]

### Rank #10: `ACME-BRE` (Score: 63.21 / 100)
- **Fuel / Material**: Methane | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `79.52` | Lunar Base (`<=70.33 kPa, >=30% O2`): `87.70` | Spacesuit (`29.65 kPa, 100% O2`): `47.60`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `95.0`, Safety `88.0`, Completeness `90.0`
- **Confidence Penalty**: `-4.00` (Missing fields: `burn_duration_s`)
- **Key Findings**: Burning Rate Emulator (ACME Project) using gaseous fuels (Ethylene/Methane doped with N2/CO2 simulating PMMA, Delrin, paper, alcohols) in 17.0-35.0% O2 at 106.35 kPa with airflow_max_cm_s=0.0 cm/s and simulates_partial_g=0.0 g.
- **Verified Citations**: [SOURCE: ACME-BRE_metadata.csv | LOC: sheet_csv]

### Rank #11: `ACME-BRE_ACME-BRE` (Score: 62.17 / 100)
- **Fuel / Material**: Pmma | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.03` | Spacesuit (`29.65 kPa, 100% O2`): `44.27`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `95.0`, Safety `88.0`, Completeness `96.0`
- **Confidence Penalty**: `-4.00` (Missing fields: `burn_duration_s`)
- **Key Findings**: Gaseous Emulation of PMMA burned in 21.0% O2 at 104.0 kPa with a burn rate of 1.2 mm/s.
- **Verified Citations**: [SOURCE: ACME-BRE_Experimental_Table.csv | LOC: sheet_csv]; [SOURCE: ACME-BRE_Experimental_Table.xlsx | LOC: sheet_Sheet1]

### Rank #12: `PSI-107_SPICE` (Score: 62.10 / 100)
- **Fuel / Material**: N/A | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.98` | Spacesuit (`29.65 kPa, 100% O2`): `44.86`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `85.0`, Completeness `90.0`
- **Confidence Penalty**: `-12.00` (Missing fields: `fuel_or_material, pressure_kpa, oxygen_pct`)
- **Key Findings**: Experiment PSI-107_SPICE conducted in 0g microgravity with Ethylene as the fuel. The experiment used a nozzle size of 1.6002 mm, with a fuel rate of 103.8 sccm (1.971 mg/s), and an air rate of 36.39 cm/s. The burn duration was 60 seconds (from 14:37:08 to 14:48:03).
- **Verified Citations**: [SOURCE: PSI-107_Experimental_Table_2.xlsx | LOC: sheet_Sheet1]; [SOURCE: PSI-107_Experimental_Table_2.csv | LOC: sheet_csv]

### Rank #13: `ACME-E-FIELD` (Score: 61.81 / 100)
- **Fuel / Material**: Methane/Ethylene | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `96.42` | Lunar Base (`<=70.33 kPa, >=30% O2`): `79.12` | Spacesuit (`29.65 kPa, 100% O2`): `43.81`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `85.0`, Completeness `90.0`
- **Confidence Penalty**: `-0.00` (Missing fields: `None`)
- **Key Findings**: Electric-field effects on laminar diffusion flames of methane/ethylene under high-voltage electric field (up to 10 kV) with oxygen concentration between 18.0% and 30.0%, at 102.35 kPa pressure and 15.0 cm/s airflow. Simulates partial gravity conditions for lunar and planetary environments.
- **Verified Citations**: [SOURCE: ACME-E-FIELD_metadata.csv | LOC: sheet_csv]

### Rank #14: `ACME-E-FIELD_ACME-E-FIELD` (Score: 61.69 / 100)
- **Fuel / Material**: Methane | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.03` | Spacesuit (`29.65 kPa, 100% O2`): `44.27`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `95.0`, Safety `88.0`, Completeness `93.0`
- **Confidence Penalty**: `-4.00` (Missing fields: `burn_duration_s`)
- **Key Findings**: Methane Diffusion Flame (3.5 kV) burned in 21.0% O2 at 104.0 kPa with an airflow of 8.5 cm/s and a spread rate of 0.16 mm/s. Methane Diffusion Flame (6.0 kV) burned in 21.0% O2 at 104.0 kPa with an airflow of 14.0 cm/s and a spread rate of 0.38 mm/s.
- **Verified Citations**: [SOURCE: ACME-E-FIELD_Experimental_Table.csv | LOC: sheet_csv]; [SOURCE: ACME-E-FIELD_Experimental_Table.xlsx | LOC: sheet_Sheet1]

### Rank #15: `SAFFIRE-II` (Score: 61.57 / 100)
- **Fuel / Material**: Hydrogen | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `87.74` | Lunar Base (`<=70.33 kPa, >=30% O2`): `93.00` | Spacesuit (`29.65 kPa, 100% O2`): `54.81`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `90.0`, Completeness `88.0`
- **Confidence Penalty**: `-8.00` (Missing fields: `oxygen_pct, burn_rate_mm_s`)
- **Key Findings**: SAFFIRE-II experiment investigates low-g flammability limits compared to normal gravity material flammability screening tests, with objectives to determine large-scale fire growth rates in microgravity and examine flammability limits in exploration atmospheres with oxygen mole fractions up to 0.34 and pressures of 8.2 psia.
- **Verified Citations**: [SOURCE: SAFFIRE-II_NASA_Report_20170000230.pdf | LOC: page_7]; [SOURCE: SAFFIRE-II_NASA_Report_20170000230.pdf | LOC: page_1]; [SOURCE: SAFFIRE-II_NASA_Report_20170000230.pdf | LOC: page_9]; [SOURCE: SAFFIRE-II_NASA_Report_20170000230.pdf | LOC: page_1]; [SOURCE: SAFFIRE-II_NASA_Report_20170000230.pdf | LOC: page_2]; [SOURCE: SAFFIRE-II_NASA_Report_20170000230.pdf | LOC: page_7]

### Rank #16: `EXP_FLEX_01` (Score: 61.01 / 100)
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
- **Key Findings**: Free-floating heptane droplet burned in 20.0% O2 at 101.325 kPa and 298.15 K with a burn rate of 1.2 mm/s for 18.0 s. The droplet diameter decreased over time, indicating evaporation, and the flame extinguished radiatively after 15 to 20 s. The LLUV measurements showed a decrease in flame diameter over time, and the droplet disrupted coincident with flame extinction.
- **Verified Citations**: [SOURCE: JASMAC-33 FLEX w video.pdf | LOC: page_14]; [SOURCE: 20150023456.pdf | LOC: page_230]; [SOURCE: 20150023456.pdf | LOC: page_76]; [SOURCE: 20150023456.pdf | LOC: page_182]; [SOURCE: 20150023456.pdf | LOC: page_8]; [SOURCE: 20150023456.pdf | LOC: page_229]

### Rank #17: `MSG-DAFT_DAFT_DAFT-2` (Score: 60.59 / 100)
- **Fuel / Material**: Lunar Dust Simulant / Cabin Aerosol | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.26` | Spacesuit (`29.65 kPa, 100% O2`): `44.41`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `92.0`, Completeness `95.0`
- **Confidence Penalty**: `-0.00` (Missing fields: `None`)
- **Key Findings**: Lunar Dust Simulant / Cabin Aerosol burned in 21.0% O2 at 103.345 kPa and 293.15 K with a burn rate of 3.8 mm/s for 10.0 s.
- **Verified Citations**: [SOURCE: MSG-DAFT_Experimental_Table.xlsx | LOC: sheet_Sheet1]; [SOURCE: MSG-DAFT_Experimental_Table.csv | LOC: sheet_csv]

### Rank #18: `COOL-FLAMES-MODEL` (Score: 60.50 / 100)
- **Fuel / Material**: N/A | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `86.72` | Lunar Base (`<=70.33 kPa, >=30% O2`): `87.77` | Spacesuit (`29.65 kPa, 100% O2`): `46.27`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `85.0`, Completeness `90.0`
- **Confidence Penalty**: `-8.00` (Missing fields: `fuel_or_material, burn_duration_s`)
- **Key Findings**: Quantitative studies of cool flame transitions (FLEX derivative) conducted in 15.0-30.0% O2 at 106.15 kPa with airflow of 15.0 cm/s in microgravity conditions, focusing on the transition between hot and cool flames for fire suppression modeling.
- **Verified Citations**: [SOURCE: Cool-Flames-Model_metadata.csv | LOC: sheet_csv]

### Rank #19: `PSI-68_FLEX-2` (Score: 58.78 / 100)
- **Fuel / Material**: Octane | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `86.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `93.00` | Spacesuit (`29.65 kPa, 100% O2`): `56.11`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `85.0`, Completeness `90.0`
- **Confidence Penalty**: `-8.00` (Missing fields: `oxygen_pct, burn_duration_s`)
- **Key Findings**: Experiment PSI-68_FLEX-2 involved testing pure fuels including IsoOctane, n-Octane, and Heptane under microgravity conditions. The ambient temperature was maintained at 25 °C (298.15 K), and the ambient pressure varied between 0.5 atm to 3.0 atm. The oxygen mole fraction ranged from 0.17 to 0.3, with the gas mixture being either O2/N2 or O2/He. The flow velocity ranged from 0.1 cm/s to 5 cm/s. The initial droplet diameter was between 1.5 mm and 5 mm.
- **Verified Citations**: [SOURCE: PSI-68_Experimental_Table_2.xlsx | LOC: sheet_Sheet1]; [SOURCE: PSI-68_Experimental_Table_2.csv | LOC: sheet_csv]

### Rank #20: `PSI-10_ACME-FLAMEDESIGN` (Score: 58.25 / 100)
- **Fuel / Material**: N/A | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.84` | Spacesuit (`29.65 kPa, 100% O2`): `44.77`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `85.0`, Completeness `90.0`
- **Confidence Penalty**: `-16.00` (Missing fields: `fuel_or_material, oxygen_pct, burn_rate_mm_s, burn_duration_s`)
- **Key Findings**: Flame experiments conducted in microgravity with varying oxygen concentrations (XO2) ranging from 0.2123 to 0.85, with mean XO2 of 0.5309. The experiments involved oxygen flow rates (mO2) ranging from 2.367 to 9.799 mg/s and nitrogen flow rates (mN2) ranging from 1.234 to 7.688 mg/s. The total mass flow rate (mtot) ranged from 9.222 to 12.72 mg/s. Initial and final concentrations of C2H4 were observed, with mean initial concentration of 0.195 and mean final concentration of 0.189. The initial pressure (pinit) ranged from 0.9492 to 1.004 atm, with a mean of 0.9807 atm. The final pressure (pfinal) ranged from 0.9492 to 1.004 atm, with a mean of 0.9807 atm. The mean pressure (pmean) was 0.9807 atm. The mean Zst and Tad (K) were recorded.
- **Verified Citations**: [SOURCE: PSI-10_Experimental_Table_2.csv | LOC: sheet_csv]; [SOURCE: PSI-10_Experimental_Table_2.xlsx | LOC: sheet_Sheet1]

### Rank #21: `PSI-69_FLEX` (Score: 58.03 / 100)
- **Fuel / Material**: Methanol | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.98` | Spacesuit (`29.65 kPa, 100% O2`): `44.86`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `85.0`, Completeness `90.0`
- **Confidence Penalty**: `-0.00` (Missing fields: `None`)
- **Key Findings**: Methanol droplet burned in 21.0% O2 at 101.325 kPa and 298.15 K with a burn rate of 4.8 mm/s for 6.34 s.
- **Verified Citations**: [SOURCE: PSI-69_Experimental_Table_2.csv | LOC: sheet_csv]; [SOURCE: PSI-69_Experimental_Table_2.xlsx | LOC: sheet_Sheet1]

### Rank #22: `BASS-II` (Score: 57.85 / 100)
- **Fuel / Material**: Pmma | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.98` | Spacesuit (`29.65 kPa, 100% O2`): `44.86`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `85.0`, Completeness `90.0`
- **Confidence Penalty**: `-0.00` (Missing fields: `None`)
- **Key Findings**: Flame spread rate over thin solid fuel in microgravity environment is influenced by opposing flow velocity. Extinction velocity increases with decreasing O2 levels. For 100-µm-thick PMMA samples, extinction velocities were found to be 1.5 cm/s at 21% O2 and 3.5 cm/s at 16% O2. The critical extinction velocity is independent of fuel thickness and increases with lower O2 levels. Flame extinction occurs due to radiative losses and reduced flow velocity, with the flame becoming blue as temperature drops. The radiometer data indicate a sudden change in slope at extinction, suggesting the radiation is emitted mostly by the sample holder.
- **Verified Citations**: [SOURCE: BASS-II_NASA_Report_20210011385.pdf | LOC: page_31]; [SOURCE: BASS-II_NASA_Report_20210011385.pdf | LOC: page_34]; [SOURCE: BASS-II_NASA_Report_20210011385.pdf | LOC: page_101]; [SOURCE: BASS-II_NASA_Report_20210011385.pdf | LOC: page_36]; [SOURCE: BASS-II_NASA_Report_20210011385.pdf | LOC: page_23]; [SOURCE: BASS-II_NASA_Report_20210011385.pdf | LOC: page_27]

### Rank #23: `PSI-100_SAFFIRE-III` (Score: 57.25 / 100)
- **Fuel / Material**: N/A | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.98` | Spacesuit (`29.65 kPa, 100% O2`): `44.86`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `78.0`, Completeness `90.0`
- **Confidence Penalty**: `-16.00` (Missing fields: `fuel_or_material, pressure_kpa, oxygen_pct, burn_duration_s`)
- **Key Findings**: SIBAL Fabric samples burned in microgravity with air flow of 30 cm/s, concurrent and opposed directions, with sample dimensions of 94 cm length, 40.6 cm width, and 0.33 cm thickness.
- **Verified Citations**: [SOURCE: PSI-100_Experimental_Table_2.csv | LOC: sheet_csv]; [SOURCE: PSI-100_Experimental_Table_2.xlsx | LOC: sheet_Sheet1]

### Rank #24: `ACME-FLAMEDESIGN` (Score: 56.89 / 100)
- **Fuel / Material**: Ethylene, Methane | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `92.42` | Lunar Base (`<=70.33 kPa, >=30% O2`): `76.98` | Spacesuit (`29.65 kPa, 100% O2`): `43.21`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `85.0`, Completeness `90.0`
- **Confidence Penalty**: `-0.00` (Missing fields: `None`)
- **Key Findings**: Spherical diffusion flames of Ethylene and Methane were studied in a CIR (ACME Modular Hardware) chamber with oxygen concentration ranging from 15.0% to 40.0%, at a pressure of 14.7 psi (101.325 kPa) and airflow of 0.0 cm/s. The experiment investigates soot formation and flame extinction limits due to radiative heat loss.
- **Verified Citations**: [SOURCE: ACME-FlameDesign_metadata.csv | LOC: sheet_csv]

### Rank #25: `MSG-SLICE_SLICE` (Score: 56.44 / 100)
- **Fuel / Material**: Diluted Methane Jet | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `99.51` | Lunar Base (`<=70.33 kPa, >=30% O2`): `80.18` | Spacesuit (`29.65 kPa, 100% O2`): `43.74`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `78.0`, Completeness `95.0`
- **Confidence Penalty**: `-0.00` (Missing fields: `None`)
- **Key Findings**: Diluted Methane Jet burned in 21.0% O2 at 106.39 kPa with a spread rate of 15.0 mm/s and airflow of 30.0 cm/s. Flame base liftoff and blowout boundary observed.
- **Verified Citations**: [SOURCE: MSG-SLICE_Experimental_Table.csv | LOC: sheet_csv]; [SOURCE: MSG-SLICE_Experimental_Table.xlsx | LOC: sheet_Sheet1]

### Rank #26: `PSI-159_ACME-CFI-G` (Score: 56.32 / 100)
- **Fuel / Material**: N/A | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `98.95` | Lunar Base (`<=70.33 kPa, >=30% O2`): `84.43` | Spacesuit (`29.65 kPa, 100% O2`): `46.39`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `80.0`, Completeness `90.0`
- **Confidence Penalty**: `-12.00` (Missing fields: `fuel_or_material, oxygen_pct, burn_rate_mm_s`)
- **Key Findings**: Experiment conducted under 0g microgravity conditions with fuel tested at an approximate pressure of 0.9444 bar (94.44 kPa), oxygen concentration of 38.39% (XO2 after test), and burn time of 44.8 seconds. The experiment involved multiple tests with varying burn times ranging from 28 to 61 seconds.
- **Verified Citations**: [SOURCE: PSI-159_Experimental_Table_2.csv | LOC: sheet_csv]; [SOURCE: PSI-159_Experimental_Table_2.xlsx | LOC: sheet_Sheet1]

### Rank #27: `FUTURE-LUCI-FM2_LUCI_FM2_UPCOMING` (Score: 56.04 / 100)
- **Fuel / Material**: Lunar Habitat Polymer (Bounding Estimate) | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `73.15` | Lunar Base (`<=70.33 kPa, >=30% O2`): `100.00` | Spacesuit (`29.65 kPa, 100% O2`): `55.39`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `78.0`, Completeness `82.0`
- **Confidence Penalty**: `-0.00` (Missing fields: `None`)
- **Key Findings**: Lunar Habitat Polymer (Bounding Estimate) burned in 34.0% O2 at 70.0 kPa with an airflow of 15.0 cm/s and a spread rate of 5.8 mm/s.
- **Verified Citations**: [SOURCE: FUTURE-LUCI-FM2_Experimental_Table.csv | LOC: sheet_csv]; [SOURCE: FUTURE-LUCI-FM2_Experimental_Table.xlsx | LOC: sheet_Sheet1]

### Rank #28: `SAME-R` (Score: 56.00 / 100)
- **Fuel / Material**: N/A | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.98` | Spacesuit (`29.65 kPa, 100% O2`): `44.86`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `95.0`, Safety `88.0`, Completeness `85.0`
- **Confidence Penalty**: `-20.00` (Missing fields: `fuel_or_material, pressure_kpa, oxygen_pct, burn_rate_mm_s, burn_duration_s`)
- **Key Findings**: The experiment observed flame behavior in microgravity, with a luminous soot core surrounded by a blue outer shell. Spherical symmetry was preserved, and soot shell formation was evident. Radiative quenching was observed, with the flame's luminosity decreasing as it moved away from the heat source. The flame appeared stable with no signs of re-ignition phenomena. The soot shell formation and radiative quenching were consistent with combustion in microgravity conditions.
- **Verified Citations**: [SOURCE: SAME-R_NASA_Report_20170007283.pdf | LOC: page_48]; [SOURCE: SAME-R_NASA_Report_20170007283.pdf | LOC: page_40]; [SOURCE: SAME-R_NASA_Report_20170007283.pdf | LOC: page_34]; [SOURCE: SAME-R_NASA_Report_20170007283.pdf | LOC: page_29]; [SOURCE: SAME-R_NASA_Report_20170007283.pdf | LOC: page_32]; [SOURCE: SAME-R_NASA_Report_20170007283.pdf | LOC: page_35]

### Rank #29: `PSI-25_BASS-II` (Score: 55.87 / 100)
- **Fuel / Material**: Pmma | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `99.28` | Lunar Base (`<=70.33 kPa, >=30% O2`): `82.98` | Spacesuit (`29.65 kPa, 100% O2`): `45.19`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `78.0`, Completeness `90.0`
- **Confidence Penalty**: `-0.00` (Missing fields: `None`)
- **Key Findings**: PMMA film burned in 22.2% O2 at 101.325 kPa and 298.15 K with a burn rate of 1.2 mm/s for 18.0 s.
- **Verified Citations**: [SOURCE: PSI-25_Experimental_Table_2.xlsx | LOC: sheet_Sheet1]; [SOURCE: PSI-25_Experimental_Table_2.csv | LOC: sheet_csv]

### Rank #30: `PSI-26_BASS` (Score: 55.75 / 100)
- **Fuel / Material**: Pmma | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.98` | Spacesuit (`29.65 kPa, 100% O2`): `44.86`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `78.0`, Completeness `90.0`
- **Confidence Penalty**: `-16.00` (Missing fields: `pressure_kpa, oxygen_pct, burn_rate_mm_s, burn_duration_s`)
- **Key Findings**: Experiment PSI-26_BASS conducted under 0g microgravity conditions with fuel samples including SIBAL 2 cm and PMMA spheres of varying sizes. The experiment involved multiple test runs with varying test and sample numbers.
- **Verified Citations**: [SOURCE: PSI-26_Experimental_Table_2.csv | LOC: sheet_csv]; [SOURCE: PSI-26_Experimental_Table_2.xlsx | LOC: sheet_Sheet1]

### Rank #31: `SAME` (Score: 55.74 / 100)
- **Fuel / Material**: N/A | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.23` | Spacesuit (`29.65 kPa, 100% O2`): `44.40`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `78.0`, Completeness `90.0`
- **Confidence Penalty**: `-12.00` (Missing fields: `fuel_or_material, burn_rate_mm_s, burn_duration_s`)
- **Key Findings**: Smoke and Aerosol Measurement Experiment in 1g Normal Baseline regime with 21.0% O2 at 103.43 kPa and 298.15 K, showing that smoke particles in microgravity coalesce into larger sizes due to the absence of natural convection, altering the sensitivity of optical and ionization smoke detectors.
- **Verified Citations**: [SOURCE: SAME_metadata.csv | LOC: sheet_csv]

### Rank #32: `DAFT_DAFT-2` (Score: 55.24 / 100)
- **Fuel / Material**: N/A | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.97` | Spacesuit (`29.65 kPa, 100% O2`): `44.86`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `78.0`, Completeness `90.0`
- **Confidence Penalty**: `-8.00` (Missing fields: `fuel_or_material, burn_duration_s`)
- **Key Findings**: Experiment DAFT_DAFT-2 involves testing the feasibility of using the SAME/SAME-R smoke sensor to measure characteristics of suspended dust, aiding in the design of fire detection systems that distinguish real smoke from lunar dust. The experiment operates at 21.0% O2, 14.7 psi pressure, and an airflow of 10.0 cm/s. The test simulates microgravity conditions.
- **Verified Citations**: [SOURCE: DAFT_DAFT-2_metadata.csv | LOC: sheet_csv]

### Rank #33: `00_ISS_REFERENCE_GUIDE` (Score: 54.32 / 100)
- **Fuel / Material**: Cotton | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `95.28` | Lunar Base (`<=70.33 kPa, >=30% O2`): `78.65` | Spacesuit (`29.65 kPa, 100% O2`): `43.76`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `78.0`, Completeness `80.0`
- **Confidence Penalty**: `-4.00` (Missing fields: `pressure_kpa`)
- **Key Findings**: Flame photographs show combustion in microgravity with varying flame colors and behaviors. In one case, a 2-cm wide cotton-fiberglass fabric burned in opposed flow with flow changes from 10 cm/s to less than 1 cm/s, resulting in a total burn time of 90 seconds. The flame response to flow changes was rapid, and the burn rate was influenced by the flow velocity. In another case, a 2-cm diameter acrylic sphere burned at 17% oxygen with a flow of 12 cm/s, and the flame remained bluer for longer, delaying soot formation. The images also show flame stability in microgravity, with spherical symmetry and no soot shell formation in some cases, while radiative quenching and re-ignition phenomena were observed in others. The flame color indicated the presence of nitrogen in some instances, and the flame extinguished after 4 seconds in zero gravity.
- **Verified Citations**: [SOURCE: ISS_Combustion_Researcher_Guide.pdf | LOC: page_26]; [SOURCE: ISS_Combustion_Researcher_Guide.pdf | LOC: page_17]; [SOURCE: ISS_Combustion_Researcher_Guide.pdf | LOC: page_17]; [SOURCE: ISS_Combustion_Researcher_Guide.pdf | LOC: page_20]; [SOURCE: ISS_Combustion_Researcher_Guide.pdf | LOC: page_21]; [SOURCE: ISS_Combustion_Researcher_Guide.pdf | LOC: page_15]

### Rank #34: `PSI-142_COOL-FLAMES-MODEL` (Score: 54.25 / 100)
- **Fuel / Material**: N/A | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.98` | Spacesuit (`29.65 kPa, 100% O2`): `44.86`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `88.0`, Safety `85.0`, Completeness `90.0`
- **Confidence Penalty**: `-20.00` (Missing fields: `fuel_or_material, pressure_kpa, oxygen_pct, burn_rate_mm_s, burn_duration_s`)
- **Key Findings**: Experiment PSI-142_COOL-FLAMES-MODEL involves CFE (Cool Flame Extinction) and HFE (Hot Flame Extinction) analysis under microgravity conditions with various data descriptions including CFE limit with ozone, CFE limit without ozone, CFE and HFE Predicted vs Measured, Measured and computed DME/O2/O3 CFE and HFE, and CH2O PLIF and thermometry. The experiment includes references to multiple publications and figures.
- **Verified Citations**: [SOURCE: PSI-142_Experimental_Table_2.csv | LOC: sheet_csv]; [SOURCE: PSI-142_Experimental_Table_2.xlsx | LOC: sheet_Sheet1]

### Rank #35: `LUCI_FM2_UPCOMING` (Score: 52.50 / 100)
- **Fuel / Material**: N/A | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `78.96` | Lunar Base (`<=70.33 kPa, >=30% O2`): `100.00` | Spacesuit (`29.65 kPa, 100% O2`): `54.22`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `78.0`, Completeness `60.0`
- **Confidence Penalty**: `-12.00` (Missing fields: `fuel_or_material, burn_rate_mm_s, burn_duration_s`)
- **Key Findings**: Experiment LUCI_FM2_UPCOMING simulates partial gravity conditions with fuels including spacecraft and Moon base fabrics/polymers at >=30% O2, <=10.2 psi. No combustion data is available for partial gravity conditions [DATA GAP TRÊN PSI]: Hiện chưa có dữ liệu cháy ở trọng lực từng phần.
- **Verified Citations**: [SOURCE: LUCI_FM2_Upcoming_metadata.csv | LOC: sheet_csv]

### Rank #36: `03_SUPPRESSION` (Score: 51.75 / 100)
- **Fuel / Material**: N/A | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.98` | Spacesuit (`29.65 kPa, 100% O2`): `44.86`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `78.0`, Completeness `90.0`
- **Confidence Penalty**: `-20.00` (Missing fields: `fuel_or_material, pressure_kpa, oxygen_pct, burn_rate_mm_s, burn_duration_s`)
- **Key Findings**: Experiment 03_SUPPRESSION involves studies on CFE (Combustion Flame Extinction) and HFE (Heat Flux Extinction) with and without ozone, DME/O2/O3 combustion, and chemiluminescence measurements. The data includes comparisons between predicted and measured values, and thermometry techniques such as CH2O PLIF.
- **Verified Citations**: [SOURCE: PSI-142_Experimental table_Data Summary Table.csv | LOC: sheet_csv]

### Rank #37: `PSI-101_SAME-R` (Score: 51.61 / 100)
- **Fuel / Material**: N/A | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.98` | Spacesuit (`29.65 kPa, 100% O2`): `44.86`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `80.0`, Completeness `90.0`
- **Confidence Penalty**: `-12.00` (Missing fields: `fuel_or_material, pressure_kpa, oxygen_pct`)
- **Key Findings**: Experiment PSI-101_SAME-R conducted under 0g microgravity conditions with Kapton samples. The inlet velocity was 8.1 cm/s, resulting in a burn rate ratio (Rt/R0) of 1.38. The burn duration was 60.0 seconds. Primary aging time was 11.0 seconds, and primary mixing time was 8.0 seconds. Net aging time varied between 38 seconds and 807 seconds. The experiment involved testing a new formula under microgravity conditions with the SAME sensor.
- **Verified Citations**: [SOURCE: PSI-101_Experimental_Table_2.csv | LOC: sheet_csv]; [SOURCE: PSI-101_Experimental_Table_2.xlsx | LOC: sheet_Sheet1]

### Rank #38: `PSI-99_SAFFIRE-II` (Score: 51.34 / 100)
- **Fuel / Material**: N/A | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `82.40` | Spacesuit (`29.65 kPa, 100% O2`): `45.00`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `78.0`, Completeness `90.0`
- **Confidence Penalty**: `-4.00` (Missing fields: `fuel_or_material`)
- **Key Findings**: Silicone material tested under 21.5% O2 at 101.325 kPa with a burn rate of 1.2 mm/s and burn duration of 0.0 s. The experiment involved samples with varying thicknesses and burn lengths, with spread rates classified as acceleratory or measured at 1.2 mm/s.
- **Verified Citations**: [SOURCE: PSI-99_Experimental_Table_2.csv | LOC: sheet_csv]; [SOURCE: PSI-99_Experimental_Table_2.xlsx | LOC: sheet_Sheet1]

### Rank #39: `PSI-102_SAME` (Score: 50.18 / 100)
- **Fuel / Material**: N/A | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.98` | Spacesuit (`29.65 kPa, 100% O2`): `44.86`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `78.0`, Completeness `90.0`
- **Confidence Penalty**: `-12.00` (Missing fields: `fuel_or_material, pressure_kpa, oxygen_pct`)
- **Key Findings**: Experiment PSI-102_SAME involved testing Teflon and Kapton materials under microgravity conditions with air flow rates ranging from 5.0 cm/s to 10.0 cm/s, weight loss rates between 1.0 mg/min and 2.0 mg/min, and aging durations from 1.0 minutes to 20.0 minutes. The experiment included 5 samples with varying conditions.
- **Verified Citations**: [SOURCE: PSI-102_Experimental_Table_2.csv | LOC: sheet_csv]; [SOURCE: PSI-102_Experimental_Table_2.xlsx | LOC: sheet_Sheet1]

### Rank #40: `PAPERS` (Score: 47.06 / 100)
- **Fuel / Material**: N/A | **Gravity Regime**: `0g`
- **Experimental Objectives**: Determine microgravity droplet/solid combustion behavior, extinction mechanisms, and limiting oxygen index (LOI).
- **Hardware / Apparatus**: CIR / MDCA
- **Sample Geometry & Size**: Spherical liquid droplet (2-5 mm initial diameter) | **Airflow Speed**: `0.0 mm/s`
- **Controlled vs. Varied Variables**: Controlled: microgravity environment, ambient temperature; Varied: chamber pressure, O2/N2/CO2 concentration, initial droplet diameter
- **Sensors & Diagnostics Used**: Visible color camera, Backlit droplet camera, LLUV (310 nm OH*) camera, pressure transducers, gas mass-flow controllers
- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `100.00` | Lunar Base (`<=70.33 kPa, >=30% O2`): `81.98` | Spacesuit (`29.65 kPa, 100% O2`): `44.86`
- **Earth Applications**: Fine-water-mist fire suppression design, spacecraft/building smoke detector calibration (SAME/DAFT), and firefighter thermal protection.
- **Component Scores**: Stability `85.0`, Safety `78.0`, Completeness `88.0`
- **Confidence Penalty**: `-12.00` (Missing fields: `fuel_or_material, pressure_kpa, oxygen_pct`)
- **Key Findings**: Flame spread rate of 2.2 mm/s observed for a 100-µm sample in microgravity, with extinction occurring at 1.1 cm/s flow velocity. The flame transitions from luminous soot to a blue core and exhibits radiative quenching. Re-ignition phenomena are observed in some images, indicating combustion stability and potential for re-ignition after extinction. The flame maintains spherical symmetry in microgravity with soot shell formation and radiative quenching effects.
- **Verified Citations**: [SOURCE: PSI-26_BASS_NTRS_20210011385.pdf | LOC: page_31]; [SOURCE: PSI-25_BASS-II_NTRS_20210011385.pdf | LOC: page_31]; [SOURCE: PSI-102_SAME_NTRS_20070031686.pdf | LOC: page_12]; [SOURCE: PSI-25_BASS-II_NTRS_20210011385.pdf | LOC: page_67]; [SOURCE: PSI-25_BASS-II_NTRS_20160000593.pdf | LOC: page_2]; [SOURCE: PSI-25_BASS-II_NTRS_20160000593.pdf | LOC: page_20]
