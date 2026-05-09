# 6-Minute Presentation Script

**Total: ~6 minutes | 20 slides (some are quick flips)**

---

## Slide 1: Title (5 sec)

Good morning everyone. My name is Yash Sakhare, and my project is on multiobjective optimization of hydrogen injection into natural gas pipelines, supervised by Professor Abhijeet Raj.

---

## Slide 2: The Problem (30 sec)

So the context here is hydrogen blending into existing natural gas grids. This is considered one of the cheapest ways to decarbonise the gas network because you don't need to rebuild anything - you just inject hydrogen into the existing methane pipeline.

But there's a fundamental problem. Hydrogen is 8 times lighter than methane. So instead of mixing uniformly, buoyancy pushes it to the top of the pipe. You get stratification.

And that causes real engineering problems - hydrogen embrittlement at the pipe crown where concentration is highest, Wobbe Index drift which destabilises burners, and metering errors because the speed of sound depends on composition.

So uniform mixing is not optional - it's a safety requirement.

> **If asked "What is Wobbe Index?"**: It's a measure of the interchangeability of fuel gases. It equals the higher heating value divided by the square root of the specific gravity. If H2 concentration varies across the pipe cross-section, different burners see different Wobbe numbers, so some run lean and some run rich.

> **If asked "What is hydrogen embrittlement?"**: When hydrogen concentration is locally high against the steel pipe wall, H2 molecules dissociate and atomic hydrogen diffuses into the steel lattice. This makes the steel brittle and prone to cracking. It's worst at the pipe crown where buoyancy pushes H2.

---

## Slide 3: Our Contribution (25 sec)

The gap in the literature is that nobody has treated the injection angle as a primary design variable. Existing studies fix it at 90 degrees and vary other things. And nobody has done a proper bi-objective optimisation looking at both mixing quality and pressure drop together.

So what we did: we swept three variables - the injection angle, the diameter ratio of the branch to the main pipe, and the velocity ratio. We also tested top versus bottom injection to understand buoyancy effects. In total, 4 campaigns, 40 validated CFD cases. Then we trained a Gaussian Process surrogate model and used NSGA-II to find the Pareto-optimal designs.

The two objectives we minimise are CoV - which is the coefficient of variation of hydrogen at the outlet, where zero means perfectly mixed - and the absolute pressure drop, which represents pumping cost.

> **If asked "What is CoV?"**: It's standard deviation of H2 mass fraction at the outlet divided by the mean. If every cell at the outlet has the same H2 concentration, CoV = 0 - perfect mixing. If some cells are pure H2 and others pure CH4, CoV approaches 1.

> **If asked "What is NSGA-II?"**: Non-dominated Sorting Genetic Algorithm II. It's a multi-objective evolutionary optimiser. It maintains a population of candidate designs, evolves them over generations, and converges to the Pareto front - the set of designs where you can't improve one objective without worsening the other.

---

## Slide 4: Methodology (30 sec)

The solver is OpenFOAM's rhoReactingBuoyantFoam - a transient compressible solver with buoyancy. Turbulence is handled by k-omega SST, which is the industry standard for internal pipe flows. We use a half-domain with symmetry at x equals zero, which cuts the mesh in half.

The main pipe is 0.46 metres diameter, 10 m/s methane flow, at 69 bar - realistic pipeline conditions. The branch injects pure hydrogen.

For the Design of Experiments, we used a sliced Latin Hypercube with 10 cases per campaign. The same sampling seed is used across all campaigns, so each case has a matched pair at the other angle - same geometry, same flow rates, only the angle differs. This lets us do rigorous paired comparisons.

The workflow goes: parametric STL generation, blockMesh plus snappyHexMesh for meshing, solver run, post-process for CoV and pressure drop, then feed into the surrogate model.

> **If asked "What is k-omega SST?"**: It's a two-equation RANS turbulence model by Menter. It solves transport equations for turbulent kinetic energy k and specific dissipation rate omega. "SST" means Shear Stress Transport - it blends k-omega near walls (which is accurate there) with k-epsilon in the freestream (which is more robust there).

> **If asked "Why half-domain?"**: The T-junction is symmetric about the vertical plane through the pipe axis. So we only simulate one half and apply a symmetry boundary condition. This halves the cell count from ~920k to ~460k, cutting runtime by roughly half.

