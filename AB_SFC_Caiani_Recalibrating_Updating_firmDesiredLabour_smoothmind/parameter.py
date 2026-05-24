import csv
import os
import math

#mu5.8

class Parameter:
      def __init__(self):                         
          self.name= 'muxSnCo1upsilon20.865polnnPolVar0.512' ### orginally: 'muxSnCo5upsilon20.7polModPolVar0.512' #1.625'#2.876'#2.231#1.625'#1.053#0.512'
          self.folder='/Users/krystofkalhous/Desktop/OUTPUT'+self.name ### orginally: self.folder='/home/ermanno/Desktop/mu/mu7.1/data/data'+self.name
          #self.folder='/home/ermanno/mu/mu7.1/data/data'+self.name
          #Monte Carlo runs
          firstrun=0#
          lastrun= 10 ### originally: 49#
          self.Lrun=range(firstrun,lastrun+1)
          self.weSeedRun='yes'      
          # space and time
          self.ncycle=1001
          self.ncountry=1 ### originally: 5#(K)
          self.nconsumer=500 ### originally: 500 #1000 #(H) # 10_000
          self.propTradable=0.0 ### orginally: 0.4 #0.4#(c_T)           
          # firms
          self.A=10#(A^0)
          self.upsilon=1.0#1.0# (upsilon)
          self.upsilon2=0.865#(upsilon2)   ### 0.85 -> 0.87->0.865
          self.phi=1.0 # (phi_0)
          self.delta=0.02#0.03 (delta) ### 0.03 -> 0.02 ->0.015 doesnt help so ->0.02
          self.dividendRate=0.95#0.95# (rho)   ### change from 0.95 ->0.90 depresses the economy -> try again 0.90 (after parameter reshuffle and wage offred rework) but still too strong -> 0.925 -> dividend rate is too sensitive, do not touch it for now
          self.gamma=0.04#(gamma)
          self.ni=0.8#1.0#(ni) 
          self.deltaInnovation=0.03# (delta) ### 0.04 -> 0.03
          self.Fcost=1.0# (F)
          self.minMarkUp=0.0#0.0# (minimum mark-up)
          self.theta=0.10 ### from 0.20 -> 0.10
          self.jobDuration=2 #self.ncycle#40 ### previous 2 -> 4 ### this is inactive !!!if active 2 (smooths)-> smoother?: 4 -> using 2, 4 does not help much
          #consumers         
          self.bound=10# # (psi)  n. matching       ### 10 -> 8 -> no back to 10, it is weird lever
          self.cDisposableIncome=0.90# (c_y)
          self.cWealth=0.10# (c_D)
          self.liqPref=0.1# (lambda) 
          self.beta=2.0#2.0#0.25#2.0#(beta)
          self.ls=1.0 #(l^S) 
          self.wBar=0.1 #(w bar)
          self.w0=1.0 #(w_0)          
          #bank
          self.probBank=0.1#0.1(eta)
          self.sigma=4.0 
          self.minReserve=0.1  #(mu_2)        
          self.xi=0.003#0.003# (chi)     
          self.rDeposit=0.001# (r_re)  
          self.mu1=16.0#12.0#(mu_1) # 20.0 -> 16.0 ->15.0 (not a good lever) ->16.0
          self.iota=0.56#0.5#1.0#(iota_l) ### 0.5->0.55 ok but try ->0.525 not better ->0.55->056
          self.iotaE=0.1#(iota_b) 
          #etat
          self.taxRatio=0.4 #(tau_0)
          self.G=0.4*self.nconsumer  #(G)              
          self.xiBonds=self.xi#(chi_B)   
          self.maxPublicDeficit=0.03#(d^max)  
          self.taxRatioMin=0.35#0.35 #(tau_{min})
          self.taxRatioMax=0.46#0.45 #(tau_{max})
          self.gMin=0.40 #(g_min)
          self.gMax=0.58#float('inf')# #(g_max)       
          #central bank initial discount value
          self.rDiscount=0.001 #(r_ {re})
          self.rBonds=0.001 #(r_{b0})   
          self.zeta=0.1 #(zeta) 
          self.rBar=0.0075 #(rBar)
          self.csi=0.8 #(xi)
          self.csiDP=2.0#(xiDP)  
          self.inflationTarget=0.005#(DeltaP) 
          # policy
          self.policyKind='nn'#'nn'#'ModAll'#'Mod'
          self.startingPolicy=500#(policy starting time)
          self.policyVariable=0.512#1.625##2.876#0.512#1.625#2.231#1.053
          self.maxPublicDeficitAusterity=self.policyVariable#(d)
          self.upsilonConsumer=self.policyVariable#10.0
          self.deltaLaborPolicy=self.delta/2.0
          self.epsilon=0.1
          self.k=30.0
          #timing  collecting simulation data
          self.timeCollectingStart=0#
          self.LtimeCollecting=[]
          self.printAgent='no' 
          for cycle in range(self.ncycle):
              self.LtimeCollecting.append(cycle)
          #name='munCo'+str(self.ncountry)+'beta'+str(self.beta)+'pol'+self.policyKind+'PolVar'+str(self.policyVariable) 
          name='muxSnCo'+str(self.ncountry)+'upsilon2'+str(self.upsilon2)+'pol'+self.policyKind+'PolVar'+str(self.policyVariable)
          #name='bdnCo'+str(self.ncountry)+'beta'+str(self.beta)+'pol'+self.policyKind+'PolVar'+str(self.policyVariable)
          # +'LPupsilon'+str(self.upsilonConsumer)+'epsilon'+str(self.epsilon)+'k'+str(self.k) 
          if name!=self.name:
             print('self.name ', self.name)
             print('name      ', name)
             print('stop', stop)
        
      def directory(self):
          newpath=self.folder
          if os.path.exists(newpath)==False:
             os.makedirs(newpath)   

     
