# Results — four relationship-lender application rules, tested across allRel and union

Companion to `RESULTS_approach_gate.md` and `PROPOSAL_relbank_nursery.md`. This tests the
firm-side application rule in four forms and two monetary-union configurations, fund OFF,
and reads them through a new **direct welfare metric**: the fill-ratio premium.

---

## 1. The four application rules (all behind `APPLY_GATE_ON`, default off = always-visible)

A firm applies to the relationship lender only if productive (`firmPhi ≥ phiRegion`); then
the probability of applying is set by `APPLY_GATE_MODE`:
- **asset** (preferred): `P = (1 − sizeScore)^EXP` — falls with assets (small productive firms apply).
- **theta_fill**: `P = logistic(k·(leverage − θ))`, θ = fixed 3.0 (the leverage where the
  fill ratio collapses in `allTxn`, measured below).
- **theta_pct**: same logistic, θ = the 30th-percentile leverage of credit-seekers each period.
- **theta_struct**: same logistic, θ = `(RET − rDiscount)/xi` from the transaction rate schedule.

If a country has no relationship banks (transaction-only), its firms simply approach the
transaction banks (no gate). Config `union` = country 0 relationship, country 1 transaction.

## 2. θ measured from allTxn (the rationing margin)

Fill ratio by leverage quartile in `allTxn` (calm, country 0): Q1(low lev) **0.88**, Q2 0.40,
Q3 0.22, Q4(high) 0.17. Transaction lenders fund only the low-leverage tail; fill collapses
above ~the 25–35th leverage percentile (medLev≈4 → θ≈3). This sets θ_fill=3.0, θ_pct=0.30.
Note the rate at leverage 3 is already ~10× the policy rate, yet firms still borrow there —
so **rationing here is quantity-driven (queue/supply), not price-driven**, which is why
θ_struct keyed to a rate hurdle is a different (and a priori mis-calibrated) margin.

## 3. The matrix (mean over seeds 0,1; calm 50–200; country 0; fund off)

| spec | spearman | frac_HH | demShare | **premium** | fill_all | maxNFirm |
|---|---|---|---|---|---|---|
| **allRel — always-visible (ctrl)** | −0.254 | 0.207 | 0.226 | **−0.008** | 0.67 | 216 |
| allRel — asset | −0.512 | 0.152 | 0.167 | **+0.279** | 0.37 | 382 |
| allRel — theta_fill | −0.519 | 0.148 | 0.162 | **+0.250** | 0.33 | 406 |
| allRel — theta_pct | −0.484 | 0.158 | 0.170 | **+0.309** | 0.37 | 432 |
| allRel — theta_struct | −0.501 | 0.153 | 0.171 | **+0.242** | 0.37 | 373 |
| **union — always-visible (ctrl)** | −0.293 | 0.206 | 0.215 | **+0.011** | 0.45 | 402 |
| union — asset | −0.254 | 0.218 | 0.231 | **+0.104** | 0.40 | 448 |
| union — theta_fill | −0.189 | 0.231 | 0.245 | **+0.108** | 0.40 | 357 |
| union — theta_pct | −0.314 | 0.207 | 0.220 | **+0.112** | 0.43 | 494 |
| union — theta_struct | −0.267 | 0.213 | 0.219 | **+0.101** | 0.40 | 454 |

`premium` = (fill ratio of high-leverage **productive** firms) − (fill ratio of high-leverage
**unproductive** firms). > 0 means soft information overrides the hard signal: the relationship
bank funds productive firms a transaction lender would ration. This is the direct test of the
thesis. (allTxn reference: spearman −0.365, frac_HH 0.188.)

## 4. What WORKS

1. **The gate is what makes soft information bite.** Always-visible relationship banking has
   premium ≈ **0** (−0.008 allRel, +0.011 union) — it does NOT preferentially fund productive
   levered firms despite seeing phi. **Every gated rule** produces a strong positive premium
   (allRel +0.24…+0.31; union +0.10…+0.11). The application gate — firms self-selecting — is
   the necessary ingredient; visibility alone dilutes the edge.
