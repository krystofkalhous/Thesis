2#enterExit.py

import random
from firm import Firm
from bank import Bank

class enterExit:
      def __init__(self,Lcountry,McountryFirmMaxNumber,\
                   folder,name,run,\
                   delta,initialA,McountryBankMaxNumber,probBank,minReserve,\
                   rDiscount,xi,dividendRate,iota,rDeposit,\
                   upsilon,gamma,deltaInnovation,mu1,\
                   propTradable,Fcost,ni,minMarkUp,iotaE,theta,sigma,upsilon2,jobDuration,\
                   sensitivity_a=0.01,chiBasel=0.0625,a0=None,aExpBank=None,aExpFirm=None,\
                   nRegion=5,useRegionalBanks=None,regionalDividendRate=None,\
                   firmEntryMode='regional',entryTrace=False,\
                   lockRelationshipReserves=False,reserveDevolution='owners'):
          self.Lcountry=Lcountry
          self.McountryFirmMaxNumber=McountryFirmMaxNumber
          self.folder=folder
          self.name=name
          self.run=run
          self.ni=ni
          self.upsilon=upsilon
          self.delta=delta
          self.initialA=initialA
          self.initialPhi=1.0
          self.initialWage=1.0
          self.initialPrice=1.0
          self.DminBankSizePast={}
          self.DmaxBankSizePast={}
          self.bound=10
          self.upsilon2=upsilon2 
          for country in Lcountry:
              self.DminBankSizePast[country]=4*self.initialA
              self.DmaxBankSizePast[country]=4*self.initialA
          self.McountryBankMaxNumber=McountryBankMaxNumber
          self.probBank=probBank 
          self.minReserve=minReserve
          self.rDeposit=rDeposit
          self.xi=xi 
          self.dividendRate=dividendRate
          # Regional banks retain more equity (no private shareholders to pay out).
          # If regionalDividendRate is not supplied, fall back to the global
          # dividendRate so the Di Guilmi baseline stays bit-identical.
          if regionalDividendRate is None:
              self.regionalDividendRate=dividendRate
          else:
              self.regionalDividendRate=regionalDividendRate
          self.initialProbBank=self.probBank
          self.iota=iota 
          self.rDiscount=rDiscount
          self.gamma=gamma
          self.deltaInnovation=deltaInnovation
          self.mu1=mu1
          self.sensitivity_a=sensitivity_a
          self.chiBasel=chiBasel
          self.a0=a0
          self.aExpBank=aExpBank
          self.aExpFirm=aExpFirm
          self.nRegion=nRegion
          # useRegionalBanks: dict {country: bool} or legacy bool for compat.
          # Default {} means all countries use Di Guilmi baseline.
          if useRegionalBanks is None:
              self.useRegionalBanks={}
          else:
              self.useRegionalBanks=useRegionalBanks
          self.firmEntryMode=firmEntryMode
          self.entryTrace=entryTrace
          self.lockRelationshipReserves=lockRelationshipReserves
          self.reserveDevolution=reserveDevolution
          self.propTradable=propTradable 
          self.DcountryFirmEnter={}
          self.Fcost=Fcost
          self.minMarkUp=minMarkUp 
          self.iotaE=iotaE 
          self.theta=theta
          self.sigma=sigma
          self.DcountryFirmEnterTradable={}
          for country in self.Lcountry:
              self.DcountryFirmEnter[country]=0
              self.DcountryFirmEnterTradable[country]=0
          self.DcountryFirmExit={}
          self.DcountryFirmExitTradable={}  
          for country in self.Lcountry:
              self.DcountryFirmExit[country]=0
              self.DcountryFirmExitTradable[country]=0
          self.DcountryBankEnter={}
          for country in self.Lcountry:
              self.DcountryBankEnter[country]=0
          self.DcountryBankExit={}
          for country in self.Lcountry:
              self.DcountryBankExit[country]=0
          self.DcountryAverageWage={} 
          for country in self.Lcountry:
              self.DcountryAverageWage[country]=1.0  
          self.DcountryFirmGone={} 
          self.DcountryBankGone={} 
          self.DcountryForeignBankLosses={}  
          self.DcountryEnterValue={}
          self.DcountryUpsilon={}
          self.DcountryJobDuration={}  
          self.DcountryIotaRelPhi={}
          for country in self.Lcountry:
              self.DcountryFirmGone[country]={}
              self.DcountryBankGone[country]={}
              self.DcountryForeignBankLosses[country]=0  
              self.DcountryEnterValue[country]=0
              self.DcountryUpsilon[country]=self.upsilon
              self.DcountryJobDuration[country]=jobDuration
              self.DcountryIotaRelPhi[country]=self.iota 
          
      def minMaxAgents(self,McountryFirm,McountryBank,country,McountryAvPrice):
          LbankSize=[]
          for bank in McountryBank[country]:
              if not getattr(McountryBank[country][bank],'isRegional',False):
                  LbankSize.append(McountryBank[country][bank].A)
          if len(LbankSize)>0:
             self.minBankSize=min(LbankSize)
             self.maxBankSize=max(LbankSize)
             self.medianBankSize=LbankSize[int(len(LbankSize)/2.0)]
          if len(LbankSize)==0:
             if McountryAvPrice[country]>0:
                self.minBankSize=self.DminBankSizePast[country]
                self.maxBankSize=self.DmaxBankSizePast[country]
                self.medianBankSize=self.initialA*McountryAvPrice[country]
             if McountryAvPrice[country]<=0:
                self.minBankSize=self.initialA
                self.maxBankSize=self.initialA 
                self.medianBankSize=self.initialA   
          self.minBankSizePast=self.DminBankSizePast[country] 
          self.maxBankSizePast=self.DmaxBankSizePast[country]          
          self.DminBankSizePast[country]=self.minBankSize
          self.DmaxBankSizePast[country]=self.maxBankSize
          LfirmSizeNotTradable=[]
          LfirmPhiNotTradable=[] 
          LfirmPriceNotTradable=[]
          LfirmWageNotTradable=[]
          LfirmExNotTradable=[]
          sumW=0
          sumL=0
          sumQ=0 
          sumQNotTradable=0
          sumQTradable=0 
          for firm in McountryFirm[country]:
              sumW=sumW+McountryFirm[country][firm].w
              sumL=sumL+McountryFirm[country][firm].l
              sumQ=sumQ+McountryFirm[country][firm].xSold #Lsold[2]
              if McountryFirm[country][firm].tradable=='no':
                 LfirmSizeNotTradable.append(McountryFirm[country][firm].A)
                 LfirmExNotTradable.append(McountryFirm[country][firm].mind.xE)
                 LfirmPhiNotTradable.append(McountryFirm[country][firm].phi) 
                 LfirmPriceNotTradable.append(McountryFirm[country][firm].price) #Lselling[0]) 
                 LfirmWageNotTradable.append(McountryFirm[country][firm].w)  
                 sumQNotTradable=sumQNotTradable+McountryFirm[country][firm].xSold #Lsold[2]
          self.averageWage=1.0       
          if sumL>0:
             self.averageWage=sumW/float(sumL)  
          if len(LfirmSizeNotTradable)>0:
             self.minFirmSizeNotTradable=min(LfirmSizeNotTradable)
             self.maxFirmSizeNotTradable=max(LfirmSizeNotTradable)
             self.minFirmExNotTradable=min(LfirmExNotTradable)
             self.maxFirmExNotTradable=max(LfirmExNotTradable)
             self.medianFirmExNotTradable=LfirmExNotTradable[int(len(LfirmExNotTradable)/2.0)] 
             self.medianFirmSizeNotTradable=LfirmSizeNotTradable[int(len(LfirmSizeNotTradable)/2.0)]
             self.minFirmPhiNotTradable=min(LfirmPhiNotTradable)
             self.maxFirmPhiNotTradable=max(LfirmPhiNotTradable)
             self.medianFirmPhiNotTradable=LfirmPhiNotTradable[int(len(LfirmPhiNotTradable)/2.0)]
             self.minFirmPriceNotTradable=min(LfirmPriceNotTradable)
             self.maxFirmPriceNotTradable=max(LfirmPriceNotTradable)
             self.medianFirmPriceNotTradable=LfirmPriceNotTradable[int(len(LfirmPriceNotTradable)/2.0)]  
             self.meanFirmPriceNotTradable=sum(LfirmPriceNotTradable)/len(LfirmPriceNotTradable)          
             self.minFirmWageNotTradable=min(LfirmWageNotTradable)
             self.maxFirmWageNotTradable=max(LfirmWageNotTradable) 
             self.medianFirmWageNotTradable=LfirmWageNotTradable[int(len(LfirmWageNotTradable)/2.0)]
          if len(LfirmSizeNotTradable)==0:
             self.minFirmSizeNotTradable=self.initialA
             self.maxFirmSizeNotTradable=self.initialA
             self.minFirmExNotTradable=self.initialA
             self.maxFirmExNotTradable=self.initialA  
             self.medianFirmExNotTradable=self.initialA
             self.medianFirmSizeNotTradable=self.initialA
             self.minFirmPhiNotTradable=self.initialPhi
             self.maxFirmPhiNotTradable=self.initialPhi
             self.medianFirmPhiNotTradable=self.initialPhi
             self.minFirmPriceNotTradable=self.initialPrice
             self.maxFirmPriceNotTradable=self.initialPrice
             self.meanFirmPriceNotTradable=self.initialPrice
             self.medianFirmPriceNotTradable=self.initialPrice
             self.minFirmWageNotTradable=self.initialWage
             self.maxFirmWageNotTradable=self.initialWage
             self.medianFirmWageNotTradable=self.initialWage
          LfirmSizeTradable=[]
          LfirmExTradable=[]
          LfirmPhiTradable=[] 
          LfirmPriceTradable=[]
          LfirmWageTradable=[]    
          for firm in McountryFirm[country]:
              if McountryFirm[country][firm].tradable=='yes':
                 LfirmSizeTradable.append(McountryFirm[country][firm].A)
                 LfirmExTradable.append(McountryFirm[country][firm].mind.xE)
                 LfirmPhiTradable.append(McountryFirm[country][firm].phi) 
                 LfirmPriceTradable.append(McountryFirm[country][firm].price) #Lselling[0]) 
                 LfirmWageTradable.append(McountryFirm[country][firm].w)
                 sumQTradable=sumQTradable+McountryFirm[country][firm].xSold #Lsold[2]
          if len(LfirmSizeTradable)>0:
             self.minFirmSizeTradable=min(LfirmSizeTradable)
             self.maxFirmSizeTradable=max(LfirmSizeTradable)
             self.minFirmExTradable=min(LfirmExTradable)
             self.maxFirmExTradable=max(LfirmExTradable)
             self.medianFirmExTradable=LfirmExTradable[int(len(LfirmExTradable)/2.0)]
             self.medianFirmSizeTradable=LfirmSizeTradable[int(len(LfirmSizeTradable)/2.0)]
             self.minFirmPhiTradable=min(LfirmPhiTradable)
             self.maxFirmPhiTradable=max(LfirmPhiTradable) 
             self.medianFirmPhiTradable=LfirmPhiTradable[int(len(LfirmPhiTradable)/2.0)]
             self.minFirmPriceTradable=min(LfirmPriceTradable)
             self.maxFirmPriceTradable=max(LfirmPriceTradable)
             self.medianFirmPriceTradable=LfirmPriceTradable[int(len(LfirmPriceTradable)/2.0)]
             self.meanFirmPriceTradable=sum(LfirmPriceTradable)/len(LfirmPriceTradable)
             self.minFirmWageTradable=min(LfirmWageTradable)
             self.maxFirmWageTradable=max(LfirmWageTradable) 
             self.medianFirmWageTradable=LfirmWageTradable[int(len(LfirmWageTradable)/2.0)]
          if len(LfirmSizeTradable)==0:
             self.minFirmSizeTradable=self.initialA
             self.maxFirmSizeTradable=self.initialA
             self.minFirmExTradable=self.initialA
             self.maxFirmExTradable=self.initialA
             self.medianFirmExTradable=self.initialA
             self.medianFirmSizeTradable=self.initialA
             self.minFirmPhiTradable=self.initialPhi
             self.maxFirmPhiTradable=self.initialPhi
             self.medianFirmPhiTradable=self.initialPhi
             self.minFirmPriceTradable=self.initialPrice
             self.maxFirmPriceTradable=self.initialPrice
             self.medianFirmPriceTradable=self.initialPrice
             self.meanFirmPriceTradable=self.initialPrice 
             self.minFirmWageTradable=self.initialWage
             self.maxFirmWageTradable=self.initialWage 
             self.medianFirmWageTradable=self.initialWage   
          self.avQ=0
          self.avQNotTradable=0  
          self.avQTradable=0 
          if len(McountryFirm[country])>0:
             self.avQ=sumQ/float(len(McountryFirm[country]))
          if len(LfirmSizeTradable)>0:
             self.avQTradable=sumQTradable/float(len(LfirmSizeTradable))
          if len(LfirmSizeNotTradable)>0:
             self.avQNotTradable=sumQNotTradable/float(len(LfirmSizeNotTradable))

      def whichSize(self,kind):
          if kind=='firmNotTradable':
             price=self.whichPrice('firmNotTradable')
             phi=self.whichPhi('firmNotTradable')
             wage=self.whichWage('firmNotTradable')
             size=max(self.initialA,wage,random.uniform(self.minFirmSizeNotTradable,self.maxFirmSizeNotTradable))
             eX=self.whichEx('firmNotTradable',phi,price,wage)
             Lkind=[kind,size,phi,price,wage,eX]
          if kind=='firmTradable':
             price=self.whichPrice('firmTradable')
             phi=self.whichPhi('firmTradable')
             wage=self.whichWage('firmTradable')
             size=max(self.initialA,wage,random.uniform(self.minFirmSizeTradable,self.maxFirmSizeTradable))
             eX=self.whichEx('firmTradable',phi,price,wage)
             Lkind=[kind,size,phi,price,wage,eX]
          if kind=='bank':
             size=random.uniform(self.minBankSizePast,self.maxBankSizePast)
             sizeMin=max(self.sigma*self.medianFirmSizeNotTradable,4*self.medianFirmSizeTradable,self.minBankSizePast) 
             size=random.uniform(sizeMin,self.maxBankSizePast)
             Lkind=[kind,size]
          return Lkind
                 
      def whichPhi(self,kind):
          if kind=='firmNotTradable':
             phi=random.uniform(self.minFirmPhiNotTradable,self.maxFirmPhiNotTradable)
          if kind=='firmTradable':
             phi=random.uniform(self.minFirmPhiTradable,self.maxFirmPhiTradable)
          return phi
          
      def whichPrice(self,kind):
          if kind=='firmNotTradable':
             price=random.uniform(self.minFirmPriceNotTradable,self.maxFirmPriceNotTradable)
          if kind=='firmTradable':
             price=random.uniform(self.minFirmPriceTradable,self.maxFirmPriceTradable)
          return price
          
      def whichWage(self,kind):
          if kind=='firmNotTradable':
             wage=random.uniform(self.minFirmWageNotTradable,self.maxFirmWageNotTradable)
          if kind=='firmTradable':
             wage=random.uniform(self.minFirmWageTradable,self.maxFirmWageTradable)
          return wage   

      def whichEx(self,kind,phi,p,wage):
          if kind=='firmNotTradable': 
             xE=random.uniform(self.minFirmExNotTradable,self.maxFirmExNotTradable)
          if kind=='firmTradable':
             xE=random.uniform(self.minFirmExTradable,self.maxFirmExTradable)
          return xE   

      def whichAgentEnter6(self, country, McountryFirm, McountryBank,
                           firmOnly=False):
          nBank=len(McountryBank[country])
          newAgent='no'
          ABank=0
          for bank in McountryBank[country]:
              ABank=ABank+McountryBank[country][bank].A
          AFirm=0
          for firm in McountryFirm[country]:
              AFirm=AFirm+McountryFirm[country][firm].A    
          nFirm=len(McountryFirm[country])
          nBank=len(McountryBank[country])
          if nFirm>0:
             ratioBankFirm=ABank/float(AFirm)
             rationBankFirmNumber=nBank/float(nFirm)
          if nFirm==0 and nBank==0:
             # No agents yet: must bootstrap with a bank first.
             # (Firms need banks to exist; setting ratio=0 triggers bank entry.)
             ratioBankFirm=0
             rationBankFirmNumber=0
          elif nFirm==0:
             ratioBankFirm=1   
             rationBankFirmNumber=1  
          if not firmOnly:
              # Normal path: may enter a bank if ratios are below threshold
              if ratioBankFirm<self.initialProbBank or rationBankFirmNumber<self.initialProbBank:
                 newAgent='bank'
          if (firmOnly or
              (ratioBankFirm>=self.initialProbBank and
               rationBankFirmNumber>=self.initialProbBank)):
             a=random.uniform(0,1)
             if a<self.propTradable:
                newAgent='firmTradable'
             else:
                newAgent='firmNotTradable'  
          return newAgent   
       

      def _consumerRegion(self, consumeride):
          try: return int(consumeride.split('n')[1]) % self.nRegion
          except: return 0

      def _mostCommonRegion(self, consumerList):
          from collections import Counter
          counts = Counter(self._consumerRegion(c) for c in consumerList)
          return counts.most_common(1)[0][0]

      def _createRegionalBanksInEnter(self, country, McountryConsumer, McountryBank,
                                       McountryCentralBank, McountryAvPrice, McountryEtat,
                                       LconsumerAsset, avWage=1.0):
          """Create one regional bank per uncovered region, funded by that region's
          investing consumers. Called from enter() BEFORE the global investing pool
          is built, so consumers used here (Investing set to 0) are excluded from
          global bank/firm entry in the same period.

          Eligibility mirrors the global entry path (Investing > wBar*avWage,
          len(DLA) <= bound). The previous Expenditure<0.009 gate has been removed:
          the global entry path funds spenders via the same cobj.paying() accounting
          without any SFC desync, so the gate was unnecessary and starved creation.

          Each eligible consumer contributes their full Investing (capped at their
          summed deposit balance as a guard). The bank's equity equals the sum
          collected. Funding/accounting is identical to the global-bank entry path,
          so checkNetWorth() is unaffected.
          """
          # Per-country toggle: dict lookup, or legacy bool support
          _urb=self.useRegionalBanks
          if isinstance(_urb,dict):
              if not _urb.get(country,False):
                  return
          else:
              if not _urb:
                  return

          # Find uncovered regions
          covered = set()
          for bide in McountryBank[country]:
              bobj = McountryBank[country][bide]
              if getattr(bobj, 'isRegional', False):
                  covered.add(getattr(bobj, 'region', -1))

          uncovered = [r for r in range(self.nRegion) if r not in covered]
          if not uncovered:
              return

          # Minimum bank cost, scaled to a single region. A region holds ~1/nRegion
          # of the economy's consumers, so it is held to ~1/nRegion of the full
          # (global) bank size floor. Without this scaling, one region's ~nconsumer/nRegion
          # investors could essentially never reach the national bank-size floor, which
          # is why no regional bank was ever created.
          _minBankCost = (self.sigma * self.medianFirmSizeNotTradable) / float(max(self.nRegion, 1))

          for r in uncovered:
              # Build regional pool: this region's investing consumers
              # (same eligibility as global entry), funded up to their deposit balance.
              _pool = []
              for consumer in McountryConsumer[country]:
                  cobj = McountryConsumer[country][consumer]
                  if self._consumerRegion(consumer) != r:
                      continue
                  # Same eligibility as the global bank/firm entry path:
                  if cobj.Investing <= cobj.wBar * avWage:
                      continue
                  if len(cobj.DLA) > self.bound:
                      continue
                  # Fund from full Investing (as the global path does), capped at the
                  # consumer's summed deposit balance as a guard against over-withdrawal.
                  _bal = 0.0
                  for _bk in cobj.Mdeposit:
                      _bal += cobj.Mdeposit[_bk][2]
                  _avail = min(cobj.Investing, max(0.0, _bal))
                  if _avail > 0.001:
                      _pool.append((consumer, cobj, _avail))

              _regionTotal = sum(av for _, _, av in _pool)
              if _regionTotal < _minBankCost:
                  continue  # region cannot afford a bank yet

              # Create the regional bank with its real equity (= the region pool total,
              # which the wiring loop below collects in full). Constructing with the true
              # A keeps Bank.__init__'s A-derived fields (pastA, PreviousA, loanSupply)
              # consistent, exactly as the global-bank entry path does.
              number = self.McountryBankMaxNumber[country]
              self.McountryBankMaxNumber[country] = number + 1
              bankide = 'B' + str(country) + 'n' + str(number)
              iotaRelPhi = self.DcountryIotaRelPhi[country]
              newbank = Bank(bankide, country, _regionTotal, self.Lcountry, self.Fcost,
                             self.folder, self.name, self.run, self.delta,
                             self.minReserve, self.rDiscount, self.xi,
                             self.dividendRate, self.iota, self.rDeposit,
                             self.mu1, self.iotaE, iotaRelPhi,
                             
                             )
              newbank.isRegional = True
              newbank.region = r
              newbank.lockReserves = getattr(self, 'lockRelationshipReserves', False)
              # Regional banks retain more equity than commercial banks: override
              # the global dividendRate with regionalDividendRate. dividending()
              # reads self.dividendRate at distribution time, so this persists for
              # the bank's lifetime.
              newbank.dividendRate = self.regionalDividendRate

              # Wire shareholders: each pays their full available amount.
              # Wire shareholders using correct SFC accounting:
              #
              # CB-deposit path (deposits still at CB, early periods):
              #   paying() handles everything: CB.Deposit -= share, CB.Reserves unchanged.
              #   We then add _share to CB.Reserves (manual credit for the new bank).
              #
              # Commercial-bank-deposit path (later periods):
              #   consumptionDemand already deducted Investing from bank deposit record.
              #   We do an interbank reserve transfer:
              #     old_bank.Reserves -= share  (via reserveWithdrawal)
              #     CB.Reserves -= share        (via reserveWithdrawal)
              #     CB.Reserves += share        (re-credit: CB now owes reserves to new bank)
              #   Net CB.Reserves change = 0. No deposit records touched.
              random.shuffle(_pool)
              _acc = 0.0
              _newBankReserves = 0.0
              for (cide, cobj, _avail) in _pool:
                  if _acc >= _regionTotal:
                      break
                  _share = _avail
                  _ratioA = _share / max(_regionTotal, 0.0001)
                  _pos = 0
                  _fromCB = country in cobj.Mdeposit
                  cobj.Investing = 0
                  cobj.DLA[newbank.ide] = [cide, newbank.ide, _share, _pos, _ratioA]
                  cobj.paying(_share, McountryBank, McountryCentralBank)
                  # For CB-deposit path: paying() reduces CB.Deposit but not
                  # CB.Reserves. Credit CB.Reserves manually so the new bank's
                  # equity is reflected in CB's reserve liability.
                  # For commercial-bank path: paying() already reduced CB.Reserves
                  # (via bank.depositWithdrawal). Add it back so net CB.Reserves
                  # change = 0 and the new bank's Reserves are properly tracked.
                  McountryCentralBank[country].Reserves += _share
                  _newBankReserves += _share
                  LconsumerAsset.append([cide, newbank.ide, _share])
                  newbank.Downer[cide] = cobj.DLA[newbank.ide]
                  newbank.ListOwners.append(cide)
                  _acc += _share

              newbank.A = _acc
              newbank.Reserves = _newBankReserves
              self.DcountryEnterValue[country] += _acc
              McountryBank[country][newbank.ide] = newbank
              self.DcountryBankEnter[country] += 1
      def enter(self,McountryConsumer,McountryFirm,time,McountryBank,McountryCentralBank,McountryAvPrice,McountryEtat):
          # Guard notes:
          # Bank entry (regional seeding + global bank branch) is ALWAYS allowed,
          # even when no commercial banks exist yet.  Bank creation debits consumers
          # via paying(), but at t=0 consumer deposits sit at the CB; the CB path
          # in paying() keeps the CB balance sheet consistent because the CB records
          # the reduction on both sides (Deposit and Reserves).
          #
          # Firm entry calls paying() for the founding investors AND then the new firm
          # immediately calls paying() again for wages/production costs.  When there
          # are no commercial banks the CB balance sheet CAN break (asset side has no
          # matching reduction).  Therefore we guard firm-entry-only behind the check
          # len(McountryBank[country]) > 0.  Banks always enter first in period 0, so
          # by the time firms are attempted in the same period the guard is satisfied.
          enteringfirm=0
          enteringbank=0
          for country in McountryConsumer: 
              self.DcountryEnterValue[country]=0  
              totalInvesting=0 
              LconsumerInvesting=[]
              LconsumerAsset=[]
              self.DcountryFirmEnter[country]=0
              self.DcountryFirmEnterTradable[country]=0
              self.DcountryBankEnter[country]=0
              banksExist = len(McountryBank[country]) > 0
              enteringfirmC=0
              pos=0
              sumL=0
              sumW=0
              for consumer in McountryConsumer[country]:
                  sumL=sumL+McountryConsumer[country][consumer].l
                  sumW=sumW+McountryConsumer[country][consumer].wOffered
              avWage=1.0
              if sumL>0:
                 avWage=sumW/float(sumL)
              # minMaxAgents and _createRegionalBanksInEnter are called unconditionally:
              # regional banks must be seeded even when no commercial banks exist yet.
              # _createRegionalBanksInEnter funds banks from consumer deposits via
              # paying(), which routes correctly through the CB when no commercial banks
              # are present (the CB records both sides of the transaction).
              self.minMaxAgents(McountryFirm,McountryBank,country,McountryAvPrice)
              self._createRegionalBanksInEnter(
                  country,McountryConsumer,McountryBank,
                  McountryCentralBank,McountryAvPrice,McountryEtat,
                  LconsumerAsset,avWage)
              # Re-evaluate banksExist after regional bank seeding: regional banks
              # created just above count as commercial banks for the firm-entry guard.
              banksExist = len(McountryBank[country]) > 0
              lenPartecipation=self.bound

              # ----------------------------------------------------------------
              # ENTRY — dual-pool mechanism
              #
              # The decision of WHAT enters next is identical to the original
              # paper: whichAgentEnter6 is called once per potential entrant and
              # returns 'firmTradable', 'firmNotTradable', or 'bank'.
              #
              # HOW it is funded depends on the type:
              #   Firm  -> regional pool of the richest available region
              #            (region with the most uninvested Investing balances)
              #   Bank  -> national pool (all remaining consumers)
              #
              # This gives firms a regional identity from birth without changing
              # the entry timing logic. Both pools are pre-built once; consumers
              # who already funded a regional bank have Investing=0 and are
              # naturally excluded from both pools.
              # ----------------------------------------------------------------

              # Pre-build regional pools (firm entry)
              _regionPools   = {r: [] for r in range(self.nRegion)}
              # Pre-build national pool (bank entry) — same consumers, both pools
              # share state: spending from one reduces the other implicitly because
              # we zero Investing on the consumer object when they contribute.
              LconsumerInvesting = []
              _pos = 0
              for consumer in McountryConsumer[country]:
                  cobj = McountryConsumer[country][consumer]
                  if (cobj.Investing > cobj.wBar * avWage
                          and len(cobj.DLA) <= lenPartecipation):
                      r = self._consumerRegion(consumer)
                      _regionPools[r].append(
                          [cobj.ide, cobj.Investing, 0, 0, _pos])
                      LconsumerInvesting.append(
                          [cobj.ide, cobj.Investing, 0, 0, _pos])
                  _pos += 1

              # Shuffle both pools independently
              for r in range(self.nRegion):
                  random.shuffle(_regionPools[r])
              random.shuffle(LconsumerInvesting)

              # ---- Firm-entry pool selection (experiment toggle) ----
              # 'regional': per-region pools (default current behaviour).
              # 'national': one pool of ALL eligible consumers; the firm's region
              #             is assigned later from its investors' plurality. This
              #             decouples entry VOLUME (national capital budget) from
              #             region ASSIGNMENT, so regional credit is preserved.
              if getattr(self, 'firmEntryMode', 'regional') == 'national':
                  _firmPools = {0: [row for r in range(self.nRegion)
                                        for row in _regionPools[r]]}
                  random.shuffle(_firmPools[0])
                  _firmKeys = [0]
              else:
                  _firmPools = _regionPools
                  _firmKeys = list(range(self.nRegion))

              # Pre-entry diagnostics (only written out if entryTrace is on)
              _preInvesting = sum(row[1] for r in range(self.nRegion)
                                          for row in _regionPools[r])
              _nEligible    = sum(len(_regionPools[r]) for r in range(self.nRegion))
              _firmSizeSum  = 0.0

              # Helper: total available in a regional pool
              def _poolTotal(pool):
                  return sum(row[1] for row in pool)

              # Helper: wire investors from a pool slice [basicJ..i] + partial i
              def _wireFirm(pool, basicJ, i, sumInv, newAgentSize, newfirm):
                  j = basicJ
                  while j < i:
                      cide = pool[j][0]
                      # Use live Investing balance — snapshot may be stale if the
                      # consumer was already spent via another pool entry this period.
                      cshare = McountryConsumer[country][cide].Investing
                      if cshare <= 0:
                          j += 1
                          continue
                      ratioA = cshare / float(newAgentSize)
                      pool[j][1] = 0; pool[j][2] += cshare
                      pos = pool[j][4]
                      McountryConsumer[country][cide].Investing = 0
                      McountryConsumer[country][cide].DLA[newfirm.ide] = \
                          [cide, newfirm.ide, cshare, pos, ratioA]
                      McountryConsumer[country][cide].paying(
                          cshare, McountryBank, McountryCentralBank)
                      LconsumerAsset.append([cide, newfirm.ide, cshare])
                      newfirm.Downer[cide] = \
                          McountryConsumer[country][cide].DLA[newfirm.ide]
                      newfirm.ListOwners.append(cide)
                      j += 1
                  # last (partial) investor
                  lastShare = pool[i][1] - (sumInv - newAgentSize)
                  cide = pool[i][0]
                  # Clamp to live Investing in case of stale snapshot
                  lastShare = min(lastShare,
                                  McountryConsumer[country][cide].Investing)
                  if lastShare > 0:
                      pool[i][1] -= lastShare; pool[i][2] += lastShare
                      pos = pool[i][4]
                      McountryConsumer[country][cide].Investing = \
                          McountryConsumer[country][cide].Investing - lastShare
                      ratioA = lastShare / float(newAgentSize)
                      McountryConsumer[country][cide].DLA[newfirm.ide] = \
                          [cide, newfirm.ide, lastShare, pos, ratioA]
                      McountryConsumer[country][cide].paying(
                          lastShare, McountryBank, McountryCentralBank)
                      LconsumerAsset.append([cide, newfirm.ide, lastShare])
                      newfirm.Downer[cide] = \
                          McountryConsumer[country][cide].DLA[newfirm.ide]
                      newfirm.ListOwners.append(cide)

              # Firm-pool cursors: one (i, basicJ, sumInv) per firm pool key
              _ri     = {k: 0   for k in _firmKeys}
              _rbasic = {k: 0   for k in _firmKeys}
              _rsum   = {k: 0.0 for k in _firmKeys}
              _nFirmBefore = len(McountryFirm[country])
              _nBankBefore = len(McountryBank[country])

              # National pool cursor (for bank entry)
              i = 0
              li = len(LconsumerInvesting)
              sumInv = 0; basicJ = 0

              self.DidEnterANewAgent = 'no'
              newAgentKind = self.whichAgentEnter6(country, McountryFirm, McountryBank)
              Lkind = self.whichSize(newAgentKind)
              newAgentSize = Lkind[1]

              # Main entry loop — continues as long as either pool has candidates
              while True:
                  if self.DidEnterANewAgent == 'yes':
                      self.DidEnterANewAgent = 'no'
                      newAgentKind = self.whichAgentEnter6(
                          country, McountryFirm, McountryBank)
                      Lkind = self.whichSize(newAgentKind)
                      newAgentSize = Lkind[1]

                  # ---- FIRM BRANCH: use capital-weighted random regional pool ----
                  if newAgentKind in ('firmNotTradable', 'firmTradable'):
                      # Firms call paying() for founders AND for production costs.
                      # paying() requires at least one commercial bank to exist so that
                      # the CB balance sheet stays consistent. If no banks exist yet
                      # (cannot happen in the regional-bank country after
                      # _createRegionalBanksInEnter, but can happen in Country 1's
                      # global-only path before any bank has entered), skip firm entry.
                      if not banksExist:
                          break
                      # Select region probabilistically, weighted by available capital.
                      # pool row[1] values are zeroed as consumed so _poolTotal
                      # naturally reflects remaining capacity per region.
                      totals   = {k: _poolTotal(_firmPools[k]) for k in _firmKeys}
                      eligible = [k for k in _firmKeys if totals[k] >= newAgentSize]
                      if not eligible:
                          break   # no pool can fund a firm of this size; exit loop
                      weights = [totals[k] for k in eligible]
                      bestR   = random.choices(eligible, weights=weights, k=1)[0]
                      pool = _firmPools[bestR]
                      ri = _ri[bestR]; rli = len(pool)
                      # Advance cursor until enough capital accumulates
                      advanced = False
                      while ri < rli:
                          _rsum[bestR] += pool[ri][1]
                          if _rsum[bestR] >= newAgentSize:
                              advanced = True
                              break
                          ri += 1
                      _ri[bestR] = ri
                      if not advanced:
                          # Cursor reached end without accumulating enough.
                          # Zero all rows so this region leaves eligible next time.
                          for row in pool:
                              row[1] = 0.0
                          _rsum[bestR] = 0.0
                          continue  # retry: a different eligible region will be chosen

                      # Create firm
                      if newAgentKind == 'firmNotTradable':
                          newfirmA = Lkind[1]
                          number = self.McountryFirmMaxNumber[country]
                          self.McountryFirmMaxNumber[country] = number + 1
                          firmide = 'F' + str(country) + 'n' + str(number)
                          phi=Lkind[2]; price=Lkind[3]; w=Lkind[4]; eX=Lkind[5]
                          upsilon = self.DcountryUpsilon[country]
                          jobDuration = self.DcountryJobDuration[country]
                          newfirm = Firm(firmide, country, newfirmA, phi,
                                         self.Lcountry, w, self.folder, self.name,
                                         self.run, self.delta, self.dividendRate,
                                         self.xi, self.iota, upsilon, self.gamma,
                                         self.deltaInnovation, price, self.Fcost,
                                         self.ni, self.minMarkUp, eX, self.theta,
                                         self.upsilon2, jobDuration)
                          self.DcountryEnterValue[country] += newfirmA
                          newfirm.tradable = 'no'
                          newfirm.time = time
                          newfirm.whichPolicy = McountryEtat[country].whichPolicy
                      else:  # firmTradable
                          newfirmA = Lkind[1]
                          number = self.McountryFirmMaxNumber[country]
                          self.McountryFirmMaxNumber[country] = number + 1
                          firmide = 'F' + str(country) + 'n' + str(number)
                          phi=Lkind[2]; price=Lkind[3]; w=Lkind[4]; eX=Lkind[5]
                          upsilon = self.DcountryUpsilon[country]
                          jobDuration = self.DcountryJobDuration[country]
                          newfirm = Firm(firmide, country, newfirmA, phi,
                                         self.Lcountry, w, self.folder, self.name,
                                         self.run, self.delta, self.dividendRate,
                                         self.xi, self.iota, upsilon, self.gamma,
                                         self.deltaInnovation, price, self.Fcost,
                                         self.ni, self.minMarkUp, eX, self.theta,
                                         self.upsilon2, jobDuration)
                          self.DcountryEnterValue[country] += newfirmA
                          self.DcountryFirmEnterTradable[country] += 1
                          newfirm.tradable = 'yes'
                          newfirm.time = time
                          newfirm.whichPolicy = McountryEtat[country].whichPolicy

                      _wireFirm(pool, _rbasic[bestR], ri, _rsum[bestR],
                                newAgentSize, newfirm)
                      _firmSizeSum += newfirmA
                      if getattr(self, 'firmEntryMode', 'regional') == 'national':
                          # region = plurality of the firm's actual investors
                          newfirm.region = (self._mostCommonRegion(newfirm.ListOwners)
                                            if newfirm.ListOwners else 0)
                      else:
                          newfirm.region = bestR
                      McountryFirm[country][newfirm.ide] = newfirm
                      enteringfirm += 1; enteringfirmC += 1
                      self.DcountryFirmEnter[country] += 1
                      _rbasic[bestR] = ri; _rsum[bestR] = 0.0; _ri[bestR] = ri
                      self.DidEnterANewAgent = 'yes'

                  # ---- BANK BRANCH: use national pool ----
                  elif newAgentKind == 'bank':
                      if i >= li:
                          break   # national pool exhausted
                      sumInv += LconsumerInvesting[i][1]
                      if sumInv >= newAgentSize:
                          newbankA = newAgentSize
                          number = self.McountryBankMaxNumber[country]
                          self.McountryBankMaxNumber[country] = number + 1
                          bankide = 'B' + str(country) + 'n' + str(number)
                          iotaRelPhi = self.DcountryIotaRelPhi[country]
                          newbank = Bank(bankide, country, newbankA,
                                         self.Lcountry, self.Fcost,
                                         self.folder, self.name, self.run,
                                         self.delta, self.minReserve,
                                         self.rDiscount, self.xi,
                                         self.dividendRate, self.iota,
                                         self.rDeposit, self.mu1,
                                         self.iotaE, iotaRelPhi)
                          self.DcountryEnterValue[country] += newbankA
                          # Wire investors using correct SFC accounting (same logic as regional):
                          # CB-deposit: paying() + manual CB.Reserves credit
                          # Commercial-bank: interbank reserve transfer, no deposit records touched
                          _newBankReservesG = 0.0
                          j = basicJ
                          while j < i:
                              cide = LconsumerInvesting[j][0]
                              cshare = LconsumerInvesting[j][1]
                              LconsumerInvesting[j][1] = 0
                              LconsumerInvesting[j][2] += cshare
                              pos = LconsumerInvesting[j][4]
                              McountryConsumer[country][cide].Investing = 0
                              ratioA = cshare / float(newAgentSize)
                              McountryConsumer[country][cide].DLA[newbank.ide] =                                   [cide, newbank.ide, cshare, pos, ratioA]
                              _fromCB = country in McountryConsumer[country][cide].Mdeposit
                              McountryConsumer[country][cide].paying(
                                  cshare, McountryBank, McountryCentralBank)
                              McountryCentralBank[country].Reserves += cshare
                              _newBankReservesG += cshare
                              LconsumerAsset.append([cide, newbank.ide, cshare])
                              newbank.Downer[cide] =                                   McountryConsumer[country][cide].DLA[newbank.ide]
                              newbank.ListOwners.append(cide)
                              j += 1
                          lastShare = LconsumerInvesting[i][1] - (sumInv - newAgentSize)
                          cide = LconsumerInvesting[i][0]
                          LconsumerInvesting[i][1] -= lastShare
                          LconsumerInvesting[i][2] += lastShare
                          pos = LconsumerInvesting[i][4]
                          McountryConsumer[country][cide].Investing =                               LconsumerInvesting[i][1]
                          ratioA = lastShare / float(newAgentSize)
                          McountryConsumer[country][cide].DLA[newbank.ide] =                               [cide, newbank.ide, lastShare, pos, ratioA]
                          _fromCB = country in McountryConsumer[country][cide].Mdeposit
                          McountryConsumer[country][cide].paying(
                              lastShare, McountryBank, McountryCentralBank)
                          McountryCentralBank[country].Reserves += lastShare
                          _newBankReservesG += lastShare
                          LconsumerAsset.append([cide, newbank.ide, lastShare])
                          newbank.Downer[cide] =                               McountryConsumer[country][cide].DLA[newbank.ide]
                          newbank.ListOwners.append(cide)
                          newbank.isRegional = False
                          newbank.region = -1
                          newbank.Reserves = _newBankReservesG
                          McountryBank[country][newbank.ide] = newbank
                          banksExist = True
                          enteringbank += 1
                          self.DcountryBankEnter[country] += 1
                          basicJ = i; sumInv = 0.0
                          self.DidEnterANewAgent = 'yes'
                      else:
                          i += 1   # bank branch: advance national cursor

                  else:
                      break   # newAgentKind == 'no' — nothing more to create

              # ---- Entry trace (diagnostic; off by default) ----
              if getattr(self, 'entryTrace', False):
                  import os
                  _tf = self.folder + self.name + 'EntryTrace.csv'
                  _new = not os.path.exists(_tf)
                  with open(_tf, 'a') as _fh:
                      if _new:
                          _fh.write('run,time,country,firmsFounded,banksFounded,'
                                    'preInvesting,nEligible,nFirmBefore,nBankBefore,'
                                    'avgFirmSize\n')
                      _avg = (_firmSizeSum / enteringfirmC) if enteringfirmC > 0 else 0.0
                      _fh.write('%s,%s,%s,%s,%s,%.2f,%s,%s,%s,%.4f\n' % (
                          self.run, time, country, enteringfirmC,
                          self.DcountryBankEnter[country], _preInvesting, _nEligible,
                          _nFirmBefore, _nBankBefore, _avg))
             
             
 
      def exitFirm(self,McountryFirm,McountryBank,McountryCentralBank):
          exitingfirm=0
          self.DfirmExit={}
          for country in McountryBank:
              self.DcountryForeignBankLosses[country]=0
          for country in McountryFirm: 
              self.DcountryFirmGone[country]={} 
              self.DcountryFirmExit[country]=0
              self.DcountryFirmExitTradable[country]=0 
              LfirmExit=[] 
              self.DfirmExit[country]=[]
              for firm in  McountryFirm[country]:
                  if McountryFirm[country][firm].closing=='yes': 
                     LfirmExit.append(firm)
                     self.DfirmExit[country].append(firm)
              exitingfirm=0 
              sumDiff=0
              for firm in LfirmExit:
                  if McountryFirm[country][firm].loanReceived>0.0:  
                     rap=McountryFirm[country][firm].loanReimboursed/float(McountryFirm[country][firm].loanReceived) 
                     diff=McountryFirm[country][firm].loanReimboursed-McountryFirm[country][firm].loanReceived
                     sumDiff=sumDiff+diff
                     totalLosses=0
                     for bank in McountryFirm[country][firm].Mloan: 
                         ideBank=bank    
                         reimboursements=0                        
                         countryBank=McountryFirm[country][firm].Mloan[bank][4]                    
                         if McountryBank[countryBank][ideBank].ide==ideBank:
                            reimbourse=rap*McountryFirm[country][firm].Mloan[ideBank][2] 
                            reimboursements=reimboursements+reimbourse
                            losses=McountryFirm[country][firm].Mloan[ideBank][2]*McountryFirm[country][firm].Mloan[ideBank][3]\
                                   +McountryFirm[country][firm].Mloan[ideBank][2]-reimbourse
                            if countryBank!=country:
                               self.DcountryForeignBankLosses[countryBank]=self.DcountryForeignBankLosses[countryBank]+losses
                               self.DcountryForeignBankLosses[country]=self.DcountryForeignBankLosses[country]-losses
                            if reimbourse<McountryFirm[country][firm].Mloan[ideBank][2]:
                               missLoan=McountryFirm[country][firm].Mloan[ideBank][2]-reimbourse 
                               bankIde=McountryFirm[country][firm].Mloan[ideBank][1]  
                               McountryFirm[country][firm].repayingLoan(bankIde,reimbourse,reimbourse,McountryBank,McountryCentralBank,countryBank)
                               McountryBank[countryBank][ideBank].Loan=McountryBank[countryBank][ideBank].Loan-missLoan
                            if reimbourse>=McountryFirm[country][firm].Mloan[ideBank][2]:
                               ideBank=bank
                               loanValue=McountryFirm[country][firm].Mloan[ideBank][2]
                               service=reimbourse-McountryFirm[country][firm].Mloan[ideBank][2]   
                               loanVolume=loanValue+service
                               McountryFirm[country][firm].repayingLoan(ideBank,loanValue,loanVolume,McountryBank,McountryCentralBank,countryBank) 
                            if losses<-0.001: 
                               raise AssertionError("SFC invariant violated: enterExit.py:855 in exitFirm()")
                            totalLosses=totalLosses+losses                            
                            McountryBank[countryBank][ideBank].losses=McountryBank[countryBank][ideBank].losses+losses   
                  for bank in McountryFirm[country][firm].Mdeposit:
                      countryBank=McountryFirm[country][firm].Mdeposit[bank][4]
                      if bank!=country:
                         del  McountryBank[countryBank][bank].Mdeposit[firm]  
                      if bank==country:
                         del  McountryCentralBank[countryBank].Mdeposit[firm]      
                  self.DcountryFirmGone[country][firm]=McountryFirm[country][firm]
                  if McountryFirm[country][firm].tradable=='yes':
                     self.DcountryFirmExitTradable[country]=self.DcountryFirmExitTradable[country]+1
                  del McountryFirm[country][firm]
                  exitingfirm=exitingfirm+1
                  self.DcountryFirmExit[country]=self.DcountryFirmExit[country]+1
                  

      def exitBank(self,McountryConsumer,McountryFirm,McountryBank,McountryCentralBank,McountryEtat):
          exitingbank=0
          self.DpastBondExit={}
          DbankLiving={}
          for country in McountryBank:
              self.DcountryBankGone[country]={}  
              DbankLiving[country]=[]
              for bank in McountryBank[country]:
                  if McountryBank[country][bank].closing=='no':
                     DbankLiving[country].append(McountryBank[country][bank].ide) 
              if len(DbankLiving[country])==0:
                 DbankLiving[country].append(country)    
          for country in McountryBank:
              LbankExit=[]
              LbankLiving=[]
              self.DcountryBankExit[country]=0
              self.DpastBondExit[country]=0 
              McountryEtat[country].coveredDeposit=0 
              for bank in McountryBank[country]:
                  if McountryBank[country][bank].closing=='yes':
                     LbankExit.append(McountryBank[country][bank].ide) 
                  else:
                     LbankLiving.append(McountryBank[country][bank].ide) 
              if len(LbankLiving)==0:
                 LbankLiving.append(country)
              McountryEtat[country].Salvatage=0                    
              for bank in LbankExit: 
                        loss=McountryBank[country][bank].loss 
                        serviceLoanCentralBank=McountryBank[country][bank].loanDiscount*(1+McountryCentralBank[country].rDiscount) 
                        McountryCentralBank[country].loanDiscount=McountryCentralBank[country].loanDiscount-McountryBank[country][bank].loanDiscount
                        McountryCentralBank[country].Bonds=McountryCentralBank[country].Bonds+serviceLoanCentralBank
                        McountryCentralBank[country].interestLoanDiscount=McountryCentralBank[country].interestLoanDiscount+\
                                                   McountryBank[country][bank].loanDiscount*McountryCentralBank[country].rDiscount
                        McountryEtat[country].Bonds=McountryEtat[country].Bonds+serviceLoanCentralBank
                        McountryEtat[country].Salvatage=McountryEtat[country].Salvatage+loss
                        salvatage=McountryBank[country][bank].loanDiscount 
                        McountryBank[country][bank].loanDiscount=0   
                        self.DpastBondExit[country]=self.DpastBondExit[country]+McountryBank[country][bank].pastBonds\
                                          +McountryBank[country][bank].pastBonds*McountryEtat[country].rBonds
                        McountryBank[country][bank].governmentCover=0  
                        sumDepositBack=0
                        sumInterestPayment=0
                        sumVolume=0
                        for agent in McountryBank[country][bank].Mdeposit: 
                            ideAgent=agent
                            volume=McountryBank[country][bank].Mdeposit[ideAgent][2]
                            countryAgent=McountryBank[country][bank].Mdeposit[ideAgent][4]
                            interest=McountryBank[country][bank].Mdeposit[ideAgent][3]                             
                            if ideAgent[0]=='C':
                               volumeCheck=McountryConsumer[countryAgent][ideAgent].Mdeposit[bank][2]
                               if volume<volumeCheck-0.0000001 or volume>volumeCheck+0.0000001:
                                  raise AssertionError("SFC invariant violated: enterExit.py:923 in exitBank()")
                               del McountryConsumer[countryAgent][ideAgent].Mdeposit[bank]
                               sumVolume=sumVolume+volume 
                            if ideAgent[0]=='F':
                               interest=0
                               volumeCheck=McountryFirm[countryAgent][ideAgent].Mdeposit[bank][2]
                               if volume<volumeCheck-0.0000001 or volume>volumeCheck+0.0000001:
                                  raise AssertionError("SFC invariant violated: enterExit.py:930 in exitBank()")
                               del McountryFirm[countryAgent][ideAgent].Mdeposit[bank]
                            depositBack=volume*interest+volume
                            sumDepositBack=sumDepositBack+depositBack  
                            interestPayment=volume*interest
                            sumInterestPayment=sumInterestPayment+interestPayment 
                            McountryBank[country][bank].exitWithdrawal(depositBack,McountryEtat,McountryCentralBank) 
                            salvatage=salvatage+McountryBank[country][bank].governmentCover
                            random.shuffle(DbankLiving[countryAgent])
                            newbankIde=DbankLiving[countryAgent][0]                           
                            if newbankIde!=countryAgent:
                               if (ideAgent in McountryBank[countryAgent][newbankIde].Mdeposit)==True:   
                                  McountryBank[countryAgent][newbankIde].Mdeposit[ideAgent][2]=\
                                           McountryBank[countryAgent][newbankIde].Mdeposit[ideAgent][2]+depositBack
                                  McountryBank[countryAgent][newbankIde].Deposit=McountryBank[countryAgent][newbankIde].Deposit+depositBack
                                  McountryBank[countryAgent][newbankIde].Reserves=McountryBank[countryAgent][newbankIde].Reserves+depositBack
                                  McountryCentralBank[countryAgent].Reserves=McountryCentralBank[countryAgent].Reserves+depositBack    
                                  if ideAgent[0]=='C':
                                     McountryConsumer[countryAgent][ideAgent].Mdeposit[newbankIde][2]=\
                                            McountryConsumer[countryAgent][ideAgent][2].Mdeposit[newbankIde][2]+depositBack
                                     McountryConsumer[countryAgent][ideAgent].depositInterest=\
                                            McountryConsumer[countryAgent][ideAgent].depositInterest+interestPayment 
                                  if ideAgent[0]=='F':
                                     McountryFirm[countryAgent][ideAgent].Mdeposit[newbankIde][2]=\
                                       McountryFirm[countryAgent][ideAgent].Mdeposit[newbankIde][2]+depositBack 
                                     McountryFirm[countryAgent][ideAgent].depositInterest=\
                                            McountryFirm[countryAgent][ideAgent].depositInterest+interestPayment 
                               if (ideAgent in McountryBank[countryAgent][newbankIde].Mdeposit)==False: 
                                  interest=McountryBank[countryAgent][newbankIde].rDeposit
                                  McountryBank[countryAgent][newbankIde].Mdeposit[ideAgent]=[ideAgent,newbankIde,depositBack,interest,countryAgent]
                                  McountryBank[countryAgent][newbankIde].Deposit=McountryBank[countryAgent][newbankIde].Deposit+depositBack
                                  McountryBank[countryAgent][newbankIde].Reserves=McountryBank[countryAgent][newbankIde].Reserves+depositBack 
                                  McountryCentralBank[countryAgent].Reserves=McountryCentralBank[countryAgent].Reserves+depositBack 
                                  if ideAgent[0]=='C':
                                     McountryConsumer[countryAgent][ideAgent].Mdeposit[newbankIde]=[ideAgent,newbankIde,depositBack,interest,countryAgent]
                                     McountryConsumer[countryAgent][ideAgent].depositInterest=\
                                            McountryConsumer[countryAgent][ideAgent].depositInterest+interestPayment
                                  if ideAgent[0]=='F':
                                     McountryFirm[countryAgent][ideAgent].Mdeposit[newbankIde]=[ideAgent,newbankIde,depositBack,interest,countryAgent]  
                                     McountryFirm[countryAgent][ideAgent].depositInterest=\
                                            McountryFirm[countryAgent][ideAgent].depositInterest+interestPayment     
                            if newbankIde==countryAgent:
                               if (ideAgent in McountryCentralBank[countryAgent].Mdeposit)==True: 
                                  McountryCentralBank[countryAgent].Mdeposit[ideAgent][2]=\
                                   McountryCentralBank[countryAgent].Mdeposit[ideAgent][2]+depositBack
                                  McountryCentralBank[countryAgent].Deposit=McountryCentralBank[countryAgent].Deposit+depositBack 
                                  if ideAgent[0]=='C':
                                     McountryConsumer[countryAgent][ideAgent].Mdeposit[newbankIde][2]=\
                                           McountryConsumer[countryAgent][ideAgent].Mdeposit[newbankIde][2]+depositBack
                                     McountryConsumer[countryAgent][ideAgent].depositInterest=\
                                            McountryConsumer[countryAgent][ideAgent].depositInterest+interestPayment
                                  if ideAgent[0]=='F':
                                     McountryFirm[countryAgent][ideAgent].Mdeposit[newbankIde][2]=\
                                        McountryFirm[countryAgent][ideAgent].Mdeposit[newbankIde][2]+depositBack 
                                     McountryFirm[countryAgent][ideAgent].depositInterest=\
                                            McountryFirm[countryAgent][ideAgent].depositInterest+interestPayment
                               if (ideAgent in McountryCentralBank[countryAgent].Mdeposit)==False: 
                                  interest=McountryCentralBank[countryAgent].rDeposit 
                                  McountryCentralBank[countryAgent].Mdeposit[ideAgent]=[ideAgent,newbankIde,depositBack,interest,countryAgent]
                                  McountryCentralBank[countryAgent].Deposit=McountryCentralBank[countryAgent].Deposit+depositBack 
                                  if ideAgent[0]=='C':
                                     McountryConsumer[countryAgent][ideAgent].Mdeposit[newbankIde]=[ideAgent,newbankIde,depositBack,interest,countryAgent]
                                     McountryConsumer[countryAgent][ideAgent].depositInterest=\
                                            McountryConsumer[countryAgent][ideAgent].depositInterest+interestPayment
                                  if ideAgent[0]=='F':                      
                                     McountryFirm[countryAgent][ideAgent].Mdeposit[newbankIde]\
                                                 =[ideAgent,newbankIde,depositBack,interest,countryAgent]                     
                                     McountryFirm[countryAgent][ideAgent].depositInterest=\
                                            McountryFirm[countryAgent][ideAgent].depositInterest+interestPayment
                        withdrawalDifference=sumDepositBack-McountryBank[country][bank].totalDeposit
                        McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves-McountryBank[country][bank].Reserves
                        McountryCentralBank[country].Bonds=McountryCentralBank[country].Bonds-McountryBank[country][bank].Reserves
                        McountryEtat[country].Bonds=McountryEtat[country].Bonds-McountryBank[country][bank].Reserves
                        intDifference=sumInterestPayment-McountryBank[country][bank].potentialExitConsumer 
                        McountryEtat[country].Salvatage=McountryEtat[country].Salvatage+intDifference
                        McountryBank[country][bank].Reserves=0
                        self.DcountryBankGone[country][bank]=McountryBank[country][bank]
                        del McountryBank[country][bank]
                        exitingbank=exitingbank+1 
                        self.DcountryBankExit[country]=self.DcountryBankExit[country]+1

