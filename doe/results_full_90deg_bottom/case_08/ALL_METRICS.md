# All metrics — `case_08`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.00872 | 0.00794 | 0.9109 | 0.0073 |
| mass | 0.00786 | 0.00762 | 0.9704 | 0.0075 |
| vol  | 0.00824 | 0.00772 | 0.9370 | 0.0073 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.00872 | 0.00794 | 0.9109 | 0.0073 |
| mass | 0.00786 | 0.00762 | 0.9704 | 0.0075 |
| vol  | 0.00824 | 0.00772 | 0.9370 | 0.0073 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.00225** (n = 54 samples in [0.804, 1.194] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **-1.309 kPa**  (⟨p_rgh⟩_inlet = 6898.7 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 54 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 11.415 | 11.415 | 11.415 |
| gauge `p_rgh` | 11.412 | 11.408 | 11.410 |
| total `p + ½ρU²` | 12.055 | 12.052 | 12.061 |
| gauge-total `p_rgh + ½ρU²` | 12.053 | 12.045 | 12.056 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+36.9933**  (σ = 7.8704, n = 54 samples, t ∈ [0.804, 1.194] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.7021** kg/s
- ṁ branch_inlet: **-0.4270** kg/s
- ṁ outlet      : **+26.2565** kg/s
- closure error : **-7.8726e+00 kg/s**  (-29.98 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.9109 | 0.9704 | 0.9370 | 11.415 | 12.052 | -29.98 |
| **AVG** | **0.9109** | **0.9704** | **0.9370** | **11.415** | **12.052** | **-29.98** |
