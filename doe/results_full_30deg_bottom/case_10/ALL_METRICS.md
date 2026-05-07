# All metrics — `case_10`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02401 | 0.02192 | 0.9128 | 0.0205 |
| mass | 0.01907 | 0.02032 | 1.0653 | 0.0221 |
| vol  | 0.02161 | 0.02112 | 0.9773 | 0.0211 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02401 | 0.02192 | 0.9128 | 0.0205 |
| mass | 0.01907 | 0.02032 | 1.0653 | 0.0221 |
| vol  | 0.02161 | 0.02112 | 0.9773 | 0.0211 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.00783** (n = 58 samples in [0.804, 1.199] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **0.092 kPa**  (⟨p_rgh⟩_inlet = 6900.1 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 58 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 25.310 | 25.311 | 25.311 |
| gauge `p_rgh` | 25.305 | 25.296 | 25.301 |
| total `p + ½ρU²` | 25.608 | 25.529 | 25.583 |
| gauge-total `p_rgh + ½ρU²` | 25.603 | 25.515 | 25.573 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+36.4928**  (σ = 8.0894, n = 58 samples, t ∈ [0.804, 1.199] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.7716** kg/s
- ṁ branch_inlet: **-0.5360** kg/s
- ṁ outlet      : **+28.6854** kg/s
- closure error : **-5.6222e+00 kg/s**  (-19.60 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.9128 | 1.0653 | 0.9773 | 25.311 | 25.529 | -19.60 |
| **AVG** | **0.9128** | **1.0653** | **0.9773** | **25.311** | **25.529** | **-19.60** |
