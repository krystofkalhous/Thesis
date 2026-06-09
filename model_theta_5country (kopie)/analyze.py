#!/usr/bin/env python3
# ============================================================================
#  analyze.py — de-confounded ensemble analysis for run_experiments.sh output
#
#  Run from the same folder, after the experiments finish:   python3 analyze.py
#
#  Core idea (do not skip): compare country 0 to the mean of countries 1-4
#  WITHIN each run, then DE-CONFOUND by subtracting the all-transaction control
#  at the same lambda (c0's raw position is itself favourable at low lambda).
#  Relationship effect = mean_seeds[config: c0-vs-c1..4] - mean_seeds[control].
#  CIs are bootstrapped over seeds. Single seeds are noise; this is why.
# ============================================================================
import glob, csv, os, math, random, statistics as st
random.seed(0)
RUNDIR = os.environ.get("RUNDIR", "./runs")

# ---- AggData column indices (0-based) ----
C_TIME, C_CTRY, C_NF, C_AVPHI, C_NBANK, C_BANKLOAN, C_PRODQ = 1, 2, 6, 9, 11, 15, 55
METRICS = [("output", C_PRODQ), ("avPhi", C_AVPHI), ("nFirm", C_NF)]

def percountry(path, w0, w1):
    d = {}
    for r in csv.reader(open(path)):
        try: c=int(float(r[C_CTRY])); t=float(r[C_TIME])
        except: continue
        if not (w0<=t<=w1): continue
        d.setdefault(c, {m:[] for m,_ in METRICS})
        try:
            for m,idx in METRICS: d[c][m].append(float(r[idx]))
        except: pass
    return {c:{m:st.mean(v[m]) for m,_ in METRICS} for c,v in d.items() if v[METRICS[0][0]]}

def within_run(path, w0, w1):
    """c0 relative to mean(c1-4), in %, per metric."""
    D = percountry(path, w0, w1)
    if 0 not in D or len(D) < 2: return None
    out = {}
    for m,_ in METRICS:
        others = st.mean([D[c][m] for c in D if c!=0])
        out[m] = 100.0*(D[0][m]/others - 1.0) if others else float('nan')
    return out

def load_tag(tag, w0=80, w1=290):
    files = sorted(glob.glob(os.path.join(RUNDIR, tag+"_s*", "*r*AggData.csv")))
    rows = [within_run(f, w0, w1) for f in files]
    rows = [r for r in rows if r]
    return rows  # list (over seeds) of {metric: c0-vs-c1..4 %}

def mean_ci(vals, B=3000):
    if not vals: return (float('nan'),)*3
    m = st.mean(vals)
    bs = sorted(st.mean([random.choice(vals) for _ in vals]) for _ in range(B))
    return m, bs[int(0.025*B)], bs[int(0.975*B)]

def diff_ci(a, b, B=3000):
    """relationship effect = mean(a)-mean(b), bootstrap 95% CI (independent samples)."""
    if not a or not b: return (float('nan'),)*3
    d = st.mean(a)-st.mean(b)
    bs = sorted(st.mean([random.choice(a) for _ in a]) - st.mean([random.choice(b) for _ in b]) for _ in range(B))
    return d, bs[int(0.025*B)], bs[int(0.975*B)]

def col(rows, m): return [r[m] for r in rows]

def report_effect(cfg_tag, ctrl_tag, label, w=(80,290)):
    cfg, ctrl = load_tag(cfg_tag,*w), load_tag(ctrl_tag,*w)
    if not cfg or not ctrl:
        print(f"  [{label}] missing data (cfg n={len(cfg)}, ctrl n={len(ctrl)})"); return
    print(f"  [{label}]  (config n={len(cfg)} seeds, control n={len(ctrl)} seeds)")
    for m,_ in METRICS:
        d,lo,hi = diff_ci(col(cfg,m), col(ctrl,m))
        star = "" if (lo<=0<=hi) else "  *"   # CI excludes 0
        print(f"      relationship effect on {m:<7}: {d:+6.2f}pp   95% CI [{lo:+.2f}, {hi:+.2f}]{star}")

def have(tag): return bool(glob.glob(os.path.join(RUNDIR, tag+"_s*")))

print(f"=== analysis of {RUNDIR} ===  (* = 95% CI excludes zero)\n")

