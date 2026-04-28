# All metrics — `case_02`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.00820 | 0.00320 | 0.3899 | 0.0013 |
| mass | 0.00818 | 0.00314 | 0.3842 | 0.0012 |
| vol  | 0.00824 | 0.00312 | 0.3792 | 0.0012 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.00820 | 0.00320 | 0.3899 | 0.0013 |
| mass | 0.00818 | 0.00314 | 0.3842 | 0.0012 |
| vol  | 0.00824 | 0.00312 | 0.3792 | 0.0012 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.00840** (n = 286 samples in [0.801, 1.199] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **2.126 kPa**  (⟨p_rgh⟩_inlet = 6902.1 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 286 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -29.016 | -29.016 | -29.016 |
| gauge `p_rgh` | -29.016 | -29.014 | -29.014 |
| total `p + ½ρU²` | -29.558 | -29.528 | -29.528 |
| gauge-total `p_rgh + ½ρU²` | -29.558 | -29.526 | -29.526 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.2660**  (σ = 7.9117, n = 286 samples, t ∈ [0.801, 1.199] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.5066** kg/s
- ṁ branch_inlet: **-0.2751** kg/s
- ṁ outlet      : **+37.3996** kg/s
- closure error : **+3.6178e+00 kg/s**  (+9.67 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.3899 | 0.3842 | 0.3792 | -29.016 | -29.528 | +9.67 |
| **AVG** | **0.3899** | **0.3842** | **0.3792** | **-29.016** | **-29.528** | **+9.67** |
