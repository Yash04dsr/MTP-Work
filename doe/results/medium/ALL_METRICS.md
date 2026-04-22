# All metrics — `openfoam_case_rans_medium`

Snapshots used: **1, 1.1, 1.2** (n = 3)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02650 | 0.00525 | 0.1981 | 0.0011 |
| mass | 0.02665 | 0.00498 | 0.1869 | 0.0010 |
| vol  | 0.02681 | 0.00487 | 0.1818 | 0.0009 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02650 | 0.00665 | 0.2815 | 0.0020 |
| mass | 0.02647 | 0.00645 | 0.2712 | 0.0018 |
| vol  | 0.02672 | 0.00630 | 0.2607 | 0.0017 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.02654** (n = 43 samples in [0.808, 1.191] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **4.344 kPa**  (⟨p_rgh⟩_inlet = 6904.3 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 43 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -9.865 | -9.865 | -9.865 |
| gauge `p_rgh` | -9.865 | -9.870 | -9.870 |
| total `p + ½ρU²` | -10.790 | -10.766 | -10.762 |
| gauge-total `p_rgh + ½ρU²` | -10.790 | -10.771 | -10.768 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+71.0122**  (σ = 43.4197, n = 43 samples, t ∈ [0.808, 1.191] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-67.1997** kg/s
- ṁ branch_inlet: **-1.9060** kg/s
- ṁ outlet      : **+46.1586** kg/s
- closure error : **-2.2947e+01 kg/s**  (-730.16 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.0 | 0.3531 | 0.3381 | 0.3215 | -41.838 | -40.051 | -1205.06 |
| 1.1 | 0.1481 | 0.1492 | 0.1487 | 41.306 | 35.031 | +45.24 |
| 1.2 | 0.3433 | 0.3263 | 0.3119 | -29.062 | -27.277 | -1030.65 |
| **AVG** | **0.2815** | **0.2712** | **0.2607** | **-9.865** | **-10.766** | **-730.16** |
