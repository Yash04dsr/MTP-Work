# All metrics — `case_10`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01562 | 0.00539 | 0.3451 | 0.0019 |
| mass | 0.01561 | 0.00535 | 0.3426 | 0.0019 |
| vol  | 0.01579 | 0.00530 | 0.3357 | 0.0018 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01562 | 0.00539 | 0.3451 | 0.0019 |
| mass | 0.01561 | 0.00535 | 0.3426 | 0.0019 |
| vol  | 0.01579 | 0.00530 | 0.3357 | 0.0018 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01073** (n = 136 samples in [0.802, 1.198] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **2.748 kPa**  (⟨p_rgh⟩_inlet = 6902.7 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 136 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 2.868 | 2.868 | 2.868 |
| gauge `p_rgh` | 2.867 | 2.868 | 2.869 |
| total `p + ½ρU²` | 2.040 | 2.079 | 2.077 |
| gauge-total `p_rgh + ½ρU²` | 2.039 | 2.078 | 2.077 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.2614**  (σ = 4.8110, n = 136 samples, t ∈ [0.802, 1.198] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.6621** kg/s
- ṁ branch_inlet: **-0.5373** kg/s
- ṁ outlet      : **+38.7739** kg/s
- closure error : **+4.5745e+00 kg/s**  (+11.80 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.3451 | 0.3426 | 0.3357 | 2.868 | 2.079 | +11.80 |
| **AVG** | **0.3451** | **0.3426** | **0.3357** | **2.868** | **2.079** | **+11.80** |
