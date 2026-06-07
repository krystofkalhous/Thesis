#!/usr/bin/env python3
"""
run_experiments.py  —  relationship vs transaction lenders in a monetary union,
                       with the IPS-style relationship-bank protection FUND.

Configurations (per-country regional-bank toggle RB_Cn; 1 = relationship lenders present):
  union   : country 0 relationship, country 1 transaction   (RB_C0=1 RB_C1=0)
  allRel  : both countries relationship                      (RB_C0=1 RB_C1=1)
  allTxn  : both transaction-only (no regional banks)        (RB_C0=0 RB_C1=0)

The fund sweep varies THREE new dials (read by parameter.py from the environment):
  FUND_CONTRIB  gamma_base  : baseline fraction of retained surplus contributed
  FUND_CCYC     theta       : countercyclical strength (contribution rises in a boom)
  RECAP_KAPPA   kappa       : recap target = kappa * viability floor

For every (config, fund-setting, seed) this launches an isolated `python timing.py`
subprocess. A fund-OFF control arm (FUND_ON=0) is ALWAYS included so each treatment cell
has a like-for-like baseline. Each cell gets a distinct CONFIG_TAG, so output folders
never collide and act as your stale-file guard.

The fund experiments were validated with --no-lock (the relationship reserve LOCK is a
separate, disproven feature; turning it off isolates the fund). Override with --lock.

A run that raises an SFC AssertionError exits non-zero -> reported FAILED with stderr tail.
A run whose AggData ends before full length HALTED on the debt breaker (initialize.py
debtExplotionBreak) -> that is your per-seed divergence signal, summarised at the end.

Two phases (either or both):
  RUN       : --first-seed/--last-seed etc. launch the grid.
  SUMMARISE : --summarize reads the output folders and prints, per (config, fund-setting):
              divergence rate (fraction of seeds halted), mean/median maxNFirm,
              mean maxLoanReg, and fund recycle% / recaps / failed recaps.

Examples:
  # Full production sweep on a Mac, all 11 seeds, full length (ncycle from parameter.py):
  python run_experiments.py --configs allRel union --first-seed 0 --last-seed 10 \
      --fund-contrib 0.1 0.25 0.5 0.75 --fund-ccyc 0 2 5 --recap-kappa 1.5 2.0 \
      --workers 8 --no-lock \
      --output-base /Users/you/Desktop/OUTPUT_fund/ --model-dir /path/to/model

  # Then summarise:
  python run_experiments.py --summarize --output-base /Users/you/Desktop/OUTPUT_fund/ \
      --ncycle 1001
"""

import argparse
import concurrent.futures as cf
import csv
import glob
import os
import re
import subprocess
import sys
import time

CONFIGS = {
    "union":  {"RB_C0": "1", "RB_C1": "0"},
    "allRel": {"RB_C0": "1", "RB_C1": "1"},
    "allTxn": {"RB_C0": "0", "RB_C1": "0"},
}

# AggData column indices (0-based) used by the summary
COL_TIME, COL_COUNTRY, COL_NFIRM, COL_LOANREG = 1, 2, 6, 72
# FundData column indices (0-based)
F_TIME, F_COUNTRY, F_RES, F_IN, F_OUT, F_NRECAPTOT, F_NRECAPFAIL = 0, 1, 2, 3, 4, 8, 9


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--configs", nargs="+", default=["allRel", "union"],
                   choices=list(CONFIGS), help="configs to run (default: allRel union)")
    p.add_argument("--first-seed", type=int, default=0)
    p.add_argument("--last-seed", type=int, default=10, help="inclusive")
    p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    p.add_argument("--payout", type=float, default=0.20,
                   help="relationship-bank payout fraction (REL_PAYOUT); rest retained")
    p.add_argument("--lock", dest="lock", action="store_true", default=False,
                   help="lock relationship retained reserves (default OFF for fund runs)")
    p.add_argument("--no-lock", dest="lock", action="store_false")
    p.add_argument("--devolution", choices=["owners", "successor"], default="owners")
    # --- fund sweep dials (each takes a list -> cartesian grid) ---
    p.add_argument("--fund-contrib", nargs="+", type=float, default=[0.25, 0.5],
                   help="gamma_base grid (FUND_CONTRIB)")
    p.add_argument("--fund-ccyc", nargs="+", type=float, default=[0.0, 3.0],
                   help="theta grid (FUND_CCYC)")
    p.add_argument("--recap-kappa", nargs="+", type=float, default=[2.0],
                   help="kappa grid (RECAP_KAPPA)")
    p.add_argument("--no-fund-off-control", dest="fund_off_control",
                   action="store_false", default=True,
                   help="omit the FUND_ON=0 control arm (kept by default)")
    p.add_argument("--norecap-arm", action="store_true", default=False,
                   help="for each fund cell, also run a recap-OFF variant "
                        "(contributions drain but no rescues) — the decoupling arm")
    p.add_argument("--ncycle", type=int, default=None,
                   help="override NCYCLE (also the 'full length' threshold for SUMMARISE)")
    p.add_argument("--output-base", default=None)
    p.add_argument("--model-dir", default=".")
    p.add_argument("--python", default=sys.executable)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--summarize", action="store_true",
                   help="skip running; parse --output-base folders and print summary")
    return p.parse_args()


