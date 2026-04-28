# All metrics — `case_08`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01120 | 0.00490 | 0.4371 | 0.0022 |
| mass | 0.01125 | 0.00487 | 0.4331 | 0.0021 |
| vol  | 0.01141 | 0.00499 | 0.4373 | 0.0022 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01120 | 0.00490 | 0.4371 | 0.0022 |
| mass | 0.01125 | 0.00487 | 0.4331 | 0.0021 |
| vol  | 0.01141 | 0.00499 | 0.4373 | 0.0022 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.00414** (n = 141 samples in [0.803, 1.199] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **3.399 kPa**  (⟨p_rgh⟩_inlet = 6903.4 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 141 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 10.240 | 10.240 | 10.240 |
| gauge `p_rgh` | 10.240 | 10.240 | 10.240 |
| total `p + ½ρU²` | 9.440 | 9.472 | 9.468 |
| gauge-total `p_rgh + ½ρU²` | 9.440 | 9.472 | 9.468 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.9746**  (σ = 5.7300, n = 141 samples, t ∈ [0.803, 1.199] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.6981** kg/s
- ṁ branch_inlet: **-0.4280** kg/s
- ṁ outlet      : **+39.1486** kg/s
- closure error : **+5.0226e+00 kg/s**  (+12.83 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.4371 | 0.4331 | 0.4373 | 10.240 | 9.472 | +12.83 |
| **AVG** | **0.4371** | **0.4331** | **0.4373** | **10.240** | **9.472** | **+12.83** |
