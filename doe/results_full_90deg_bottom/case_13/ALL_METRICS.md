# All metrics — `case_13`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.06585 | 0.02085 | 0.3167 | 0.0071 |
| mass | 0.06112 | 0.02000 | 0.3273 | 0.0070 |
| vol  | 0.06307 | 0.01924 | 0.3050 | 0.0063 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.06585 | 0.02085 | 0.3167 | 0.0071 |
| mass | 0.06112 | 0.02000 | 0.3273 | 0.0070 |
| vol  | 0.06307 | 0.01924 | 0.3050 | 0.0063 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.07708** (n = 124 samples in [0.803, 1.197] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **2.365 kPa**  (⟨p_rgh⟩_inlet = 6902.4 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 124 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 20.683 | 20.683 | 20.683 |
| gauge `p_rgh` | 20.682 | 20.673 | 20.674 |
| total `p + ½ρU²` | 21.955 | 21.887 | 21.910 |
| gauge-total `p_rgh + ½ρU²` | 21.955 | 21.877 | 21.901 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+39.8208**  (σ = 15.7634, n = 124 samples, t ∈ [0.803, 1.197] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.7473** kg/s
- ṁ branch_inlet: **-2.5748** kg/s
- ṁ outlet      : **+14.4422** kg/s
- closure error : **-2.1880e+01 kg/s**  (-151.50 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.3167 | 0.3273 | 0.3050 | 20.683 | 21.887 | -151.50 |
| **AVG** | **0.3167** | **0.3273** | **0.3050** | **20.683** | **21.887** | **-151.50** |
