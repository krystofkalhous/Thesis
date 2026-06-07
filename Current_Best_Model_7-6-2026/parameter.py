import csv
import os
import math

#mu5.8

class Parameter:
      def __init__(self):
          #Monte Carlo runs
          firstrun=0
          lastrun=10 ### originally: 49
          self.Lrun=range(firstrun,lastrun+1)
          self.weSeedRun='yes'
          # space and time
          self.ncycle=1001
          self.ncountry=2  ### originally: 5 (K)
          self.nconsumer=500  ### originally: 500 (H)
          self.propTradable=0.4  ### originally: 0.4 (c_T)
          # firms
          self.A=10  # (A^0)
          self.upsilon=1.625  # (upsilon)
          self.upsilon2=0.7  # (upsilon2)
          self.phi=1.0  # (phi_0)
          self.delta=0.04  # (delta)
          self.dividendRate=0.95  # (rho) dividend payout rate for global/private banks
          # Regional (Sparkasse-like) banks retain more equity because they have
          # no private shareholders to pay out. Surplus stays in the institution.
          # 0.0  = all profit retained (pure Sparkasse)
          # 0.20 = cooperative-style: small member dividend, most retained
          # 0.95 = same as global banks (current default, no differentiation)
          self.regionalDividendRate=0.20 # relationship-bank PAYOUT fraction; rest retained (was 0.95)
          self.lockRelationshipReserves=True # retained reserves excluded from household reinvestment
          self.reserveDevolution='owners'    # 'owners' (SFC-safe default) | 'successor'
          self.gamma=0.03  # (gamma)
          self.ni=0.8  # (ni)
          self.deltaInnovation=0.04  # (delta)
          self.lambdaInn=1.0  # innovation catch-up strength (1=full free convergence; <1 = stronger path dependence)
          self.rcapOn=False    # research-capital stock modification
          self.rcapDeprec=0.15
          self.rcapMaint=0.15
          self.rcapAbsorp=1.0
          self.Fcost=1.0  # (F)
          self.minMarkUp=0.0  # (minimum mark-up)
          self.theta=0.2
          self.jobDuration=0
          # consumers
          self.bound=10  # (psi) n. matching
          self.cDisposableIncome=0.9  # (c_y)
          self.cWealth=0.1  # (c_D)
          self.liqPref=0.1  # (lambda)
          self.liqPrefFloor=0.0  # household minimum liquidity preference (deposit-share floor)
          self.cEquity=0.0  # consumption propensity out of equity wealth (wealth effect)
          # --- Relationship-bank protection fund (IPS-style) ---
          self.fundOn=False           # master switch for the protection fund
          self.fundContribBase=0.0    # gamma_base: baseline contribution fraction of retained surplus
          self.fundCountercyclical=0.0# theta: countercyclical strength (extra contribution per unit boom)
          self.recapKappa=2.0         # recap target = recapKappa * viability floor
          self.fundRecapOn=True       # if False: contributions still drain, but NO recaps (decoupling arm)
          self.beta=2.0  # (beta)
          self.ls=1.0  # (l^S)
          self.wBar=0.1  # (w bar)
          self.w0=1.0  # (w_0)
          # bank
          self.probBank=0.1  # (eta)
          self.sigma=4.0
          self.minReserve=0.1  # (mu_2)
          self.xi=0.003  # (chi)
          self.rDeposit=0.001  # (r_re)
          self.mu1=20.0  # (mu_1)
          self.iota=0.5  # (iota_l)
          self.iotaE=0.1  # (iota_b)
          # Di Guilmi credit-network extension
          self.sensitivity_a=0.01
          self.chiBasel=0.0625
          self.psiCredit=0.2        # fraction of GLOBAL banks sampled per firm per period ### try change 0.2 -> 0.4 => bigger global banks? ->try 0.2
          self.a0=0.006
          self.aExpBank=1.0
          self.aExpFirm=1.0
          # Regional banking extension
          # nRegion: number of geographic regions within each country.
          # Consumers are partitioned into nRegion equal bins
          # (consumer i -> region i % nRegion). Entering firms inherit the
          # region of the investing consumer (plurality vote). Each region
          # may have one dedicated regional bank that:
          #   (a) is always visible to its region's firms (bypasses psiCredit sampling)
          #   (b) observes firm phi relative to the regional mean phi_region
          #   (c) adjusts rate: r *= (phi_region/phi_firm)^aExpPhiRegional
          #       phi_firm > phi_region  ->  ratio<1  ->  rate falls  (hidden gem)
          #       phi_firm < phi_region  ->  ratio>1  ->  rate rises  (dirty secret)
          #   (d) ranks borrowers by leverage - wRegionalRank*(phi_firm/phi_region - 1)
          # Global banks (isRegional=False) operate as in the Di Guilmi baseline.
          self.nRegion=10            # must divide nconsumer evenly; 500/5=100 per region ### try 5->10

          self.aExpPhiRegional=0.8  # phi-adjustment strength; 0=none; 1=linear; 2=quadratic ### 0.5 -> 0.8

          # Per-country regional bank toggle.
          # Set useRegionalBanks[country] = True  to activate regional banks in that country.
          # Set useRegionalBanks[country] = False to run Di Guilmi baseline in that country.
          # Countries not listed here default to False.
          # Example: both countries off  -> {}  or  {0: False, 1: False}
          #          country 0 on only   -> {0: True}
          #          both on             -> {0: True, 1: True}
          self.useRegionalBanks={0: False, 1: False}  ### <-- toggle per country here

          # ---- Firm-entry funding mode ----
          # firmEntryMode: how entering firms are funded.
          #   'national' (DEFAULT) -> a single national capital pool, as in the
          #                 original model and in bank entry. Firm entry is NOT
          #                 limited by regional borders: any consumer's savings
          #                 may help capitalize any firm. The new firm is assigned
          #                 a region by the *plurality* of its founders' home
          #                 regions (see _mostCommonRegion in enterExit.py).
          #   'regional'  -> retained for reference only: one capital pool per
          #                 region, firm bound to the pool it was founded from.
          #                 This is the configuration that drives the unbounded
          #                 both-regional (True/True) firm-entry spiral; not for
          #                 production use.
          self.firmEntryMode='national'
          # entryTrace: when True, append per-period entry diagnostics to
          # <folder><name>EntryTrace.csv (firms/banks founded, capital available,
          # eligible investors, avg firm size). Leave False for production runs.
          self.entryTrace=False

          # Local deposit bias: probability that a regional consumer's deposit
          # lands at their regional bank in a given period.
          # 0.0 = pure random (Di Guilmi baseline); 0.35 = default; 1.0 = always local
          # Only active when the country's useRegionalBanks entry is True.
          self.depositLocalBias=0.35 ### 0.35 -> 0.0 nothing happens

          # Size-indifference: how much the phi-adjustment fades for large firms.
          # Uses economy-wide p5/p95 equity as bounds.
          # 0.0 = all firms get full phi adjustment (size-blind)
          # 0.7 = largest firms (p95) retain only 30% of the adjustment
          # 1.0 = largest firms fully indifferent (effectiveExp=0)
          self.sizeIndifference=0.7

          # Regional borrower-ranking weight.
          # global banks : score = leverage
          # regional bank: score = leverage - wRegionalRank*(phi_firm/phi_region - 1)
          # 0.0 = regional banks rank by leverage only (like global banks)
          self.wRegionalRank=2.0 ### try 1.0 ->2.0

          # etat
          self.taxRatio=0.4  # (tau_0)
          self.G=0.4*self.nconsumer  # (G)
          self.xiBonds=self.xi  # (chi_B)
          self.maxPublicDeficit=0.03  # (d^max)
          self.taxRatioMin=0.35  # (tau_{min})
          self.taxRatioMax=0.45  # (tau_{max})
          self.gMin=0.4  # (g_min)
          self.gMax=0.6  # (g_max)
          # central bank
          self.rDiscount=0.001  # (r_{re})
          self.rBonds=0.001  # (r_{b0})
          self.zeta=0.1  # (zeta)
          self.rBar=0.0075  # (rBar)
          self.csi=0.8  # (xi)
          self.csiDP=2.0  # (xiDP)
          self.inflationTarget=0.005  # (DeltaP)
          # policy
          self.policyKind='nn'
          self.startingPolicy=500
          self.policyVariable=0.512
          self.maxPublicDeficitAusterity=self.policyVariable
          self.upsilonConsumer=self.policyVariable
          self.deltaLaborPolicy=self.delta/2.0
          self.epsilon=0.1
          self.k=30.0
          # timing
          self.timeCollectingStart=0
          self.LtimeCollecting=[]
          self.printAgent='no'
          for cycle in range(self.ncycle):
              self.LtimeCollecting.append(cycle)

          # ---- Environment overrides (used by run_experiments.py) ----
          def _envbool(k,d):
              v=os.environ.get(k)
              return d if v is None else v.lower() in ('1','true','yes','on')
          def _envfloat(k,d):
              v=os.environ.get(k)
              return d if v is None else float(v)
          for c in range(self.ncountry):
              v=os.environ.get('RB_C%d'%c)
              if v is not None:
                  self.useRegionalBanks[c]=v.lower() in ('1','true','yes','on')
          self.regionalDividendRate=_envfloat('REL_PAYOUT',self.regionalDividendRate)
          self.lockRelationshipReserves=_envbool('REL_LOCK',self.lockRelationshipReserves)
          self.reserveDevolution=os.environ.get('REL_DEVOLUTION',self.reserveDevolution)
          _fr=os.environ.get('FIRSTRUN'); _lr=os.environ.get('LASTRUN')
          if _fr is not None and _lr is not None:
              self.Lrun=range(int(_fr),int(_lr)+1)
          self._configTag=os.environ.get('CONFIG_TAG','')
          self.liqPrefFloor=_envfloat('LIQPREF_FLOOR',self.liqPrefFloor)
          self.ncycle=int(os.environ.get('NCYCLE',self.ncycle))
          self.cEquity=_envfloat('CEQUITY',self.cEquity)
          self.fundOn=_envbool('FUND_ON',self.fundOn)
          self.fundContribBase=_envfloat('FUND_CONTRIB',self.fundContribBase)
          self.fundCountercyclical=_envfloat('FUND_CCYC',self.fundCountercyclical)
          self.recapKappa=_envfloat('RECAP_KAPPA',self.recapKappa)
          self.fundRecapOn=_envbool('FUND_RECAP',self.fundRecapOn)
          self.lambdaInn=_envfloat('LAMBDA_INN',self.lambdaInn)
          self.psiCredit=_envfloat('PSI_CREDIT',self.psiCredit)
          self.wRegionalRank=_envfloat('WREG_RANK',self.wRegionalRank)
          self.aExpPhiRegional=_envfloat('AEXP_PHI',self.aExpPhiRegional)
          self.rcapOn=_envbool('RCAP_ON',self.rcapOn)
          self.rcapDeprec=_envfloat('RCAP_DEPREC',self.rcapDeprec)
          self.rcapMaint=_envfloat('RCAP_MAINT',self.rcapMaint)
          self.rcapAbsorp=_envfloat('RCAP_ABSORP',self.rcapAbsorp)

          # Build name: per-country regional suffix + relationship-lender encoding
          # (payout/lock/devolution/config-tag in the folder name is the stale-file guard)
          anyOn=any(self.useRegionalBanks.get(c,False) for c in range(self.ncountry))
          if anyOn:
              onList=[str(c) for c in range(self.ncountry)
                      if self.useRegionalBanks.get(c,False)]
              suffix='_RegionalCo'+''.join(onList)
          else:
              suffix='_RegionalOff'
          name='muxSnCo'+str(self.ncountry)+'upsilon2'+str(self.upsilon2)\
               +'pol'+self.policyKind+'PolVar'+str(self.policyVariable)+suffix
          name=name+'_relPay'+str(self.regionalDividendRate)\
               +('_lock' if self.lockRelationshipReserves else '_nolock')\
               +'_dev'+str(self.reserveDevolution)+'_lpf'+str(self.liqPrefFloor)+'_ce'+str(self.cEquity)
          if self.fundOn:
              name=name+'_fund'+str(self.fundContribBase)+'cc'+str(self.fundCountercyclical)\
                   +'k'+str(self.recapKappa)
              if not self.fundRecapOn:
                  name=name+'norecap'
          if self.lambdaInn!=1.0:
              name=name+'_lam'+str(self.lambdaInn)
          if self.psiCredit!=0.2:
              name=name+'_psi'+str(self.psiCredit)
          if self.wRegionalRank!=2.0:
              name=name+'_wr'+str(self.wRegionalRank)
          if self.aExpPhiRegional!=0.8:
              name=name+'_ae'+str(self.aExpPhiRegional)
          if self.rcapOn:
              name=name+'_rcapM'+str(self.rcapMaint)+'_d'+str(self.rcapDeprec)+'_a'+str(self.rcapAbsorp)
          if getattr(self,'_configTag',''):
              name=name+'_'+self._configTag
          self.name=name
          _base=os.environ.get('OUTPUT_BASE','/Users/krystofkalhous/Desktop/OUTPUT')
          self.folder=_base+self.name

      def directory(self):
          newpath=self.folder
          if os.path.exists(newpath)==False:
             os.makedirs(newpath, exist_ok=True)
