# matchingCredit_regional.py
#
# Regional banking extension of Di Guilmi (2020) credit-network matching.
#
# ARCHITECTURE
# ============
# Each firm has firm.region (int).  Each regional bank has bank.isRegional=True,
# bank.region (int).  Global banks have bank.isRegional=False (default).
#
# CREDIT MARKET — SINGLE SIMULTANEOUS ROUND
# ==========================================
# Regional ("relationship") and global ("transactional") banks compete in ONE
# matching round at the same timestep. There is no regional-first pass.
#
# For each firm (processed in randomized order), the candidate set is assembled
# once and contains BOTH bank types:
#   - the firm's always-visible regional bank (if one exists for its region),
#     bypassing psiCredit sampling — the relationship is unconditional;
#   - PLUS a psiCredit sample of global (transactional) banks.
# Every candidate quotes a rate in the same round: the regional bank uses the
# soft-information (phi-adjusted) rate
#       r_adj = r_base * (phi_region / phi_firm)^effectiveExp
#   effectiveExp = aExpPhiRegional * (1 - sizeIndifference * sizeScore)
#   sizeScore = (A_firm - p5_economy) / (p95_economy - p5_economy)  in [0,1]
#   (Berger et al. 2005: soft-information value decreasing in firm size;
#    phi_firm > phi_region -> cheaper "hidden gem"; < -> dearer "dirty secret")
# while global banks quote the standard Di Guilmi leverage-only rate.
# The firm approaches candidates cheapest-first, all-or-nothing under running
# Basel capacity (unchanged from Di Guilmi).
#
# This replaces the earlier two-pass design (regional Pass 1 with first claim
# on demand, then a global Pass 2). Under that design the regional credit share
# was inflated by the priority ordering; competing both types in one round makes
# the share reflect genuine rate/relationship competition instead.
#
# When useRegionalBanks=False, no bank is tagged regional, regionalBankMap is
# empty, and the round reduces exactly to the Di Guilmi global market.
#
# OUTPUT ATTRIBUTES (new, available after each creditNetworkEvolution call)
# =========================================================================
#   self.creditCapitalInflow[country]    – unchanged Di Guilmi flow tracking
#   self.creditCapitalOutflow[country]   – unchanged
#   self.loanReceivedRegional[country]   – realised credit from regional banks
#   self.loanReceivedGlobal[country]     – realised credit from global banks
#   self.loanDemandedRegional[country]   – demand of firms that HAD a regional
#                                          bank available this period
#   self.loanDemandedGlobal[country]     – demand of firms with no regional option

import random

