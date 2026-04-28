# All metrics — `case_09`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01838 | 0.00565 | 0.3074 | 0.0018 |
| mass | 0.01827 | 0.00559 | 0.3059 | 0.0017 |
| vol  | 0.01847 | 0.00553 | 0.2994 | 0.0017 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01838 | 0.00565 | 0.3074 | 0.0018 |
| mass | 0.01827 | 0.00559 | 0.3059 | 0.0017 |
| vol  | 0.01847 | 0.00553 | 0.2994 | 0.0017 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01609** (n = 165 samples in [0.801, 1.200] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **3.609 kPa**  (⟨p_rgh⟩_inlet = 6903.6 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 165 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -6.690 | -6.689 | -6.689 |
| gauge `p_rgh` | -6.690 | -6.688 | -6.688 |
| total `p + ½ρU²` | -7.999 | -7.966 | -7.966 |
| gauge-total `p_rgh + ½ρU²` | -8.000 | -7.965 | -7.965 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.3223**  (σ = 6.1835, n = 165 samples, t ∈ [0.801, 1.200] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.6155** kg/s
- ṁ branch_inlet: **-0.6355** kg/s
- ṁ outlet      : **+41.8163** kg/s
- closure error : **+7.5652e+00 kg/s**  (+18.09 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.3074 | 0.3059 | 0.2994 | -6.689 | -7.966 | +18.09 |
| **AVG** | **0.3074** | **0.3059** | **0.2994** | **-6.689** | **-7.966** | **+18.09** |
