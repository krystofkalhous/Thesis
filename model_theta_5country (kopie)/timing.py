# timing.py
#
# Regional banking extension wired into the Multi-Country Monetary Union ABM.
# All regional logic is controlled from parameter.py:
#   para.useRegionalBanks  – dict {country: bool}  (toggle per country independently)
#   para.nRegion           – number of geographic regions per country
#   para.depositLocalBias  – local deposit probability [0,1]
#   para.psiCredit         – fraction of global banks sampled per firm per period
#   para.aExpPhiRegional   – phi-adjustment exponent for regional bank rates
#   para.sizeIndifference  – fade of phi-adjustment for large firms
#   para.wRegionalRank     – productivity weight in regional bank's borrower ranking
#
# Set useRegionalBanks = {} or {c: False for all c} to run the Di Guilmi baseline
# identically to the original timing.py for every country.
#
#    Copyright (C) 2017  Alessandro Caiani, Ermanno Catullo, Mauro Gallegati.
#    GNU General Public License v3 — see READMY.txt for details.

from parameter import *
from initialize import *
from firm import *
from consumer import *
from matchingConsumption import *
from matchingLaborCapital import *
from enterExit import *
from aggregator import *
from time import *
import random
from bank import *
from matchingCredit import *
from matchingBonds import *
from matchingDeposit import *
from globalInnovation import *
from printParameters import *
from centralBankUnion import *
from policy import *
from fund import *
from softInfo import *
import os

# --- optional union risk-sharing transfer (surplus recycling); default OFF = baseline ---
_UNION_TRANSFER_ON=os.environ.get('UNION_TRANSFER_ON','0').lower() in ('1','true','yes','on')
_UNION_TRANSFER_RATE=float(os.environ.get('UNION_TRANSFER_RATE','0.5'))      # fraction of the per-period imbalance recycled
_UNION_TRANSFER_SAFEDY=float(os.environ.get('UNION_TRANSFER_SAFEDY','5.0'))  # stop transferring if source debt/Y exceeds this
_UNION_TRANSFER_TOHH=os.environ.get('UNION_TRANSFER_TOHH','0').lower() in ('1','true','yes','on')  # also inject to recipient households (demand)

# parameter
para=Parameter()
para.directory()
printPa=PrintParameters(para.name,para.folder)