# ---- E1: core anchor -------------------------------------------------------
if have("E1_relTh"):
    print("E1  CORE ANCHOR  (lambda=0.3): relationship+theta vs all-transaction control")
    report_effect("E1_relTh", "E1_ctrl", "lambda=0.3")
    print()

# ---- E2: lambda sweep ------------------------------------------------------
if have("E2_rel_L03"):
    print("E2  LAMBDA SWEEP: relationship effect by lambda (does output tip positive?)")
    for L,t in [("1.0","10"),("0.5","05"),("0.3","03"),("0.1","01")]:
        report_effect(f"E2_rel_L{t}", f"E2_ctrl_L{t}", f"lambda={L}")
    print()

# ---- E3: rotation ----------------------------------------------------------
if have("E3_relC0"):
    print("E3  ROTATION (lambda=0.3): relationship effect with the rel-bank in each country")
    print("    (consistent sign across countries => not an artifact of country-0's position)")
    for C in range(5):
        report_effect(f"E3_relC{C}", "E3_ctrl", f"rel bank in country {C}")
    print()

# ---- E5: lever sweeps ------------------------------------------------------
if have("E5_kappa05"):
    ctrl = "E1_ctrl" if have("E1_ctrl") else "E3_ctrl"
    print(f"E5  LEVER SWEEPS (lambda=0.3, control={ctrl})")
    print("  selection exclusivity (GAP_KAPPA; higher = more exclusive):")
    for K,t in [("0.0","00"),("0.25","025"),("0.5","05"),("1.0","10")]:
        if have(f"E5_kappa{t}"): report_effect(f"E5_kappa{t}", ctrl, f"kappa={K}")
    print("  lending capacity / retention (REL_PAYOUT; lower = retain more):")
    for P,t in [("0.0","00"),("0.2","02"),("0.5","05"),("0.95","095")]:
        if have(f"E5_pay{t}"): report_effect(f"E5_pay{t}", ctrl, f"payout={P}")
    print()

# ---- E4: corr(theta, phi) across lambda (per-firm dumps) --------------------
def firm_corr(tag, w0=100, w1=150):
    files = sorted(glob.glob(os.path.join(RUNDIR, tag+"_s*", "*r*Firm.csv")))
    rel_th=[]; rel_phi=[]; txn_th=[]; txn_phi=[]
    for f in files:
        rd = csv.reader(open(f)); hdr = next(rd, None)
        if not hdr: continue
        try:
            it,ic,ip,ith = hdr.index('time'),hdr.index('country'),hdr.index('phi'),hdr.index('thetaType')
        except ValueError:
            it,ic,ip,ith = 2,3,4,16
        for r in rd:
            try: t=float(r[it]); c=int(float(r[ic])); phi=float(r[ip]); th=float(r[ith])
            except: continue
            if not (w0<=t<=w1): continue
            (rel_th if c==0 else txn_th).append(th); (rel_phi if c==0 else txn_phi).append(phi)
    def corr(x,y):
        if len(x)<3: return float('nan')
        mx,my=st.mean(x),st.mean(y)
        cov=sum((a-mx)*(b-my) for a,b in zip(x,y))
        sx=math.sqrt(sum((a-mx)**2 for a in x)); sy=math.sqrt(sum((b-my)**2 for b in y))
        return cov/(sx*sy) if sx*sy else float('nan')
    return corr(rel_th,rel_phi), corr(txn_th,txn_phi)

if have("E4_corr_L03"):
    print("E4  corr(theta, phi) ACROSS LAMBDA  (footprint of the latent type; window t[100,150])")
    print(f"    {'lambda':>7} | {'c0 (relationship)':>18} | {'c1-4 (transaction)':>19}")
    for L,t in [("1.0","10"),("0.5","05"),("0.3","03"),("0.1","01")]:
        if have(f"E4_corr_L{t}"):
            cr,ct = firm_corr(f"E4_corr_L{t}")
            print(f"    {L:>7} | {cr:>18.3f} | {ct:>19.3f}")
    print()

print("Reading: a positive 'relationship effect on output' with a CI excluding 0 would mean")
print("relationship banking RAISES the relationship country's output. The session found this")
print("effect ~0 at lambda=0.3 (productivity +, output flat); these ensembles put CIs on it.")
