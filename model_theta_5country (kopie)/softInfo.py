# softInfo.py
#
# Soft-information diagnostic (Stein 2002 / Berger-Udell). The relationship
# bank's only edge over transaction lenders is that it observes firm
# productivity (phi, the SOFT signal), while global banks rank and price on
# leverage alone (the HARD signal). That edge has real content ONLY if phi
# carries information BEYOND leverage. If productive firms are simply the
# low-leverage ones, a leverage-ranking transaction bank already knows what phi
# would tell it, and the relationship bank is distinctive in name only.
#
# This module measures, each period, across the firms that are actually SEEKING
# credit (the population the lending decision applies to), the relationship
# between the soft signal phi and the hard signal leverage = loanDemand/A.
#
# Read straight off matchingCredit's MloanDemand rows, which are a frozen
# snapshot at decision time:
#   row = [ide, pos, country, demand, filled, leverage, relPhi, region,
#          phiRegion, phi, firmA]
# so leverage=row[5], phi=row[9], firmA=row[10], demand=row[3], country=row[2].
#
# Headline readings:
#   spearman_phi_lev : rank correlation phi vs leverage among credit-seekers.
#       ~ -1  -> productive firms self-finance (low leverage); leverage already
#               reveals quality; soft info redundant; Stein has little room.
#       ~  0  -> phi independent of leverage; soft info has content.
#       ~ +1  -> productive firms are the LEVERED ones; a leverage-averse
#               transaction bank rejects exactly the productive borrowers ->
#               maximal room for the relationship bank's soft-info edge.
#   frac_HH / demandShare_HH : share of seekers (and of credit demanded) that
#       are BOTH above-median phi AND above-median leverage. This is literally
#       the population Stein's mechanism acts on: productive-but-levered firms a
#       transaction bank disfavours. ~0 -> no room; large -> real room.
#   spearman_small vs spearman_large : the opacity gradient (Berger). Soft info
#       should matter MORE for small/opaque firms, i.e. phi-leverage coupling
#       weaker (more independent content) among small firms.

_COLS = ['nSeekers', 'spearman_phi_lev', 'pearson_phi_lev',
         'spearman_small', 'spearman_large',
         'frac_HH', 'demandShare_HH', 'medPhi', 'medLev', 'medA',
         'fill_HL_highphi', 'fill_HL_lowphi', 'softinfo_premium',
         'fill_all', 'fill_hiphi', 'fill_lophi',
         'fill_levQ1', 'fill_levQ2', 'fill_levQ3', 'fill_levQ4', 'lev_p75']


def _ranks(xs):
    """Average (fractional) ranks, 1-based, ties shared."""
    n = len(xs)
    order = sorted(range(n), key=lambda i: xs[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 1e-12 or syy <= 1e-12:
        return 0.0
    sxy = sum((xs[k] - mx) * (ys[k] - my) for k in range(n))
    return sxy / ((sxx * syy) ** 0.5)


def _spearman(xs, ys):
    if len(xs) < 3:
        return 0.0
    return _pearson(_ranks(xs), _ranks(ys))


def _median(xs):
    if not xs:
        return 0.0
    sv = sorted(xs)
    n = len(sv)
    return sv[n // 2] if n % 2 else 0.5 * (sv[n // 2 - 1] + sv[n // 2])


class SoftInfo:
    """Per-period phi-vs-leverage diagnostics, computed from MloanDemand."""

    @staticmethod
    def column_names():
        return list(_COLS)

    @staticmethod
    def compute(MloanDemand):
        """Return {country: [values in column_names() order]} from the
        credit-seeking firms in MloanDemand (frozen at decision time)."""
        by = {}
        for row in MloanDemand:
            if len(row) < 11:
                continue
            c = row[2]
            # (phi, leverage, firmA, demand)
            by.setdefault(c, []).append((row[9], row[5], row[10], row[3] + row[4], row[4]))
        out = {}
        for c, rows in by.items():
            n = len(rows)
            phi = [r[0] for r in rows]
            lev = [r[1] for r in rows]
            A = [r[2] for r in rows]
            dem = [r[3] for r in rows]
            medPhi = _median(phi)
            medLev = _median(lev)
            medA = _median(A)
            sp = _spearman(phi, lev)
            pe = _pearson(phi, lev)
            s_phi = [p for (p, l, a, d, f) in rows if a <= medA]
            s_lev = [l for (p, l, a, d, f) in rows if a <= medA]
            l_phi = [p for (p, l, a, d, f) in rows if a > medA]
            l_lev = [l for (p, l, a, d, f) in rows if a > medA]
            sp_s = _spearman(s_phi, s_lev)
            sp_l = _spearman(l_phi, l_lev)
            totDem = sum(dem) or 1.0
            hh = [(p, l, a, d, f) for (p, l, a, d, f) in rows if p > medPhi and l > medLev]
            frac_hh = len(hh) / float(n) if n else 0.0
            demshare_hh = sum(d for (_, _, _, d, _f) in hh) / totDem
            # Fill-ratio premium: among HIGH-LEVERAGE seekers (the rationing
            # margin a phi-blind transaction lender disfavours), do PRODUCTIVE
            # firms get more of their demand filled than UNPRODUCTIVE ones?
            #   premium > 0  -> soft info overrides the hard signal (Stein at work)
            #   premium ~ 0  -> phi-blind rationing (transaction-like)
            def _fr(sub):
                v = [min(1.0, f / d) for (p, l, a, d, f) in sub if d > 1e-9]
                return sum(v) / len(v) if v else float('nan')
            hl_hi = [r for r in rows if r[1] > medLev and r[0] > medPhi]   # high-lev, high-phi
            hl_lo = [r for r in rows if r[1] > medLev and r[0] <= medPhi]  # high-lev, low-phi
            fill_hi = _fr(hl_hi)
            fill_lo = _fr(hl_lo)
            premium = (fill_hi - fill_lo) if (fill_hi == fill_hi and fill_lo == fill_lo) else float('nan')
            fill_all = _fr(rows)
            fill_hiphi = _fr([r for r in rows if r[0] > medPhi])
            fill_lophi = _fr([r for r in rows if r[0] <= medPhi])
            # fill ratio by leverage quartile (to locate the rationing margin theta)
            sl = sorted(rows, key=lambda r: r[1])
            q = max(1, len(sl) // 4)
            def _frq(sub):
                v = [min(1.0, f / d) for (p, l, a, d, f) in sub if d > 1e-9]
                return sum(v) / len(v) if v else float('nan')
            flq1 = _frq(sl[:q]); flq2 = _frq(sl[q:2*q]); flq3 = _frq(sl[2*q:3*q]); flq4 = _frq(sl[3*q:])
            levs = sorted(r[1] for r in rows)
            lev_p75 = levs[min(len(levs)-1, int(0.75*len(levs)))] if levs else 0.0
            out[c] = [n, sp, pe, sp_s, sp_l, frac_hh, demshare_hh, medPhi, medLev, medA,
                      fill_hi, fill_lo, premium, fill_all, fill_hiphi, fill_lophi,
                      flq1, flq2, flq3, flq4, lev_p75]
        return out