class MatchingCredit:

      def creditNetworkEvolution(self, McountryFirm, McountryBank, McountryCentralBank,
                                 DglobalPhiNotTradable, DglobalPhiTradable,
                                 avPhiGlobalTradable, psiCredit=0.2,
                                 aExpPhiRegional=0.5, useRegionalBanks=True,
                                 sizeIndifference=0.7, wRegionalRank=1.0):
          self.psiCredit=psiCredit
          self.aExpPhiRegional=aExpPhiRegional
          self.useRegionalBanks=useRegionalBanks
          self.sizeIndifference=sizeIndifference
          self.wRegionalRank=wRegionalRank
          # Regional phi only needed when regional banks are active
          # Per-country dict: compute regional phi if any country has it on
          _anyOn=(useRegionalBanks if isinstance(useRegionalBanks,bool)
                  else any(useRegionalBanks.get(c,False) for c in McountryFirm))
          if _anyOn:
              self._computeRegionalPhi(McountryFirm)
          else:
              self.DregionalPhi={c:{} for c in McountryFirm}
          self.extractingCreditOpen(McountryFirm,McountryBank,
                                    DglobalPhiNotTradable,DglobalPhiTradable,avPhiGlobalTradable)
          self.matchCreditOpen(McountryFirm,McountryBank,McountryCentralBank)

      # ------------------------------------------------------------------
      def _computeRegionalPhi(self,McountryFirm):
          self.DregionalPhi={}   # DregionalPhi[country][region] = mean phi
          # Economy-wide p5/p95 of firm equity for size-indifference normalisation
          self.DeconomyA_p5={}   # DeconomyA_p5[country]
          self.DeconomyA_p95={}  # DeconomyA_p95[country]
          for country in McountryFirm:
              self.DregionalPhi[country]={}
              sumPhi={}
              sumA={}
              allA=[]
              for firm in McountryFirm[country]:
                  fobj=McountryFirm[country][firm]
                  r=getattr(fobj,'region',0)
                  A=max(fobj.A,0.0001)
                  sumPhi[r]=sumPhi.get(r,0.0)+fobj.phi*A
                  sumA[r]  =sumA.get(r,  0.0)+A
                  allA.append(A)
              for r in sumA:
                  self.DregionalPhi[country][r]=(sumPhi[r]/sumA[r]) if sumA[r]>0 else 1.0
              # p5/p95 — sort once, index; fall back to min/max if <20 firms
              if len(allA)>=2:
                  allA_s=sorted(allA)
                  n=len(allA_s)
                  p5_idx =max(0, int(0.05*n))
                  p95_idx=min(n-1, int(0.95*n))
                  self.DeconomyA_p5[country] =allA_s[p5_idx]
                  self.DeconomyA_p95[country]=allA_s[p95_idx]
              else:
                  self.DeconomyA_p5[country] =0.0001
                  self.DeconomyA_p95[country]=0.0001

      def _effectiveExp(self, firmA, country):
          """Compute the effective phi-adjustment exponent for a firm,
          scaled down for large firms (size-indifference mechanism).
          Uses economy-wide p5/p95 equity as normalisation bounds.
          sizeScore=0 at p5 (small firm, full adjustment)
          sizeScore=1 at p95 (large firm, adjustment reduced by sizeIndifference)
          effectiveExp = aExpPhiRegional * (1 - sizeIndifference * sizeScore)
          Clamped to [0, aExpPhiRegional].
          """
          aExp  = getattr(self,'aExpPhiRegional',0.5)
          si    = getattr(self,'sizeIndifference',0.7)
          if si<=0:
              return aExp
          A_lo  = self.DeconomyA_p5.get(country,  0.0001)
          A_hi  = self.DeconomyA_p95.get(country, 0.0001)
          span  = max(A_hi - A_lo, 0.0001)
          score = min(1.0, max(0.0, (firmA - A_lo) / span))
          return max(0.0, aExp * (1.0 - si * score))

      # ------------------------------------------------------------------
      def extractingCreditOpen(self,McountryFirm,McountryBank,
                                DglobalPhiNotTradable,DglobalPhiTradable,avPhiGlobalTradable):
          self.MloanDemand=[]
          self.MloanSupply=[]
          self.ListLoanSupply={}

          avPhiGlobalNotTradable=0.0
          for country in DglobalPhiNotTradable:
              avPhiGlobalNotTradable+=DglobalPhiNotTradable[country]
          if len(DglobalPhiNotTradable)>0:
              avPhiGlobalNotTradable/=len(DglobalPhiNotTradable)

          for country in McountryFirm:
              posFirm=0
              for firm in McountryFirm[country]:
                  fobj=McountryFirm[country][firm]
                  fobj.orderCreditor()
                  fobj.Mloan={}
                  fobj.loanReceived=0
                  fobj.losses=0
                  fobj.interestRate=0
                  if fobj.loanDemand>0.001:
                      leverage=fobj.loanDemand/float(fobj.A)
                      if fobj.tradable=='yes':
                          relPhi=fobj.phi/avPhiGlobalTradable if avPhiGlobalTradable>0 else 1.0
                      else:
                          relPhi=fobj.phi/avPhiGlobalNotTradable if avPhiGlobalNotTradable>0 else 1.0
                      region=getattr(fobj,'region',0)
                      phiRegion=self.DregionalPhi.get(country,{}).get(region,1.0)
                      # demand row: [ide, pos, country, demand, filled, leverage,
                      #              relPhi, region, phiRegion, firmPhi]
                      self.MloanDemand.append(
                          [fobj.ide, posFirm, fobj.country,
                           fobj.loanDemand, 0, leverage,
                           relPhi, region, phiRegion, fobj.phi,
                           fobj.A])  # index 10: firmA for size-indifference
                  posFirm+=1

              posBank=0
              for bank in McountryBank[country]:
                  bobj=McountryBank[country][bank]
                  bobj.Mloan={}
                  bobj.loanAllocated=0
                  bobj.losses=0
                  bobj.serviceReceived=0
                  bobj.volumeLoanReceived=0
                  bobj.loanSupply=bobj.mu1*bobj.A  # Di Guilmi baseline formula (Model-2 bank has no maxLoanSupplyBasel)
                  bobj.maxLoanFirm=5.0*bobj.A     # Basel large-exposure cap: max 25% of equity to one borrower ### -> change to 0.25->2 ->4 
                  bobj.checkNetWorth()
                  if bobj.loanSupply>0.001:
                      isRegional=getattr(bobj,'isRegional',False)
                      bankRegion=getattr(bobj,'region',-1)
                      # supply row: [ide, pos, country, remainingCap, allocated,
                      #              maxLoanFirm, isRegional, bankRegion]
                      srow=[bobj.ide,posBank,bobj.country,
                            bobj.loanSupply,0,bobj.maxLoanFirm,
                            isRegional,bankRegion]
                      self.MloanSupply.append(srow)
                      self.ListLoanSupply[bobj.ide]=posBank
                      posBank+=1

      # ------------------------------------------------------------------
      def matchCreditOpen(self,McountryFirm,McountryBank,McountryCentralBank):
          self.creditCapitalInflow={}
          self.creditCapitalOutflow={}
          self.loanReceivedRegional={}
          self.loanReceivedGlobal={}
          self.loanDemandedRegional={}
          self.loanDemandedGlobal={}
          for country in McountryFirm:
              self.creditCapitalInflow[country]=0
              self.creditCapitalOutflow[country]=0
              self.loanReceivedRegional[country]=0
              self.loanReceivedGlobal[country]=0
              self.loanDemandedRegional[country]=0
              self.loanDemandedGlobal[country]=0

          # O(1) capacity lookup by bank ide
          supplyByIde={row[0]:row for row in self.MloanSupply}
          psi=getattr(self,'psiCredit',0.2)
          aExpPhi=getattr(self,'aExpPhiRegional',0.5)

          # ---- Build regional-bank lookup: (country,region) -> bank ide ----
          regionalBankMap={}   # (country,region) -> ide  (only if capacity>0)
          _urb_map=getattr(self,'useRegionalBanks',False)
          def _countryRegOn(c):
              if isinstance(_urb_map,dict): return _urb_map.get(c,False)
              return bool(_urb_map)
          for srow in self.MloanSupply:
              if srow[6] and _countryRegOn(srow[2]):   # isRegional and country has regional on
                  key=(srow[2],srow[7])   # (country, bankRegion)
                  regionalBankMap[key]=srow[0]

          # ================================================================
          # SINGLE-PASS TWO-SIDED MATCHING ROUND
          # ================================================================
          # Regional ("relationship") and global ("transactional") banks compete
          # in ONE round at the same timestep — no regional-first pass. Both
          # sides rank:
          #
          # STEP 1 — Firms approach a candidate set (no priority ordering):
          #   each firm approaches its always-visible regional bank (bypassing
          #   psiCredit sampling — the relationship is unconditional) PLUS a
          #   psiCredit sample of global banks. This builds, for each bank, the
          #   queue of borrowers approaching it.
          #
          # STEP 2 — Banks rank their borrower queue (lower score served first):
          #   - global/transactional banks rank by leverage ascending
          #       score = leverage           (safest borrowers first)
          #   - regional banks rank by leverage AND productivity-relative-to-region,
          #     with tunable weight wRegionalRank on the soft-information signal:
          #       score = leverage - wRegionalRank*(phi_firm/phi_region - 1)
          #     so a firm more productive than its region (relScore>1) gets a
          #     better (lower) rank; less productive (relScore<1) a worse rank.
          #   Each bank tenders an OFFER (rate, bank) to the borrowers it can fund
          #   in rank order, reserving Basel capacity tentatively. Rate: regional
          #   bank uses the soft-information (phi-adjusted) rate; global banks the
          #   standard leverage-only Di Guilmi rate.
          #
          # STEP 3 — Firms rank received offers by price and accept the cheapest.
          #   Single pass: when a firm commits to a bank, that bank's capacity is
          #   deducted; an offer whose bank no longer has capacity (consumed by an
          #   earlier, for-it-cheaper commitment) is skipped and the firm takes its
          #   next-cheapest still-fundable offer. Firms crowded out of a bank's
          #   ranked queue do not re-propose this period (single pass).
          #
          # Demand-attribution for the diagnostic columns:
          #   loanDemandedRegional[country] += demand of firms that HAD a regional
          #       bank available this period; loanDemandedGlobal otherwise.
          #   loanReceivedRegional/Global   += realised loans by lender type.
          # ================================================================
          _urbSetting=getattr(self,'useRegionalBanks',False)
          def _useRegForCountry(c):
              if isinstance(_urbSetting,dict): return _urbSetting.get(c,False)
              return bool(_urbSetting)
          wRank=getattr(self,'wRegionalRank',1.0)

          # drow indices: 0 ide,1 pos,2 country,3 demand,4 filled,5 leverage,
          #               6 relPhi,7 region,8 phiRegion,9 firmPhi,10 firmA
          drowByFirm={drow[0]:drow for drow in self.MloanDemand}

          # ---- STEP 1: firms approach; build each bank's borrower queue ----
          # bankQueue[ideBank] = list of (rankScore, rate, ideFirm)
          bankQueue={ide:[] for ide in supplyByIde}
          for drow in self.MloanDemand:
              ideFirm    =drow[0]
              countryFirm=drow[2]
              demand     =drow[3]
              leverage   =drow[5]
              firmRegion =drow[7]
              phiRegion  =drow[8]
              firmPhi    =drow[9]
              firmA      =drow[10]
              if demand<=0.001:
                  continue
              firmObj=McountryFirm[countryFirm][ideFirm]

              _useRegHere=_useRegForCountry(countryFirm)
              regBankIde=regionalBankMap.get((countryFirm,firmRegion)) if _useRegHere else None

              # demand attribution: did the firm have a usable regional option?
              if regBankIde is not None and regBankIde not in firmObj.Lcreditor:
                  self.loanDemandedRegional[countryFirm]+=demand
              else:
                  self.loanDemandedGlobal[countryFirm]+=demand

              # global candidates, psiCredit-sampled
              if _useRegHere:
                  globalCandidates=[ide for ide,srow in supplyByIde.items()
                                    if not srow[6] and ide not in firmObj.Lcreditor]
              else:
                  globalCandidates=[ide for ide,srow in supplyByIde.items()
                                    if ide not in firmObj.Lcreditor]
              if psi<1.0:
                  ksample=max(1,int(round(psi*len(globalCandidates))))
                  approached=random.sample(globalCandidates,min(ksample,len(globalCandidates)))
              else:
                  approached=list(globalCandidates)

              # always-visible regional bank joins the same round
              if (regBankIde is not None and regBankIde in supplyByIde
                      and regBankIde not in firmObj.Lcreditor
                      and regBankIde not in approached):
                  approached.append(regBankIde)

              # register this firm in each approached bank's queue, with the
              # bank's rank score for this borrower and the rate it would quote
              for ideBank in approached:
                  srow=supplyByIde[ideBank]
                  cBank=srow[2]
                  isReg=srow[6]
                  base=McountryBank[cBank][ideBank].computeInterestRate(leverage)
                  if isReg and phiRegion>0 and firmPhi>0:
                      relScore=firmPhi/phiRegion
                      phiR=phiRegion/firmPhi
                      eExp=self._effectiveExp(firmA,countryFirm)
                      rate=base*(phiR**eExp) if eExp>0 else base
                      rate=max(rate,McountryBank[cBank][ideBank].rDiscount)
                      # regional ranking: leverage minus weighted productivity edge
                      rankScore=leverage - wRank*(relScore-1.0)
                  else:
                      rate=base
                      rankScore=leverage   # global banks rank by leverage only
                  bankQueue[ideBank].append((rankScore,rate,ideFirm))

          # ---- STEP 2: each bank ranks its queue; tender offers under capacity ----
          # offersByFirm[ideFirm] = list of (rate, ideBank)
          offersByFirm={}
          for ideBank,queue in bankQueue.items():
              if not queue:
                  continue
              srow=supplyByIde[ideBank]
              cap=srow[3]
              # lower rankScore served first; random tie-break
              random.shuffle(queue)
              queue.sort(key=lambda x:x[0])
              reserved=0.0
              for rankScore,rate,ideFirm in queue:
                  dem=drowByFirm[ideFirm][3]
                  if dem<=0.001:
                      continue
                  # Basel large-exposure cap: offer at most maxLoanFirm to one borrower
                  maxFirm=srow[5]   # maxLoanFirm stored at index 5
                  offerable=min(dem,maxFirm)
                  if offerable<=0.001:
                      continue
                  # tentative reservation under total-supply cap
                  if cap-reserved>=offerable-0.000001:
                      reserved+=offerable
                      offersByFirm.setdefault(ideFirm,[]).append((rate,ideBank,offerable))
                  # if this borrower doesn't fit, continue down the queue:
                  # a smaller later borrower may still fit the remaining cap

          # ---- STEP 3: firms rank offers by price; accept cheapest; commit ----
          # Process firms in random order so no firm has systematic priority in
          # claiming shared bank capacity. Capacity is deducted as we commit.
          firmsWithOffers=list(offersByFirm.keys())
          random.shuffle(firmsWithOffers)
          for ideFirm in firmsWithOffers:
              drow=drowByFirm[ideFirm]
              demand=drow[3]
              if demand<=0.001:
                  continue
              countryFirm=drow[2]
              firmObj=McountryFirm[countryFirm][ideFirm]
              offers=offersByFirm[ideFirm]
              random.shuffle(offers)              # tie-break equal prices
              offers.sort(key=lambda x:x[0])      # cheapest first
              for rate,ideBank,offerable in offers:
                  srow=supplyByIde[ideBank]
                  remainingCap=srow[3]
                  countryBank =srow[2]
                  isRegionalLender=srow[6]
                  # loan is the smaller of what the firm still needs and what
                  # the bank offered (already capped at 0.25*A in Step 2)
                  loan=min(demand,offerable)
                  if remainingCap>=loan-0.000001:
                      srow[3]-=loan
                      srow[4]+=loan
                      drow[3]-=loan
                      drow[4]+=loan
                      firmObj.receavingLoan(
                          ideBank,loan,rate,
                          McountryBank[countryBank][ideBank].rDeposit,
                          countryBank,McountryBank,McountryCentralBank)
                      McountryBank[countryBank][ideBank].loanCreation(
                          ideFirm,loan,rate,countryFirm,McountryCentralBank)
                      if countryFirm!=countryBank:
                          self.creditCapitalInflow[countryFirm] +=loan
                          self.creditCapitalOutflow[countryBank]+=loan
                          McountryCentralBank[countryFirm].moneyInflow +=loan
                          McountryCentralBank[countryBank].moneyOutflow+=loan
                      # A regional bank is only counted as "regional" for the
                      # firm if they share the same country. A regional bank
                      # lending cross-border acts as a global/transactional
                      # lender from the borrowing firm's perspective.
                      if isRegionalLender and countryBank == countryFirm:
                          self.loanReceivedRegional[countryFirm]+=loan
                      else:
                          self.loanReceivedGlobal[countryFirm]+=loan
                      break
