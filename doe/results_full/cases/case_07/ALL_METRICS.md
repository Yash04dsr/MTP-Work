# All metrics — `case_07`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01851 | 0.00815 | 0.4404 | 0.0037 |
| mass | 0.01839 | 0.00807 | 0.4386 | 0.0036 |
| vol  | 0.01879 | 0.00804 | 0.4275 | 0.0035 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01851 | 0.00815 | 0.4404 | 0.0037 |
| mass | 0.01839 | 0.00807 | 0.4386 | 0.0036 |
| vol  | 0.01879 | 0.00804 | 0.4275 | 0.0035 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.02078** (n = 216 samples in [0.801, 1.198] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **3.953 kPa**  (⟨p_rgh⟩_inlet = 6904.0 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 216 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -32.467 | -32.466 | -32.466 |
| gauge `p_rgh` | -32.469 | -32.469 | -32.467 |
| total `p + ½ρU²` | -32.810 | -32.779 | -32.780 |
| gauge-total `p_rgh + ½ρU²` | -32.812 | -32.781 | -32.781 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+36.0378**  (σ = 8.5997, n = 216 samples, t ∈ [0.801, 1.198] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.4863** kg/s
- ṁ branch_inlet: **-0.6982** kg/s
- ṁ outlet      : **+34.6541** kg/s
- closure error : **+4.6954e-01 kg/s**  (+1.35 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.4404 | 0.4386 | 0.4275 | -32.466 | -32.779 | +1.35 |
| **AVG** | **0.4404** | **0.4386** | **0.4275** | **-32.466** | **-32.779** | **+1.35** |
