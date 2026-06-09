# model_theta_5country — 5-country monetary union with one relationship-banking country

This is the Caiani–Catullo–Gallegati monetary-union SFC ABM, configured as a **5-country
union** in which **country 0 has relationship ("Sparkassen-like") lenders with the θ
latent-type + borrower-self-selection extension**, and countries 1–4 are ordinary
transaction-bank economies. All extensions are **default-off and byte-identical** to the
clean baseline when their switches are unset.

## What changed vs the 2-country model
- `parameter.py`: `ncountry = 5` (the model is natively 5-country — line 16 originally read
  `5`; a prior user reduced it to 2). Country handling is fully programmatic (`range(ncountry)`
  loops, a `useRegionalBanks` dict keyed by country index, per-country name building), so no
  other structural change is needed. Each country has its own `nRegion` regions.
- `lebalance.py`: the θ productivity channel is the **v3** formulation — θ scales innovation
  **efficiency** only (`b = 1 − exp(−ni·θ·effort)`); innovation **magnitude** and the catch-up
  **target** are left at baseline. This is the *stable* formulation. A new env flag
  `THETA_PROD` (default on) can disable this channel entirely (`THETA_PROD=0`), leaving θ to
  drive only self-selection + relationship pricing — a stable "allocation-only" θ arm.

> Implementation note: during this 5-country build, the working copy of `lebalance.py` had
> drifted to the explosive *v1* formulation (θ on magnitude **and** target), which made the first
> θ-on run blow up. This package contains the corrected **v3**; default-off byte-identity and θ-on
> stability when coupled are both verified. (The previously-shipped 2-country package was not
> affected — it carried the stable formulation and its scorecard reproduces exactly under v3.)

## Run it

```sh
cd model_theta_5country

# (A) all-transaction baseline, theta off:
OUTPUT_BASE=./A_ CONFIG_TAG=A NCYCLE=300 FIRSTRUN=0 LASTRUN=1 python3 timing.py

# (C) country 0 = relationship banking, theta OFF (stable; the relationship-banking effect):
RB_C0=1 OUTPUT_BASE=./C_ CONFIG_TAG=C NCYCLE=300 FIRSTRUN=0 LASTRUN=1 python3 timing.py

# (B) country 0 = relationship + theta self-selection (v3), c1-4 transaction:
RB_C0=1 THETA_ON=1 THETA_SPREAD=0.5 SELF_NOISE=0.1 GAP_KAPPA=0.5 \
    OUTPUT_BASE=./B_ CONFIG_TAG=B NCYCLE=300 FIRSTRUN=0 LASTRUN=1 python3 timing.py

# (B') same, but theta drives ONLY allocation (no productivity channel) -- stable comparison:
RB_C0=1 THETA_ON=1 THETA_PROD=0 THETA_SPREAD=0.5 SELF_NOISE=0.1 GAP_KAPPA=0.5 \
    OUTPUT_BASE=./Bp_ CONFIG_TAG=Bp NCYCLE=300 FIRSTRUN=0 LASTRUN=1 python3 timing.py
```

Output dirs are `{OUTPUT_BASE}{config}_{CONFIG_TAG}/`; AggData files
`{config}{CONFIG_TAG}r{seed}AggData.csv`. The config string embeds `Co5` (country count) and
`_RegionalCo0` (which countries are relationship) so runs never collide.

## Key env switches
- **Relationship banks (per country):** `RB_C0 RB_C1 RB_C2 RB_C3 RB_C4` (default all off).
- **θ extension:** `THETA_ON` (master), `THETA_SPREAD` (=σ_θ, log-sd of the latent type, def 0.5),
  `SELF_NOISE` (=σ_self, self-estimate noise, def 0.3), `GAP_KAPPA` (=κ, size hurdle, def 0.5),
  `THETA_PROD` (def on; =0 disables the productivity channel).
- **Single-country isolation** (turn the union into one open economy + fixed "abroad"; all four
  → mean|CA|≈0): `XBORDER_CREDIT_OFF HOME_BIAS XBORDER_BONDS_OFF TAYLOR_PER_COUNTRY`.
- **Run control:** `NCYCLE FIRSTRUN LASTRUN CONFIG_TAG OUTPUT_BASE PRINT_AGENT`.

## Important conventions
- A run that ends before `NCYCLE` (exit 0) hit the **debt breaker** (`initialize.py`): a
  *designed* graceful halt when public-debt/Y exceeds the threshold, **not a crash**. Judge
  stability by the debt/Y breaker + avPhi not exploding, never by nominal prices.
- Not bit-reproducible across OSes → compare **ensembles across seeds**, not single seeds, for
  any headline. Cross-country heterogeneity at 5 countries is large (~13% output spread even in
  the symmetric all-transaction baseline), so use several seeds.

See `RESULTS_5country_union.md` for the experiment and findings.
