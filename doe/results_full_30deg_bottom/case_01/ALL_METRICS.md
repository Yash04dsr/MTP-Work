# All metrics — `case_01`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.03530 | 0.00820 | 0.2323 | 0.0020 |
| mass | 0.03518 | 0.00818 | 0.2325 | 0.0020 |
| vol  | 0.03555 | 0.00799 | 0.2249 | 0.0019 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.03530 | 0.00820 | 0.2323 | 0.0020 |
| mass | 0.03518 | 0.00818 | 0.2325 | 0.0020 |
| vol  | 0.03555 | 0.00799 | 0.2249 | 0.0019 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.02964** (n = 250 samples in [0.801, 1.199] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **-2.377 kPa**  (⟨p_rgh⟩_inlet = 6897.6 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 250 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 3.194 | 3.194 | 3.194 |
| gauge `p_rgh` | 3.195 | 3.197 | 3.196 |
| total `p + ½ρU²` | 4.177 | 4.220 | 4.220 |
| gauge-total `p_rgh + ½ρU²` | 4.178 | 4.223 | 4.221 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.5367**  (σ = 12.1018, n = 250 samples, t ∈ [0.801, 1.199] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.6637** kg/s
- ṁ branch_inlet: **-0.9621** kg/s
- ṁ outlet      : **+20.4319** kg/s
- closure error : **-1.4194e+01 kg/s**  (-69.47 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.2323 | 0.2325 | 0.2249 | 3.194 | 4.220 | -69.47 |
| **AVG** | **0.2323** | **0.2325** | **0.2249** | **3.194** | **4.220** | **-69.47** |
