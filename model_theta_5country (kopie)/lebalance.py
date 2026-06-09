
# lebalance.py
import random
import math
import os
# theta extension: the theta->innovation-efficiency PRODUCTIVITY channel is bounded
# but, with unrestricted credit (a coupled union), it still drives a frontier runaway.
# THETA_PROD=1 (default) keeps it on (as tested at ncountry=2 under isolation);
# THETA_PROD=0 disables it, so theta affects ONLY self-selection + relationship pricing
# (a stable "allocation-only" arm usable in the coupled multi-country union).
_THETA_PROD=os.environ.get("THETA_PROD","1").lower() in ("1","true","yes","on")
_LAMBDA_INN=float(os.environ.get("LAMBDA_INN","1.0"))  # innovation catch-up strength (path dependence)
_RCAP_ON=os.environ.get("RCAP_ON","0").lower() in ("1","true","yes","on")  # research-capital stock
_RCAP_DEPREC=float(os.environ.get("RCAP_DEPREC","0.15"))  # knowledge depreciation rate d
_RCAP_MAINT=float(os.environ.get("RCAP_MAINT","0.15"))    # maintenance spend = fraction of stock (size-independent)
_RCAP_ABSORP=float(os.environ.get("RCAP_ABSORP","1.0"))   # absorptive-capacity slope (R-gated imitation)
#import numpy

