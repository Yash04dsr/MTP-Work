# All metrics — `case_07`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02000 | 0.00476 | 0.2378 | 0.0012 |
| mass | 0.01981 | 0.00471 | 0.2376 | 0.0011 |
| vol  | 0.01994 | 0.00471 | 0.2363 | 0.0011 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02000 | 0.00476 | 0.2378 | 0.0012 |
| mass | 0.01981 | 0.00471 | 0.2376 | 0.0011 |
| vol  | 0.01994 | 0.00471 | 0.2363 | 0.0011 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.02051** (n = 135 samples in [0.800, 1.197] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **3.210 kPa**  (⟨p_rgh⟩_inlet = 6903.2 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 135 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -11.588 | -11.587 | -11.587 |
| gauge `p_rgh` | -11.587 | -11.584 | -11.585 |
| total `p + ½ρU²` | -12.538 | -12.507 | -12.503 |
| gauge-total `p_rgh + ½ρU²` | -12.537 | -12.504 | -12.501 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+34.8177**  (σ = 4.4622, n = 135 samples, t ∈ [0.800, 1.197] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.5916** kg/s
- ṁ branch_inlet: **-0.7059** kg/s
- ṁ outlet      : **+39.0885** kg/s
- closure error : **+4.7910e+00 kg/s**  (+12.26 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.2378 | 0.2376 | 0.2363 | -11.587 | -12.507 | +12.26 |
| **AVG** | **0.2378** | **0.2376** | **0.2363** | **-11.587** | **-12.507** | **+12.26** |
