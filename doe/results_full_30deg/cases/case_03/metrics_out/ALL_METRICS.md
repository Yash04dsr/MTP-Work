# All metrics — `case_03`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01094 | 0.00304 | 0.2778 | 0.0009 |
| mass | 0.01080 | 0.00300 | 0.2777 | 0.0008 |
| vol  | 0.01086 | 0.00301 | 0.2769 | 0.0008 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01094 | 0.00304 | 0.2778 | 0.0009 |
| mass | 0.01080 | 0.00300 | 0.2777 | 0.0008 |
| vol  | 0.01086 | 0.00301 | 0.2769 | 0.0008 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01172** (n = 389 samples in [0.801, 1.200] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **1.893 kPa**  (⟨p_rgh⟩_inlet = 6901.9 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 389 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -26.706 | -26.705 | -26.705 |
| gauge `p_rgh` | -26.705 | -26.702 | -26.703 |
| total `p + ½ρU²` | -26.982 | -26.949 | -26.947 |
| gauge-total `p_rgh + ½ρU²` | -26.981 | -26.946 | -26.944 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.2289**  (σ = 8.1106, n = 389 samples, t ∈ [0.801, 1.200] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.5179** kg/s
- ṁ branch_inlet: **-0.3720** kg/s
- ṁ outlet      : **+34.8866** kg/s
- closure error : **+9.9668e-01 kg/s**  (+2.86 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.2778 | 0.2777 | 0.2769 | -26.705 | -26.949 | +2.86 |
| **AVG** | **0.2778** | **0.2777** | **0.2769** | **-26.705** | **-26.949** | **+2.86** |