2. **All four rules work, and similarly.** asset (your preferred) gives premium +0.28; the
   three θ rules +0.24…+0.31. theta_pct is marginally best (+0.31, most firms). theta_struct
   works as well as the rest **despite** its price-vs-quantity mis-calibration — the logistic
   is forgiving, so the result is robust to how θ is set. Net: the *form* (productive +
   self-selection) matters; the exact θ does not.
3. **Gates de-concentrate.** ~370–490 firms vs 216 always-visible (allRel); at full length the
   firm-proliferation explosion is eliminated (firms bounded ~460–550, not 2000+).
4. **In `union`, relationship banking stabilises the adopting country.** Full length: country 0
   (relationship) stays fiscally healthy (Bonds/Y≈0, firms bounded), while country 1
   (transaction-only) blows up fiscally (Bonds/Y=8.1, firms collapse 494→133) and halts the
   union at t≈492. The country with gated relationship lending is the stable one.

### On the negative spearman (resolving the earlier confusion)
Gated allRel drives spearman *more* negative (−0.51 vs −0.25). That is **not** the room
closing in a bad sense — paired with premium > 0 it is the **footprint of the mechanism
working**: productive levered firms get funded (premium +0.28) and therefore delever, so phi
sorts toward low leverage. The correct welfare reading is the premium, not the correlation.
(In `union` the spearman stays moderate — less delevering, because cross-border coupling to the
transaction economy dilutes the relationship advantage; premium correspondingly smaller, +0.10.)

## 5. What does NOT work (fund off)

5. **Divergence is not eliminated — it migrates to the fiscal channel.** Full length, asset
   rule: allRel halts t=461 (public debt blows up, Bonds/Y→6.8, though firms stay bounded);
   union halts t=492 (the transaction-only country’s public debt → 8.1). The gates fix credit
   *allocation*, not *fiscal* dynamics, so with the fund off the union still diverges via
   public debt. The protection fund (separately shown to take allRel to 0% divergence) is the
   lever for that; gates + fund is the untested-here combination to run next.
6. **Always-visible relationship banking is the wrong design** on both axes: no soft-info
   premium AND concentrates (216 firms) → the configuration that diverges 100% at full length.
7. **The relationship advantage is diluted in `union`** (premium +0.10 vs +0.27 in allRel):
   a relationship-banking country coupled to a transaction-only partner gets a smaller
   soft-information benefit, and the partner’s instability still halts the union.

## 6. Bottom line / recommendation

- **Adopt the application gate** — it is what turns "the bank sees phi" into "productive
  rationed firms actually get credit" (premium 0 → +0.28). Always-visibility does not.
- **Your asset rule is a fine choice** — it performs as well as the leverage-based rules, and
  the result is robust to rule form and θ calibration, so the empirically-grounded asset rule
  needs no apology.
- **Pair with the fund** — the gate removes the firm-credit explosion and (in union) stabilises
  the adopting country, but the residual fiscal divergence (fund off) means the full
  efficiency+stability claim needs gate + fund. That is the next run.
- **Union is the cleaner demonstration of the thesis’ stability side**: the relationship
  country is stable, the transaction country diverges.

## 7. Caveats / next runs (full length, 11 seeds, faster machine)

n=2 for the structure table; full-length stability is 1 seed per spec (in-sandbox the
non-gated controls explode and time out). Confirm as ensembles: (1) the premium ordering
(gated >> always-visible) across 11 seeds and into the boom window; (2) the union asymmetry
(c0 stable, c1 diverges) across seeds; (3) **gate + fund** in both configs — does the fund
close the residual fiscal divergence while the gate preserves the premium? Read premium and
fill_all alongside divergence/firm-count throughout.

## 8. Files

`/mnt/user-data/outputs/nursery_patch/`: `matchingCredit.py` (switches `APPLY_GATE_ON`,
`APPLY_GATE_MODE` ∈ {asset, theta_fill, theta_pct, theta_struct}, dials `APPLY_GATE_EXP`,
`APPLY_THETA_K/FILL/PCT/RET`, plus the earlier `NURSERY_ON`); `softInfo.py` (adds
`softinfo_premium`, `fill_all`, and leverage-quartile fill columns for measuring θ). All
default off = exact always-visible baseline.
