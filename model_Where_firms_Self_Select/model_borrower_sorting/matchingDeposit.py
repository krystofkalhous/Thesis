# matchingDeposit.py
#
# Contains two classes:
#   MatchingDeposit         — baseline Di Guilmi deposit allocation (random shuffle)
#   MatchingDepositRegional — extends MatchingDeposit with a local deposit bias
#                             for regional consumers (per-country toggle)
#
# REGIONAL MECHANISM
# ==================
# matchDeposit is overridden in MatchingDepositRegional. For each consumer,
# instead of a pure random shuffle of all bank demand slots, we first check
# whether the consumer has a regional bank (looked up via
# DregionalBankByRegion[country][region]). If yes:
#   - With probability depositLocalBias, the regional bank is placed FIRST
#     in the shuffled demand list (it wins the deposit allocation that period).
#   - With probability (1 - depositLocalBias), the list is shuffled randomly
#     as in the baseline (the regional bank has no advantage).
#
# Only the selection of ideBank in matchDeposit changes. The deposit/reserve
# accounting lines are identical to the baseline. checkNetWorth() is unaffected.

import random


# ---------------------------------------------------------------------------
# Base class: Di Guilmi baseline (unchanged from original matchingDeposit.py)
# ---------------------------------------------------------------------------

class MatchingDeposit:
      def __init__(self,Lcountry):
         self.DinCentralBank={}
         for country in Lcountry:
             self.DinCentralBank[country]='zero'

      def creatingAccount(self,McountryConsumer,McountryFirm,McountryBank,McountryCentralBank):
          for country in McountryConsumer:
              Lbank=[]
              for bank in McountryBank[country]:
                  Lbank.append(bank)
              if len(McountryBank[country])>0 and self.DinCentralBank[country]=='no':
                 for consumer in McountryConsumer[country]:
                     if len(McountryConsumer[country][consumer].Mdeposit)==0:
                        random.shuffle(Lbank)
                        ideBank=Lbank[0]
                        ideConsumer=consumer
                        interestRate=McountryBank[country][ideBank].rDeposit
                        deposit=0
                        McountryBank[country][ideBank].Mdeposit[ideConsumer]=[ideConsumer,ideBank,deposit,interestRate,country]
                        McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                        McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit
                        McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+deposit
                        McountryConsumer[country][ideConsumer].Mdeposit[ideBank]=[ideConsumer,ideBank,deposit,interestRate,country]
                     elif (country in McountryConsumer[country][consumer].Mdeposit)==True:
                        random.shuffle(Lbank)
                        ideBank=Lbank[0]
                        ideConsumer=consumer
                        interestRate=McountryBank[country][ideBank].rDeposit
                        deposit=McountryConsumer[country][consumer].Mdeposit[country][2]
                        del McountryConsumer[country][consumer].Mdeposit[country]
                        del McountryCentralBank[country].Mdeposit[ideConsumer]
                        McountryCentralBank[country].Deposit=McountryCentralBank[country].Deposit-deposit
                        McountryBank[country][ideBank].Mdeposit[ideConsumer]=[ideConsumer,ideBank,deposit,interestRate,country]
                        McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                        McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit
                        McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+deposit
                        McountryConsumer[country][ideConsumer].Mdeposit[ideBank]=[ideConsumer,ideBank,deposit,interestRate,country]
                 for firm in McountryFirm[country]:
                     if len(McountryFirm[country][firm].Mdeposit)==0:
                        random.shuffle(Lbank)
                        ideBank=Lbank[0]
                        ideFirm=firm
                        interestRate=McountryBank[country][ideBank].rDeposit
                        deposit=McountryFirm[country][firm].A
                        McountryBank[country][ideBank].Mdeposit[ideFirm]=[ideFirm,ideBank,deposit,interestRate,country]
                        McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                        McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit
                        McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+deposit
                        McountryFirm[country][ideFirm].Mdeposit[ideBank]=[ideFirm,ideBank,deposit,interestRate,country]
                     elif (country in McountryFirm[country][firm].Mdeposit)==True:
                          if len(McountryFirm[country][firm].Mdeposit)==1:
                              random.shuffle(Lbank)
                              ideBank=Lbank[0]
                              ideFirm=firm
                              interestRate=McountryBank[country][ideBank].rDeposit
                              deposit=McountryFirm[country][firm].Mdeposit[country][2]
                              del McountryCentralBank[country].Mdeposit[ideFirm]
                              del McountryFirm[country][firm].Mdeposit[country]
                              McountryCentralBank[country].Deposit=McountryCentralBank[country].Deposit-deposit
                              McountryBank[country][ideBank].Mdeposit[ideFirm]=[ideFirm,ideBank,deposit,interestRate,country]
                              McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                              McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit
                              McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+deposit
                              McountryFirm[country][ideFirm].Mdeposit[ideBank]=[ideFirm,ideBank,deposit,interestRate,country]
                          else:
                              for bank in self.LbankDeposit:
                                  if bank!=country:
                                     ideBank=bank
                                     ideFirm=firm
                                     interestRate=McountryBank[country][ideBank].rDeposit
                                     deposit=McountryFirm[country][firm].Mdeposit[country][2]
                                     del McountryCentralBank[country].Mdeposit[ideFirm]
                                     del McountryFirm[country][firm].Mdeposit[country]
                                     McountryCentralBank[country].Deposit=McountryCentralBank[country].Deposit-deposit
                                     McountryBank[country][ideBank].Mdeposit[ideFirm]=[ideFirm,ideBank,deposit,interestRate,country]
                                     McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                                     McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit
                                     McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+deposit
                                     McountryFirm[country][ideFirm].Mdeposit[ideBank]=[ideFirm,ideBank,deposit,interestRate,country]
                     McountryFirm[country][firm].orderBankDeposit(McountryBank)
              if len(McountryBank[country])>0 and self.DinCentralBank[country]=='yes':
                 for consumer in McountryConsumer[country]:
                     if (country in McountryConsumer[country][consumer].Mdeposit)==True:
                        random.shuffle(Lbank)
                        ideBank=Lbank[0]
                        ideConsumer=consumer
                        interestRate=McountryBank[country][ideBank].rDeposit
                        deposit=McountryConsumer[country][consumer].Mdeposit[country][2]
                        if deposit<McountryCentralBank[country].Mdeposit[ideConsumer][2]-0.00001 or\
                           deposit>McountryCentralBank[country].Mdeposit[ideConsumer][2]+0.00001:
                           raise AssertionError("SFC invariant violated: matchingDeposit.py:120 in creatingAccount()")
                        del McountryConsumer[country][consumer].Mdeposit[country]
                        del McountryCentralBank[country].Mdeposit[ideConsumer]
                        McountryCentralBank[country].Deposit=McountryCentralBank[country].Deposit-deposit
                        McountryBank[country][ideBank].Mdeposit[ideConsumer]=[ideConsumer,ideBank,deposit,interestRate,country]
                        McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                        McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit
                        McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+deposit
                        McountryConsumer[country][ideConsumer].Mdeposit[ideBank]=[ideConsumer,ideBank,deposit,interestRate,country]
                        McountryConsumer[country][ideConsumer].orderBankDeposit()
                 for firm in McountryFirm[country]:
                     if (country in McountryFirm[country][firm].Mdeposit)==True:
                        random.shuffle(Lbank)
                        ideBank=Lbank[0]
                        ideFirm=firm
                        interestRate=McountryBank[country][ideBank].rDeposit
                        deposit=McountryFirm[country][firm].Mdeposit[country][2]
                        if deposit<McountryCentralBank[country].Mdeposit[ideFirm][2]-0.00001 or\
                           deposit>McountryCentralBank[country].Mdeposit[ideFirm][2]+0.00001:
                           raise AssertionError("SFC invariant violated: matchingDeposit.py:139 in creatingAccount()")
                        del McountryCentralBank[country].Mdeposit[ideFirm]
                        del McountryFirm[country][firm].Mdeposit[country]
                        McountryCentralBank[country].Deposit=McountryCentralBank[country].Deposit-deposit
                        McountryBank[country][ideBank].Mdeposit[ideFirm]=[ideFirm,ideBank,deposit,interestRate,country]
                        McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                        McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit
                        McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+deposit
                        McountryFirm[country][ideFirm].Mdeposit[ideBank]=[ideFirm,ideBank,deposit,interestRate,country]
                        if interestRate<-0.00001:
                           raise AssertionError("SFC invariant violated: matchingDeposit.py:149 in creatingAccount()")
                     else:
                        random.shuffle(Lbank)
                        ideBank=Lbank[0]
                        ideFirm=firm
                        interestRate=McountryBank[country][ideBank].rDeposit
                        deposit=McountryFirm[country][firm].A
                        McountryBank[country][ideBank].Mdeposit[ideFirm]=[ideFirm,ideBank,deposit,interestRate,country]
                        McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                        McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit
                        McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+deposit
                        McountryFirm[country][ideFirm].Mdeposit[ideBank]=[ideFirm,ideBank,deposit,interestRate,country]
                     McountryFirm[country][firm].orderBankDeposit(McountryBank)
              if len(McountryBank[country])==0:
                 self.DinCentralBank[country]='yes'
                 for consumer in McountryConsumer[country]:
                     if len(McountryConsumer[country][consumer].Mdeposit)==0:
                        ideBank=country
                        ideConsumer=consumer
                        interestRate=McountryCentralBank[country].rDeposit
                        deposit=0
                        McountryCentralBank[country].Mdeposit[ideConsumer]=[ideConsumer,ideBank,deposit,interestRate,country]
                        McountryCentralBank[country].Deposit=McountryCentralBank[country].Deposit+deposit
                        McountryConsumer[country][ideConsumer].Mdeposit[ideBank]=[ideConsumer,ideBank,deposit,interestRate,country]
                        McountryConsumer[country][ideConsumer].orderBankDeposit()
                 for firm in McountryFirm[country]:
                     if len(McountryFirm[country][firm].Mdeposit)==0:
                        ideBank=country
                        ideFirm=firm
                        interestRate=McountryCentralBank[country].rDeposit
                        deposit=McountryFirm[country][firm].A
                        McountryCentralBank[country].Mdeposit[ideFirm]=[ideFirm,ideBank,deposit,interestRate,country]
                        McountryFirm[country][ideFirm].Mdeposit[ideBank]=[ideFirm,ideBank,deposit,interestRate,country]
                        McountryCentralBank[country].Deposit=McountryCentralBank[country].Deposit+deposit
                     McountryFirm[country][firm].orderBankDeposit(McountryBank)

      def allocatingConsumerDeposit(self,McountryConsumer,McountryBank):
          self.MdepositSupply={}
          self.MdepositDemand={}
          for country in McountryBank:
              if len(McountryBank[country])>1 and self.DinCentralBank[country]=='no':
                 self.extractingDeposit(McountryConsumer,McountryBank,country)
                 self.matchDeposit(McountryConsumer,McountryBank,country)
                 if self.createdReserves>self.delatedReserves+0.00001 or self.createdReserves<self.delatedReserves-0.00001:
                    raise AssertionError("SFC invariant violated: matchingDeposit.py:193 in allocatingConsumerDeposit()")
              if len(McountryBank[country])>0:
                 self.DinCentralBank[country]='no'

      def extractingDeposit(self,McountryConsumer,McountryBank,country):
              self.delatedReserves=0
              self.MdepositDemand[country]=[]
              self.MdepositSupply[country]=[]
              for consumer in McountryConsumer[country]:
                  if len(McountryConsumer[country][consumer].Mdeposit)>1:
                     raise AssertionError("SFC invariant violated: matchingDeposit.py:203 in extractingDeposit()")
                  for ideBank in McountryConsumer[country][consumer].Mdeposit:
                      deposit=McountryConsumer[country][consumer].Mdeposit[ideBank][2]
                  del McountryBank[country][ideBank].Mdeposit[consumer]
                  McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit-deposit
                  McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves-deposit
                  self.delatedReserves=self.delatedReserves+deposit
                  McountryConsumer[country][consumer].Mdeposit
                  McountryConsumer[country][consumer].Mdeposit={}
                  McountryConsumer[country][consumer].depositAllocated=0
                  depositSupply=[McountryConsumer[country][consumer].ide,deposit]
                  McountryConsumer[country][consumer].Depositing
                  self.MdepositSupply[country].append(depositSupply)
              for bank in McountryBank[country]:
                  depositDemand=[McountryBank[country][bank].ide,McountryBank[country][bank].rDeposit]
                  self.MdepositDemand[country].append(depositDemand)

      def matchDeposit(self,McountryConsumer,McountryBank,country):
              self.createdReserves=0
              for depositSupply in self.MdepositSupply[country]:
                  random.shuffle(self.MdepositDemand[country])
                  depositDemand=self.MdepositDemand[country][0]
                  ideConsumer=depositSupply[0]
                  deposit=depositSupply[1]
                  ideBank=depositDemand[0]
                  interestRate=depositDemand[1]
                  McountryConsumer[country][ideConsumer].Mdeposit[ideBank]=[ideConsumer,ideBank,deposit,interestRate,country]
                  McountryBank[country][ideBank].Mdeposit[ideConsumer]=[ideConsumer,ideBank,deposit,interestRate,country]
                  McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                  McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit
                  self.createdReserves=self.createdReserves+deposit


