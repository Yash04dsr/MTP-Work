# All metrics — `case_05`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01424 | 0.00822 | 0.5770 | 0.0048 |
| mass | 0.01406 | 0.00811 | 0.5764 | 0.0047 |
| vol  | 0.01448 | 0.00812 | 0.5612 | 0.0046 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01424 | 0.00822 | 0.5770 | 0.0048 |
| mass | 0.01406 | 0.00811 | 0.5764 | 0.0047 |
| vol  | 0.01448 | 0.00812 | 0.5612 | 0.0046 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01383** (n = 141 samples in [0.801, 1.200] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **4.823 kPa**  (⟨p_rgh⟩_inlet = 6904.8 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 141 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -27.054 | -27.053 | -27.053 |
| gauge `p_rgh` | -27.056 | -27.056 | -27.053 |
| total `p + ½ρU²` | -28.291 | -28.260 | -28.261 |
| gauge-total `p_rgh + ½ρU²` | -28.293 | -28.263 | -28.261 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.3062**  (σ = 8.4971, n = 141 samples, t ∈ [0.801, 1.200] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.5127** kg/s
- ṁ branch_inlet: **-0.4598** kg/s
- ṁ outlet      : **+41.8718** kg/s
- closure error : **+7.8993e+00 kg/s**  (+18.87 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.5770 | 0.5764 | 0.5612 | -27.053 | -28.260 | +18.87 |
| **AVG** | **0.5770** | **0.5764** | **0.5612** | **-27.053** | **-28.260** | **+18.87** |
