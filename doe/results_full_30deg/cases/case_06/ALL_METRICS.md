# All metrics — `case_06`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02985 | 0.00264 | 0.0883 | 0.0002 |
| mass | 0.02984 | 0.00261 | 0.0875 | 0.0002 |
| vol  | 0.02988 | 0.00260 | 0.0871 | 0.0002 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02985 | 0.00264 | 0.0883 | 0.0002 |
| mass | 0.02984 | 0.00261 | 0.0875 | 0.0002 |
| vol  | 0.02988 | 0.00260 | 0.0871 | 0.0002 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.02993** (n = 493 samples in [0.801, 1.200] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **-0.676 kPa**  (⟨p_rgh⟩_inlet = 6899.3 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 493 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 13.609 | 13.609 | 13.609 |
| gauge `p_rgh` | 13.609 | 13.610 | 13.610 |
| total `p + ½ρU²` | 13.560 | 13.600 | 13.600 |
| gauge-total `p_rgh + ½ρU²` | 13.560 | 13.601 | 13.601 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+34.8855**  (σ = 6.1985, n = 493 samples, t ∈ [0.801, 1.200] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.7145** kg/s
- ṁ branch_inlet: **-1.0289** kg/s
- ṁ outlet      : **+31.0953** kg/s
- closure error : **-3.6481e+00 kg/s**  (-11.73 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.0883 | 0.0875 | 0.0871 | 13.609 | 13.600 | -11.73 |
| **AVG** | **0.0883** | **0.0875** | **0.0871** | **13.609** | **13.600** | **-11.73** |
