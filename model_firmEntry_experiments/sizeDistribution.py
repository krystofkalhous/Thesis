# sizeDistribution.py
#
# Computes per-period size-distribution statistics for firms and banks,
# broken down by type (tradable/non-tradable firms; regional/global banks),
# per country.
#
# Design: NO separate output files. Statistics are returned as a flat list
# and appended directly to the aggregator's DcountryCollectData row, so
# each run produces exactly two files: <name>Para.csv and <name>AggData.csv.
#
# Usage in aggregator (inside checkCA, after the four .append() calls):
#   dist_vals = distTracker.get_stats(country, McountryFirm, McountryBank)
#   self.DcountryCollectData[country].extend(dist_vals)
#
# Column names are returned by SizeDistribution.column_names() and must be
# added to the WriteInitial header list in the same order.

import math


# ── statistics helper ────────────────────────────────────────────────────────

def _stats(values):
    """Summary statistics for a list of positive floats.
    Returns an ordered list matching _STAT_KEYS."""
    if not values:
        return [0] * len(_STAT_KEYS)
    sv    = sorted(values)
    n     = len(sv)
    total = sum(sv)
    mean  = total / n
    var   = sum((x - mean) ** 2 for x in sv) / n
    std   = math.sqrt(var)

    def _pct(p):
        idx  = (n - 1) * p / 100.0
        lo   = int(idx)
        hi   = min(lo + 1, n - 1)
        frac = idx - lo
        return sv[lo] * (1 - frac) + sv[hi] * frac

    cutoff       = max(1, int(math.ceil(0.1 * n)))
    share_top10  = sum(sv[n - cutoff:]) / total if total > 0 else 0.0
    herfindahl   = sum((x / total) ** 2 for x in sv) if total > 0 else 0.0

    return [n, mean, std, sv[0],
            _pct(10), _pct(25), _pct(50), _pct(75), _pct(90), sv[-1],
            share_top10, herfindahl]


_STAT_KEYS = ['n', 'mean', 'std', 'min',
              'p10', 'p25', 'p50', 'p75', 'p90', 'max',
              'share_top10pct', 'herfindahl']

# Agent types tracked, in fixed order
_TYPES = ['firmTradable', 'firmNotTradable', 'bankRegional', 'bankGlobal']


# ── public API ───────────────────────────────────────────────────────────────

class SizeDistribution:
    """Collects size-distribution stats; returns them for inline aggregation."""

    @staticmethod
    def column_names():
        """Ordered list of column names to add to the aggregator header."""
        cols = []
        for atype in _TYPES:
            for key in _STAT_KEYS:
                cols.append(f'sz_{atype}_{key}')
        return cols

    @staticmethod
    def get_stats(country, McountryFirm, McountryBank):
        """Return a flat list of stats for one country at the current period.
        Order matches column_names()."""
        A_ft, A_fnt, A_br, A_bg = [], [], [], []

        for fide in McountryFirm.get(country, {}):
            f = McountryFirm[country][fide]
            if f.A is not None and f.A > 0:
                if f.tradable == 'yes':
                    A_ft.append(f.A)
                else:
                    A_fnt.append(f.A)

        for bide in McountryBank.get(country, {}):
            b = McountryBank[country][bide]
            if b.A is not None and b.A > 0:
                if getattr(b, 'isRegional', False):
                    A_br.append(b.A)
                else:
                    A_bg.append(b.A)

        result = []
        for vals in [A_ft, A_fnt, A_br, A_bg]:
            result.extend(_stats(vals))
        return result

    # ── kept for backward compatibility with timing.py calls ────────────────
    def __init__(self, Lcountry=None, folder=None, name=None, run=None):
        """Parameters accepted but ignored — no file I/O in this version."""
        pass

    def collect(self, t, McountryFirm, McountryBank):
        """No-op: stats are pulled on demand via get_stats()."""
        pass

    def close(self):
        """No-op: no files to close."""
        pass
