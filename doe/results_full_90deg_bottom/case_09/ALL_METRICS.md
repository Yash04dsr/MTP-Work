# All metrics — `case_09`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02268 | 0.01876 | 0.8272 | 0.0159 |
| mass | 0.01863 | 0.01788 | 0.9596 | 0.0175 |
| vol  | 0.02060 | 0.01826 | 0.8864 | 0.0165 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02268 | 0.01876 | 0.8272 | 0.0159 |
| mass | 0.01863 | 0.01788 | 0.9596 | 0.0175 |
| vol  | 0.02060 | 0.01826 | 0.8864 | 0.0165 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01094** (n = 61 samples in [0.803, 1.199] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **0.733 kPa**  (⟨p_rgh⟩_inlet = 6900.7 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 61 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 33.609 | 33.610 | 33.610 |
| gauge `p_rgh` | 33.604 | 33.595 | 33.600 |
| total `p + ½ρU²` | 33.635 | 33.531 | 33.588 |
| gauge-total `p_rgh + ½ρU²` | 33.630 | 33.517 | 33.579 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+36.3518**  (σ = 8.9862, n = 61 samples, t ∈ [0.803, 1.199] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.8103** kg/s
- ṁ branch_inlet: **-0.6332** kg/s
- ṁ outlet      : **+31.2002** kg/s
- closure error : **-3.2434e+00 kg/s**  (-10.40 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.8272 | 0.9596 | 0.8864 | 33.610 | 33.531 | -10.40 |
| **AVG** | **0.8272** | **0.9596** | **0.8864** | **33.610** | **33.531** | **-10.40** |