for run in para.Lrun:
    if para.weSeedRun=='yes':
       random.seed(run)

    printPa.printingPara(para,run)

    # --- Initialisation ---
    ite=Initialize(para.ncountry,para.nconsumer,para.A,para.phi,
                   para.beta,para.folder,para.name,run,para.delta,
                   para.taxRatio,para.rDiscount,para.G,
                   para.cDisposableIncome,para.cWealth,para.liqPref,para.rDeposit,para.rBonds,
                   para.upsilon,para.maxPublicDeficit,para.xiBonds,para.ls,para.taxRatioMin,
                   para.taxRatioMax,para.gMin,para.gMax,para.w0,para.wBar,para.upsilon2,
                   nRegion=para.nRegion)

    ite.createCentralBank()
    ite.createConsumer()
    for _c in ite.McountryConsumer:
        for _id in ite.McountryConsumer[_c]:
            ite.McountryConsumer[_c][_id].liqPrefFloor=para.liqPrefFloor
            ite.McountryConsumer[_c][_id].cEquity=para.cEquity
    ite.createBasic()
    ite.createEtat()

    name=para.name+'r'+str(run)
    gloInnovation=GlobalInnovation(ite.Lcountry,para.phi)

    enEx=enterExit(ite.Lcountry,ite.McountryFirmMaxNumber,
                   para.folder,para.name,run,para.delta,para.A,
                   ite.McountryBankMaxNumber,para.probBank,para.minReserve,
                   para.rDiscount,para.xi,para.dividendRate,para.iota,para.rDeposit,
                   para.upsilon,para.gamma,para.deltaInnovation,para.mu1,
                   para.propTradable,para.Fcost,para.ni,para.minMarkUp,
                   para.iotaE,para.theta,para.sigma,para.upsilon2,para.jobDuration,
                   nRegion=para.nRegion,
                   useRegionalBanks=para.useRegionalBanks,
                   regionalDividendRate=para.regionalDividendRate,
                   firmEntryMode=para.firmEntryMode,
                   entryTrace=para.entryTrace,
                   lockRelationshipReserves=para.lockRelationshipReserves,
                   reserveDevolution=para.reserveDevolution)

    maConsumption=MatchingConsumption(ite.Lcountry,para.bound,para.propTradable)
    maLaborCapital=MatchingLaborCapital(para.bound)
    aggrega=Aggregator(ite.Lcountry,name,para.folder,para.timeCollectingStart,
                       para.LtimeCollecting,para.printAgent)
    maCredit=MatchingCredit()
    maBonds=MatchingBonds()
    maDeposit=MatchingDepositRegional(ite.Lcountry,
                                     depositLocalBias=para.depositLocalBias,
                                     useRegionalBanks=para.useRegionalBanks)
    maDeposit._nRegion=para.nRegion   # needed by _consumerRegion()

    McountryFund=createFunds(ite.Lcountry,on=para.fundOn,
                             contribBase=para.fundContribBase,
                             countercyclical=para.fundCountercyclical,
                             recapKappa=para.recapKappa,
                             recapOn=para.fundRecapOn)

    aggrega.basicL(ite.McountryConsumer)
    centralBankUnion=CentralBankUnion(para.rDiscount,para.rDeposit,para.zeta,para.rBar,
                                      para.csi,para.csiDP,para.inflationTarget)
    maDeposit.creatingAccount(ite.McountryConsumer,ite.McountryFirm,
                              ite.McountryBank,ite.McountryCentralBank)
    poli=policy(para.startingPolicy,para.policyKind,para.maxPublicDeficitAusterity,
                para.maxPublicDeficit,para.upsilonConsumer,para.deltaLaborPolicy,
                ite.Lcountry,para.k,para.epsilon)

    # --- Fund log (per period, per country) ---
    _fundLog=open(para.folder+'/'+name+'FundData.csv','w')
    _fundLog.write('time,country,reserves,totalIn,totalOut,contribThisPeriod,'
                   'recapThisPeriod,nRecap,nRecapTotal,nRecapFailed,gammaEff,boom\n')

    # --- Soft-information log (phi vs leverage among credit-seekers) ---
    _softLog=open(para.folder+'/'+name+'SoftInfoData.csv','w')
    _softLog.write('time,country,'+','.join(SoftInfo.column_names())+'\n')

    # --- Main loop ---
    for t in range(para.ncycle):
        print()
        print('name ', para.name, '---- run', run, ' --- t ', t)

        maLaborCapital.bargaining(ite.McountryFirm,ite.McountryConsumer,
                                  aggrega.McountryUnemployement,aggrega.McountryPastUnemployement,
                                  aggrega.McountryYL,aggrega.McountryPastYL,t)

        for country in ite.McountryFirm:
            for firm in ite.McountryFirm[country]:
                ite.McountryFirm[country][firm].learning()
                ite.McountryFirm[country][firm].productionDesired(
                    ite.McountryBank,ite.McountryCentralBank,t,aggrega.McountryAvPrice)

        # Credit matching — regional banks active per-country per useRegionalBanks dict
        maCredit.creditNetworkEvolution(
            ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank,
            gloInnovation.DglobalPhiNotTradable,gloInnovation.DglobalPhiTradable,
            aggrega.avPhiGlobalTradable,
            psiCredit=para.psiCredit,
            aExpPhiRegional=para.aExpPhiRegional,
            useRegionalBanks=para.useRegionalBanks,
            sizeIndifference=para.sizeIndifference,
            wRegionalRank=para.wRegionalRank)

        # Build regionalCreditData dict for aggregator
        regionalCreditData={}
        for country in ite.Lcountry:
            regionalCreditData[country]=[
                maCredit.loanReceivedRegional.get(country,0),
                maCredit.loanReceivedGlobal.get(country,0),
                maCredit.loanDemandedRegional.get(country,0),
                maCredit.loanDemandedGlobal.get(country,0)]

        # Soft-information diagnostic: phi vs leverage among credit-seekers
        _si=SoftInfo.compute(getattr(maCredit,'MloanDemand',[]))
        _ncols=len(SoftInfo.column_names())
        for country in ite.Lcountry:
            vals=_si.get(country,[0]*_ncols)
            _softLog.write('%d,%s,'%(t,str(country))+','.join('%.6f'%v for v in vals)+'\n')
        _softLog.flush()

        for country in ite.McountryBank:
            for bank in ite.McountryBank[country]:
                ite.McountryBank[country][bank].reservingCompulsory(ite.McountryCentralBank)

        maLaborCapital.working(ite.McountryFirm,ite.McountryConsumer,ite.McountryEtat,
                               ite.McountryBank,ite.McountryCentralBank,
                               aggrega.McountryUnemployement)

        for country in ite.McountryFirm:
            for firm in ite.McountryFirm[country]:
                ite.McountryFirm[country][firm].effectiveSelling(
                    gloInnovation.DglobalPhiNotTradable,aggrega.avPhiGlobalTradable,
                    aggrega.avPriceGlobalTradable,aggrega.McountryAvPriceNotTradable,
                    gloInnovation.DglobalPhi,aggrega.McountryAvPrice)

        for country in ite.McountryConsumer:
            for consumer in ite.McountryConsumer[country]:
                ite.McountryConsumer[country][consumer].income(ite.McountryBank,ite.McountryCentralBank)

        for etat in ite.McountryEtat:
            ite.McountryEtat[etat].expectingTaxation(ite.McountryConsumer,ite.McountryCentralBank,
                                                      aggrega.McountryUnemployement)

        poli.implementingPolicy(t,ite.McountryEtat,aggrega.McountryYReal,gloInnovation.DglobalPhi,
                                aggrega.DcountryAvWage,aggrega.McountryAvPrice,
                                aggrega.McountryUnemployement,aggrega.DcumulativeDTBC,
                                aggrega.DcountryTradeBalance,ite.McountryConsumer,ite.McountryFirm,
                                enEx.DcountryUpsilon,enEx.DcountryJobDuration,
                                aggrega.McountryDebtY,aggrega.McountryCumCA,
                                aggrega.McountryY,ite.McountryBank,enEx.DcountryIotaRelPhi)

        # --- optional union risk-sharing transfer: recycle surplus-country trade surplus to deficit country ---
        ite._lastTransfer=0.0
        if _UNION_TRANSFER_ON and len(ite.McountryEtat)==2:
            _cs=list(ite.McountryEtat.keys())
            _cum={c:float(aggrega.McountryCumCA.get(c,0.0)) for c in _cs}  # persistent imbalance
            _tb={c:float(aggrega.DcountryTradeBalance.get(c,0.0)) for c in _cs}  # current flow
            _s=max(_cs,key=lambda c:_cum[c]); _d=min(_cs,key=lambda c:_cum[c])  # direction from CUMULATIVE CA
            _dYs=float(aggrega.McountryDebtY.get(_s,0.0))
            if os.environ.get('UNION_TRANSFER_DEBUG','0')=='1' and t%50==0:
                _cumt=getattr(ite,'_cumTransferNet',0.0); _grs=getattr(ite,'_cumTransferGross',0.0)
                print('TRDBG t=%d tb=%s cumCA=%s s=%s d=%s | cumGross=%.1f cumNet(c0->c1)=%.1f'%(
                    t,{k:round(v,1) for k,v in _tb.items()},{k:round(v,1) for k,v in _cum.items()},_s,_d,_grs,_cumt))
            # transfer ONLY in the persistent (cumulative) direction, sized by the current flow that agrees with it
            if _s!=_d and _cum[_s]>0.0 and _cum[_d]<0.0 and _dYs<_UNION_TRANSFER_SAFEDY:
                _T=_UNION_TRANSFER_RATE*min(max(0.0,_tb[_s]),max(0.0,-_tb[_d]))  # 0 when current flow disagrees with persistent direction
                _T=min(_T,max(0.0,ite.McountryEtat[_s].LiquidityEtat))  # never drive source liquidity negative (SFC-safe)
                if _T>0.0:
                    # symmetric reallocation: government liquidity + surplus + CB deposit (union totals preserved)
                    ite.McountryEtat[_d].LiquidityEtat+=_T
                    ite.McountryEtat[_d].surplusEtat+=_T
                    ite.McountryCentralBank[_d].DepositEtatCentralBank+=_T
                    ite.McountryEtat[_s].LiquidityEtat-=_T
                    ite.McountryEtat[_s].surplusEtat-=_T
                    ite.McountryCentralBank[_s].DepositEtatCentralBank-=_T
                    ite._lastTransfer=_T
                    ite._cumTransferGross=getattr(ite,'_cumTransferGross',0.0)+_T
                    ite._cumTransferNet=getattr(ite,'_cumTransferNet',0.0)+(_T if _d==1 else -_T)

        for etat in ite.McountryEtat:
            ite.McountryEtat[etat].governmentPlannedExpenditure(
                ite.McountryConsumer,ite.McountryBank,ite.McountryCentralBank,
                aggrega.McountryAvPrice,aggrega.McountryY,t,
                aggrega.DcountryAvWage,poli.policy,
                aggrega.DcountryTradeBalance,aggrega.McountryUnemployement,gloInnovation.DglobalPhi)

        maBonds.allocatingBonds(ite.McountryBank,ite.McountryCentralBank,ite.McountryEtat)

        for etat in ite.McountryEtat:
            ite.McountryEtat[etat].taxationConsumer(ite.McountryConsumer,ite.McountryBank,
                                                     ite.McountryCentralBank)

        for etat in ite.McountryEtat:
            ite.McountryEtat[etat].redistributionConsumer(ite.McountryConsumer,ite.McountryBank,
                                                           ite.McountryCentralBank,
                                                           aggrega.McountryAvPrice,t)

        for country in ite.McountryConsumer:
            for consumer in ite.McountryConsumer[country]:
                ite.McountryConsumer[country][consumer].consumptionDemand(
                    ite.McountryBank,ite.McountryCentralBank,aggrega.DcountryFailureProbability)

        maConsumption.consuming(ite.McountryConsumer,ite.McountryFirm,t,ite.McountryEtat,
                                ite.McountryBank,ite.McountryCentralBank,
                                aggrega.McountryAvPrice,aggrega.avPriceGlobalTradable,
                                aggrega.McountryAvPriceNotTradable)

        for country in ite.McountryFirm:
            for firm in ite.McountryFirm[country]:
                ite.McountryFirm[country][firm].changingInventory()

        if para.printAgent=='yes':
            for country in ite.McountryFirm:
                for firm in ite.McountryFirm[country]:
                    ite.McountryFirm[country][firm].write(t,run)
            for country in ite.McountryBank:
                for bank in ite.McountryBank[country]:
                    ite.McountryBank[country][bank].write(t,run)

        aggrega.income(ite.McountryConsumer,t,
                       run,ite.McountryFirm,ite.McountryEtat,ite.McountryBank,ite.McountryCentralBank,
                       gloInnovation.DglobalPhi,enEx.DcountryFirmEnter,enEx.DcountryFirmExit,
                       enEx.DcountryFirmEnterTradable,enEx.DcountryFirmExitTradable,
                       enEx.DcountryBankEnter,enEx.DcountryBankExit,gloInnovation.DglobalPhiTradable,
                       gloInnovation.DglobalPhiNotTradable,maCredit.creditCapitalInflow,
                       maCredit.creditCapitalOutflow,
                       maBonds.creditBondInflow,maBonds.creditBondOutflow,enEx.DcountryEnterValue,
                       regionalCreditData=regionalCreditData)

        gloInnovation.spillover(ite.McountryFirm,t)

        for country in ite.McountryFirm:
            for firm in ite.McountryFirm[country]:
                ite.McountryFirm[country][firm].existence(ite.McountryBank,ite.McountryCentralBank)

        for etat in ite.McountryEtat:
            ite.McountryEtat[etat].taxationFirm(ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank)

        for country in ite.McountryFirm:
            for firm in ite.McountryFirm[country]:
                ite.McountryFirm[country][firm].distributingDividends(
                    ite.McountryConsumer,ite.McountryBank,ite.McountryCentralBank)

        enEx.exitFirm(ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank)

        for country in ite.McountryBank:
            for bank in ite.McountryBank[country]:
                ite.McountryBank[country][bank].existence(
                    ite.McountryConsumer,ite.McountryFirm,ite.McountryCentralBank,
                    ite.McountryEtat[country].rBonds,ite.McountryEtat,aggrega.DcountryAvWage,
                    fund=McountryFund[country])

        for etat in ite.McountryEtat:
            ite.McountryEtat[etat].taxationBank(ite.McountryBank,ite.McountryCentralBank)

        for country in McountryFund:
            McountryFund[country].updatePolicy(ite.McountryBank)

        for country in ite.McountryBank:
            for bank in ite.McountryBank[country]:
                ite.McountryBank[country][bank].distributingDividends(
                    ite.McountryConsumer,ite.McountryBank,ite.McountryCentralBank,
                    fund=McountryFund[country],gammaEff=McountryFund[country].gammaEff)

        for country in McountryFund:
            McountryFund[country].checkIdentity()

        for country in McountryFund:
            f=McountryFund[country]
            _fundLog.write('%d,%s,%.6f,%.6f,%.6f,%.6f,%.6f,%d,%d,%d,%.6f,%.6f\n'%(
                t,str(country),f.Reserves,f.totalIn,f.totalOut,f.contribThisPeriod,
                f.recapThisPeriod,f.nRecap,f.nRecapTotal,f.nRecapFailed,f.gammaEff,f.lastBoom))
            _fundLog.flush()

        enEx.exitBank(ite.McountryConsumer,ite.McountryFirm,ite.McountryBank,
                      ite.McountryCentralBank,ite.McountryEtat)

        enEx.enter(ite.McountryConsumer,ite.McountryFirm,t,ite.McountryBank,
                   ite.McountryCentralBank,aggrega.McountryAvPrice,ite.McountryEtat)

        for country in ite.McountryConsumer:
            for consumer in ite.McountryConsumer[country]:
                ite.McountryConsumer[country][consumer].ownershipCheck(ite.McountryBank)

        maDeposit.creatingAccount(ite.McountryConsumer,ite.McountryFirm,
                                  ite.McountryBank,ite.McountryCentralBank)
        maDeposit.updateRegionalBankMap(ite.McountryBank)
        maDeposit.allocatingConsumerDeposit(ite.McountryConsumer,ite.McountryBank)

        for country in ite.McountryCentralBank:
            ite.McountryCentralBank[country].balancing(
                ite.McountryConsumer,ite.McountryFirm,ite.McountryEtat,
                centralBankUnion,aggrega.DTBC)

        aggrega.checkCA(ite.McountryConsumer,t,run,ite.McountryFirm,ite.McountryEtat,
                        ite.McountryBank,ite.McountryCentralBank,
                        maCredit.creditCapitalInflow,maCredit.creditCapitalOutflow,
                        maBonds.creditBondInflow,maBonds.creditBondOutflow,
                        enEx.DcountryFirmGone,enEx.DcountryBankGone,
                        enEx.DcountryForeignBankLosses,t)

        aggrega.checkNetWorth(ite.McountryConsumer,ite.McountryFirm,ite.McountryBank,
                              ite.McountryCentralBank,ite.McountryEtat,enEx.DpastBondExit,
                              McountryFund=McountryFund)

        centralBankUnion.taylorRule1(aggrega.McountryInflation,aggrega.McountryUnemployement,
                                     ite.McountryBank,ite.McountryCentralBank,t,
                                     ite.McountryConsumer,ite.McountryFirm)

        ite.debtExplotionBreak(aggrega.McountryY,t)
        if ite.breaking=='yes':
            break

print()
print('the end')
