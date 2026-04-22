# All metrics — `openfoam_case_rans_fast`

Snapshots used: **1.3, 1.4, 1.5** (n = 3)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.03219 | 0.00454 | 0.1409 | 0.0007 |
| mass | 0.03219 | 0.00446 | 0.1384 | 0.0006 |
| vol  | 0.03230 | 0.00442 | 0.1367 | 0.0006 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.03219 | 0.00554 | 0.1845 | 0.0010 |
| mass | 0.03224 | 0.00538 | 0.1770 | 0.0010 |
| vol  | 0.03240 | 0.00538 | 0.1759 | 0.0010 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.02658** (n = 46 samples in [0.812, 1.493] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **10.358 kPa**  (⟨p_rgh⟩_inlet = 6910.4 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 46 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 10.025 | 10.026 | 10.026 |
| gauge `p_rgh` | 10.025 | 10.024 | 10.024 |
| total `p + ½ρU²` | 7.212 | 7.232 | 7.234 |
| gauge-total `p_rgh + ½ρU²` | 7.212 | 7.230 | 7.232 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+67.8520**  (σ = 38.0123, n = 46 samples, t ∈ [0.812, 1.493] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-67.3945** kg/s
- ṁ branch_inlet: **-1.9082** kg/s
- ṁ outlet      : **+83.5441** kg/s
- closure error : **+1.4241e+01 kg/s**  (-82.31 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.3 | 0.1402 | 0.1382 | 0.1376 | 29.720 | 24.503 | +41.41 |
| 1.4 | 0.2543 | 0.2358 | 0.2337 | -20.250 | -18.556 | -328.46 |
| 1.5 | 0.1588 | 0.1569 | 0.1564 | 20.607 | 15.748 | +40.12 |
| **AVG** | **0.1845** | **0.1770** | **0.1759** | **10.026** | **7.232** | **-82.31** |
