# All metrics — `case_03`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01184 | 0.00117 | 0.0990 | 0.0001 |
| mass | 0.01188 | 0.00115 | 0.0967 | 0.0001 |
| vol  | 0.01189 | 0.00115 | 0.0964 | 0.0001 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01184 | 0.00117 | 0.0990 | 0.0001 |
| mass | 0.01188 | 0.00115 | 0.0967 | 0.0001 |
| vol  | 0.01189 | 0.00115 | 0.0964 | 0.0001 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01101** (n = 471 samples in [0.801, 1.200] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **3.224 kPa**  (⟨p_rgh⟩_inlet = 6903.2 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 471 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -20.984 | -20.983 | -20.983 |
| gauge `p_rgh` | -20.984 | -20.983 | -20.982 |
| total `p + ½ρU²` | -21.185 | -21.147 | -21.148 |
| gauge-total `p_rgh + ½ρU²` | -21.185 | -21.146 | -21.147 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.1213**  (σ = 7.5905, n = 471 samples, t ∈ [0.801, 1.200] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.5458** kg/s
- ṁ branch_inlet: **-0.3730** kg/s
- ṁ outlet      : **+34.2317** kg/s
- closure error : **+3.1289e-01 kg/s**  (+0.91 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.0990 | 0.0967 | 0.0964 | -20.983 | -21.147 | +0.91 |
| **AVG** | **0.0990** | **0.0967** | **0.0964** | **-20.983** | **-21.147** | **+0.91** |
