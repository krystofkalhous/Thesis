# Caiani–Catullo–Gallegati 2-country SFC model — relationship-bank extension

This is the complete, runnable model used in the experiments: the baseline 2-country monetary-union
stock-flow-consistent agent-based macro model, extended with regional "Sparkassen-like" relationship
banks plus every switch added across the sessions (borrower sorting, the protection fund, the fiscal
rule, the innovation variants, and the credit-sampling hooks). **Every switch defaults OFF and the
default configuration reproduces the original baseline byte-identically** (verified each session).

- Entry point: `python3 timing.py`
- Parameters: `parameter.py`
- Python 3, standard library only (csv, random, os, math). No external packages.

## Quick start

```bash
# baseline, both countries regional (allRel), seeds 0..10, full length
RB_C0=1 RB_C1=1 NCYCLE=1001 FIRSTRUN=0 LASTRUN=10 \
  CONFIG_TAG=baseline_allRel OUTPUT_BASE=./OUT_ python3 timing.py
```

Output lands in `./OUT_<...tag...>/` as four CSVs per run: `AggData.csv` (macro series),
`SoftInfoData.csv` (soft-information diagnostics incl. the fill premium), `FundData.csv` (fund
series), `Para.csv` (the parameter dump for that run).

## How to read results (working discipline)

The model is **not bit-reproducible across OSes**, so a single seed proves nothing. Always run a
seed range (`FIRSTRUN`/`LASTRUN`, e.g. 0..10) and compare **divergence rates / ensembles**, not
single runs. A run that ends before `NCYCLE` is a **designed halt** (the debt breaker fires when
`publicDebt/Yprod > 8` and `t > 400`) — that is a divergence signal, not a crash. The welfare metric
is the soft-information **fill premium** in `SoftInfoData.csv` (`softinfo_premium` > 0 = productive
rationed firms getting credit); the leverage–productivity correlation is a side effect, not the goal.

---

## Switch reference (all via environment variables; defaults in parentheses)

### Run control
| var | default | meaning |
|---|---|---|
| `NCYCLE` | 1001 | number of periods |
| `FIRSTRUN` / `LASTRUN` | — | inclusive seed range (e.g. 0 / 10) |
| `CONFIG_TAG` | — | label appended to the output folder name |
| `OUTPUT_BASE` | — | output directory prefix |

### Bank configuration (which country uses regional relationship banks)
| var | default | meaning |
|---|---|---|
| `RB_C0` | per `parameter.py` | country 0: 1 = regional, 0 = transaction-only |
| `RB_C1` | per `parameter.py` | country 1: 1 = regional, 0 = transaction-only |

`{1,1}` = allRel · `{0,0}` = allTxn · `{1,0}` = union · `{0,1}` = mirror union.

### Borrower sorting / application gate (`matchingCredit.py`)
Removes the regional bank's always-visibility; firms self-select. Productivity screen
(`firmPhi >= phiRegion`) is common to all modes.
| var | default | meaning |
|---|---|---|
| `APPLY_GATE_ON` | 0 | master switch for borrower self-selection |
| `APPLY_GATE_MODE` | `asset` | `asset` \| `theta_fill` \| `theta_pct` \| `theta_struct` |
| `APPLY_GATE_EXP` | 1.0 | asset mode: steepness of the size-falling approach probability |
| `APPLY_THETA_K` | 1.5 | theta modes: logistic steepness in leverage |
| `APPLY_THETA_FILL` | 3.0 | `theta_fill`: fixed rationing-margin leverage |
| `APPLY_THETA_PCT` | 0.30 | `theta_pct`: leverage percentile for the threshold |
| `APPLY_THETA_RET` | 0.013 | `theta_struct`: return hurdle, theta = (RET - rDiscount)/xi |

### Nursery (`matchingCredit.py`)
Size-tilts the regional credit queue toward small productive firms.
| var | default | meaning |
|---|---|---|
| `NURSERY_ON` | 0 | master switch |
| `NURSERY_BOOST` | 2.0 | extra queue promotion for small productive firms |

### Fiscal rule (`etat.py`) — debt-stock bang-bang austerity
When `pastBonds/Y` exceeds the target, set tax to `FISCAL_TAXMAX` (above the normal 0.45 cap) and
floor spending at `gMin*Y`.
| var | default | meaning |
|---|---|---|
| `FISCAL_RULE_ON` | 0 | master switch |
| `FISCAL_DEBT_TGT` | 2.0 | debt/Y trigger for austerity |
| `FISCAL_TAXMAX` | 0.65 | tax rate applied under austerity |

