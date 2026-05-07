# All metrics — `case_03`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01105 | 0.00522 | 0.4723 | 0.0025 |
| mass | 0.01092 | 0.00517 | 0.4733 | 0.0025 |
| vol  | 0.01109 | 0.00513 | 0.4628 | 0.0024 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01105 | 0.00522 | 0.4723 | 0.0025 |
| mass | 0.01092 | 0.00517 | 0.4733 | 0.0025 |
| vol  | 0.01109 | 0.00513 | 0.4628 | 0.0024 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01066** (n = 222 samples in [0.801, 1.199] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **3.197 kPa**  (⟨p_rgh⟩_inlet = 6903.2 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 222 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -28.595 | -28.594 | -28.594 |
| gauge `p_rgh` | -28.596 | -28.595 | -28.594 |
| total `p + ½ρU²` | -29.289 | -29.261 | -29.259 |
| gauge-total `p_rgh + ½ρU²` | -29.290 | -29.261 | -29.258 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.4185**  (σ = 8.1152, n = 222 samples, t ∈ [0.801, 1.199] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.5052** kg/s
- ṁ branch_inlet: **-0.3558** kg/s
- ṁ outlet      : **+38.2785** kg/s
- closure error : **+4.4175e+00 kg/s**  (+11.54 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.4723 | 0.4733 | 0.4628 | -28.594 | -29.261 | +11.54 |
| **AVG** | **0.4723** | **0.4733** | **0.4628** | **-28.594** | **-29.261** | **+11.54** |
