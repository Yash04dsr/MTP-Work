# All metrics — `case_02`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01061 | 0.01262 | 1.1892 | 0.0152 |
| mass | 0.01005 | 0.01218 | 1.2118 | 0.0149 |
| vol  | 0.01101 | 0.01276 | 1.1585 | 0.0149 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01061 | 0.01262 | 1.1892 | 0.0152 |
| mass | 0.01005 | 0.01218 | 1.2118 | 0.0149 |
| vol  | 0.01101 | 0.01276 | 1.1585 | 0.0149 |

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- time-series data not found in postProcessing/

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 0.377 | 0.378 | 0.378 |
| gauge `p_rgh` | 0.375 | 0.374 | 0.376 |
| total `p + ½ρU²` | -1.099 | -1.073 | -1.069 |
| gauge-total `p_rgh + ½ρU²` | -1.101 | -1.077 | -1.071 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- outletFlux function object not found in postProcessing/

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.6500** kg/s
- ṁ branch_inlet: **-0.2698** kg/s
- ṁ outlet      : **+44.1305** kg/s
- closure error : **+1.0211e+01 kg/s**  (+23.14 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 1.1892 | 1.2118 | 1.1585 | 0.378 | -1.073 | +23.14 |
| **AVG** | **1.1892** | **1.2118** | **1.1585** | **0.378** | **-1.073** | **+23.14** |