def fund_settings(args):
    """List of (tag, env-dict) fund cells; first is the off control if enabled."""
    cells = []
    if args.fund_off_control:
        cells.append(("fundoff", {"FUND_ON": "0"}))
    for k in args.recap_kappa:
        for cc in args.fund_ccyc:
            for g in args.fund_contrib:
                tag = "fund_g%s_cc%s_k%s" % (g, cc, k)
                cells.append((tag, {"FUND_ON": "1", "FUND_CONTRIB": str(g),
                                    "FUND_CCYC": str(cc), "RECAP_KAPPA": str(k)}))
                if args.norecap_arm:
                    cells.append((tag + "_norecap",
                                  {"FUND_ON": "1", "FUND_CONTRIB": str(g),
                                   "FUND_CCYC": str(cc), "RECAP_KAPPA": str(k),
                                   "FUND_RECAP": "0"}))
    return cells


def build_env(args, config_name, fund_tag, fund_env, seed):
    env = dict(os.environ)
    env.update(CONFIGS[config_name])
    env["REL_PAYOUT"] = str(args.payout)
    env["REL_LOCK"] = "1" if args.lock else "0"
    env["REL_DEVOLUTION"] = args.devolution
    env.update(fund_env)
    env["FIRSTRUN"] = str(seed)
    env["LASTRUN"] = str(seed)
    env["CONFIG_TAG"] = "EXP-%s-%s" % (config_name, fund_tag)
    if args.ncycle:
        env["NCYCLE"] = str(args.ncycle)
    if args.output_base:
        env["OUTPUT_BASE"] = args.output_base
    return env