> **If asked "What is Latin Hypercube?"**: It's a space-filling sampling method. You divide each variable's range into N equal bins, then place exactly one sample per bin in each dimension. Compared to random sampling, it guarantees you cover the full range of every variable even with few points. "Sliced" means we group cases by d/D so cases sharing the same branch diameter can reuse the same mesh.

---

## Slide 5: Mesh and Validation (20 sec)

Here's a typical mesh on the symmetry plane. You can see the boundary layers at the walls and the refinement near the junction where the jet enters. About 460k cells per half-domain.

Grid independence was checked at three levels - 230k, 460k, and 920k cells. Going from medium to fine changes CoV by only 0.2% and pressure drop by 0.7%, so the medium mesh is sufficient.

All 40 cases pass validation: continuity errors below 10 to the minus 2, residuals below 10 to the minus 8, mass balance within 0.5%, and no floating point exceptions.

> **If asked "What is non-orthogonality?"**: It's the angle between the line connecting two cell centres and the face normal vector between them. In a perfect hex mesh it's zero. High non-orthogonality (above 65-70 degrees) causes numerical errors. Ours is 49 degrees - well within limits.

---

## Slide 6: Results Walkthrough - Top Injection (20 sec)

This is Case 04 - a 90 degree top injection with velocity ratio 3.81. Six panels showing the full picture.

Panel (a) is the geometry, (b) is the mesh. Panel (c) is a 3D isosurface showing the hydrogen plume - you can see it spreads outward from the injection point. Panel (d) shows cross-sections at different downstream distances - by z equals 5 metres, the mixture is nearly uniform. Panel (e) is the outlet face - very uniform distribution. And panel (f) is the CoV versus distance plot - CoV drops from 0.70 near the junction to 0.063 at the outlet, well below the 0.05 industrial target.

---

## Slide 7: Same Case - Bottom Injection (25 sec)

Now the exact same case - same angle, same diameter ratio, same velocity ratio - but with the branch moved to the bottom of the pipe.

The isosurface in panel (a) tells the whole story. Instead of spreading laterally, the hydrogen rises as a narrow column and collects at the crown. The cross-sections in (b) show a persistent bright streak at the top all the way to the outlet. The outlet in (c) still has a strong concentration gradient. CoV is 0.271 - four times worse than top injection.

Across all 17 matched pairs we tested, top injection wins every single time, with a p-value of 1.5 times 10 to the minus 5. Median CoV degradation going from top to bottom is 109% at 90 degrees and 324% at 30 degrees. And the pressure drop is the same - so top injection is strictly better.

> **If asked "Why does top injection work better?"**: With top injection, buoyancy opposes the jet. The H2 tries to rise but the jet pushes it down. This flattens it into a thin, wide layer with a large surface area for turbulent diffusion. With bottom injection, buoyancy assists the jet - H2 rises as a coherent narrow column with much less surface area, so mixing is poor.

---

## Slide 8: Velocity Ratio Effect (20 sec)

These two strip plots compare Case 03 and Case 04 - same pipe, same 90-degree angle, same branch diameter. The only difference is VR.

At VR = 1.33, the hydrogen hugs the crown of the pipe. The dark regions at the bottom are unmixed methane. CoV is 0.472.

Triple the velocity ratio to 3.81, and the jet penetrates past the centreline. By z equals 5 metres, the cross-section is nearly uniform. CoV drops to 0.066 - a factor of 7 improvement. VR is the single strongest lever on mixing quality.

---

## Slide 9: Angle Effect (20 sec)

Same comparison, but now we hold the design point fixed and change the angle. Same d/D, same VR, same HBR - only the angle differs.

At 90 degrees, Case 06 has CoV = 0.202 with vertical streaks persisting to the outlet. At 30 degrees, same case, CoV drops to 0.088 - the teardrop plume at z equals 3 metres homogenises completely by z equals 5.

Across all 7 matched pairs, the median CoV drops 46% and the median pressure drop drops 63%. Both are statistically significant.

---

## Slide 10: Power-Law Scaling (20 sec)

Plotting CoV versus VR on a log-log scale reveals a clean power-law relationship for all four campaigns.

The key number is the exponent. For 30-degree top injection, the exponent is minus 1.88 - nearly twice as steep as the minus 1.16 for 90-degree top. Each unit of VR buys nearly twice as much mixing improvement on the tilted geometry.