# ---------------------------------------------------------------------------
# Subclass: regional deposit bias (extends MatchingDeposit above)
# ---------------------------------------------------------------------------

class MatchingDepositRegional(MatchingDeposit):

    def __init__(self, Lcountry, depositLocalBias=0.35, useRegionalBanks=None):
        super().__init__(Lcountry)
        self.depositLocalBias = depositLocalBias
        # useRegionalBanks: dict {country: bool} or legacy bool.
        # None / missing key -> False (Di Guilmi baseline for that country).
        if useRegionalBanks is None:
            self.useRegionalBanks = {}
        else:
            self.useRegionalBanks = useRegionalBanks
        # DregionalBankByRegion[country][region] = bank ide
        # Populated each period by updateRegionalBankMap() called from timing.
        self.DregionalBankByRegion = {}

    def updateRegionalBankMap(self, McountryBank):
        """Rebuild the region -> regional bank ide lookup each period.
        Called from timing.py before allocatingConsumerDeposit.
        Only banks tagged isRegional=True and with positive equity are included.
        Banks in countries where useRegionalBanks=False are excluded.
        """
        self.DregionalBankByRegion = {}
        for country in McountryBank:
            self.DregionalBankByRegion[country] = {}
            _urb = self.useRegionalBanks
            _countryOn = (_urb.get(country, False) if isinstance(_urb, dict) else bool(_urb))
            if not _countryOn:
                continue
            for bide in McountryBank[country]:
                bobj = McountryBank[country][bide]
                if (getattr(bobj, 'isRegional', False)
                        and getattr(bobj, 'region', -1) >= 0
                        and bobj.closing == 'no'):
                    r = bobj.region
                    self.DregionalBankByRegion[country][r] = bide

    def _consumerRegion(self, consumeride):
        """Extract region from consumer ide 'C<country>n<i>' -> i % nRegion.
        Returns -1 if parsing fails (guard for unexpected ide formats).
        """
        try:
            return int(consumeride.split('n')[1]) % self._nRegion
        except Exception:
            return -1

    def matchDeposit(self, McountryConsumer, McountryBank, country):
        """Override: bias deposit allocation toward regional bank.
        For each consumer, with probability depositLocalBias the regional
        bank is moved to the front of the shuffled demand list.
        All accounting is identical to the baseline.
        """
        self.createdReserves = 0

        regByRegion = self.DregionalBankByRegion.get(country, {})
        _urb = self.useRegionalBanks
        _countryOn = (_urb.get(country, False) if isinstance(_urb, dict) else bool(_urb))
        useReg = _countryOn and len(regByRegion) > 0
        bias = self.depositLocalBias

        for depositSupply in self.MdepositSupply[country]:
            ideConsumer = depositSupply[0]
            deposit     = depositSupply[1]

            # Shuffle demand list (baseline behaviour)
            random.shuffle(self.MdepositDemand[country])

            if useReg and bias > 0:
                consRegion = self._consumerRegion(ideConsumer)
                regBankIde = regByRegion.get(consRegion)
                if regBankIde is not None:
                    regIdx = next(
                        (i for i, d in enumerate(self.MdepositDemand[country])
                         if d[0] == regBankIde),
                        None
                    )
                    if regIdx is not None and random.random() < bias:
                        regEntry = self.MdepositDemand[country].pop(regIdx)
                        self.MdepositDemand[country].insert(0, regEntry)

            # Take first bank from (possibly reordered) demand list
            depositDemand = self.MdepositDemand[country][0]
            ideBank       = depositDemand[0]
            interestRate  = depositDemand[1]

            # Accounting: identical to baseline matchDeposit
            McountryConsumer[country][ideConsumer].Mdeposit[ideBank] = [
                ideConsumer, ideBank, deposit, interestRate, country]
            McountryBank[country][ideBank].Mdeposit[ideConsumer] = [
                ideConsumer, ideBank, deposit, interestRate, country]
            McountryBank[country][ideBank].Deposit  += deposit
            McountryBank[country][ideBank].Reserves += deposit
            self.createdReserves += deposit
