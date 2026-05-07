# All metrics — `case_08`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01307 | 0.00923 | 0.7066 | 0.0066 |
| mass | 0.01274 | 0.00906 | 0.7107 | 0.0065 |
| vol  | 0.01327 | 0.00915 | 0.6899 | 0.0064 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01307 | 0.00923 | 0.7066 | 0.0066 |
| mass | 0.01274 | 0.00906 | 0.7107 | 0.0065 |
| vol  | 0.01327 | 0.00915 | 0.6899 | 0.0064 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01120** (n = 132 samples in [0.803, 1.199] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **5.338 kPa**  (⟨p_rgh⟩_inlet = 6905.3 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 132 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -7.837 | -7.837 | -7.837 |
| gauge `p_rgh` | -7.835 | -7.833 | -7.834 |
| total `p + ½ρU²` | -9.428 | -9.405 | -9.403 |
| gauge-total `p_rgh + ½ρU²` | -9.426 | -9.401 | -9.401 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.1087**  (σ = 7.9506, n = 132 samples, t ∈ [0.803, 1.199] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.6064** kg/s
- ṁ branch_inlet: **-0.4261** kg/s
- ṁ outlet      : **+44.4684** kg/s
- closure error : **+1.0436e+01 kg/s**  (+23.47 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.7066 | 0.7107 | 0.6899 | -7.837 | -9.405 | +23.47 |
| **AVG** | **0.7066** | **0.7107** | **0.6899** | **-7.837** | **-9.405** | **+23.47** |
