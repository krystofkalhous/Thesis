# centralbank.py

class CentralBankUnion:
      def __init__(self,rDiscount,rDeposit,zeta,rBar,csi,csiDP,inflationTarget):
          self.basicMoney=0
          self.Bonds=0
          self.ReservesCompulsory=0
          self.loanDiscount=0
          self.Liquidity=0     
          self.rDiscount=rDiscount
          ### ----------------------------------------------------------------------------------------------
          # MY CODE: store past rDiscount, we equate it to self.rDiscount, in order to avoid spurious jump in t=0 -> t=1
          self.pastrDiscount = self.rDiscount
          ### ----------------------------------------------------------------------------------------------
          self.Mdeposit={} 
          self.Deposit=0
          self.Reserves=0  
          self.profit=0
          self.rDeposit=rDeposit 
          self.depositInterest=0
          self.pastProfitPos=0
          self.interestLoanDiscount=0 
          self.endTransitionTime=1
          self.LoanCentralBankUnion=0
          self.DepositCentralBankUnion=0
          self.CreditTaxCentralBankUnion=0
          self.DebtTaxCentralBankUnion=0 
          self.zeta=zeta 
          self.rBar=rBar
          self.csi=csi
          self.csiDP=csiDP
          self.inflationTarget=inflationTarget  
 
      def taylorRule(self,McountryInflation,McountryUnemployement,McountryBank,McountryCentralBank,t,McountryConsumer):
         ### ----------------------------------------------------------------------------------------------
         # MY CODE: store past rDiscount
         self.pastrDiscount = self.rDiscount
         ### ----------------------------------------------------------------------------------------------

         if t>self.endTransitionTime:
          inflationSum=0
          uSum=0
          for country in  McountryInflation:
              inflationSum=inflationSum+McountryInflation[country]
              uSum=uSum+McountryUnemployement[country]
          inflation=inflationSum/float(len(McountryInflation))
          u=uSum/float(len(McountryUnemployement))
          rcB=self.rBar*(1-self.csi)+self.csi*self.rDiscount+(1-self.csi)*self.csiDP*(inflation-self.inflationTarget)
          #self.rDiscount=max(0,rcB)
          for country in McountryBank:
              McountryCentralBank[country].rDiscount=self.rDiscount
              rDeposit=self.zeta*self.rDiscount
              for bank in McountryBank[country]:
                  McountryBank[country][bank].rDiscount=self.rDiscount
                  McountryBank[country][bank].rDeposit=rDeposit
              for consumer in McountryConsumer[country]:
                  McountryConsumer[country][consumer].rDeposit=rDeposit
                  
      def checknetWorth(self):
          if self.DepositCentralbankUnion>self.LoanCentralbankUnion+0.00001 or\
             self.DepositCentralbankUnion<self.LoanCentralbankUnion-0.00001:
             print('stop', stop)

      # this is the taylorRule that is used in the code (i.e.: taylorRule1 is used, not taylorRule)
      def taylorRule1(self,McountryInflation,McountryUnemployement,McountryBank,McountryCentralBank,t,McountryConsumer,McountryFirm):
         ### ----------------------------------------------------------------------------------------------
         # MY CODE: store past rDiscount
         self.pastrDiscount = self.rDiscount
         ### ----------------------------------------------------------------------------------------------

         if t>self.endTransitionTime:
          inflationSum=0
          uSum=0
          for country in McountryInflation:
              inflationSum=inflationSum+McountryInflation[country]
              uSum=uSum+McountryUnemployement[country]   
          inflation=inflationSum/float(len(McountryInflation))
          u=uSum/float(len(McountryUnemployement))
          rcB=self.rBar*(1-self.csi)+self.csi*self.rDiscount+(1-self.csi)*self.csiDP*(inflation-self.inflationTarget)
          self.rDiscount=max(0,rcB)
          for country in McountryBank:
              McountryCentralBank[country].rDiscount=self.rDiscount
              rDeposit=self.zeta*self.rDiscount
              McountryCentralBank[country].rDeposit=rDeposit 
              for bank in McountryBank[country]:
                  ### ----------------------------------------------------------------------------------------------
                  # MY CODE: make bank store past rDiscount
                  McountryBank[country][bank].pastrDiscount = self.pastrDiscount
                  ### ----------------------------------------------------------------------------------------------
                  McountryBank[country][bank].rDiscount=self.rDiscount
                  McountryBank[country][bank].rDeposit=rDeposit
                  for agent in  McountryBank[country][bank].Mdeposit:
                      McountryBank[country][bank].Mdeposit[agent][3]=rDeposit
              for consumer in McountryConsumer[country]:     
                  McountryConsumer[country][consumer].rDeposit=rDeposit   
                  for bank in  McountryConsumer[country][consumer].Mdeposit:
                       McountryConsumer[country][consumer].Mdeposit[bank][3]=rDeposit
              for firm in McountryFirm[country]:
                  for bank in McountryFirm[country][firm].Mdeposit:
                      McountryFirm[country][firm].Mdeposit[bank][3]=rDeposit
              for agent in McountryCentralBank[country].Mdeposit:
                  McountryCentralBank[country].Mdeposit[agent][3]=rDeposit  
                
           
           
      
           
 

      
