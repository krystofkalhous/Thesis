# fund.py
#
# Relationship-bank protection fund (one per country), modelled on the
# institutional protection schemes of the German Sparkassen (DSGV) and
# cooperative (BVR) sectors and the Italian cooperative guarantee funds.
#
# Design (agreed spec):
#   * The fund starts EMPTY. It has no seed capital. Every unit it holds was
#     contributed out of a regional bank's retained surplus. Nothing comes
#     from outside the regional-bank sector (no state backstop).
#   * Contributions: each period a regional ("relationship") bank diverts a
#     fraction gammaEff of its retained surplus to the fund. gammaEff is
#     countercyclical: it rises when regional credit is booming. This is the
#     drain that is meant to tame the boom at the source.
#   * Recapitalisation: when a regional bank would fail (A at/below the
#     viability floor), the fund recapitalises it to a viable level — but ONLY
#     if it can cover the FULL amount. Otherwise it spends nothing and the bank
#     fails through the existing exit path; the region then re-founds a bank.
#   * The fund holds central-bank reserves. Money is conserved: a contribution
#     moves reserves bank->fund (CB total unchanged); a recap moves reserves
#     fund->bank and raises the bank's equity (CB total unchanged). The fund is
#     NOT a bank (outside every bank's loanSupply) and its equity is
#     non-distributable (never marked back into household A).
#
# Accounting identity (asserted every period):
#       Reserves == totalIn - totalOut   and   Reserves >= 0
#
# SFC reserve identity, extended to include the fund:
#       sum(bank.Reserves) + sum(fund.Reserves) == centralBank.Reserves

class RelationshipFund:
    def __init__(self, country, on=False, contribBase=0.0, countercyclical=0.0,
                 recapKappa=2.0, emaAlpha=0.1, recapOn=True):
        self.country = country
        self.on = on
        self.recapOn = recapOn                # if False: contributions drain but no recaps
        self.contribBase = contribBase        # gamma_base: baseline contribution fraction
        self.countercyclical = countercyclical # theta: countercyclical strength
        self.recapKappa = recapKappa          # recap target = kappa * viability floor
        self.emaAlpha = emaAlpha

        self.Reserves = 0.0                   # the fund's only asset (CB reserves)
        self.totalIn = 0.0                    # cumulative contributions received
        self.totalOut = 0.0                   # cumulative recapitalisations paid

        self.gammaEff = 0.0                   # current-period effective contribution fraction
        self._baseEMA = None                  # EMA of regional-equity base (boom signal)
        self.lastBoom = 0.0

        # bookkeeping for reporting
        self.nRecap = 0                       # recaps performed this period
        self.nRecapTotal = 0
        self.nRecapFailed = 0                 # banks that asked but fund could not cover
        self.contribThisPeriod = 0.0
        self.recapThisPeriod = 0.0

    # ---- policy update: compute the countercyclical contribution fraction ----
    def updatePolicy(self, McountryBank):
        """Set gammaEff for this period from a regional-credit boom signal.

        Boom signal = deviation of the regional-equity base (sum of regional
        banks' A, which drives loanSupply = mu1*A) above its EMA. gammaEff rises
        with the boom, so the fund drains harder exactly when credit is running
        away. When the fund is off, gammaEff is 0 (exact baseline behaviour)."""
        self.nRecap = 0
        self.contribThisPeriod = 0.0
        self.recapThisPeriod = 0.0
        if not self.on:
            self.gammaEff = 0.0
            return
        base = 0.0
        for bank in McountryBank.get(self.country, {}):
            b = McountryBank[self.country][bank]
            if getattr(b, 'isRegional', False) and getattr(b, 'closing', 'no') == 'no':
                base += max(0.0, b.A)
        if self._baseEMA is None or self._baseEMA <= 1e-9:
            self._baseEMA = base if base > 0 else 1e-9
            boom = 0.0
        else:
            boom = max(0.0, base / self._baseEMA - 1.0)
            self._baseEMA = self.emaAlpha * base + (1.0 - self.emaAlpha) * self._baseEMA
        self.lastBoom = boom
        g = self.contribBase * (1.0 + self.countercyclical * boom)
        if g < 0.0:
            g = 0.0
        if g > 1.0:
            g = 1.0
        self.gammaEff = g

    # ---- contribution: bank -> fund (called from bank.distributingDividends) ----
    # The caller has already reduced bank.A by `amount`. Here we move the cash:
    # the bank pays `amount` out of its reserves (reserveWithdrawal also debits
    # the central bank), and the fund receives those reserves (re-crediting the
    # central bank, so CB total is unchanged).
    def receiveContribution(self, amount, bank, McountryCentralBank):
        if amount <= 0.0:
            return
        bank.reserveWithdrawal(amount, McountryCentralBank)          # bank.Reserves-=, CB.Reserves-=
        self.Reserves += amount
        McountryCentralBank[bank.country].Reserves += amount         # CB.Reserves+= (held by fund)
        self.totalIn += amount
        self.contribThisPeriod += amount

    # ---- recapitalisation: fund -> bank (all-or-nothing) ----
    # Bring the bank's equity up to `target` by injecting reserves. Returns True
    # iff the fund could cover the FULL amount.
    def attemptRecap(self, bank, target, McountryCentralBank):
        need = target - bank.A
        if need <= 0.0:
            return True  # already viable; nothing to do
        if self.Reserves + 1e-9 < need:
            self.nRecapFailed += 1
            return False
        # fund pays `need` in reserves ...
        self.Reserves -= need
        McountryCentralBank[bank.country].Reserves -= need
        # ... bank receives reserves and the matching equity injection
        bank.Reserves += need
        McountryCentralBank[bank.country].Reserves += need
        bank.A += need
        self.totalOut += need
        self.recapThisPeriod += need
        self.nRecap += 1
        self.nRecapTotal += 1
        return True

    # ---- accounting tripwire ----
    def checkIdentity(self, tol=1e-6):
        if self.Reserves < -1e-9:
            raise AssertionError(
                "SFC invariant violated: fund.py negative Reserves (country %s)" % str(self.country))
        residual = self.Reserves - (self.totalIn - self.totalOut)
        if abs(residual) > tol:
            raise AssertionError(
                "SFC invariant violated: fund.py Reserves != totalIn-totalOut "
                "(country %s, residual %.6g)" % (str(self.country), residual))


def createFunds(Lcountry, on=False, contribBase=0.0, countercyclical=0.0,
                recapKappa=2.0, recapOn=True):
    """Build {country: RelationshipFund} for every country."""
    return {c: RelationshipFund(c, on=on, contribBase=contribBase,
                                countercyclical=countercyclical,
                                recapKappa=recapKappa, recapOn=recapOn)
            for c in Lcountry}
