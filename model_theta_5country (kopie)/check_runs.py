#!/usr/bin/env python3
# ============================================================================
#  check_runs.py — did every run in the sweep actually finish?
#
#  Run it with the SAME env you gave run_trimmed.sh, e.g.:
#       NCYCLE=1000 python3 check_runs.py
#  (reads NCYCLE, NSEEDS, LAMBDAS, RUNDIR; defaults match run_trimmed.sh)
#
#  Classifies each expected (tag, seed) run as:
#    completed  - reached the final period t = NCYCLE-1, rows rectangular
#    halted     - stopped early (public-debt/Y breaker; graceful exit 0)  [not an error]
#    missing    - no AggData.csv produced                                  [error]
#    corrupt    - ragged columns or short-written final period            [error]
#  Exit code 0 unless something is missing or corrupt.
# ============================================================================
import glob, csv, os, sys

RUNDIR  = os.environ.get("RUNDIR", "./runs")
NCYCLE  = int(os.environ.get("NCYCLE", 1000))
NSEEDS  = int(os.environ.get("NSEEDS", 12))
LAMBDAS = os.environ.get("LAMBDAS", "1.0 0.5 0.3 0.1").split()
C_TIME, C_CTRY = 1, 2
LAST = NCYCLE - 1

def scan(path):
    mx=-1; n=0; ctry=set(); ncols=set()
    try:
        for r in csv.reader(open(path)):
            if not r: continue
            ncols.add(len(r))
            try: t=float(r[C_TIME]); c=int(float(r[C_CTRY]))
            except: continue          # header row
            if t>mx: mx=t
            ctry.add(c); n+=1
    except Exception:
        return None
    if n==0: return None
    return int(mx), n, len(ctry), (len(ncols)==1)

expected=[]
for L in LAMBDAS:
    t=L.replace('.','')
    for arm in ("rel","ctrl"):
        for s in range(NSEEDS):
            expected.append((f"E2_{arm}_L{t}", s))

completed=[]; halted=[]; missing=[]; corrupt=[]
for tag,s in expected:
    fs=[f for f in glob.glob(os.path.join(RUNDIR, f"{tag}_s{s}_*", "*AggData.csv"))
        if not os.path.basename(f).startswith("._")]
    if not fs: missing.append((tag,s)); continue
    info=scan(fs[0])
    if info is None: corrupt.append((tag,s,"empty/unreadable")); continue
    mx,n,nc,rect=info
    if (not rect) or (nc>0 and n!=(mx+1)*nc):
        corrupt.append((tag,s,f"maxT={mx}, rows={n}, countries={nc}")); continue
    (completed if mx>=LAST else halted).append((tag,s) if mx>=LAST else (tag,s,mx))

E=len(expected); found=E-len(missing)
print(f"=== run completion check: {RUNDIR}   (NCYCLE={NCYCLE}, full length = t reaches {LAST}) ===")
print(f"expected runs: {E}    found: {found}")
print(f"  completed all {NCYCLE} periods : {len(completed)}")
print(f"  halted early (debt breaker)   : {len(halted)}")
print(f"  missing                       : {len(missing)}")
print(f"  corrupt / short-written       : {len(corrupt)}")
if halted:
    print("  -- halted early (graceful exit 0; reached t):")
    for tag,s,mx in sorted(halted): print(f"       {tag} seed {s}: t->{mx}")
if missing:
    print("  -- MISSING:")
    for tag,s in sorted(missing): print(f"       {tag} seed {s}")
if corrupt:
    print("  -- CORRUPT:")
    for tag,s,why in sorted(corrupt): print(f"       {tag} seed {s}: {why}")
ok=(not missing) and (not corrupt)
if ok and not halted:
    print(f"\nVERDICT: all {found} runs finished and reached full length ({NCYCLE} periods).")
elif ok:
    print(f"\nVERDICT: all {found} runs intact; {len(halted)} hit the debt breaker before t={LAST} (by design, not a failure).")
else:
    print(f"\nVERDICT: PROBLEM — {len(missing)} missing, {len(corrupt)} corrupt. Re-run those seeds.")
sys.exit(0 if ok else 1)
