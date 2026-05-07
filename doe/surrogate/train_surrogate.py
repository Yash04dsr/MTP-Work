#!/usr/bin/env python3
"""train_surrogate.py — Train DNN & baseline surrogates on CFD DoE data.

Reads cross_campaign_metrics.csv, trains:
  1. DNN (architecture from Project1.tex: 6→64→128→64→32→2)
  2. Gaussian Process Regression (GPR)
  3. Random Forest (RF)
  4. Gradient Boosting (XGB-style via sklearn)

Performs Leave-One-Out Cross-Validation (LOOCV) given the small dataset (N=40),
generates parity plots, training curves, and error analysis.

Then runs NSGA-II on the best surrogate to produce the Pareto front.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import LeaveOneOut, KFold, cross_val_predict
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import MinMaxScaler

warnings.filterwarnings("ignore")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── paths ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "cross_campaign_metrics.csv"
OUTDIR = Path(__file__).resolve().parent / "figures"
OUTDIR.mkdir(parents=True, exist_ok=True)

# ── load & encode ──────────────────────────────────────────────────────
df = pd.read_csv(DATA)
print(f"Loaded {len(df)} cases from {DATA.name}")

# Feature engineering (matching Project1.tex Section 4.2.2)
# One-hot for injection side: top=[1,0], bottom=[0,1]
df["side_top"] = (df["side"] == "top").astype(float)
df["side_bot"] = (df["side"] == "bottom").astype(float)

FEATURE_COLS = ["side_top", "side_bot", "angle", "d_D", "VR", "HBR"]
TARGET_COLS = ["CoV", "dP_LP_kPa"]

X_raw = df[FEATURE_COLS].values.astype(np.float64)
Y_raw = df[TARGET_COLS].values.astype(np.float64)

# MinMax scale features to [0,1]
scaler_X = MinMaxScaler()
scaler_Y = MinMaxScaler()
X = scaler_X.fit_transform(X_raw)
Y = scaler_Y.fit_transform(Y_raw)

print(f"Features shape: {X.shape}, Targets shape: {Y.shape}")
print(f"CoV  range: [{Y_raw[:,0].min():.4f}, {Y_raw[:,0].max():.4f}]")
print(f"ΔP   range: [{Y_raw[:,1].min():.4f}, {Y_raw[:,1].max():.4f}] kPa")


# ══════════════════════════════════════════════════════════════════════
#  1. DNN SURROGATE (PyTorch)
# ══════════════════════════════════════════════════════════════════════

class DNNSurrogate(nn.Module):
    """6→64→128→64→32→2 as specified in Project1.tex."""
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(6, 64), nn.ReLU(),
            nn.Linear(64, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, 32), nn.ReLU(),
            nn.Linear(32, 2),
        )

    def forward(self, x):
        return self.net(x)


def train_dnn(X_train, Y_train, X_val, Y_val, epochs=2000, lr=1e-3, wd=1e-4,
              patience=100):
    """Train one DNN instance, return model + loss history."""
    model = DNNSurrogate()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=wd)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, patience=30, factor=0.5, min_lr=1e-6
    )

    Xt = torch.tensor(X_train, dtype=torch.float32)
    Yt = torch.tensor(Y_train, dtype=torch.float32)
    Xv = torch.tensor(X_val, dtype=torch.float32)
    Yv = torch.tensor(Y_val, dtype=torch.float32)

    best_val = float("inf")
    best_state = None
    wait = 0
    train_losses, val_losses = [], []

    for ep in range(1, epochs + 1):
        model.train()
        pred = model(Xt)
        loss = nn.MSELoss()(pred, Yt)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        model.eval()
        with torch.no_grad():
            val_pred = model(Xv)
            val_loss = nn.MSELoss()(val_pred, Yv).item()

        scheduler.step(val_loss)
        train_losses.append(loss.item())
        val_losses.append(val_loss)

        if val_loss < best_val:
            best_val = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1
            if wait >= patience:
                break

    model.load_state_dict(best_state)
    return model, train_losses, val_losses


# ── DNN: 5-fold CV (more robust than single split for N=40) ───────────
print("\n" + "=" * 60)
print("DNN Surrogate — 5-Fold Cross-Validation")
print("=" * 60)

kf = KFold(n_splits=5, shuffle=True, random_state=42)
dnn_preds = np.zeros_like(Y)
all_train_losses = []
all_val_losses = []

for fold, (train_idx, test_idx) in enumerate(kf.split(X)):
    Xtr, Ytr = X[train_idx], Y[train_idx]
    Xte, Yte = X[test_idx], Y[test_idx]

    # Use 15% of train as validation for early stopping
    n_val = max(2, int(0.15 * len(Xtr)))
    perm = np.random.RandomState(fold).permutation(len(Xtr))
    val_idx_inner = perm[:n_val]
    tr_idx_inner = perm[n_val:]

    model, tl, vl = train_dnn(
        Xtr[tr_idx_inner], Ytr[tr_idx_inner],
        Xtr[val_idx_inner], Ytr[val_idx_inner],
        epochs=3000, lr=1e-3, wd=1e-4, patience=150
    )
    all_train_losses.append(tl)
    all_val_losses.append(vl)

    model.eval()
    with torch.no_grad():
        pred = model(torch.tensor(Xte, dtype=torch.float32)).numpy()
    dnn_preds[test_idx] = pred
    print(f"  Fold {fold+1}: trained {len(tl)} epochs, "
          f"test MSE = {mean_squared_error(Yte, pred):.6f}")

# Inverse-transform predictions to physical units
dnn_preds_phys = scaler_Y.inverse_transform(dnn_preds)


# ── DNN: also train a FINAL model on ALL data for NSGA-II ─────────────
print("\nTraining final DNN on all 40 samples...")
n_val_final = 6
perm_final = np.random.RandomState(99).permutation(len(X))
val_final = perm_final[:n_val_final]
tr_final = perm_final[n_val_final:]

final_model, final_tl, final_vl = train_dnn(
    X[tr_final], Y[tr_final], X[val_final], Y[val_final],
    epochs=5000, lr=1e-3, wd=1e-4, patience=200
)
print(f"  Final model: {len(final_tl)} epochs")

# Save model
torch.save(final_model.state_dict(), OUTDIR.parent / "dnn_surrogate.pt")


# ══════════════════════════════════════════════════════════════════════
#  2. BASELINE SURROGATES (sklearn) — LOOCV
# ══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("Baseline Surrogates — Leave-One-Out Cross-Validation")
print("=" * 60)

surrogates = {
    "GPR": MultiOutputRegressor(GaussianProcessRegressor(
        kernel=ConstantKernel() * Matern(nu=2.5) + WhiteKernel(),
        n_restarts_optimizer=10, random_state=42
    )),
    "Random Forest": MultiOutputRegressor(RandomForestRegressor(
        n_estimators=200, max_depth=None, min_samples_leaf=2,
        random_state=42
    )),
    "Gradient Boosting": MultiOutputRegressor(GradientBoostingRegressor(
        n_estimators=200, max_depth=3, learning_rate=0.05,
        min_samples_leaf=2, random_state=42
    )),
}

loo = LeaveOneOut()
results = {}

for name, model in surrogates.items():
    preds_loo = cross_val_predict(model, X, Y, cv=loo)
    preds_phys = scaler_Y.inverse_transform(preds_loo)
    results[name] = preds_phys
    r2_cov = r2_score(Y_raw[:, 0], preds_phys[:, 0])
    r2_dp = r2_score(Y_raw[:, 1], preds_phys[:, 1])
    mae_cov = mean_absolute_error(Y_raw[:, 0], preds_phys[:, 0])
    mae_dp = mean_absolute_error(Y_raw[:, 1], preds_phys[:, 1])
    print(f"\n  {name}:")
    print(f"    CoV  — R²={r2_cov:.4f}, MAE={mae_cov:.4f}")
    print(f"    ΔP   — R²={r2_dp:.4f}, MAE={mae_dp:.2f} kPa")

# DNN results (5-fold, not LOOCV, but comparable)
results["DNN (5-fold CV)"] = dnn_preds_phys


# ══════════════════════════════════════════════════════════════════════
#  3. ERROR ANALYSIS SUMMARY
# ══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("COMPREHENSIVE ERROR ANALYSIS")
print("=" * 60)

summary_rows = []
for name, preds in results.items():
    for j, target in enumerate(["CoV", "ΔP (kPa)"]):
        y_true = Y_raw[:, j]
        y_pred = preds[:, j]
        r2 = r2_score(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mape = np.mean(np.abs((y_true - y_pred) / (np.abs(y_true) + 1e-8))) * 100
        row = {"Model": name, "Target": target,
               "R²": r2, "MAE": mae, "RMSE": rmse, "MAPE(%)": mape}
        summary_rows.append(row)
        print(f"  {name:25s} | {target:10s} | R²={r2:+.4f} | MAE={mae:.4f} | RMSE={rmse:.4f} | MAPE={mape:.1f}%")

summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv(OUTDIR.parent / "surrogate_error_analysis.csv", index=False)

# ── Identify best model ────────────────────────────────────────────────
cov_r2 = {}
for name, preds in results.items():
    cov_r2[name] = r2_score(Y_raw[:, 0], preds[:, 0])

best_model_name = max(cov_r2, key=cov_r2.get)
print(f"\n*** Best model for CoV: {best_model_name} (R²={cov_r2[best_model_name]:.4f})")


# ══════════════════════════════════════════════════════════════════════
#  4. FIGURES
# ══════════════════════════════════════════════════════════════════════

plt.rcParams.update({
    "font.size": 11, "axes.labelsize": 12, "axes.titlesize": 13,
    "figure.dpi": 150, "savefig.bbox": "tight",
})

# ── Fig 1: Training loss curve (best fold) ────────────────────────────
fig, ax = plt.subplots(figsize=(7, 4))
best_fold = min(range(5), key=lambda i: min(all_val_losses[i]))
ax.semilogy(all_train_losses[best_fold], label="Train", alpha=0.8)
ax.semilogy(all_val_losses[best_fold], label="Validation", alpha=0.8)
ax.set_xlabel("Epoch")
ax.set_ylabel("MSE Loss")
ax.set_title("DNN Training Convergence (Best Fold)")
ax.legend()
ax.grid(True, alpha=0.3)
fig.savefig(OUTDIR / "fig_dnn_training_loss.png")
plt.close(fig)

# ── Fig 2: Parity plots (all 4 models) ────────────────────────────────
fig, axes = plt.subplots(2, 4, figsize=(18, 8))
model_names = list(results.keys())
for col, name in enumerate(model_names):
    preds = results[name]
    for row, (target, unit) in enumerate(zip(["CoV", "ΔP"], ["", " (kPa)"])):
        ax = axes[row, col]
        y_true = Y_raw[:, row]
        y_pred = preds[:, row]
        r2 = r2_score(y_true, y_pred)

        ax.scatter(y_true, y_pred, s=30, alpha=0.7, edgecolors="k", linewidth=0.5)
        lims = [min(y_true.min(), y_pred.min()),
                max(y_true.max(), y_pred.max())]
        margin = (lims[1] - lims[0]) * 0.1
        lims = [lims[0] - margin, lims[1] + margin]
        ax.plot(lims, lims, "r--", lw=1.5, label=f"R²={r2:.3f}")
        ax.set_xlim(lims)
        ax.set_ylim(lims)
        ax.legend(loc="upper left", fontsize=9)
        ax.grid(True, alpha=0.3)
        if row == 0:
            ax.set_title(name, fontsize=10)
        if col == 0:
            ax.set_ylabel(f"Predicted {target}{unit}")
        if row == 1:
            ax.set_xlabel(f"Actual {target}{unit}")

fig.suptitle("Parity Plots: Predicted vs Actual (Cross-Validated)", fontsize=14, y=1.02)
fig.tight_layout()
fig.savefig(OUTDIR / "fig_parity_all_models.png")
plt.close(fig)

# ── Fig 3: Bar chart of R² by model ───────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
for j, target in enumerate(["CoV", "ΔP (kPa)"]):
    ax = axes[j]
    names = list(results.keys())
    r2_vals = [r2_score(Y_raw[:, j], results[n][:, j]) for n in names]
    colors = ["#d62728" if v < 0.7 else "#ff7f0e" if v < 0.9 else "#2ca02c" for v in r2_vals]
    bars = ax.barh(names, r2_vals, color=colors, edgecolor="k", linewidth=0.5)
    ax.set_xlabel("R² Score")
    ax.set_title(f"{target}")
    ax.set_xlim([min(0, min(r2_vals) - 0.1), 1.05])
    ax.axvline(0.9, ls="--", color="gray", alpha=0.5, label="R²=0.9 threshold")
    ax.legend(fontsize=8)
    ax.grid(True, axis="x", alpha=0.3)
    for bar, val in zip(bars, r2_vals):
        ax.text(max(val + 0.02, 0.02), bar.get_y() + bar.get_height()/2,
                f"{val:.3f}", va="center", fontsize=9)

fig.suptitle("Model Comparison: R² by Target", fontsize=13)
fig.tight_layout()
fig.savefig(OUTDIR / "fig_r2_comparison.png")
plt.close(fig)

# ── Fig 4: Residual distribution ──────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for j, target in enumerate(["CoV", "ΔP (kPa)"]):
    ax = axes[j]
    for name in results:
        residuals = Y_raw[:, j] - results[name][:, j]
        ax.hist(residuals, bins=12, alpha=0.4, label=name, edgecolor="k", linewidth=0.3)
    ax.set_xlabel(f"Residual ({target})")
    ax.set_ylabel("Count")
    ax.set_title(f"Residual Distribution — {target}")
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(OUTDIR / "fig_residuals.png")
plt.close(fig)


# ══════════════════════════════════════════════════════════════════════
#  5. NSGA-II OPTIMIZATION
# ══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("NSGA-II Optimization")
print("=" * 60)

# Also train the best sklearn model on full data for NSGA-II
# (we'll use both DNN and GPR if GPR is better)
best_sklearn = None
best_sklearn_name = None
best_r2_avg = -999
for name in ["GPR", "Random Forest", "Gradient Boosting"]:
    preds = results[name]
    avg_r2 = (r2_score(Y_raw[:, 0], preds[:, 0]) + r2_score(Y_raw[:, 1], preds[:, 1])) / 2
    if avg_r2 > best_r2_avg:
        best_r2_avg = avg_r2
        best_sklearn_name = name

# Re-fit best sklearn on all data
print(f"Using best sklearn model: {best_sklearn_name} (avg R²={best_r2_avg:.4f})")
best_sklearn = surrogates[best_sklearn_name]
best_sklearn.fit(X, Y)

from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.optimize import minimize
from pymoo.termination import get_termination


class SurrogateProblem(Problem):
    """Bi-objective: minimize CoV, minimize |ΔP|."""
    def __init__(self, model_fn, side_encoding):
        super().__init__(n_var=4, n_obj=2, n_constr=0,
                         xl=np.array([0, 0, 0, 0]),
                         xu=np.array([1, 1, 1, 1]))
        self.model_fn = model_fn
        self.side_encoding = side_encoding

    def _evaluate(self, x, out, *args, **kwargs):
        n = x.shape[0]
        X_full = np.zeros((n, 6))
        X_full[:, 0] = self.side_encoding[0]
        X_full[:, 1] = self.side_encoding[1]
        X_full[:, 2:] = x
        preds_scaled = self.model_fn(X_full)
        preds_phys = scaler_Y.inverse_transform(preds_scaled)
        cov = np.clip(preds_phys[:, 0], 0.0, None)
        dp = np.abs(preds_phys[:, 1])
        out["F"] = np.column_stack([cov, dp])


def sklearn_predict(X_input):
    return best_sklearn.predict(X_input)


def dnn_predict(X_input):
    final_model.eval()
    with torch.no_grad():
        return final_model(torch.tensor(X_input, dtype=torch.float32)).numpy()


# Determine which model to use for NSGA-II
dnn_avg_r2 = (r2_score(Y_raw[:, 0], dnn_preds_phys[:, 0]) +
              r2_score(Y_raw[:, 1], dnn_preds_phys[:, 1])) / 2
print(f"DNN avg R²={dnn_avg_r2:.4f}, {best_sklearn_name} avg R²={best_r2_avg:.4f}")

if dnn_avg_r2 > best_r2_avg:
    nsga_predict = dnn_predict
    nsga_model_name = "DNN"
else:
    nsga_predict = sklearn_predict
    nsga_model_name = best_sklearn_name

print(f"→ Using {nsga_model_name} for NSGA-II optimization")

# Run NSGA-II for both Top and Bottom injection
pareto_results = {}
for side_label, side_enc in [("Top", [1.0, 0.0]), ("Bottom", [0.0, 1.0])]:
    problem = SurrogateProblem(nsga_predict, side_enc)

    algorithm = NSGA2(
        pop_size=200,
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
    )

    res = minimize(
        problem, algorithm,
        termination=get_termination("n_gen", 150),
        seed=42,
        verbose=False,
    )
    pareto_results[side_label] = res
    print(f"  {side_label}: {len(res.F)} Pareto-optimal solutions")

# ── Fig 5: Pareto Front ───────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 6))
colors = {"Top": "#1f77b4", "Bottom": "#d62728"}
for side_label, res in pareto_results.items():
    F = res.F
    sorted_idx = np.argsort(F[:, 0])
    ax.scatter(F[sorted_idx, 0], F[sorted_idx, 1], s=20, alpha=0.6,
               color=colors[side_label], label=f"{side_label} injection",
               edgecolors="k", linewidth=0.3)
    ax.plot(F[sorted_idx, 0], F[sorted_idx, 1], "-", alpha=0.3,
            color=colors[side_label])

# Overlay actual CFD data
for side_val, marker, label in [("top", "^", "CFD Top"), ("bottom", "s", "CFD Bottom")]:
    mask = df["side"] == side_val
    ax.scatter(df.loc[mask, "CoV"], np.abs(df.loc[mask, "dP_LP_kPa"]),
               s=80, marker=marker, edgecolors="k", linewidth=1,
               facecolors="none", label=f"{label} (CFD)", zorder=5)

ax.set_xlabel("CoV (Coefficient of Variation)")
ax.set_ylabel("|ΔP| (kPa)")
ax.set_title(f"Pareto Front — {nsga_model_name} Surrogate + NSGA-II")
ax.legend()
ax.grid(True, alpha=0.3)
fig.savefig(OUTDIR / "fig_pareto_front_surrogate.png")
plt.close(fig)

# ── Fig 6: Pareto solutions — design variable distributions ───────────
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
var_names = ["Angle (°)", "d/D", "VR", "HBR"]
# Use actual scaler ranges (columns 2-5 of scaler_X)
var_ranges = list(zip(scaler_X.data_min_[2:], scaler_X.data_max_[2:]))

for side_label, res in pareto_results.items():
    X_pareto = res.X  # scaled [0,1]
    for i, (ax, vname, (lo, hi)) in enumerate(zip(axes.flat, var_names, var_ranges)):
        vals = lo + X_pareto[:, i] * (hi - lo)
        ax.hist(vals, bins=20, alpha=0.4, label=side_label,
                color=colors[side_label], edgecolor="k", linewidth=0.3)
        ax.set_xlabel(vname)
        ax.set_ylabel("Count")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

fig.suptitle("Design Variable Distribution on Pareto Front", fontsize=13)
fig.tight_layout()
fig.savefig(OUTDIR / "fig_pareto_design_vars.png")
plt.close(fig)


# ══════════════════════════════════════════════════════════════════════
#  6. SHAP ANALYSIS (on best sklearn model, fitted on all data)
# ══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SHAP Sensitivity Analysis")
print("=" * 60)

try:
    import shap

    # Use kernel SHAP for model-agnostic explanation
    # We explain the CoV output
    feature_names = ["Side(top)", "Side(bot)", "Angle", "d/D", "VR", "HBR"]

    def predict_cov(x):
        pred = best_sklearn.predict(x)
        return scaler_Y.inverse_transform(pred)[:, 0]

    def predict_dp(x):
        pred = best_sklearn.predict(x)
        return scaler_Y.inverse_transform(pred)[:, 1]

    explainer_cov = shap.KernelExplainer(predict_cov, X[:10])
    shap_values_cov = explainer_cov.shap_values(X)

    explainer_dp = shap.KernelExplainer(predict_dp, X[:10])
    shap_values_dp = explainer_dp.shap_values(X)

    # Bar summary
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    ax = axes[0]
    mean_abs_shap = np.abs(shap_values_cov).mean(axis=0)
    idx_sorted = np.argsort(mean_abs_shap)
    ax.barh([feature_names[i] for i in idx_sorted], mean_abs_shap[idx_sorted],
            color="#2ca02c", edgecolor="k", linewidth=0.5)
    ax.set_xlabel("Mean |SHAP value|")
    ax.set_title("Feature Importance — CoV")
    ax.grid(True, axis="x", alpha=0.3)

    ax = axes[1]
    mean_abs_shap = np.abs(shap_values_dp).mean(axis=0)
    idx_sorted = np.argsort(mean_abs_shap)
    ax.barh([feature_names[i] for i in idx_sorted], mean_abs_shap[idx_sorted],
            color="#1f77b4", edgecolor="k", linewidth=0.5)
    ax.set_xlabel("Mean |SHAP value|")
    ax.set_title("Feature Importance — ΔP")
    ax.grid(True, axis="x", alpha=0.3)

    fig.suptitle(f"SHAP Feature Importance ({best_sklearn_name})", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUTDIR / "fig_shap_importance.png")
    plt.close(fig)
    print("  SHAP figures saved.")

except Exception as e:
    print(f"  SHAP failed: {e}")


# ══════════════════════════════════════════════════════════════════════
#  7. SAVE SUMMARY
# ══════════════════════════════════════════════════════════════════════

# Extract knee point (closest to utopia)
for side_label, res in pareto_results.items():
    F = res.F
    # Normalize objectives to [0,1]
    f_min = F.min(axis=0)
    f_max = F.max(axis=0)
    F_norm = (F - f_min) / (f_max - f_min + 1e-12)
    dist_to_utopia = np.sqrt((F_norm ** 2).sum(axis=1))
    knee_idx = np.argmin(dist_to_utopia)
    knee_X = res.X[knee_idx]
    knee_F = F[knee_idx]

    # Map back to physical using scaler's actual learned ranges
    var_ranges_dict = {
        "angle": (scaler_X.data_min_[2], scaler_X.data_max_[2]),
        "d_D":   (scaler_X.data_min_[3], scaler_X.data_max_[3]),
        "VR":    (scaler_X.data_min_[4], scaler_X.data_max_[4]),
        "HBR":   (scaler_X.data_min_[5], scaler_X.data_max_[5]),
    }
    phys = {}
    for i, (k, (lo, hi)) in enumerate(var_ranges_dict.items()):
        phys[k] = lo + knee_X[i] * (hi - lo)

    print(f"\n  Knee point ({side_label} injection):")
    print(f"    Angle={phys['angle']:.1f}°, d/D={phys['d_D']:.3f}, "
          f"VR={phys['VR']:.2f}, HBR={phys['HBR']:.3f}")
    print(f"    CoV={knee_F[0]:.4f}, |ΔP|={knee_F[1]:.2f} kPa")

print("\n" + "=" * 60)
print("ALL DONE. Figures saved to:", OUTDIR)
print("=" * 60)
