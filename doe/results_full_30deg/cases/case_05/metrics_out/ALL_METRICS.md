# All metrics — `case_05`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01373 | 0.00409 | 0.2977 | 0.0012 |
| mass | 0.01361 | 0.00402 | 0.2956 | 0.0012 |
| vol  | 0.01372 | 0.00402 | 0.2931 | 0.0012 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01373 | 0.00409 | 0.2977 | 0.0012 |
| mass | 0.01361 | 0.00402 | 0.2956 | 0.0012 |
| vol  | 0.01372 | 0.00402 | 0.2931 | 0.0012 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01411** (n = 235 samples in [0.801, 1.200] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **3.309 kPa**  (⟨p_rgh⟩_inlet = 6903.3 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 235 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -19.310 | -19.309 | -19.309 |
| gauge `p_rgh` | -19.309 | -19.306 | -19.307 |
| total `p + ½ρU²` | -20.318 | -20.288 | -20.286 |
| gauge-total `p_rgh + ½ρU²` | -20.317 | -20.286 | -20.284 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.0192**  (σ = 7.1679, n = 235 samples, t ∈ [0.801, 1.200] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.5540** kg/s
- ṁ branch_inlet: **-0.4660** kg/s
- ṁ outlet      : **+40.2695** kg/s
- closure error : **+6.2495e+00 kg/s**  (+15.52 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.2977 | 0.2956 | 0.2931 | -19.309 | -20.288 | +15.52 |
| **AVG** | **0.2977** | **0.2956** | **0.2931** | **-19.309** | **-20.288** | **+15.52** |
