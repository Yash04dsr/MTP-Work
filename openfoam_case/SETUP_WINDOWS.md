# OpenFOAM Setup on Windows 11 via Moonlight (Remote-Safe)

**Machine:** Intel i7-14700 (20 cores, 28 threads), 64 GB RAM, Windows 11 Pro  
**Access:** Moonlight game streaming (remote — sessions can drop)

> **Golden rule:** Every long-running command uses `tmux` or `nohup`
> so that Moonlight disconnects, screen-off, or network drops do NOT
> kill the simulation. You reconnect and pick up exactly where it was.

---

## Part A: One-Time Setup (15-20 minutes)

### A1. Install WSL2

Open **PowerShell as Administrator** (right-click Start → Terminal (Admin)):

```powershell
wsl --install -d Ubuntu-24.04
```

**Restart the PC** when prompted.  After reboot, Ubuntu will open
automatically.  Create a username and password (keep it simple, e.g.
your first name + "123").

Verify:

```powershell
wsl --list --verbose
```

You should see `Ubuntu-24.04` with VERSION **2**.

### A2. Configure WSL2 for your hardware

Open **Notepad** and paste this:

```ini
[wsl2]
memory=56GB
processors=20
swap=8GB
```

Save as:  `C:\Users\YOUR_USERNAME\.wslconfig`  
(Replace YOUR_USERNAME with your actual Windows username.)

Then in PowerShell:

```powershell
wsl --shutdown
```

Open Ubuntu again from the Start menu.

### A3. Install OpenFOAM + tools inside Ubuntu

Open the **Ubuntu** app and run these blocks one at a time.  Copy-paste
each block, wait for it to finish, then do the next:

**Block 1 — System update:**
```bash
sudo apt update && sudo apt upgrade -y
```

**Block 2 — Add OpenFOAM repo and install:**
```bash
curl -s https://dl.openfoam.com/add-debian-repo.sh | sudo bash
sudo apt install -y openfoam2406
```

**Block 3 — Install tmux, Python, and utilities:**
```bash
sudo apt install -y tmux python3-pip python3-numpy htop
pip3 install --break-system-packages numpy-stl
```

**Block 4 — Make OpenFOAM load automatically:**
```bash
echo 'source /usr/lib/openfoam/openfoam2406/etc/bashrc' >> ~/.bashrc
source ~/.bashrc
```

**Block 5 — Verify everything works:**
```bash
blockMesh -help 2>&1 | head -1
rhoReactingBuoyantFoam -help 2>&1 | head -1
python3 -c "from stl import mesh; print('numpy-stl OK')"
echo "ALL GOOD"
```

If you see version info for both solvers and "ALL GOOD", setup is done.

---

## Part B: Copy Case Files (5 minutes)

### B1. Transfer case to your Windows PC

Copy the `openfoam_case` folder from this Mac to your Windows PC.
Use any method:
- USB drive
- OneDrive / Google Drive
- AirDrop to iPhone → share to PC
- `scp` if you have SSH set up

Place it on your Desktop, e.g. `C:\Users\YOUR_USERNAME\Desktop\openfoam_case`

### B2. Copy into WSL2 Linux filesystem

**This is critical — never run OpenFOAM from /mnt/c/.  It is 10x slower.**

In the Ubuntu terminal:

```bash
cp -r "/mnt/c/Users/YOUR_USERNAME/Desktop/openfoam_case" ~/openfoam_case
cd ~/openfoam_case
ls
```

You should see: `0/  Allclean  Allrun  constant/  generateSTL.py  system/`

---

## Part C: Mesh Generation and Test (30 minutes)

### C1. Start a tmux session

**This is the key step for Moonlight safety.** Everything inside tmux
survives disconnects.

```bash
tmux new -s cfd
```

You are now inside a tmux session named "cfd". The green bar at the
bottom confirms this.

> **If Moonlight disconnects:** reconnect, open Ubuntu, type:
> `tmux attach -t cfd` — you're right back where you were.

### C2. Generate STL and build mesh

```bash
cd ~/openfoam_case

# Generate geometry
python3 generateSTL.py

# Build background mesh
blockMesh

# Extract features
surfaceFeatureExtract

# Build conformal mesh (takes 10-30 min)
snappyHexMesh -overwrite

# Verify mesh quality
checkMesh 2>&1 | tail -20
```

**What to check in checkMesh output:**
- `Mesh OK.` at the end = good
- Cell count should be 2.5-5.0 million
- If it says `***` errors, do not proceed — come back and tell me

### C3. Patch initial conditions

```bash
setFields
```

### C4. Quick test run (5 minutes, catches errors early)

```bash
# Temporarily set short run
cp system/controlDict system/controlDict.backup
sed -i 's/^endTime.*/endTime         0.05;/' system/controlDict

# Run on 1 core (serial, no decompose needed)
rhoReactingBuoyantFoam 2>&1 | tee log.test

# Check results
echo "---"
echo "Last 10 lines of log:"
tail -10 log.test
echo "---"
grep -i "error\|fatal\|exception" log.test && echo "ERRORS FOUND" || echo "NO ERRORS - TEST PASSED"
```

