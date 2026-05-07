# All metrics — `case_07`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.03791 | 0.04127 | 1.0887 | 0.0467 |
| mass | 0.03174 | 0.03750 | 1.1813 | 0.0457 |
| vol  | 0.03976 | 0.04183 | 1.0521 | 0.0458 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.03791 | 0.04127 | 1.0887 | 0.0467 |
| mass | 0.03174 | 0.03750 | 1.1813 | 0.0457 |
| vol  | 0.03976 | 0.04183 | 1.0521 | 0.0458 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.02488** (n = 58 samples in [0.805, 1.196] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **3.657 kPa**  (⟨p_rgh⟩_inlet = 6903.7 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 58 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 38.990 | 38.991 | 38.991 |
| gauge `p_rgh` | 38.983 | 38.978 | 38.985 |
| total `p + ½ρU²` | 38.212 | 38.201 | 38.256 |
| gauge-total `p_rgh + ½ρU²` | 38.204 | 38.188 | 38.251 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+34.0522**  (σ = 9.6517, n = 58 samples, t ∈ [0.805, 1.196] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.8383** kg/s
- ṁ branch_inlet: **-0.7046** kg/s
- ṁ outlet      : **+36.8256** kg/s
- closure error : **+2.2827e+00 kg/s**  (+6.20 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 1.0887 | 1.1813 | 1.0521 | 38.991 | 38.201 | +6.20 |
| **AVG** | **1.0887** | **1.1813** | **1.0521** | **38.991** | **38.201** | **+6.20** |
