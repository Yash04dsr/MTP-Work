# All metrics — `case_07`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02932 | 0.02797 | 0.9538 | 0.0275 |
| mass | 0.02436 | 0.02609 | 1.0712 | 0.0286 |
| vol  | 0.02841 | 0.02742 | 0.9654 | 0.0272 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02932 | 0.02797 | 0.9538 | 0.0275 |
| mass | 0.02436 | 0.02609 | 1.0712 | 0.0286 |
| vol  | 0.02841 | 0.02742 | 0.9654 | 0.0272 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01781** (n = 66 samples in [0.807, 1.197] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **5.121 kPa**  (⟨p_rgh⟩_inlet = 6905.1 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 66 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 32.435 | 32.435 | 32.435 |
| gauge `p_rgh` | 32.428 | 32.422 | 32.428 |
| total `p + ½ρU²` | 31.274 | 31.193 | 31.279 |
| gauge-total `p_rgh + ½ρU²` | 31.268 | 31.180 | 31.271 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+36.1063**  (σ = 9.6564, n = 66 samples, t ∈ [0.807, 1.197] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.8046** kg/s
- ṁ branch_inlet: **-0.7030** kg/s
- ṁ outlet      : **+40.0276** kg/s
- closure error : **+5.5200e+00 kg/s**  (+13.79 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.9538 | 1.0712 | 0.9654 | 32.435 | 31.193 | +13.79 |
| **AVG** | **0.9538** | **1.0712** | **0.9654** | **32.435** | **31.193** | **+13.79** |
