# All metrics — `case_08`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01313 | 0.01369 | 1.0430 | 0.0145 |
| mass | 0.01079 | 0.01261 | 1.1694 | 0.0149 |
| vol  | 0.01181 | 0.01306 | 1.1052 | 0.0146 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01313 | 0.01369 | 1.0430 | 0.0145 |
| mass | 0.01079 | 0.01261 | 1.1694 | 0.0149 |
| vol  | 0.01181 | 0.01306 | 1.1052 | 0.0146 |

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- time-series data not found in postProcessing/

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 2.296 | 2.297 | 2.297 |
| gauge `p_rgh` | 2.292 | 2.286 | 2.289 |
| total `p + ½ρU²` | 2.989 | 2.957 | 2.978 |
| gauge-total `p_rgh + ½ρU²` | 2.985 | 2.946 | 2.970 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- outletFlux function object not found in postProcessing/

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.6593** kg/s
- ṁ branch_inlet: **-0.4270** kg/s
- ṁ outlet      : **+25.2366** kg/s
- closure error : **-8.8498e+00 kg/s**  (-35.07 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 1.0430 | 1.1694 | 1.1052 | 2.297 | 2.957 | -35.07 |
| **AVG** | **1.0430** | **1.1694** | **1.1052** | **2.297** | **2.957** | **-35.07** |
