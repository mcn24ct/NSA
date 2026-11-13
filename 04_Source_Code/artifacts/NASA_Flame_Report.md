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
| **1** | `EXP_FLEX_01` | N/A | N/A | N/A | 10.000 | 20.00 | -12.00 | **23.77** |

## 3. Detailed Experiment Breakdown & Citations

### Rank #1: `EXP_FLEX_01` (Score: 23.77 / 100)
- **Fuel / Material**: N/A
- **Component Scores**: Stability `9.5`, Safety `8.2`, Completeness `9.0`
- **Confidence Penalty**: `-12.00` (Missing fields: `fuel_or_material, pressure_kpa, oxygen_pct`)
- **Key Findings**: The experiment involved the combustion of a free-floating heptane droplet in a microgravity environment with an ambient atmosphere of 0.20/0.75/0.05 O2/N2/CO2 at 1.0 atm. The droplet burned cleanly to a small size before disrupting coincident with flame extinction. The flame exhibited spherical symmetry, indicating uniform mixing and combustion. The radiative quenching effect was observed at the edges of the flame, and a large vapor cloud formed 15 to 20 seconds after the visible flame extinguished, suggesting cool flame burning and extinction occurred after the visible flame extinguished. The droplet diameter and flame diameter histories were recorded using multiple cameras, with the LLUV camera providing data on the time of extinction. The experiment also documented both radiative and diffusive extinctions for heptane, with observed LOI values slightly lower than expected.
- **Verified Citations**: SOURCE: JASMAC-33 FLEX w video.pdf | LOC: page_14; SOURCE: 20150023456.pdf | LOC: page_230; SOURCE: 20150023456.pdf | LOC: page_8; SOURCE: 20150023456.pdf | LOC: page_182; SOURCE: 20150023456.pdf | LOC: page_76; SOURCE: 20150023456.pdf | LOC: page_22
