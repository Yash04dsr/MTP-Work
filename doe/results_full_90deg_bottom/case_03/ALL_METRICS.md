# All metrics — `case_03`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01314 | 0.01450 | 1.1035 | 0.0162 |
| mass | 0.01195 | 0.01372 | 1.1482 | 0.0159 |
| vol  | 0.01316 | 0.01434 | 1.0901 | 0.0158 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01314 | 0.01450 | 1.1035 | 0.0162 |
| mass | 0.01195 | 0.01372 | 1.1482 | 0.0159 |
| vol  | 0.01316 | 0.01434 | 1.0901 | 0.0158 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01036** (n = 50 samples in [0.803, 1.194] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **3.908 kPa**  (⟨p_rgh⟩_inlet = 6903.9 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 50 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 27.665 | 27.665 | 27.665 |
| gauge `p_rgh` | 27.662 | 27.659 | 27.662 |
| total `p + ½ρU²` | 26.544 | 26.553 | 26.572 |
| gauge-total `p_rgh + ½ρU²` | 26.541 | 26.547 | 26.569 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+34.1064**  (σ = 8.5350, n = 50 samples, t ∈ [0.803, 1.194] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.7814** kg/s
- ṁ branch_inlet: **-0.3580** kg/s
- ṁ outlet      : **+41.4297** kg/s
- closure error : **+7.2904e+00 kg/s**  (+17.60 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 1.1035 | 1.1482 | 1.0901 | 27.665 | 26.553 | +17.60 |
| **AVG** | **1.1035** | **1.1482** | **1.0901** | **27.665** | **26.553** | **+17.60** |
