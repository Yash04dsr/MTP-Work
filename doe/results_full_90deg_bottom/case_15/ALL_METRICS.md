# All metrics — `case_15`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.10540 | 0.01816 | 0.1723 | 0.0035 |
| mass | 0.10477 | 0.01825 | 0.1742 | 0.0035 |
| vol  | 0.10611 | 0.01774 | 0.1672 | 0.0033 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.10540 | 0.01816 | 0.1723 | 0.0035 |
| mass | 0.10477 | 0.01825 | 0.1742 | 0.0035 |
| vol  | 0.10611 | 0.01774 | 0.1672 | 0.0033 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.07003** (n = 203 samples in [0.801, 1.200] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **2.224 kPa**  (⟨p_rgh⟩_inlet = 6902.2 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 203 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 65.497 | 65.497 | 65.497 |
| gauge `p_rgh` | 65.499 | 65.500 | 65.498 |
| total `p + ½ρU²` | 60.228 | 60.269 | 60.266 |
| gauge-total `p_rgh + ½ρU²` | 60.230 | 60.271 | 60.267 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+36.1678**  (σ = 15.9400, n = 203 samples, t ∈ [0.801, 1.200] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.9658** kg/s
- ṁ branch_inlet: **-2.6139** kg/s
- ṁ outlet      : **+51.0862** kg/s
- closure error : **+1.4506e+01 kg/s**  (+28.40 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.1723 | 0.1742 | 0.1672 | 65.497 | 60.269 | +28.40 |
| **AVG** | **0.1723** | **0.1742** | **0.1672** | **65.497** | **60.269** | **+28.40** |
