# All metrics — `case_10`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01631 | 0.00664 | 0.4073 | 0.0027 |
| mass | 0.01625 | 0.00660 | 0.4062 | 0.0027 |
| vol  | 0.01652 | 0.00658 | 0.3983 | 0.0027 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01631 | 0.00664 | 0.4073 | 0.0027 |
| mass | 0.01625 | 0.00660 | 0.4062 | 0.0027 |
| vol  | 0.01652 | 0.00658 | 0.3983 | 0.0027 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01552** (n = 110 samples in [0.804, 1.197] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **5.754 kPa**  (⟨p_rgh⟩_inlet = 6905.8 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 110 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -4.204 | -4.203 | -4.203 |
| gauge `p_rgh` | -4.204 | -4.201 | -4.201 |
| total `p + ½ρU²` | -5.901 | -5.874 | -5.877 |
| gauge-total `p_rgh + ½ρU²` | -5.901 | -5.872 | -5.876 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+34.7602**  (σ = 8.3299, n = 110 samples, t ∈ [0.804, 1.197] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.6241** kg/s
- ṁ branch_inlet: **-0.5342** kg/s
- ṁ outlet      : **+44.6688** kg/s
- closure error : **+1.0511e+01 kg/s**  (+23.53 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.4073 | 0.4062 | 0.3983 | -4.203 | -5.874 | +23.53 |
| **AVG** | **0.4073** | **0.4062** | **0.3983** | **-4.203** | **-5.874** | **+23.53** |
