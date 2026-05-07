# All metrics — `case_09`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01727 | 0.00673 | 0.3896 | 0.0027 |
| mass | 0.01728 | 0.00671 | 0.3884 | 0.0027 |
| vol  | 0.01756 | 0.00668 | 0.3804 | 0.0026 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01727 | 0.00673 | 0.3896 | 0.0027 |
| mass | 0.01728 | 0.00671 | 0.3884 | 0.0027 |
| vol  | 0.01756 | 0.00668 | 0.3804 | 0.0026 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01883** (n = 131 samples in [0.802, 1.198] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **5.811 kPa**  (⟨p_rgh⟩_inlet = 6905.8 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 131 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -17.818 | -17.817 | -17.817 |
| gauge `p_rgh` | -17.820 | -17.818 | -17.817 |
| total `p + ½ρU²` | -19.540 | -19.512 | -19.518 |
| gauge-total `p_rgh + ½ρU²` | -19.542 | -19.513 | -19.517 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.3212**  (σ = 8.9662, n = 131 samples, t ∈ [0.802, 1.198] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.5577** kg/s
- ṁ branch_inlet: **-0.6304** kg/s
- ṁ outlet      : **+44.6559** kg/s
- closure error : **+1.0468e+01 kg/s**  (+23.44 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.3896 | 0.3884 | 0.3804 | -17.817 | -19.512 | +23.44 |
| **AVG** | **0.3896** | **0.3884** | **0.3804** | **-17.817** | **-19.512** | **+23.44** |
