# Model with borrower sorting (relationship-lender application gate)

Complete, runnable Caiani–Catullo–Gallegati two-country monetary-union SFC agent-based model
with regional ("Sparkassen-like") relationship banks, extended this session with **borrower
sorting**: firms self-select which lender to approach, instead of the regional bank being
auto-visible to everyone.

Entry point: `python3 timing.py`. Parameters in `parameter.py`. All new behaviour is behind
environment switches; **with every switch at its default, the model reproduces the original
baseline exactly** (verified byte-identical).

## How to run borrower sorting

```bash
# both countries relationship banks, fund off, asset-based sorting rule:
RB_C0=1 RB_C1=1 FUND_ON=0 APPLY_GATE_ON=1 APPLY_GATE_MODE=asset \
  NCYCLE=1001 FIRSTRUN=0 LASTRUN=0 CONFIG_TAG=AR_asset OUTPUT_BASE=./OUT_ python3 timing.py
```

Outputs land in a folder under `OUTPUT_BASE` whose name encodes the settings (stale-file
guard): `AggData`, `FundData`, `SoftInfoData`, `Para` CSVs.

## The borrower-sorting switches (matchingCredit.py)

- `APPLY_GATE_ON` (default `0`): off = original always-visible regional bank. On = firms
  apply to the relationship lender only if **productive** (`firmPhi ≥ phiRegion`) and pass a
  probability rule.
- `APPLY_GATE_MODE` (default `asset`): which sorting rule —
  - `asset` — apply probability **falls with assets**: `P=(1−sizeScore)^APPLY_GATE_EXP`
    (small productive firms self-select in). [`APPLY_GATE_EXP`, default 1.0]
  - `theta_fill` — apply probability **rises with leverage** via `logistic(k·(lev−θ))`,
    θ = fixed rationing margin. [`APPLY_THETA_FILL`=3.0, `APPLY_THETA_K`=1.5]
  - `theta_pct` — same logistic, θ = a per-period leverage percentile. [`APPLY_THETA_PCT`=0.30]
  - `theta_struct` — same logistic, θ = `(APPLY_THETA_RET−rDiscount)/xi` from the rate
    schedule. [`APPLY_THETA_RET`=0.013]
- `NURSERY_ON` (default `0`): bank-side — size-tilts the regional credit queue toward small
  productive firms. [`NURSERY_BOOST`=2.0]

Config selection (per-country regional banks): `RB_C0`, `RB_C1` ∈ {0,1}.
allRel = `RB_C0=1 RB_C1=1`; union = `RB_C0=1 RB_C1=0`; allTxn = `RB_C0=0 RB_C1=0`.
In a transaction-only country there is no regional bank, so its firms simply approach the
transaction banks (no gate).

## Other switches present (default off = baseline)

- Protection fund: `FUND_ON`, `FUND_CONTRIB`, `FUND_CCYC`, `RECAP_KAPPA`, `FUND_RECAP` (fund.py).
- Innovation path dependence (both default off/neutral, NOT used in the borrower-sorting runs):
  - `LAMBDA_INN` (default 1.0 = original free catch-up) — innovation catch-up strength.
  - `RCAP_ON` (default off) + `RCAP_DEPREC/MAINT/ABSORP` — research-capital stock (lebalance.py).

## Diagnostics (softInfo.py + timing.py)

Every run writes `…SoftInfoData.csv`: per-period phi-vs-leverage structure among credit-seekers
plus the **fill-ratio premium** (`softinfo_premium` = fill ratio of high-leverage *productive*
firms minus that of high-leverage *unproductive* firms; >0 = soft information overriding the
hard signal) and leverage-quartile fill columns. Read with the reader/queries documented in
the session handoffs.

## What the borrower-sorting runs showed (fund off, n=2 seeds, calm window)

Gating (any rule) produces a positive fill-ratio premium (allRel ≈ +0.25–0.31; union ≈ +0.10),
i.e. productive rationed firms get credit; the always-visible bank gives ≈0. Gating also
de-concentrates (more firms) and removes the firm-proliferation explosion, though with the
fund off the union still diverges via the fiscal channel. See `RESULTS_application_rules.md`.

## Files

25 `.py` files — the complete model. Modified this session: `matchingCredit.py` (borrower
sorting + nursery), `softInfo.py` + `timing.py` (diagnostics), `lebalance.py` + `parameter.py`
(lambdaInn / RCAP switches, default off). All others are the original model, unchanged.
