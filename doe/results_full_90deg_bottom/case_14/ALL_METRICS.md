# All metrics — `case_14`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.07657 | 0.01826 | 0.2385 | 0.0047 |
| mass | 0.07540 | 0.01785 | 0.2367 | 0.0046 |
| vol  | 0.07685 | 0.01805 | 0.2348 | 0.0046 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.07657 | 0.01826 | 0.2385 | 0.0047 |
| mass | 0.07540 | 0.01785 | 0.2367 | 0.0046 |
| vol  | 0.07685 | 0.01805 | 0.2348 | 0.0046 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.12208** (n = 180 samples in [0.801, 1.199] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **6.484 kPa**  (⟨p_rgh⟩_inlet = 6906.5 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 180 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -10.016 | -10.016 | -10.016 |
| gauge `p_rgh` | -10.017 | -10.018 | -10.017 |
| total `p + ½ρU²` | -20.459 | -20.472 | -20.428 |
| gauge-total `p_rgh + ½ρU²` | -20.460 | -20.474 | -20.429 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+39.6037**  (σ = 21.4002, n = 180 samples, t ∈ [0.801, 1.199] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.5976** kg/s
- ṁ branch_inlet: **-3.8516** kg/s
- ṁ outlet      : **+71.4771** kg/s
- closure error : **+3.4028e+01 kg/s**  (+47.61 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.2385 | 0.2367 | 0.2348 | -10.016 | -20.472 | +47.61 |
| **AVG** | **0.2385** | **0.2367** | **0.2348** | **-10.016** | **-20.472** | **+47.61** |
