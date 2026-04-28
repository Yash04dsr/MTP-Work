# All metrics — `case_06`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02929 | 0.00397 | 0.1357 | 0.0006 |
| mass | 0.02893 | 0.00395 | 0.1366 | 0.0006 |
| vol  | 0.02902 | 0.00393 | 0.1355 | 0.0005 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02929 | 0.00397 | 0.1357 | 0.0006 |
| mass | 0.02893 | 0.00395 | 0.1366 | 0.0006 |
| vol  | 0.02902 | 0.00393 | 0.1355 | 0.0005 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.02934** (n = 414 samples in [0.801, 1.199] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **2.650 kPa**  (⟨p_rgh⟩_inlet = 6902.6 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 414 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 2.688 | 2.688 | 2.688 |
| gauge `p_rgh` | 2.688 | 2.690 | 2.690 |
| total `p + ½ρU²` | 2.462 | 2.472 | 2.479 |
| gauge-total `p_rgh + ½ρU²` | 2.462 | 2.473 | 2.480 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+34.9832**  (σ = 3.5626, n = 414 samples, t ∈ [0.801, 1.199] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.6613** kg/s
- ṁ branch_inlet: **-1.0031** kg/s
- ṁ outlet      : **+32.6298** kg/s
- closure error : **-2.0345e+00 kg/s**  (-6.24 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.1357 | 0.1366 | 0.1355 | 2.688 | 2.472 | -6.24 |
| **AVG** | **0.1357** | **0.1366** | **0.1355** | **2.688** | **2.472** | **-6.24** |