def run_one(args, config_name, fund_tag, fund_env, seed):
    env = build_env(args, config_name, fund_tag, fund_env, seed)
    label = "%s/%s seed=%d" % (config_name, fund_tag, seed)
    if args.dry_run:
        shown = " ".join("%s=%s" % (k, env.get(k, "")) for k in
                         ("RB_C0", "RB_C1", "REL_PAYOUT", "REL_LOCK", "FUND_ON",
                          "FUND_CONTRIB", "FUND_CCYC", "RECAP_KAPPA", "FUND_RECAP",
                          "CONFIG_TAG"))
        return (label, 0, "DRY-RUN  " + shown)
    t0 = time.time()
    proc = subprocess.run([args.python, "timing.py"], cwd=args.model_dir, env=env,
                          stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    dt = time.time() - t0
    if proc.returncode == 0:
        return (label, 0, "ok (%.0fs)" % dt)
    tail = (proc.stderr or b"").decode("utf-8", "replace").strip().splitlines()[-6:]
    return (label, proc.returncode, "FAILED (%.0fs)\n    " % dt + "\n    ".join(tail))


# ----------------------------- summary phase -----------------------------

def _read_agg(path):
    """Return (maxNFirm, lastTime, maxLoanReg) for country 0 of an AggData file."""
    mx_nfirm = last_t = mx_loanreg = 0.0
    try:
        with open(path, newline="") as fh:
            rd = csv.reader(fh)
            next(rd, None)
            for row in rd:
                if len(row) <= COL_LOANREG:
                    continue
                try:
                    if int(float(row[COL_COUNTRY])) != 0:
                        continue
                    t = float(row[COL_TIME]); nf = float(row[COL_NFIRM])
                    lr = float(row[COL_LOANREG])
                except (ValueError, IndexError):
                    continue
                last_t = max(last_t, t)
                mx_nfirm = max(mx_nfirm, nf)
                mx_loanreg = max(mx_loanreg, lr)
    except OSError:
        return None
    return (mx_nfirm, last_t, mx_loanreg)


def _read_fund(path):
    """Return (reservesEnd, maxReserves, totalIn, totalOut, nRecapTot, nRecapFail) country 0."""
    rows = []
    try:
        with open(path, newline="") as fh:
            rd = csv.reader(fh)
            next(rd, None)
            for row in rd:
                if len(row) <= F_NRECAPFAIL:
                    continue
                try:
                    if int(float(row[F_COUNTRY])) != 0:
                        continue
                    rows.append(row)
                except (ValueError, IndexError):
                    continue
    except OSError:
        return None
    if not rows:
        return None
    maxres = max(float(r[F_RES]) for r in rows)
    last = rows[-1]
    return (float(last[F_RES]), maxres, float(last[F_IN]), float(last[F_OUT]),
            float(last[F_NRECAPTOT]), float(last[F_NRECAPFAIL]))


_TAG_RE = re.compile(r"EXP-([A-Za-z]+)-(fundoff|fund_g[\d.]+_cc[\d.]+_k[\d.]+(?:_norecap)?)")
_SEED_RE = re.compile(r"r(\d+)[^/]*AggData\.csv$")


def summarize(args):
    base = args.output_base or "."
    full_len = (args.ncycle or 1001) - 1   # last logged t for a full run
    # --output-base may be a directory (ends in os.sep) OR a literal prefix glued
    # onto the folder name (e.g. /home/you/sw_). Cover both.
    patterns = [os.path.join(base, "**", "*AggData.csv"),
                base + "*" + os.sep + "**" + os.sep + "*AggData.csv",
                base + "*AggData.csv"]
    seen = set()
    aggs = []
    for pat in patterns:
        for p in glob.glob(pat, recursive=True):
            if p not in seen:
                seen.add(p)
                aggs.append(p)
    if not aggs:
        sys.exit("no *AggData.csv under %r" % base)
    # group: (config, fund_tag) -> list of per-seed dicts
    cells = {}
    for ap in aggs:
        m = _TAG_RE.search(ap)
        if not m:
            continue
        config, ftag = m.group(1), m.group(2)
        sm = _SEED_RE.search(os.path.basename(ap))
        seed = int(sm.group(1)) if sm else -1
        agg = _read_agg(ap)
        if agg is None:
            continue
        fundp = ap.replace("AggData.csv", "FundData.csv")
        fnd = _read_fund(fundp) if os.path.isfile(fundp) else None
        cells.setdefault((config, ftag), []).append((seed, agg, fnd))

    def fmt_cell(rows):
        n = len(rows)
        halted = sum(1 for _, (nf, lt, lr), _ in rows if lt < full_len - 0.5)
        nfirms = sorted(nf for _, (nf, lt, lr), _ in rows)
        loanregs = [lr for _, (nf, lt, lr), _ in rows]
        mean_nf = sum(nfirms) / n
        med_nf = nfirms[n // 2]
        mean_lr = sum(loanregs) / n
        fline = ""
        fnds = [f for _, _, f in rows if f]
        if fnds:
            tin = sum(f[2] for f in fnds); tout = sum(f[3] for f in fnds)
            recyc = 100.0 * tout / tin if tin > 0 else 0.0
            nrt = sum(f[4] for f in fnds) / len(fnds)
            nrf = sum(f[5] for f in fnds) / len(fnds)
            maxres = sum(f[1] for f in fnds) / len(fnds)
            fline = ("  | fund recycle=%2.0f%% maxRes~%.0f recap~%.0f fail~%.0f"
                     % (recyc, maxres, nrt, nrf))
        return ("seeds=%2d  divergence=%4.0f%% (%d/%d halted)  maxNFirm mean=%5.0f med=%5.0f"
                "  maxLoanReg mean=%6.0f%s"
                % (n, 100.0 * halted / n, halted, n, mean_nf, med_nf, mean_lr, fline))

    print("\n=== FUND SWEEP SUMMARY (country 0; 'halted' = hit debt breaker before t=%d) ===\n"
          % full_len)
    for config in sorted({c for c, _ in cells}):
        print("[%s]" % config)
        ftags = sorted({ft for c, ft in cells if c == config},
                       key=lambda t: (t != "fundoff", t))
        for ft in ftags:
            print("  %-26s %s" % (ft, fmt_cell(cells[(config, ft)])))
        print("")


def main():
    args = parse_args()
    if args.summarize:
        summarize(args)
        return
    if not os.path.isfile(os.path.join(args.model_dir, "timing.py")):
        sys.exit("timing.py not found in --model-dir=%r" % args.model_dir)

    cells = fund_settings(args)
    seeds = range(args.first_seed, args.last_seed + 1)
    tasks = [(c, tag, env, s)
             for c in args.configs
             for (tag, env) in cells
             for s in seeds]
    print("Launching %d runs = %d configs x %d fund-cells x %d seeds, workers=%d, "
          "payout=%s, lock=%s"
          % (len(tasks), len(args.configs), len(cells),
             args.last_seed - args.first_seed + 1, args.workers, args.payout, args.lock))
    print("Fund cells: " + ", ".join(t for t, _ in cells))

    failures = []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_one, args, c, tag, env, s): (c, tag, s)
                for (c, tag, env, s) in tasks}
        for fut in cf.as_completed(futs):
            label, rc, msg = fut.result()
            print("[%s] %s" % (label, msg))
            if rc != 0:
                failures.append(label)

    print("\n%d/%d runs ok." % (len(tasks) - len(failures), len(tasks)))
    if failures:
        print("FAILED (SFC error, not a debt-breaker halt): " + ", ".join(sorted(failures)))
    print("\nNow summarise with:  python run_experiments.py --summarize "
          "--output-base %s --ncycle %s"
          % (args.output_base or "<base>", args.ncycle or 1001))


if __name__ == "__main__":
    main()