Bottom injection exponents are shallower - buoyancy limits how much mixing VR can achieve.

> **If asked "Why power-law?"**: In jet mixing theory, the centreline concentration decay follows a power law with distance. Since VR controls the jet penetration depth, and CoV depends on how well the jet fills the pipe cross-section, a power-law relationship between CoV and VR is physically expected.

---

## Slide 11: Pareto Front (15 sec)

The Pareto plot puts everything together. 30-degree top injection points sit in the desirable lower-left corner - low CoV and low pressure drop.

Best mixing: Case 01 at 30 degrees top achieves CoV of 0.005 - essentially perfect mixing. Cheapest operation: Case 09 at just 0.3 kPa pressure drop. Every 90-degree point is dominated by some 30-degree point.

---

## Slide 12: Physical Mechanism (20 sec)

Two synergistic effects explain these results.

First, the tilt effect. At 90 degrees, the jet hits the opposite wall head-on and splits, trapping a low-H2 core. At 30 degrees, the jet momentum is partially aligned with the main flow, creating a long streamwise shear layer that entrains methane continuously. This also means less turning loss, so pressure drop is lower.

Second, the buoyancy effect. Top injection: buoyancy opposes the jet, flattening hydrogen into a thin wide layer - large interfacial area for diffusion. Bottom injection: buoyancy assists the jet, creating a narrow rising column - small interfacial area, poor mixing.

---

## Slide 13: Surrogate Model (20 sec)

We trained four ML models on the 40 CFD cases. GPR - Gaussian Process Regression with a Matern 5/2 kernel - gives the best CoV prediction with R-squared of 0.925.

The DNN with 17,000 parameters overfits badly at only 40 training points. Random Forest and Gradient Boosting fall in between.

For pressure drop, all models struggle because the acoustic noise from the compressible solver is 10 to 25 kPa, while the actual flow-loss signal is only 1 to 3 kPa. Fixing this requires either a steady-state solver or much longer transients.

> **If asked "What is GPR?"**: Gaussian Process Regression is a Bayesian non-parametric model. It places a prior distribution over functions (defined by a kernel/covariance function) and updates it with the training data to get a posterior. The Matern 5/2 kernel is a common choice - it assumes the underlying function is twice differentiable. GPR naturally provides uncertainty estimates, which is valuable with only 40 data points.

> **If asked "Why does DNN overfit?"**: The DNN has ~17,400 trainable parameters but only 40 training samples. That's a 435:1 parameter-to-sample ratio. The network has more than enough capacity to memorise the training data perfectly without learning the underlying trends. GPR, being non-parametric, adapts its effective complexity to the data size.

---

## Slide 14: NSGA-II Optimisation (15 sec)

We ran NSGA-II on the GPR surrogate with 200 population size over 150 generations.

The top injection knee point is at 30 degrees, d/D of 0.45, VR of 5.82 - predicted CoV around 0.089 at only 0.14 kPa pressure drop. Both knee points maximise VR, which is consistent with the SHAP feature importance analysis showing injection side and VR as the two dominant features.

---

## Slide 15: Limitations and Future Work (15 sec)

Main limitations: the pressure drop surrogate is unreliable due to acoustic noise, we only tested two angles, and 40 cases aren't enough for the DNN.

Next steps: expand to 300 cases covering 5 angles, 3 diameter ratios, and 2 injection sides. Fix the pressure drop prediction using steady-state RANS. Then build the full angular Pareto map.

---

## Slide 16: Conclusions (20 sec)

To summarise. This is the first multi-objective CFD study of hydrogen T-junction injection with angle as a design variable. 30-degree top injection dominates everything else - 46% lower CoV, 63% lower pressure drop. Top injection is strictly superior to bottom in all 17 matched pairs. Buoyancy is the key mechanism. And the GPR surrogate at R-squared 0.93 enables real-time design exploration. All code and data are on GitHub.

---

## Slides 17-19: Case Structure, BCs, References (quick flip, 10 sec)

These backup slides show the full OpenFOAM case directory structure, boundary conditions for every field, and the key references. They're here for reference during questions.

---

## Slide 20: Thank You (5 sec)

Thank you. Happy to take questions.

---

# Concept Clarifications (for Q&A preparation)

