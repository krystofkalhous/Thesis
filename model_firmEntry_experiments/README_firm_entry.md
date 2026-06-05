# Firm entry — national pool (region borders removed)

Firm entry is no longer limited by regional borders. Entering firms are funded
from a single **national** capital pool (the original model's behaviour, and the
same pool bank entry uses): any consumer's uninvested savings may help
capitalize any firm, regardless of region. This removes the unbounded
both-regional firm-entry spiral that per-region capital pools produced.

## Setting (parameter.py)

```python
self.firmEntryMode = 'national'   # DEFAULT — firm funding not limited by region
                                  # 'regional' retained for reference only
```

Regional **banks** are untouched: with `useRegionalBanks[country] = True` they
still form and still lend preferentially within their region. The Regionalprinzip
(relationship lending bounded by region) lives in the bank lending rule, not in
firm funding, so it is fully preserved.

## How firms get a region now

Because founding capital is pooled nationally, a firm's region can no longer be
"the pool it came from." Each entering firm is assigned the region that is the
**plurality (modal) home region of its founders** — i.e. the firm is sited where
most of its owners live (`_mostCommonRegion(newfirm.ListOwners)` in
`enterExit.py`). This is the design intent already documented at the top of the
`nRegion` block ("entering firms inherit the region of the investing consumer,
plurality vote").

Why plurality of *founders* and not capital-weighted "richest region":
- It ties the firm to where its owners actually are — economically interpretable
  and stable.
- It is **wealth-neutral**: firms disperse across regions by where people are,
  not by where money is concentrated. A capital-weighted rule ("assign to the
  region contributing the most founding capital") would re-introduce exactly the
  rich-region concentration that drove the runaway, so it is deliberately avoided.
- Founders are drawn from the shuffled national pool, so plurality spreads new
  firms across regions roughly in proportion to population — no region accrues a
  self-reinforcing advantage.

If you ever want a different rule, change the single line at the `newfirm.region`
assignment in `enterExit.py`:
- largest single backer: `newfirm.region = self._consumerRegion(newfirm.ListOwners[0])`
  (the lead investor — the first, largest slice of the founding pool);
- capital-weighted: sum founding shares by region and take the argmax (not
  recommended — reintroduces the concentration bias).

## Optional diagnostics

`self.entryTrace = False` — set True to append per-period entry diagnostics to
`<folder><name>EntryTrace.csv` (firms/banks founded, capital available, eligible
investors, average firm size). Off for production.

## Note

Results are not bit-identical across operating systems, so per-seed trajectories
differ from machine to machine; compare ensembles / divergence rates rather than
single seeds.
