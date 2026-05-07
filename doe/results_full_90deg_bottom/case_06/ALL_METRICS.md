# All metrics — `case_06`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.03097 | 0.01214 | 0.3921 | 0.0049 |
| mass | 0.03022 | 0.01205 | 0.3987 | 0.0050 |
| vol  | 0.03106 | 0.01198 | 0.3858 | 0.0048 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.03097 | 0.01214 | 0.3921 | 0.0049 |
| mass | 0.03022 | 0.01205 | 0.3987 | 0.0050 |
| vol  | 0.03106 | 0.01198 | 0.3858 | 0.0048 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.02987** (n = 133 samples in [0.800, 1.200] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **3.109 kPa**  (⟨p_rgh⟩_inlet = 6903.1 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 133 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -47.060 | -47.060 | -47.060 |
| gauge `p_rgh` | -47.060 | -47.061 | -47.062 |
| total `p + ½ρU²` | -46.968 | -46.946 | -46.939 |
| gauge-total `p_rgh + ½ρU²` | -46.968 | -46.948 | -46.941 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+36.7268**  (σ = 11.2964, n = 133 samples, t ∈ [0.800, 1.200] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.4170** kg/s
- ṁ branch_inlet: **-0.9658** kg/s
- ṁ outlet      : **+29.7930** kg/s
- closure error : **-4.5898e+00 kg/s**  (-15.41 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.3921 | 0.3987 | 0.3858 | -47.060 | -46.946 | -15.41 |
| **AVG** | **0.3921** | **0.3987** | **0.3858** | **-47.060** | **-46.946** | **-15.41** |