## What is CoV and why use it?
CoV = standard deviation / mean of H2 mass fraction at the outlet. It's dimensionless and independent of the blend ratio, so you can compare cases with different HBR directly. CoV = 0 is perfect mixing, CoV = 1 is completely unmixed. The industrial target is CoV < 0.05.

## What is rhoReactingBuoyantFoam?
It's an OpenFOAM solver for transient, compressible, buoyant flows with multiple species. "rho" means density-based (compressible), "Reacting" means it can handle species transport (though we disabled reactions), "Buoyant" means it accounts for gravity-driven density differences. It solves the Navier-Stokes equations coupled with species transport and an equation of state.

## What is the PIMPLE algorithm?
It's OpenFOAM's pressure-velocity coupling method for transient simulations. It combines PISO (Pressure Implicit with Splitting of Operators) and SIMPLE (Semi-Implicit Method for Pressure-Linked Equations). In our setup with 1 outer corrector, it's effectively PISO mode: predict velocity, correct pressure twice per time step.

## What is snappyHexMesh?
OpenFOAM's automatic mesh generator. It starts with a uniform hex background mesh (from blockMesh), then: (1) removes cells outside the geometry, (2) refines cells near important features, (3) snaps the mesh vertices onto the STL surface, (4) adds prismatic boundary layers at walls. The result is a predominantly hex mesh with some polyhedral cells near complex surfaces.

## Why first-order upwind for convection?
It's a deliberate trade-off for a DoE screening study. First-order upwind introduces numerical diffusion (~5-10% effect on CoV) but guarantees stable convergence for all 40 cases. Since all cases use the same scheme, the comparison is fair. A second-order scheme (linearUpwind) would be more accurate but risks oscillations near the sharp H2 jet interface, potentially causing some cases to diverge.

## What is the acoustic noise problem?
The compressible solver captures real acoustic pressure waves bouncing between the fixed-velocity inlet and fixed-pressure outlet. These waves have ~25 kPa amplitude, but the actual pressure drop from flow losses is only ~1-3 kPa. It's like trying to measure a 1 cm water level change while 25 cm waves are sloshing around. We apply a low-pass filter (100 ms moving average) to extract the steady-state signal, but the residual noise still makes ΔP hard to predict with ML.

## What is a matched pair and why is it important?
A matched pair means two CFD cases that share the exact same d/D, HBR, and VR - the only difference is the variable being tested (angle or injection side). Because everything else is controlled, any difference in CoV or ΔP can be attributed to that one variable. This is like a controlled experiment. We use matched pairs to make statements like "30 degree beats 90 degree in all 7 pairs" with statistical confidence (binomial test p = 0.008).

## How does the symmetry half-domain work?
The T-junction is symmetric about the vertical plane (x = 0) through the pipe centreline. We only mesh and simulate the x >= 0 half, with a symmetryPlane boundary condition at x = 0 (which enforces: normal velocity = 0, zero normal gradient for all other fields). This halves the cell count and runtime. For visualisation, we mirror the results back to the full circle.

## What is the 1/7th power-law inlet profile?
Instead of uniform velocity at the inlets, we use u(r) = u_max * (1 - (2r/D)^2)^(1/7), which approximates a fully-developed turbulent pipe profile. This avoids an unphysical entrance effect where a flat profile develops into a turbulent profile, which would contaminate the first few diameters of the pipe. The 1/7th power law is a standard approximation valid for Re > 10^5.

## What is a Pareto front?
In multi-objective optimisation, a Pareto front is the set of solutions where you cannot improve one objective without worsening another. Every point on the front is "non-dominated" - no other point is better in ALL objectives simultaneously. Points below and to the left (in our CoV vs ΔP plot) are better. The "knee point" is the solution closest to the ideal (utopia) point where both objectives are at their minimum - it represents the best compromise.

## Why GPR and not DNN?
With only 40 training samples, GPR has three advantages: (1) it doesn't overfit because its complexity adapts to the data, (2) it provides uncertainty estimates (confidence intervals on predictions), and (3) the Matern 5/2 kernel imposes smoothness assumptions appropriate for physical systems. The DNN's 17,400 parameters give it too much capacity for 40 points - it memorises rather than generalises (R^2 = 0.735 on cross-validation vs 0.925 for GPR).
