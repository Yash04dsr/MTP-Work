# All metrics — `case_09`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01879 | 0.00791 | 0.4207 | 0.0034 |
| mass | 0.01881 | 0.00786 | 0.4181 | 0.0034 |
| vol  | 0.01919 | 0.00786 | 0.4097 | 0.0033 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01879 | 0.00791 | 0.4207 | 0.0034 |
| mass | 0.01881 | 0.00786 | 0.4181 | 0.0034 |
| vol  | 0.01919 | 0.00786 | 0.4097 | 0.0033 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01277** (n = 146 samples in [0.803, 1.198] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **4.162 kPa**  (⟨p_rgh⟩_inlet = 6904.2 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 146 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 6.584 | 6.585 | 6.585 |
| gauge `p_rgh` | 6.583 | 6.583 | 6.584 |
| total `p + ½ρU²` | 5.326 | 5.363 | 5.356 |
| gauge-total `p_rgh + ½ρU²` | 5.324 | 5.361 | 5.355 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.4977**  (σ = 6.3622, n = 146 samples, t ∈ [0.803, 1.198] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.6803** kg/s
- ṁ branch_inlet: **-0.6341** kg/s
- ṁ outlet      : **+41.4848** kg/s
- closure error : **+7.1704e+00 kg/s**  (+17.28 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.4207 | 0.4181 | 0.4097 | 6.585 | 5.363 | +17.28 |
| **AVG** | **0.4207** | **0.4181** | **0.4097** | **6.585** | **5.363** | **+17.28** |
