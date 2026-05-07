# All metrics — `case_06`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02880 | 0.00581 | 0.2016 | 0.0012 |
| mass | 0.02823 | 0.00578 | 0.2048 | 0.0012 |
| vol  | 0.02843 | 0.00577 | 0.2030 | 0.0012 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02880 | 0.00581 | 0.2016 | 0.0012 |
| mass | 0.02823 | 0.00578 | 0.2048 | 0.0012 |
| vol  | 0.02843 | 0.00577 | 0.2030 | 0.0012 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.02903** (n = 298 samples in [0.800, 1.199] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **1.435 kPa**  (⟨p_rgh⟩_inlet = 6901.4 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 298 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -19.254 | -19.254 | -19.254 |
| gauge `p_rgh` | -19.254 | -19.248 | -19.249 |
| total `p + ½ρU²` | -18.795 | -18.782 | -18.775 |
| gauge-total `p_rgh + ½ρU²` | -18.795 | -18.777 | -18.771 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.8272**  (σ = 7.9971, n = 298 samples, t ∈ [0.800, 1.199] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.5507** kg/s
- ṁ branch_inlet: **-0.9820** kg/s
- ṁ outlet      : **+26.3977** kg/s
- closure error : **-8.1351e+00 kg/s**  (-30.82 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.2016 | 0.2048 | 0.2030 | -19.254 | -18.782 | -30.82 |
| **AVG** | **0.2016** | **0.2048** | **0.2030** | **-19.254** | **-18.782** | **-30.82** |
