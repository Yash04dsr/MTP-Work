# All metrics — `case_10`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01555 | 0.00600 | 0.3862 | 0.0024 |
| mass | 0.01564 | 0.00594 | 0.3795 | 0.0023 |
| vol  | 0.01586 | 0.00596 | 0.3761 | 0.0023 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01555 | 0.00600 | 0.3862 | 0.0024 |
| mass | 0.01564 | 0.00594 | 0.3795 | 0.0023 |
| vol  | 0.01586 | 0.00596 | 0.3761 | 0.0023 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.00795** (n = 124 samples in [0.803, 1.198] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **2.673 kPa**  (⟨p_rgh⟩_inlet = 6902.7 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 124 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 13.993 | 13.994 | 13.994 |
| gauge `p_rgh` | 13.993 | 13.994 | 13.994 |
| total `p + ½ρU²` | 13.340 | 13.378 | 13.373 |
| gauge-total `p_rgh + ½ρU²` | 13.339 | 13.378 | 13.373 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.5520**  (σ = 5.2594, n = 124 samples, t ∈ [0.803, 1.198] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.7164** kg/s
- ṁ branch_inlet: **-0.5366** kg/s
- ṁ outlet      : **+37.5353** kg/s
- closure error : **+3.2823e+00 kg/s**  (+8.74 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.3862 | 0.3795 | 0.3761 | 13.994 | 13.378 | +8.74 |
| **AVG** | **0.3862** | **0.3795** | **0.3761** | **13.994** | **13.378** | **+8.74** |
