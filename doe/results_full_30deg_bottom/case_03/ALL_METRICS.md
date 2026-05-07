# All metrics — `case_03`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01449 | 0.01946 | 1.3431 | 0.0265 |
| mass | 0.01292 | 0.01800 | 1.3931 | 0.0254 |
| vol  | 0.01499 | 0.01963 | 1.3095 | 0.0261 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01449 | 0.01946 | 1.3431 | 0.0265 |
| mass | 0.01292 | 0.01800 | 1.3931 | 0.0254 |
| vol  | 0.01499 | 0.01963 | 1.3095 | 0.0261 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01330** (n = 64 samples in [0.801, 1.199] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **6.549 kPa**  (⟨p_rgh⟩_inlet = 6906.6 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 64 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 14.070 | 14.071 | 14.071 |
| gauge `p_rgh` | 14.067 | 14.065 | 14.068 |
| total `p + ½ρU²` | 12.608 | 12.619 | 12.638 |
| gauge-total `p_rgh + ½ρU²` | 12.604 | 12.613 | 12.635 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+34.4694**  (σ = 8.5846, n = 64 samples, t ∈ [0.801, 1.199] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.7168** kg/s
- ṁ branch_inlet: **-0.3593** kg/s
- ṁ outlet      : **+43.6635** kg/s
- closure error : **+9.5875e+00 kg/s**  (+21.96 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 1.3431 | 1.3931 | 1.3095 | 14.071 | 12.619 | +21.96 |
| **AVG** | **1.3431** | **1.3931** | **1.3095** | **14.071** | **12.619** | **+21.96** |
