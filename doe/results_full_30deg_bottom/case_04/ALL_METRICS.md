# All metrics — `case_04`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.04126 | 0.01438 | 0.3484 | 0.0052 |
| mass | 0.04028 | 0.01410 | 0.3501 | 0.0051 |
| vol  | 0.04136 | 0.01400 | 0.3386 | 0.0049 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.04126 | 0.01438 | 0.3484 | 0.0052 |
| mass | 0.04028 | 0.01410 | 0.3501 | 0.0051 |
| vol  | 0.04136 | 0.01400 | 0.3386 | 0.0049 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.03389** (n = 151 samples in [0.802, 1.198] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **-0.818 kPa**  (⟨p_rgh⟩_inlet = 6899.2 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 151 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -21.702 | -21.702 | -21.702 |
| gauge `p_rgh` | -21.701 | -21.701 | -21.702 |
| total `p + ½ρU²` | -20.656 | -20.618 | -20.615 |
| gauge-total `p_rgh + ½ρU²` | -20.655 | -20.618 | -20.615 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+36.1561**  (σ = 13.0888, n = 151 samples, t ∈ [0.802, 1.198] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.5423** kg/s
- ṁ branch_inlet: **-1.0246** kg/s
- ṁ outlet      : **+19.2600** kg/s
- closure error : **-1.5307e+01 kg/s**  (-79.48 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.3484 | 0.3501 | 0.3386 | -21.702 | -20.618 | -79.48 |
| **AVG** | **0.3484** | **0.3501** | **0.3386** | **-21.702** | **-20.618** | **-79.48** |