### Credit sampling & regional generosity (`parameter.py`)
| var | default | meaning |
|---|---|---|
| `PSI_CREDIT` | 0.2 | fraction of global banks each firm samples |
| `WREG_RANK` | 2.0 | regional queue promotion for productive firms (leverage leniency) |
| `AEXP_PHI` | 0.8 | strength of the regional rate discount for productive firms |

### Protection fund / IPS (`parameter.py`, `fund.py`)
| var | default | meaning |
|---|---|---|
| `FUND_ON` | 0 | master switch for the mutual protection fund |
| `FUND_RECAP` | on | bank recapitalisation channel |
| `FUND_CONTRIB` | per `parameter.py` | base contribution rate |
| `FUND_CCYC` | per `parameter.py` | countercyclical contribution component |
| `RECAP_KAPPA` | per `parameter.py` | recap intensity |

### Innovation variants (`lebalance.py`, `parameter.py`)
| var | default | meaning |
|---|---|---|
| `LAMBDA_INN` | 1.0 | catch-up strength (1.0 = free full catch-up to frontier) |
| `RCAP_ON` | 0 | research-capital stock model (replaces free catch-up) |
| `RCAP_DEPREC` | 0.15 | research-capital depreciation |
| `RCAP_MAINT` | 0.15 | maintenance cost proportional to stock |
| `RCAP_ABSORP` | 1.0 | absorptive-capacity gate on catch-up |

### Advanced (leave at default unless replicating a specific probe)
`REL_PAYOUT`, `LIQPREF_FLOOR`, `CEQUITY`, `REL_DEVOLUTION`, `REL_CREDIT_THROTTLE`.

---

## Key recipes (commands)

```bash
# Baseline allRel (everything default off)
RB_C0=1 RB_C1=1 NCYCLE=1001 FIRSTRUN=0 LASTRUN=10 CONFIG_TAG=allRel OUTPUT_BASE=./OUT_ python3 timing.py

# allTxn control
RB_C0=0 RB_C1=0 ... CONFIG_TAG=allTxn ...

# Borrower sorting (the soft-information / fill-premium result)
RB_C0=1 RB_C1=1 APPLY_GATE_ON=1 APPLY_GATE_MODE=asset ... CONFIG_TAG=allRel_sort ...

# Protection fund (the 0% divergence result via bank recap)
RB_C0=1 RB_C1=1 FUND_ON=1 ... CONFIG_TAG=allRel_fund ...

# Fund-free stabilising recipe: sorting + loose fiscal rule (completes full length, seeds 0-2)
RB_C0=1 RB_C1=1 APPLY_GATE_ON=1 APPLY_GATE_MODE=asset \
  FISCAL_RULE_ON=1 FISCAL_DEBT_TGT=4.0 FISCAL_TAXMAX=0.65 \
  NCYCLE=1001 FIRSTRUN=0 LASTRUN=10 CONFIG_TAG=allRel_sort_fiscal OUTPUT_BASE=./OUT_ python3 timing.py
```

## CSV column quick-reference

- **AggData** (1-based): time 2, country 3, Yprod 4, nFirm 7, nBank 11, publicDeficit 13,
  publicDebt 14, avPrice 15, netWorthFirm 19, netWorthBank 26, badDebt 40. Bonds/Y = publicDebt/Yprod.
- **SoftInfoData** (after time,country): nSeekers, spearman_phi_lev, ..., frac_HH, demandShare_HH, ...,
  `softinfo_premium`, fill_all, fill_hiphi, fill_lophi, fill_levQ1-Q4, lev_p75.
- **FundData** (1-based): time 1, country 2, reserves 3, totalIn 4, totalOut 5, contribThisPeriod 6,
  recapThisPeriod 7, nRecap 8, ..., boom 12.

## Findings docs (in the outputs folder)

`RESULTS_application_rules.md` (sorting / fill premium), `RESULTS_blowup_cause_sweeps.md`
(reach-not-terms; psi), `RESULTS_fiscal_rule_recipe.md` (the fund-free recipe + 3-seed full-length),
`RESULTS_fiscal_rule_otherconfigs.md` (allTxn + mixed config), plus the fund and soft-info handoffs.
