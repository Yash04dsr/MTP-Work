# All metrics — `case_12`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.04410 | 0.01198 | 0.2716 | 0.0034 |
| mass | 0.04104 | 0.01109 | 0.2702 | 0.0031 |
| vol  | 0.04170 | 0.01121 | 0.2689 | 0.0031 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.04410 | 0.01198 | 0.2716 | 0.0034 |
| mass | 0.04104 | 0.01109 | 0.2702 | 0.0031 |
| vol  | 0.04170 | 0.01121 | 0.2689 | 0.0031 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.05666** (n = 146 samples in [0.802, 1.200] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **-2.326 kPa**  (⟨p_rgh⟩_inlet = 6897.7 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 146 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 28.908 | 28.908 | 28.908 |
| gauge `p_rgh` | 28.907 | 28.902 | 28.902 |
| total `p + ½ρU²` | 30.104 | 30.070 | 30.083 |
| gauge-total `p_rgh + ½ρU²` | 30.103 | 30.064 | 30.078 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+36.3584**  (σ = 14.6235, n = 146 samples, t ∈ [0.802, 1.200] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.7874** kg/s
- ṁ branch_inlet: **-1.9196** kg/s
- ṁ outlet      : **+16.8522** kg/s
- closure error : **-1.8855e+01 kg/s**  (-111.88 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.2716 | 0.2702 | 0.2689 | 28.908 | 30.070 | -111.88 |
| **AVG** | **0.2716** | **0.2702** | **0.2689** | **28.908** | **30.070** | **-111.88** |