If it says "NO ERRORS - TEST PASSED" and you see residuals dropping
in the log, the setup is working.

**Restore the original controlDict:**
```bash
mv system/controlDict.backup system/controlDict
```

---

## Part D: Full Production Run (6-10 hours)

### D1. Clean the test run

```bash
cd ~/openfoam_case
rm -rf 0.* [1-9]* processor* log.test
```

### D2. Decompose for parallel

```bash
decomposePar
```

### D3. Launch the simulation (disconnect-safe)

**Still inside tmux** (check for the green bar at the bottom).

```bash
nohup mpirun -np 16 rhoReactingBuoyantFoam -parallel \
    > log.rhoReactingBuoyantFoam 2>&1 &

echo "Solver running in background with PID: $!"
```

**What this does:**
- `nohup` = survives terminal close
- `&` = runs in background
- `> log.rhoReactingBuoyantFoam` = all output goes to a file
- Even if tmux dies, even if WSL restarts, the process continues

### D4. Monitor progress

You can safely disconnect from Moonlight now.  When you reconnect:

```bash
# Reconnect to tmux
tmux attach -t cfd

# See live progress
tail -f ~/openfoam_case/log.rhoReactingBuoyantFoam

# Press Ctrl+C to stop watching (does NOT stop the simulation)
```

**Useful monitoring commands:**

```bash
# How many time steps completed?
ls ~/openfoam_case/processor0/ | grep -E '^[0-9]' | wc -l

# Current simulation time
ls ~/openfoam_case/processor0/ | grep -E '^[0-9]' | sort -g | tail -1

# Is it still running?
ps aux | grep rhoReacting

# CPU usage (all 16 cores should be busy)
htop
```

### D5. How to tell when it is done

The simulation is complete when:
- `grep "End" log.rhoReactingBuoyantFoam` shows "End"
- OR the latest time directory is `5` (i.e. 5 seconds simulated)

---

## Part E: Post-Processing (20 minutes)

### E1. Reconstruct parallel results

```bash
cd ~/openfoam_case
reconstructPar
```

### E2. Check key results

```bash
# Outlet H2 mass fraction over time
cat postProcessing/outletH2/0/surfaceFieldValue.dat | tail -20

# Mass balance
echo "=== Outlet ==="
tail -1 postProcessing/outletMassFlow/0/surfaceFieldValue.dat
echo "=== Main inlet ==="
tail -1 postProcessing/mainInletMassFlow/0/surfaceFieldValue.dat
echo "=== Branch inlet ==="
tail -1 postProcessing/branchInletMassFlow/0/surfaceFieldValue.dat

# Wall probe H2 (top vs bottom at z/d1=4)
echo "=== Wall probes ==="
tail -5 postProcessing/wallH2Probes/0/H2
```

### E3. Open ParaView

Windows 11 WSLg supports GUI apps:

```bash
paraFoam &
```

If ParaView doesn't open (Moonlight sometimes blocks WSLg), copy
results to Windows and use ParaView for Windows:

```bash
cp -r ~/openfoam_case /mnt/c/Users/YOUR_USERNAME/Desktop/openfoam_results
```

Then download ParaView from https://www.paraview.org/download/ on
Windows, and open the case from Desktop.

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Open tmux | `tmux new -s cfd` |
| Reconnect after disconnect | `tmux attach -t cfd` |
| Check if solver is running | `ps aux \| grep rhoReacting` |
| Watch live log | `tail -f ~/openfoam_case/log.rhoReactingBuoyantFoam` |
| Stop watching (NOT the solver) | `Ctrl+C` |
| Current sim time | `ls ~/openfoam_case/processor0/ \| sort -g \| tail -1` |
| Kill the solver (emergency) | `pkill -f rhoReacting` |
| CPU monitor | `htop` |
| Copy results to Windows | `cp -r ~/openfoam_case /mnt/c/Users/YOU/Desktop/results` |

---

## Troubleshooting

### Moonlight disconnected mid-run
No problem. Reconnect → open Ubuntu → `tmux attach -t cfd`.
The solver keeps running in the background regardless.

### WSL2 closed / PC rebooted
The solver will have stopped. Check the last completed time step:
```bash
ls ~/openfoam_case/processor0/ | sort -g | tail -1
```
Then restart from that time:
```bash
cd ~/openfoam_case
# Edit system/controlDict: set startFrom to latestTime
sed -i 's/^startFrom.*/startFrom       latestTime;/' system/controlDict
nohup mpirun -np 16 rhoReactingBuoyantFoam -parallel \
    >> log.rhoReactingBuoyantFoam 2>&1 &
```

### "codedFixedValue" won't compile
```bash
sudo apt install -y openfoam2406-default build-essential
```

### Solver diverges (residuals explode)
Halve the time step temporarily:
```bash
sed -i 's/^deltaT.*/deltaT          1e-4;/' system/controlDict
```
The solver picks this up automatically (runTimeModifiable is on).
After 1000 steps, restore: `sed -i 's/^deltaT.*/deltaT          2e-4;/' system/controlDict`

### PC goes to sleep during the run
Prevent this: Windows Settings → System → Power → Screen and sleep →
set "When plugged in, put my device to sleep after" → **Never**.
