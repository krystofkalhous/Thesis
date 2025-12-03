#bank.py
import random
import math
import csv

class Bank:
      def __init__(self,ide,homecountry,A,Lcountry,Fcost,folder,name,run,delta,minReserve\
                       ,rDiscount,xi,dividendRate,iota,rDeposit,mu1,iotaE,iotaRelPhi):
          self.ide=ide
          self.homecountry=homecountry
          self.country=homecountry
          self.A=A
          self.Lcountry=Lcountry
          self.Fcost=Fcost
          self.folder=folder
          self.name=name
          self.delta=delta
          self.minReserve=minReserve
          self.Mloan=[]
          self.rDiscount=rDiscount 
          ### ----------------------------------------------------------------------------------------------
          # MY CODE
          self.pastrDiscount=rDiscount # to avoid jump at t0 -> t1, and division by 0
          self.NPLflow = 0.0
          self.pastNPLflow = 0.0

          self.ratingLevels = ['D','C', 'B', 'A'] # index 0,1,2, 3  ### !!! change, think through later
          self.minRatingIndex = 1
          self.minRating = self.ratingLevels[self.minRatingIndex]
          self.idx = 1
          ### ----------------------------------------------------------------------------------------------
          self.xi=xi
          self.Lowner=[]  
          self.closing='no'
          self.Mdeposit={}
          self.losses=0
          self.ListOwners=[]
          ### ----------------------------------------------------------------------------------------------
          # MY CODE
          self.pastLoanAllocated=0 
          ### ----------------------------------------------------------------------------------------------
          self.loanAllocated=0 
          self.loanSupply=self.A
          self.depositReceived=0
          self.PreviousA=self.A
          self.ResourceAvailable=0
          self.dividendRate=dividendRate
          self.iota=iota
          self.pastA=self.A
          self.Downer={}  
          self.Bonds=0
          self.pastBonds=self.Bonds 
          self.Reserves=0
          #self.ReservesCompulsory=0  
          self.Loan=0
          self.rDeposit=rDeposit  
          self.Deposit=0
          self.loanDiscount=0 
          self.potentialEnter=0
          self.profit=0
          self.bondsInterest=0  
          self.mu1=mu1
          self.serviceReceived=0 
          self.volumeLoanReceived=0 
          self.serviceFirm=0
          self.pastServiceFirm=0 
          self.pastBankSaving=0
          self.bankSaving=0 
          self.pastProfit=0
          self.potentialExitConsumer=0    
          self.potentialExitCB=0
          self.iotaE=iotaE
          self.iotaRelPhi=iotaRelPhi
          self.profitRate=0 
                    
      def moneyCreating(self):
          self.moneyCreated=0
          if self.loanAllocated>self.A+self.depositReceived:
             self.moneyCreated=self.loanAllocated-self.A-self.depositReceived

      def computeInterestRate(self,leverage):
          interestRate=self.xi*leverage+self.rDiscount 
          if interestRate<-0.001:
             print('stop', stop)
          return interestRate
      
      ### ----------------------------------------------------------------------------------------------
      # MY CODE
          
      def updateMinRating(self):
          """d_capital ... relative difference in bank Assets (A)
             d_NPL_ratio ... """
          # calculate d_capital
          if self.PreviousA > 0.0:
              d_capital = (self.A - self.PreviousA) / float(self.PreviousA)
              
          else:
              d_capital = 0.0
          
          # calculate d_NPL_ratio (NPL := non performing loans), ratio - because it is bank size agnostic
          if self.pastLoanAllocated > 0:
              
              NPL_ratio_T_minus_1 = self.pastNPLflow / self.pastLoanAllocated
              NPL_ratio_T = self.NPLflow / self.loanAllocated

              d_NPL_ratio = (NPL_ratio_T - NPL_ratio_T_minus_1) # (for numerical reasons) -> DONT (divide by...) : / float(NPL_ratio_T_minus_1)

              eps = 1e-6
              if NPL_ratio_T_minus_1 > eps:
                  d_NPL_ratio = (NPL_ratio_T - NPL_ratio_T_minus_1) / NPL_ratio_T_minus_1

              else:
                  # when previous NPL was ~0, just use the level
                  d_NPL_ratio = NPL_ratio_T

          else:
              d_NPL_ratio = 0.0
          
          # calculate d_rDiscount (relative difference in Union bank interest rates)
          if self.pastrDiscount > 0.0: # we set self.pastrDiscount = self.rDiscount to avoid jump in t0 ->t1
              d_rDeposit = (self.rDiscount - self.pastrDiscount) / float(self.pastrDiscount)
              
          else:
              d_rDeposit = 0.0

          ### !!! So far this is just a concept, I will modify this later, especially starting from this sentence
          # combine into a single pressure term
          beta_capital = 0.1 # originally 1.0, 0.5, 0.25
          beta_npl = 0.1 # originally 1.0, 0.5, 0.25
          beta_r = 0.1 # originally 1.0, 0.5, 0.25

          pressure = (-beta_capital * d_capital) \
                     + (beta_npl * d_NPL_ratio) \
                     + (beta_r * d_rDeposit)
          
          idx = self.minRatingIndex

          # Only move one step at a time, and only if pressure big enough

          if pressure > 0.0 and self.idx < len(self.ratingLevels) - 1:
              self.idx += 1

          elif pressure <= 0.0 and idx > 0:
              self.idx -=1
          

          self.minRatingIndex = idx
          self.minRating = self.ratingLevels[idx]


          

      def computeBorrowerRating(self, leverage):
          """self.alphaQ ... sensitivity of the 'big' bank to quality of the loan
             self.iota ... sensitivity of the 'big' bank to leverage (from original code)
             
             """

          # raw_score = self.iota * leverage # later add + self.alphaQ * "QUALITY OF LOAN"
          # score = 1 / 1 + math.exp(-raw_score) # use sigmoid to convert raw_score to probability
          
          # Tune later, include also loan quality, sensitivities etc
          if leverage < 1.0:
              return 'A'
          elif leverage < 2:
              return 'B'
          elif leverage < 3:
              return 'C'
          else:
              return 'D'

      def computeProbProvidingLoan(self,leverage,relPhi, minRating):
          # We remake this function
          # probLoan=math.exp(-1*self.iota*leverage)
          # if relPhi<=1.0:                                 
          #  probLoan=math.exp(-1*self.iotaRelPhi*leverage)
          # return probLoan

          ### ----------------------------
          # MY CODE

          # Big banks sort loans into categories

          rating = self.computeBorrowerRating(leverage)

          # order for comparisons
          ratingOrder = {'D': 0, 'C': 1, 'B': 2, 'A': 3} # Update so as to jump across ratings more slowly

          # hard cutoff: below minRating => no lending
          if ratingOrder[rating] < ratingOrder[minRating]: ### !!! add min_rating -> based on macro conditions and r of central bank
              return 0.0
          

          ### This I will modify later !!!

          # otherwise use the original probabilistic kernel
          probLoan = math.exp(-1*self.iota * leverage)
          if relPhi <= 1.0:
              probLoan = math.exp(-1*self.iotaRelPhi * leverage)


          return max(0.0, min(1.0, probLoan))
          ### ----------------------------

      ### ----------------------------------------------------------------------------------------------


      def computeProbBuyingBondLoan(self,leverage):
          probBond=math.exp(-1*self.iotaE*leverage)
          return probBond 

      def existence(self,McountryConsumer,McountryFirm,McountryCentralBank,rBonds,McountryEtat,DcountryAvWage):
          if self.closing=='no' or self.closing=='yes':  
             self.PreviousA=self.A
             self.capitalDismiss=0   
             potentialEnter=0
             self.loanAllocatedTest=0
             for firm in self.Mloan:
                 potentialEnter=potentialEnter+self.Mloan[firm][2]*self.Mloan[firm][3]
                 self.loanAllocatedTest=self.loanAllocatedTest+self.Mloan[firm][2]
             self.potentialEnter=potentialEnter 
             self.moneyUsed=self.Bonds+self.loanAllocatedTest
             self.nonAllocatedMoney=0 
             if self.A>self.moneyUsed: 
                self.nonAllocatedMoney=self.A-self.moneyUsed 
             self.liquidatingBonds(rBonds,McountryCentralBank,McountryEtat)  
             potentialEnter=potentialEnter+self.bondsInterest
             potentialExit=self.serviceFirm
             sumVolume=0  
             self.potentialExitConsumer=0   
             self.potentialExitFirm=0
             for agent in self.Mdeposit:
                 if agent[0]=='C':
                    potentialExit=potentialExit+self.Mdeposit[agent][2]*self.Mdeposit[agent][3]
                    self.potentialExitConsumer=self.potentialExitConsumer+self.Mdeposit[agent][2]*self.Mdeposit[agent][3]
                 if agent[0]=='F':
                    self.potentialExitFirm=self.potentialExitFirm+self.Mdeposit[agent][2]*self.Mdeposit[agent][3]
                 sumVolume=sumVolume+self.Mdeposit[agent][2]
             serviceFirm=self.serviceFirm             
             self.potentialExitDeposit=potentialExit 
             self.totalDeposit=self.potentialExitDeposit+sumVolume
             potentialExitCB=self.loanDiscount*McountryCentralBank[self.country].rDiscount 
             self.potentialExitCB=potentialExitCB
             potentialExit=potentialExit+potentialExitCB       
             self.pastProfit=self.profit     
             self.profit=potentialEnter-potentialExit-self.losses
             self.profitRate=self.profit/float(self.A)       
             self.netProfit=self.profit 
             self.A=self.A+self.profit
             if self.loanAllocated<=self.PreviousA:
                self.depositNotUsed=self.depositReceived 
             if self.loanAllocated>self.PreviousA: 
                self.depositNotUsed=self.depositReceived-(self.loanAllocated-self.PreviousA)
             self.pastServiceFirm=self.serviceFirm  
             self.serviceFirm=0 
             self.depositReimboursed=0
          if self.A>1*self.Fcost*DcountryAvWage[self.country] and self.A>0.0 and self.closing=='no':  
             self.payDepositInterest(McountryConsumer,McountryFirm)
             self.repayingCBLoan(McountryCentralBank)
             self.checkNetWorth() 

             ### ----------------------------------------------------------------------------------------------
             ### Update min rating

             self.updateMinRating()
             ### ----------------------------------------------------------------------------------------------

          if self.A<=1*self.Fcost*DcountryAvWage[self.country] or self.A<=0.0 or self.closing=='yes':
             self.AInExit=self.A
             self.closing='yes'
             self.ResourceAvailable=0
             if self.A>=0: 
                self.capitalDismiss=self.A
                self.depositReimboursed=self.depositReceived+self.potentialExitDeposit
                self.repayingCBLoan(McountryCentralBank)   
                self.loss=0 
             if self.A<0: 
                self.capitalDismiss=0
                self.loss=-self.A 
                if self.ide[1]=='Z1':
                   print()
                   print('self.ide', self.ide)
                   print('self.loanDiscount', self.loanDiscount)
                   print('self.Reserves', self.Reserves)
             self.A=0

      def distributingDividends(self,McountryConsumer,McountryBank,McountryCentralBank):
          self.dividending()
          self.capitalVariation(McountryConsumer,McountryBank,McountryCentralBank)

      def dividending(self):
          self.dividends=0 
          if self.closing=='no' and self.profit>0:  
                self.dividends=self.dividendRate*self.netProfit
                self.A=self.A-self.dividends
          self.pastBankSaving=self.bankSaving 
          self.bankSaving=self.netProfit-self.dividends
       
      def capitalVariation(self,McountryConsumer,McountryBank,McountryCentralBank):
          self.pastA=self.A 
          if self.closing=='no': 
             if self.ResourceAvailable>0:
                self.capitalDismiss=self.ResourceAvailable
             self.A=self.A-self.capitalDismiss
          Ashare=self.A/float(self.PreviousA)
          checkPreviousA=0
          checkA=0    
          givenA=0
          checkinBank=0 
          lastA=0
          totConsumerOldA=0
          subtotal=0  
          totalPayement=0
          for consumeride in self.Downer:
              if self.closing=='yes':# or self.A<=0:
                    ConsumerAshare=0
                    self.closing='yes'
                    distributingA=self.capitalDismiss+self.dividends
                    ConsumerA=McountryConsumer[self.homecountry][consumeride].DLA[self.ide][2]   
                    DismissShare=distributingA*ConsumerA/float(self.PreviousA)
                    McountryConsumer[self.homecountry][consumeride].capitalDismiss=\
                    McountryConsumer[self.homecountry][consumeride].capitalDismiss\
                                                               +DismissShare 
                    totalPayement=totalPayement+DismissShare
                    McountryConsumer[self.homecountry][consumeride].receiving(DismissShare,McountryBank,McountryCentralBank)           
                    if  DismissShare<-0.0000001:
                        print('stop', stop)
                    del McountryConsumer[self.homecountry][consumeride].DLA[self.ide]                    
                    if self.capitalDismiss<-0.00000001:
                       print('stop', stop)
              else:
                  ConsumerAshare=self.A*McountryConsumer[self.homecountry][consumeride].DLA[self.ide][4]
                  subtotal=subtotal+McountryConsumer[self.homecountry][consumeride].DLA[self.ide][4]
                  checkPreviousA=checkPreviousA+McountryConsumer[self.homecountry][consumeride].DLA[self.ide][2]
                  checkinBank=checkinBank+self.Downer[consumeride][2]
                  if  McountryConsumer[self.homecountry][consumeride].DLA[self.ide][2]<-0.000001:
                      print('stop', stop)
                  if self.Downer[consumeride][2]<McountryConsumer[self.homecountry][consumeride].DLA[self.ide][2]-0.00000001 or\
                     self.Downer[consumeride][2]>McountryConsumer[self.homecountry][consumeride].DLA[self.ide][2]+0.00000001:
                     print('stop', stop)
                  givenA=givenA+ConsumerAshare
                  DismissShare=(self.capitalDismiss+self.dividends)*ConsumerAshare/float(self.A)  
                  if  DismissShare<-0.00000001:
                        print('stop', stop)
                  ratioA=ConsumerAshare/float(self.A)
                  McountryConsumer[self.homecountry][consumeride].DLA[self.ide][2]=ConsumerAshare
                  McountryConsumer[self.homecountry][consumeride].DLA[self.ide][4]=ratioA  
                  self.Downer[consumeride][2]=McountryConsumer[self.homecountry][consumeride].DLA[self.ide][2]
                  self.Downer[consumeride][4]=McountryConsumer[self.homecountry][consumeride].DLA[self.ide][4] 
                  checkA=checkA+McountryConsumer[self.homecountry][consumeride].DLA[self.ide][2]
                  McountryConsumer[self.homecountry][consumeride].capitalDismiss=\
                  McountryConsumer[self.homecountry][consumeride].capitalDismiss+DismissShare         
                  totalPayement=totalPayement+DismissShare
                  McountryConsumer[self.homecountry][consumeride].receiving(DismissShare,McountryBank,McountryCentralBank)            
                  if self.capitalDismiss<-0.00000001:
                     print('stop', stop)
          self.reserveWithdrawal(totalPayement,McountryCentralBank) 
          if  givenA<self.A-0.0001 or givenA>self.A+0.0001:
              print('stop', stop)
 
      def reviseA(self):
          if self.A<=self.Fcost or self.A<=0.0:
             print('stop', stop)
         
      def revisingOwnership(self,McountryCentralBank): 
          if self.A<self.pastA:
             payment=self.pastA-self.A
             self.reserveWithdrawal(payment,McountryCentralBank)

      def depositVariation(self,variation,ideAgent,McountryCentralBank):
          if variation>=0: 
             self.depositInjection(variation,ideAgent,McountryCentralBank)
          else:
             reduction=-1*variation
             self.depositWithdrawal(reduction,ideAgent,McountryCentralBank)
             
      def depositInjection(self,injection,ideAgent,McountryCentralBank):
          self.Mdeposit[ideAgent][2]=self.Mdeposit[ideAgent][2]+injection
          self.Deposit=self.Deposit+injection
          self.Reserves=self.Reserves+injection 
          McountryCentralBank[self.country].Reserves=McountryCentralBank[self.country].Reserves+injection


      def depositWithdrawal(self,reduction,ideAgent,McountryCentralBank):
          self.Mdeposit[ideAgent][2]=self.Mdeposit[ideAgent][2]-reduction
          self.Deposit=self.Deposit-reduction     
          if reduction>self.Reserves:
             askingLoan=reduction-self.Reserves  
             self.askingLoanCentralBank(askingLoan,McountryCentralBank)
          self.Reserves=self.Reserves-reduction 
          McountryCentralBank[self.country].Reserves=McountryCentralBank[self.country].Reserves-reduction
         
      def reserveWithdrawal(self,reduction,McountryCentralBank):
          if reduction>self.Reserves:
             askingLoan=reduction-self.Reserves
             self.askingLoanCentralBank(askingLoan,McountryCentralBank)
          self.Reserves=self.Reserves-reduction
          McountryCentralBank[self.country].Reserves=McountryCentralBank[self.country].Reserves-reduction

      def repayingCBLoan(self,McountryCentralBank):
          reduction=self.loanDiscount
          if reduction>self.Reserves+0.0000000001:
             print('stop', stop)
          McountryCentralBank[self.country].Reserves=McountryCentralBank[self.country].Reserves-reduction
          McountryCentralBank[self.country].loanDiscount=McountryCentralBank[self.country].loanDiscount-reduction
          self.Reserves=self.Reserves-reduction
          potentialExitCB=self.loanDiscount*McountryCentralBank[self.country].rDiscount
          self.reserveWithdrawal(potentialExitCB,McountryCentralBank)
          McountryCentralBank[self.country].interestLoanDiscount=McountryCentralBank[self.country].interestLoanDiscount+potentialExitCB
          self.loanDiscount=0
          
      def exitWithdrawal(self,reduction,McountryEtat,McountryCentralBank):
          if reduction<=self.Reserves:
             self.Reserves=self.Reserves-reduction 
             McountryCentralBank[self.country].Reserves=McountryCentralBank[self.country].Reserves-reduction   
          elif reduction>self.Reserves:
             covering=reduction-self.Reserves    
             McountryCentralBank[self.country].Reserves=McountryCentralBank[self.country].Reserves-self.Reserves
             self.Reserves=0
             McountryEtat[self.country].coveringDeposit(covering,McountryCentralBank)

      def loanCreation(self,firmIde,loanValue,interestRate,countryFirm,McountryCentralBank):
          if self.country==countryFirm:
             self.loanCreationDomestic(firmIde,loanValue,interestRate,countryFirm)
          else:
             self.loanCreationForeigner(firmIde,loanValue,interestRate,countryFirm,McountryCentralBank)   
          
      def loanCreationDomestic(self,firmIde,loanValue,interestRate,countryFirm):
          if (firmIde in self.Mloan)==True:
             print('stop', stop)
          self.Mloan[firmIde]=[firmIde,self.ide,loanValue,interestRate,countryFirm]
          self.Loan=self.Loan+loanValue
          self.Deposit=self.Deposit+loanValue
          if (firmIde in self.Mdeposit)==True:
             self.Mdeposit[firmIde][2]=self.Mdeposit[firmIde][2]+loanValue
          if (firmIde in self.Mdeposit)==False:
             self.Mdeposit[firmIde]=[firmIde,self.ide,loanValue,self.rDeposit,countryFirm]
          if self.Mdeposit[firmIde][3]<-0.001:
             print('stop', stop)
 
      def loanCreationForeigner(self,firmIde,loanValue,interestRate,countryFirm,McountryCentralBank):
          if (firmIde in self.Mloan)==True:
             print('stop', stop)
          self.Mloan[firmIde]=[firmIde,self.ide,loanValue,interestRate,countryFirm]
          self.Loan=self.Loan+loanValue
          reduction=loanValue
          if reduction>self.Reserves:
             askingLoan=reduction-self.Reserves
             self.askingLoanCentralBank(askingLoan,McountryCentralBank)
          self.Reserves=self.Reserves-reduction
          McountryCentralBank[self.country].Reserves=McountryCentralBank[self.country].Reserves-reduction

      
      def buyingBonds(self,bondsVolume,rBonds,McountryCentralBank,countryEtat):
          if countryEtat==self.country:
             self.buyingBondsDomestic(bondsVolume,rBonds,McountryCentralBank)  
          if countryEtat!=self.country:
             self.buyingBondsOpen(bondsVolume,rBonds,McountryCentralBank,countryEtat)
                     

      def buyingBondsDomestic(self,bondsVolume,rBonds,McountryCentralBank):
          self.Reserves=self.Reserves-bondsVolume
          McountryCentralBank[self.country].Reserves=McountryCentralBank[self.country].Reserves-bondsVolume
          self.Bonds=self.Bonds+bondsVolume
          self.rBonds=rBonds

      def buyingBondsOpen(self,bondsVolume,rBonds,McountryCentralBank,countryEtat):
          self.Reserves=self.Reserves-bondsVolume
          McountryCentralBank[self.country].Reserves=McountryCentralBank[self.country].Reserves-bondsVolume
          self.Bonds=self.Bonds+bondsVolume
          self.Mbonds.append([bondsVolume,rBonds,countryEtat])

      def liquidatingBonds(self,rBonds,McountryCentralBank,McountryEtat):
          if len(self.Mbonds)>0:
             self.liquidatingBondsOpen(rBonds,McountryCentralBank,McountryEtat)
          else:
             self.liquidatingBondsDomestic(rBonds,McountryCentralBank,McountryEtat)
               
      def liquidatingBondsDomestic(self,rBonds,McountryCentralBank,McountryEtat):
          bondsVolume=self.Bonds*(1+rBonds)  
          bondsService=self.Bonds*rBonds 
          self.Reserves=self.Reserves+bondsVolume
          McountryCentralBank[self.country].Reserves=McountryCentralBank[self.country].Reserves+bondsVolume
          McountryCentralBank[self.country].Bonds=McountryCentralBank[self.country].Bonds+bondsVolume 
          McountryEtat[self.country].Bonds=McountryEtat[self.country].Bonds+bondsService
          self.bondsInterest=self.Bonds*rBonds
          McountryEtat[self.country].interestExpenditure=McountryEtat[self.country].interestExpenditure+self.bondsInterest               
          self.pastBonds=self.Bonds
          self.Bonds=0   
  
      def liquidatingBondsOpen(self,rBonds,McountryCentralBank,McountryEtat):
          self.bondsInterest=0 
          for bonds in self.Mbonds:
              countryEtat=bonds[2]
              bondsService=bonds[0]*bonds[1]
              McountryEtat[countryEtat].Bonds=McountryEtat[countryEtat].Bonds+bondsService
              self.bondsInterest=self.bondsInterest+bondsService
              bondsVolume=bonds[0]+bondsService
              self.Reserves=self.Reserves+bondsVolume
              McountryCentralBank[self.country].Reserves=McountryCentralBank[self.country].Reserves+bondsVolume
              McountryCentralBank[countryEtat].Bonds=McountryCentralBank[countryEtat].Bonds+bondsVolume      
              McountryEtat[countryEtat].interestExpenditure=McountryEtat[countryEtat].interestExpenditure+bondsService 
              if self.country!=countryEtat: 
                 McountryCentralBank[self.country].bondRepeymentInflow=McountryCentralBank[self.country].bondRepeymentInflow+bondsVolume
                 McountryCentralBank[countryEtat].bondRepeymentOutflow=McountryCentralBank[countryEtat].bondRepeymentOutflow+bondsVolume            
          self.pastBonds=self.Bonds      
          self.Bonds=0

      def reservingCompulsory(self,McountryCentralBank):
          minReservesCompulsory=self.minReserve*self.Deposit         
          if minReservesCompulsory>self.Reserves:
             askingLoan=minReservesCompulsory-self.Reserves   
             self.askingLoanCentralBank(askingLoan,McountryCentralBank)              
         
      def askingLoanCentralBank(self,askingLoan,McountryCentralBank):
          pastLoanDiscount=self.loanDiscount             
          self.loanDiscount=self.loanDiscount+askingLoan
          self.Reserves=self.Reserves+askingLoan 
          McountryCentralBank[self.country].loanDiscount=McountryCentralBank[self.country].loanDiscount+askingLoan
          McountryCentralBank[self.country].Reserves=McountryCentralBank[self.country].Reserves+askingLoan
          if self.loanDiscount<0:
             print('stop', stop)

      def payDepositInterest(self,McountryConsumer,McountryFirm):
          for agent in self.Mdeposit: 
              if agent[0]=='C':
                 volume=self.Mdeposit[agent][2]   
                 interest=self.Mdeposit[agent][3]
                 service=volume*interest
                 self.Mdeposit[agent][2]=self.Mdeposit[agent][2]+service
                 self.Deposit=self.Deposit+service
                 McountryConsumer[self.country][agent].Mdeposit[self.ide][2]=\
                   McountryConsumer[self.country][agent].Mdeposit[self.ide][2]+service
                 McountryConsumer[self.country][agent].depositInterest=\
                   McountryConsumer[self.country][agent].depositInterest+service
             
      def demandingBonds(self):
          minReservesCompulsory=self.minReserve*self.Deposit  
          if self.Reserves>minReservesCompulsory:
             self.bondsDemand=self.Reserves-minReservesCompulsory
          else:
             self.bondsDemand=0


      def checkNetWorth(self):
          Liabilities=self.A+self.Deposit+self.loanDiscount 
          Assets=self.Reserves+self.Loan+self.Bonds  
          printing='no'  
          printingControl='no'
          if (Liabilities-Assets)/float(Liabilities+Assets)>0.0001 or (Liabilities-Assets)/float(Liabilities+Assets)<-0.0001 or self.Reserves<-0.001:   
             print('stop', stop)

      def write(self,t,run):
          nameWrite=self.folder+'/'+self.name+'r'+str(run)+'Bank.csv'
          b=open(nameWrite,'a')   
          B=[run, self.ide,t,self.country, self.A,self.profit,self.Bonds,self.Loan,self.Deposit]             
          writer = csv.writer(b)
          writer.writerow(B)
          b.close()    
           
