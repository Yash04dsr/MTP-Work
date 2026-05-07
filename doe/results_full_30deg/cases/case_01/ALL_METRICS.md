# All metrics — `case_01`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.04746 | 0.00025 | 0.0052 | 0.0000 |
| mass | 0.04746 | 0.00025 | 0.0052 | 0.0000 |
| vol  | 0.04746 | 0.00025 | 0.0052 | 0.0000 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.04746 | 0.00025 | 0.0052 | 0.0000 |
| mass | 0.04746 | 0.00025 | 0.0052 | 0.0000 |
| vol  | 0.04746 | 0.00025 | 0.0052 | 0.0000 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.04660** (n = 2780 samples in [0.800, 1.200] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **3.320 kPa**  (⟨p_rgh⟩_inlet = 6903.3 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 2780 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 19.788 | 19.789 | 19.789 |
| gauge `p_rgh` | 19.788 | 19.789 | 19.789 |
| total `p + ½ρU²` | 17.880 | 17.924 | 17.924 |
| gauge-total `p_rgh + ½ρU²` | 17.880 | 17.924 | 17.924 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.3327**  (σ = 6.0152, n = 2780 samples, t ∈ [0.800, 1.200] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.7446** kg/s
- ṁ branch_inlet: **-1.6867** kg/s
- ṁ outlet      : **+42.0889** kg/s
- closure error : **+6.6575e+00 kg/s**  (+15.82 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.0052 | 0.0052 | 0.0052 | 19.789 | 17.924 | +15.82 |
| **AVG** | **0.0052** | **0.0052** | **0.0052** | **19.789** | **17.924** | **+15.82** |
