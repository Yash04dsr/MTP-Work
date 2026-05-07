# All metrics — `case_11`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.04353 | 0.00944 | 0.2169 | 0.0021 |
| mass | 0.04221 | 0.00932 | 0.2208 | 0.0021 |
| vol  | 0.04268 | 0.00926 | 0.2171 | 0.0021 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.04353 | 0.00944 | 0.2169 | 0.0021 |
| mass | 0.04221 | 0.00932 | 0.2208 | 0.0021 |
| vol  | 0.04268 | 0.00926 | 0.2171 | 0.0021 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.05924** (n = 159 samples in [0.800, 1.199] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **-2.478 kPa**  (⟨p_rgh⟩_inlet = 6897.5 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 159 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 69.954 | 69.954 | 69.954 |
| gauge `p_rgh` | 69.954 | 69.952 | 69.951 |
| total `p + ½ρU²` | 70.617 | 70.605 | 70.617 |
| gauge-total `p_rgh + ½ρU²` | 70.618 | 70.603 | 70.615 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.9896**  (σ = 15.2936, n = 159 samples, t ∈ [0.800, 1.199] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.9876** kg/s
- ṁ branch_inlet: **-2.0919** kg/s
- ṁ outlet      : **+23.5638** kg/s
- closure error : **-1.2516e+01 kg/s**  (-53.11 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.2169 | 0.2208 | 0.2171 | 69.954 | 70.605 | -53.11 |
| **AVG** | **0.2169** | **0.2208** | **0.2171** | **69.954** | **70.605** | **-53.11** |