class Lebalance:
      def __init__(self,delta,firmcountry,ide,dividendRate,iota,gamma,deltaInnovation,Fcost,ni,xi,A):
          self.delta=delta
          self.firmcountry=firmcountry
          self.country=firmcountry
          self.ide=ide
          self.dividendRate=dividendRate
          self.iota=iota 
          self.ResourceAvailable=0 
          self.gamma=gamma
          self.deltaInnovation=deltaInnovation
          self.Fcost=Fcost
          self.ni=ni
          self.totalExpenditure=0
          self.xi=xi
          self.Aspending=A
          self.Lsold=[0,0,0,0]
          self.Rmoney=0.0  # research-capital stock (money units, depreciated cumulative innovation spend)

      def rebalancing(self,A,debtService,innovationExpenditure,loanReceived,laborExpenditure,xSold,price):
          losses=debtService
          self.loanNotUsed=0
          self.loanUsed=0
          self.loanEffReceived=0
          self.Entrance=0
          self.totProfit=-debtService
          self.ResourceAvailable=0
          self.toWorkers=0
          expenditure=innovationExpenditure+laborExpenditure
          p=price
          revenue=p*xSold
          Amp=A
          loan=loanReceived
          loanNotUsed=0
          if expenditure<=Amp: 
             loanNotUsed=loan
             loanUsed=0
          if expenditure>Amp:
             loanNotUsed=loan-(expenditure-Amp)
             loanUsed=expenditure-Amp   
          if expenditure>Amp+loan+0.001:
             raise AssertionError("SFC invariant violated: lebalance.py:47 in rebalancing()")
          self.loanNotUsed=self.loanNotUsed+loanNotUsed
          self.loanUsed=self.loanUsed+loanUsed 
          self.loanEffReceived=self.loanEffReceived+loan
          self.Entrance=self.Entrance+revenue   
          profit=revenue-expenditure
          self.totalExpenditure=expenditure+debtService
          self.toWorkers=self.toWorkers+expenditure
          self.totProfit=self.totProfit+profit 
          self.wantedNotToUse=0
          Amp=Amp+self.totProfit
          self.Aspending=Amp
          self.A=Amp  

      def dividending(self,A,closing,profit,loanDemand):
          self.dividends=0
          if A>0.0 and profit>0 and closing=='no':
             self.dividends=profit*self.dividendRate
             base=self.wantedNotToUse+profit
             if base<0:
                base=0
             self.dividendToA=self.dividends
             newA=A-self.dividendToA
             self.Aspending=newA

      def producingObjectives4(self,Wage,A,phi,xProducing,price,nAlreadyEmployed):
          self.ResourceAvailable=0
          self.loanDemand=0
          self.ResourceMissing=0
          totnewA=0
          checkA=0
          Adisp=A
          Adisp=self.Aspending
          p=price
          xObjectProduct=xProducing
          if xObjectProduct<0:
             raise AssertionError("SFC invariant violated: lebalance.py:83 in producingObjectives4()")
             xObjectProduct=0
          productivity=phi
          nWorkerProduct=int(xObjectProduct/float(productivity))+1
          nWorkerProduct=xObjectProduct/float(productivity)+1 
          expenditureProduct=nWorkerProduct*Wage
          expenditureAlreadyEmployed=nAlreadyEmployed*Wage
          totProductivity=productivity
          totalExpenditure=max(expenditureProduct,expenditureAlreadyEmployed)
          if totalExpenditure<=Adisp:
             diffExpenditureNeeded=Adisp-totalExpenditure  
             Areduction=diffExpenditureNeeded             
             self.ResourceAvailable=self.ResourceAvailable+Areduction
             self.Aspending=totalExpenditure  
          if totalExpenditure>Adisp:
             self.ResourceMissing=totalExpenditure-Adisp
             loanDemand=totalExpenditure-Adisp
             self.loanDemand=loanDemand 
             self.Aspending=A
          self.workForceProductionExpenditureDesired=totalExpenditure
          self.workForceNumberDesired=totalExpenditure/float(Wage) 
          self.workForceNumberDesiredOptimal=expenditureProduct/float(Wage)
          self.workForceExpenditureNoInnovation=totalExpenditure

      def innovatingAttempt(self,A,rDiscount,xProducing,price,w,inventory,profit,xE,xSold,pastPrice):
             leverage=self.loanDemand/float(A)
             r=self.xi*leverage+rDiscount     
             #self.workForceInnovationExpenditureDesired=self.gamma*(self.workForceProductionExpenditureDesired)#+r*self.loanDemand)
             #self.workForceInnovationExpenditureDesired=self.gamma*((xProducing+inventory)*price)
             #self.workForceInnovationExpenditureDesired=self.gamma*(xE*price)
             self.workForceInnovationExpenditureDesired=self.gamma*(xSold*pastPrice)
             if _RCAP_ON:
                self.workForceInnovationExpenditureDesired=self.workForceInnovationExpenditureDesired+_RCAP_MAINT*self.Rmoney
             #self.workForceInnovationExpenditureDesired=0
             #if profit>0:
             #   self.workForceInnovationExpenditureDesired=self.gamma*(profit)
             if self.workForceInnovationExpenditureDesired<=self.ResourceAvailable:
                self.ResourceAvailable=self.ResourceAvailable-self.workForceInnovationExpenditureDesired
                self.Aspending=self.Aspending+self.workForceInnovationExpenditureDesired
             else:
                self.loanDemand=self.loanDemand+self.workForceInnovationExpenditureDesired-self.ResourceAvailable
                self.Aspending=self.Aspending+self.ResourceAvailable
                self.ResourceAvailable=0
             self.workForceNumberInnovation=0.0*self.workForceInnovationExpenditureDesired/w#1.0*self.gamma*self.workForceNumberDesired
             self.workForceNumberProduction=self.workForceNumberDesired
             self.workForceNumberDesired=self.workForceNumberDesired+self.workForceNumberInnovation
                 
      
      def innovatingEffective3(self, innovationExpenditure, phi,l,\
                             DglobalPhiNotTradable,avPhiGlobalTradable,tradable,avPriceGlobalTradable,\
                             McountryAvPriceNotTradable,w,DglobalPhi,McountryAvPrice):
          self.workerInnovationAvailableEffective=0
          self.probInn=0
          self.innSuccess=0
          if self.gamma>0.00000001:   
             if tradable=='yes':
                 if l>0 and avPriceGlobalTradable*avPhiGlobalTradable>0:
                        workerInnovationAvailableEffective=innovationExpenditure/float(avPriceGlobalTradable*avPhiGlobalTradable)
                 if l<=0 or avPriceGlobalTradable*avPhiGlobalTradable<=0:
                    workerInnovationAvailableEffective=0
             if tradable=='no':            
                 if l>0 and McountryAvPriceNotTradable[self.country]*DglobalPhiNotTradable[self.country]>0:               
                   workerInnovationAvailableEffective=innovationExpenditure/float(McountryAvPriceNotTradable[self.country]\
                                                       *DglobalPhiNotTradable[self.country])
                 if l<=0 or  McountryAvPriceNotTradable[self.country]*DglobalPhiNotTradable[self.country]<=0:            
                    workerInnovationAvailableEffective=0             
             a=random.uniform(0,1)            
             self.workerInnovationAvailableEffective=workerInnovationAvailableEffective  
             b=(1-math.exp(-self.ni*workerInnovationAvailableEffective))
             c=b
             self.probInn=b
             self.innSuccess=0
             if a<b:
                self.innSuccess=self.innSuccess+1
                u=random.uniform(0,self.deltaInnovation)
                phi=phi*(1+u)
             d=random.uniform(0,1)
             lambdaInn=_LAMBDA_INN
             if d<c:
                  self.innSuccess=self.innSuccess+1 
                  if tradable=='yes':
                     if phi<avPhiGlobalTradable:
                        phi=phi+random.uniform(0,lambdaInn*(avPhiGlobalTradable-phi)) 
                  if tradable=='no':
                     if phi<avPhiGlobalTradable:
                        phi=phi+random.uniform(0,lambdaInn*(DglobalPhiNotTradable[self.country]-phi))  
          return phi

      def innovatingEffective4(self, innovationExpenditure, phi,l,\
                             DglobalPhiNotTradable,avPhiGlobalTradable,tradable,avPriceGlobalTradable,\
                             McountryAvPriceNotTradable,w,DglobalPhi,McountryAvPrice,thetaType=1.0):
          self.workerInnovationAvailableEffective=0
          self.probInn=0
          self.innSuccess=0
          if self.gamma>0.00000001:   
             if tradable=='yes':
                 if l>0 and McountryAvPrice[self.country]*DglobalPhi[self.country]>0: 
                        workerInnovationAvailableEffective=innovationExpenditure/float(McountryAvPrice[self.country]*DglobalPhi[self.country])
                 if l<=0 or McountryAvPrice[self.country]*DglobalPhi[self.country]<=0:
                    workerInnovationAvailableEffective=0
             if tradable=='no':            
                 if l>0 and McountryAvPrice[self.country]*DglobalPhi[self.country]>0:               
                   workerInnovationAvailableEffective=innovationExpenditure/float(McountryAvPrice[self.country]*DglobalPhi[self.country])
                 if l<=0 or  McountryAvPrice[self.country]*DglobalPhi[self.country]<=0:            
                    workerInnovationAvailableEffective=0             
             a=random.uniform(0,1)            
             self.workerInnovationAvailableEffective=workerInnovationAvailableEffective  
             if _RCAP_ON:
                self.Rmoney=(1.0-_RCAP_DEPREC)*self.Rmoney+innovationExpenditure
                _den=McountryAvPrice[self.country]*DglobalPhi[self.country]
                R_eff=self.Rmoney/float(_den) if _den>0 else 0.0
                R_norm=_RCAP_DEPREC*R_eff   # steady-state-matched to baseline flow effort
                b=(1-math.exp(-self.ni*R_norm))
                self._absorp=(1-math.exp(-_RCAP_ABSORP*R_norm))
             else:
                b=(1-math.exp(-self.ni*(thetaType if _THETA_PROD else 1.0)*workerInnovationAvailableEffective))
                self._absorp=_LAMBDA_INN
             c=b
             self.probInn=b
             self.innSuccess=0 
             if a<b:
                self.innSuccess=self.innSuccess+1
                u=random.uniform(0,self.deltaInnovation)
                phi=phi*(1+u)
             d=random.uniform(0,1)
             lambdaInn=self._absorp
             if d<c:
                  self.innSuccess=self.innSuccess+1 
                  if tradable=='yes':
                     if phi<avPhiGlobalTradable:
                        phi=phi+random.uniform(0,lambdaInn*(avPhiGlobalTradable-phi))
                  if tradable=='no':
                     if phi<avPhiGlobalTradable:
                        phi=phi+random.uniform(0,lambdaInn*(DglobalPhiNotTradable[self.country]-phi))
          return phi

      def loanDemanding(self,A,w,phi,p,rDiscount,xi):
          leverage=self.loanDemand/float(A)
          r=xi*leverage+rDiscount
          gain=p*(self.loanDemand/float(w))*phi
          cost=r*self.loanDemand
          if gain<cost:  
             self.loanDemand=0 
    
             
          
                                                
