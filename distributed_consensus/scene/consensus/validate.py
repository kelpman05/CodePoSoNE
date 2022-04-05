import xlrd
import xlwt
import numpy as np
from gams import *
import sys
import subprocess
import os


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ws = GamsWorkspace(system_directory = sys.argv[1])
    else:
        ws = GamsWorkspace()
    T=24
    CHPnum = 2
    CHPHP = 1.5
    CHPPeff = 0.277
    GasHV = 10.833
    GasBoeff = 0.792
    Cp = 4.2
    TCHPout = 85
    Toutside = 15
    MassFlowC = 20

    data = xlrd.open_workbook('C:/Users/miller/Desktop/ptry/IES_data.xls')
    EBus = data.sheet_by_name('EBus')
    EBranch = data.sheet_by_name('EBranch')
    HBus = data.sheet_by_name('HBus')
    HBranch = data.sheet_by_name('HBranch')
    GBus = data.sheet_by_name('GBus')
    GBranch = data.sheet_by_name('GBranch')
    CHPMax=[1000,1000]
    K_g=np.zeros(GBranch.nrows)
    for i in range(1,GBranch.nrows):
        K_g[i] = 11.7*GBranch[i,3].value/np.power(GBranch[i,4].value*1000,5)
    EloadCurve=np.zeros(T)
    for i in range(T):
        EloadCurve[i]=0.76+i/100
    HloadCurve=np.zeros(T)
    for i in range(T):
        HloadCurve[i]=0.76+i/100
    GloadCurve=np.zeros(T)
    for i in range(T):
        GloadCurve[i]=0.76+i/100

    db = ws.add_database_from_gdx("C:/Users/miller/Desktop/ptry/Optimization_data.gdx")
    CHP = { tuple((int(rec.key(0)),int(rec.key(1)),rec.key(2))):rec.value for rec in db["CHP"] }
    mainGridP = { int(rec.key(0)):rec.value for rec in db["mainGridP"] }
    mainGridQ = { int(rec.key(0)):rec.value for rec in db["mainGridQ"] }
    Pij = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["Pij"] }
    Qij = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["Qij"] }
    Iij = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["Iij"] }
    Vi = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["Vi"] }
    
    GasBo = { tuple((int(rec.key(0)),int(rec.key(1)),rec.key(2))):rec.value for rec in db["GasBo"] }
    MassFlowL = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["MassFlowL"] }
    MassFlowS = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["MassFlowS"] }
    MassFlowR = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["MassFlowR"] }
    MassFlowCHP = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["MassFlowCHP"] }
    TempBusS = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["TempBusS"] }
    TempBranEndS = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["TempBranEndS"] }
    TempBusR = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["TempBusR"] }
    TempBranEndR = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["TempBranEndR"] }
    TempLoadout = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["TempLoadout"] }

    GasFlow = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GasFlow"] }
    GasSource = { int(rec.key(0)):rec.value for rec in db["GasSource"] }
    GasPressure = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GasPressure"] }    

    db = ws.add_database_from_gdx("C:/Users/miller/Desktop/ptry/dual_data.gdx")
    #electric restrictions
    ENodePeq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["ENodePeq"] }
    ENodeQeq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["ENodeQeq"] }
    EBranchPeq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["EBranchPeq"] }
    EBranchPpositive = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["EBranchPpositive"] }
    EBranchQpositive = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["EBranchQpositive"] }
    SOCPeq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["SOCPeq"] }
    CHPOutputLimit = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["CHPOutputLimit"] }

    #Heat restrictions
    HNodeLoadeq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["HNodeLoadeq"] }
    HNodeCHPeq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["HNodeCHPeq"] }
    HBranchTempLossS = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["HBranchTempLossS"] }
    HBranchTempLossR = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["HBranchTempLossR"] }
    HNodeMixLoadS = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["HNodeMixLoadS"] }
    HNodeMixLoadR = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["HNodeMixLoadR"] }
    HNodeMixCHPS = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["HNodeMixCHPS"] }
    HNodeMixCHPR = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["HNodeMixCHPR"] }
    HnLoadTempLoadout = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["HnLoadTempLoadout"] }

    #Gas restrictions
    GNodeLoadeq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GNodeLoadeq"] }
    GNodeCHPeq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GNodeCHPeq"] }
    GSlackBuseq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GSlackBuseq"] }
    GWeymoutheq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GWeymoutheq"] }
    GSlackBusPressure = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GSlackBusPressure"] }

    #CHP restrictions
    CHPEfficiencyeq1 = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["CHPEfficiencyeq1"] }
    CHPEfficiencyeq2 = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["CHPEfficiencyeq2"] }
    GasBoEfficiencyeq1 = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GasBoEfficiencyeq1"] }
    GasBoEfficiencyeq2 = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GasBoEfficiencyeq2"] }


    #deltaL/CHP(P)
    LagrangeMatrix_CHP_P = np.zeros((T,CHPnum))
    for i in range(1,T+1):
        LagrangeMatrix_CHP_P[i-1,0] = ENodePeq[i,13] - 2*CHP[i,1,'P']*CHPOutputLimit[i,1] + CHPEfficiencyeq1[i,1] + CHPEfficiencyeq2[i,1]*CHPHP 
        LagrangeMatrix_CHP_P[i-1,1] = ENodePeq[i,14] - 2*CHP[i,2,'P']*CHPOutputLimit[i,2] + CHPEfficiencyeq1[i,2] + CHPEfficiencyeq2[i,2]*CHPHP 

    #deltaL/CHP(Q)
    LagrangeMatrix_CHP_Q = np.zeros((T,CHPnum))
    for i in range(1,T+1):
        LagrangeMatrix_CHP_Q[i-1,0] = ENodeQeq[i,13] - 2*CHP[i,1,'Q']*CHPOutputLimit[i,1] 
        LagrangeMatrix_CHP_Q[i-1,1] = ENodeQeq[i,14] - 2*CHP[i,2,'Q']*CHPOutputLimit[i,2] 

    #deltaL/CHP(H)
    LagrangeMatrix_CHP_H = np.zeros((T,CHPnum))
    for i in range(1,T+1):
        LagrangeMatrix_CHP_H[i-1,0] = HNodeCHPeq[i,35] - CHPEfficiencyeq2[i,1] 
        LagrangeMatrix_CHP_H[i-1,1] = HNodeCHPeq[i,36] - CHPEfficiencyeq2[i,2]

    #deltaL/CHP(G)
    LagrangeMatrix_CHP_G = np.zeros((T,CHPnum))
    for i in range(1,T+1):
        LagrangeMatrix_CHP_G[i-1,0] = -GNodeCHPeq[i,1] - CHPEfficiencyeq1[i,1]*CHPPeff*GasHV 
        LagrangeMatrix_CHP_G[i-1,1] = -GNodeCHPeq[i,15] - CHPEfficiencyeq1[i,2]*CHPPeff*GasHV

    #deltaL/mainGridP
    LagrangeMatrix_mainGridP = np.zeros(T)
    for i in range(1,T+1):
        LagrangeMatrix_mainGridP[i-1] = 1 - ENodePeq[i,15]

    #deltaL/mainGridQ
    LagrangeMatrix_mainGridQ = np.zeros(T)
    for i in range(1,T+1):
        LagrangeMatrix_mainGridQ[i-1] = ENodeQeq[i,15]

    #deltaL/deltaPij
    LagrangeMatrix_Pij = np.zeros((T,EBranch.nrows-1))
    for i in range(1,T+1):
        for j in range(1,EBranch.nrows):
            mhn1=int(EBranch[j,1].value)
            mhn2=int(EBranch[j,2].value)
            LagrangeMatrix_Pij[i-1,j-1]=ENodePeq[i,mhn1] - ENodePeq[i,mhn2]
            LagrangeMatrix_Pij[i-1,j-1]=LagrangeMatrix_Pij[i-1,j-1] - 2/1000*EBranch[j,3].value*EBranchPeq[i,j]
            LagrangeMatrix_Pij[i-1,j-1]=LagrangeMatrix_Pij[i-1,j-1] - EBranchPpositive[i,j]
            LagrangeMatrix_Pij[i-1,j-1]=LagrangeMatrix_Pij[i-1,j-1] + 8*Pij[i,j]*SOCPeq[i,j]
    
    #deltaL/deltaQij
    LagrangeMatrix_Qij = np.zeros((T,EBranch.nrows-1))
    for i in range(1,T+1):
        for j in range(1,EBranch.nrows):
            mhn1=int(EBranch[j,1].value)
            mhn2=int(EBranch[j,2].value)
            LagrangeMatrix_Qij[i-1,j-1]=ENodeQeq[i,mhn1] - ENodeQeq[i,mhn2]
            LagrangeMatrix_Qij[i-1,j-1]=LagrangeMatrix_Qij[i-1,j-1] - 2/1000*EBranch[j,4].value*EBranchPeq[i,j]
            LagrangeMatrix_Qij[i-1,j-1]=LagrangeMatrix_Qij[i-1,j-1] - EBranchQpositive[i,j]
            LagrangeMatrix_Qij[i-1,j-1]=LagrangeMatrix_Qij[i-1,j-1] + 8*Qij[i,j]*SOCPeq[i,j]
    
    #deltaL/deltaVi
    LagrangeMatrix_Vi = np.zeros((T,EBus.nrows-1))
    for i in range(1,T+1):
        for j in range(1,EBus.nrows):
            for k in range(1,EBranch.nrows):
                if int(EBranch[k,1].value) == j:
                    LagrangeMatrix_Vi[i-1,j-1]=LagrangeMatrix_Vi[i-1,j-1] + EBranchPeq[i,k]
                    LagrangeMatrix_Vi[i-1,j-1]=LagrangeMatrix_Vi[i-1,j-1] - 4*Iij[i,k]*SOCPeq[i,k]
                if int(EBranch[k,2].value) == j:
                    LagrangeMatrix_Vi[i-1,j-1]=LagrangeMatrix_Vi[i-1,j-1] - EBranchPeq[i,k]
    
    #deltaL/deltaIij
    LagrangeMatrix_Iij = np.zeros((T,EBranch.nrows-1))
    for i in range(1,T+1):
        for j in range(1,EBranch.nrows):
            LagrangeMatrix_Iij[i-1,j-1]=-ENodePeq[i,j]*EBranch[j,3].value/1000
            LagrangeMatrix_Iij[i-1,j-1]=LagrangeMatrix_Iij[i-1,j-1] - ENodeQeq[i,j]*EBranch[j,4].value/1000
            LagrangeMatrix_Iij[i-1,j-1]=LagrangeMatrix_Iij[i-1,j-1] + EBranch[j,5].value*EBranchPeq[i,j]/1000/1000
            LagrangeMatrix_Iij[i-1,j-1]=LagrangeMatrix_Iij[i-1,j-1] + EBranchPpositive[i,j]*EBranch[j,3].value/1000
            LagrangeMatrix_Iij[i-1,j-1]=LagrangeMatrix_Iij[i-1,j-1] + EBranchQpositive[i,j]*EBranch[j,4].value/1000
            LagrangeMatrix_Iij[i-1,j-1]=LagrangeMatrix_Iij[i-1,j-1] - 4*Vi[i,int(EBranch[j,1].value)]*SOCPeq[i,j]
    
    #deltaL/deltaGasBo(H)
    LagrangeMatrix_GasBo_H = np.zeros((T,CHPnum))
    for i in range(1,T+1):
        LagrangeMatrix_GasBo_H[i-1,0] = HNodeCHPeq[i,35] - GasBoEfficiencyeq1[i,1] - GasBoEfficiencyeq2[i,1]
        LagrangeMatrix_GasBo_H[i-1,1] = HNodeCHPeq[i,36] - GasBoEfficiencyeq1[i,2] - GasBoEfficiencyeq2[i,2]
    
    #deltaL/deltaGasBo(G)
    LagrangeMatrix_GasBo_G = np.zeros((T,CHPnum))
    for i in range(1,T+1):
        LagrangeMatrix_GasBo_G[i-1,0] = -GNodeCHPeq[i,1] + GasBoEfficiencyeq1[i,1]*GasHV*GasBoeff
        LagrangeMatrix_GasBo_G[i-1,1] = -GNodeCHPeq[i,15] + GasBoEfficiencyeq1[i,2]*GasHV*GasBoeff
    
    #deltaL/deltaTempBusS
    LagrangeMatrix_TempBusS = np.zeros((T,HBus.nrows-1))
    for i in range(1,T+1):
        for j in range(1,HBus.nrows):
            if HBus[j,2].value != 0:
                LagrangeMatrix_TempBusS[i-1,j-1] = Cp*MassFlowL[i,j]*HNodeLoadeq[i,j]
            for k in range(1,HBranch.nrows):
                if HBranch[k,1].value == j:
                    LagrangeMatrix_TempBusS[i-1,j-1] = LagrangeMatrix_TempBusS[i-1,j-1] + HBranchTempLossS[i,k]*np.exp(-HBranch[k,6].value*HBranch[k,3].value/Cp/1000/MassFlowS[i,k])
            if HBus[j,1].value <= 0:
                LagrangeMatrix_TempBusS[i-1,j-1] = LagrangeMatrix_TempBusS[i-1,j-1] + HNodeMixLoadS[i,j]*(MassFlowL[i,j]+sum(MassFlowS[i,k] for k in range(1,HBranch.nrows) if (HBranch[k,1].value == j)))
            if HBus[j,1].value >= 1:
                LagrangeMatrix_TempBusS[i-1,j-1] = LagrangeMatrix_TempBusS[i-1,j-1] - HNodeMixCHPS[i,j]
    
    #deltaL/deltaTempBranEndS
    LagrangeMatrix_TempBranEndS = np.zeros((T,HBranch.nrows-1))
    for i in range(1,T+1):
        for j in range(1,HBranch.nrows):
            LagrangeMatrix_TempBranEndS[i-1,j-1] = - HBranchTempLossS[i,j]
            for k in range(1,35):
                if HBranch[j,2].value ==k:
                    LagrangeMatrix_TempBranEndS[i-1,j-1] = LagrangeMatrix_TempBranEndS[i-1,j-1] - HNodeMixLoadS[i,k]*MassFlowS[i,j] 
    
    #deltaL/deltaTempBusR
    LagrangeMatrix_TempBusR = np.zeros((T,HBus.nrows-1))
    for i in range(1,T+1):
        for j in range(1,HBus.nrows):
            if HBus[j,1].value >= 1:
                LagrangeMatrix_TempBusR[i-1,j-1] = Cp*MassFlowCHP[i,j-34]*HNodeCHPeq[i,j]
            for k in range(1,HBranch.nrows):
                if HBranch[k,2].value == j:
                    LagrangeMatrix_TempBusR[i-1,j-1] = LagrangeMatrix_TempBusR[i-1,j-1] + HBranchTempLossR[i,k]*np.exp(-HBranch[k,6].value*HBranch[k,3].value/Cp/1000/MassFlowR[i,k])
            if HBus[j,1].value <= 0:
                LagrangeMatrix_TempBusR[i-1,j-1] = LagrangeMatrix_TempBusR[i-1,j-1] + HNodeMixLoadR[i,j]*(sum(MassFlowR[i,k] for k in range(1,HBranch.nrows) if (HBranch[k,2].value == j)))
            if HBus[j,1].value >= 1:
                LagrangeMatrix_TempBusR[i-1,j-1] = LagrangeMatrix_TempBusR[i-1,j-1] + MassFlowCHP[i,j-34]*HNodeMixCHPR[i,j]

    #deltaL/deltaTempBranEndR
    LagrangeMatrix_TempBranEndR = np.zeros((T,HBranch.nrows-1))
    for i in range(1,T+1):
        for j in range(1,HBranch.nrows):
            LagrangeMatrix_TempBranEndR[i-1,j-1] = - HBranchTempLossR[i,j]
            for k in range(1,35):
                if HBranch[j,1].value ==k:
                    LagrangeMatrix_TempBranEndR[i-1,j-1] = LagrangeMatrix_TempBranEndR[i-1,j-1] - HNodeMixLoadR[i,k]*MassFlowR[i,j]
            for k in range(35,37):
                if HBranch[j,1].value ==k:
                    LagrangeMatrix_TempBranEndR[i-1,j-1] = LagrangeMatrix_TempBranEndR[i-1,j-1] + HNodeMixCHPR[i,k]*MassFlowR[i,j]

    #deltaL/deltaTempLoadout              
    LagrangeMatrix_TempLoadout = np.zeros((T,HBus.nrows-1))
    for i in range(1,T+1):
        for j in range(1,HBus.nrows):
            if HBus[j,2].value != 0:
                LagrangeMatrix_TempLoadout[i-1,j-1] = - Cp*MassFlowL[i,j]*HNodeLoadeq[i,j]
            if HBus[j,1].value <= 0:
                LagrangeMatrix_TempLoadout[i-1,j-1] = LagrangeMatrix_TempLoadout[i-1,j-1] - MassFlowL[i,j]*HNodeMixLoadR[i,j]
            if HBus[j,1].value >= 1:
                LagrangeMatrix_TempLoadout[i-1,j-1] = LagrangeMatrix_TempLoadout[i-1,j-1] + MassFlowL[i,j]*HNodeMixCHPR[i,j]
            if HBus[j,2] ==0:
                LagrangeMatrix_TempLoadout[i-1,j-1] = LagrangeMatrix_TempLoadout[i-1,j-1] + HnLoadTempLoadout[i,j]
    
    #deltaL/deltaGasFlow
    LagrangeMatrix_GasFlow = np.zeros((T,GBranch.nrows-1))
    for i in range(1,T+1):
        for j in range(1,GBranch.nrows):
            mhn1=int(GBranch[j,1].value)
            mhn2=int(GBranch[j,2].value)
            for k in range(1,GBus.nrows):
                if mhn1 == k:
                    if GBus[k,1].value == 0:
                        LagrangeMatrix_GasFlow[i-1,j-1] = LagrangeMatrix_GasFlow[i-1,j-1] + GNodeLoadeq[i,mhn1]
                    if GBus[k,1].value >= 1:
                        LagrangeMatrix_GasFlow[i-1,j-1] = LagrangeMatrix_GasFlow[i-1,j-1] + GNodeCHPeq[i,mhn1]
                    if GBus[k,1].value == -1:
                        LagrangeMatrix_GasFlow[i-1,j-1] = LagrangeMatrix_GasFlow[i-1,j-1] + GSlackBuseq[i,mhn1]
                if mhn2 == k:
                    if GBus[k,1].value == 0:
                        LagrangeMatrix_GasFlow[i-1,j-1] = LagrangeMatrix_GasFlow[i-1,j-1] - GNodeLoadeq[i,mhn2]
                    if GBus[k,1].value >= 1:
                        LagrangeMatrix_GasFlow[i-1,j-1] = LagrangeMatrix_GasFlow[i-1,j-1] - GNodeCHPeq[i,mhn2]
                    if GBus[k,1].value == -1:
                        LagrangeMatrix_GasFlow[i-1,j-1] = LagrangeMatrix_GasFlow[i-1,j-1] - GSlackBuseq[i,mhn2]
            LagrangeMatrix_GasFlow[i-1,j-1] = LagrangeMatrix_GasFlow[i-1,j-1] - 2*K_g[j]*GasFlow[i,j]*GWeymoutheq[i,j]
    
    #deltaL/deltaGasSource
    LagrangeMatrix_GasSource = np.zeros(T)
    for i in range(1,T+1):
        LagrangeMatrix_GasSource[i-1] = 1 - GSlackBuseq[i,37]
    
    #deltaL/deltaGasPressure
    LagrangeMatrix_GasPressure = np.zeros((T,GBus.nrows-1))
    for i in range(1,T+1):
        for j in range(1,GBus.nrows):
            for k in range(1,GBranch.nrows):
                mhn1=int(GBranch[k,1].value)
                mhn2=int(GBranch[k,2].value)
                if mhn1 == j:
                    LagrangeMatrix_GasPressure[i-1,j-1] = LagrangeMatrix_GasPressure[i-1,j-1] + GWeymoutheq[i,k]
                if mhn2 == j:
                    LagrangeMatrix_GasPressure[i-1,j-1] = LagrangeMatrix_GasPressure[i-1,j-1] - GWeymoutheq[i,k]   
            if GBus[j,1].value == -1:
                LagrangeMatrix_GasPressure[i-1,j-1] = LagrangeMatrix_GasPressure[i-1,j-1] + GSlackBusPressure[i,37]    

    #h=0  g*miu=0
    #electric validate
    Flag_E1 = np.zeros((T,EBus.nrows-1))
    Flag_E2 = np.zeros((T,EBus.nrows-1))
    Flag_E3 = np.zeros((T,EBranch.nrows-1))
    Flag_E4 = np.zeros((T,EBranch.nrows-1))
    Flag_E5 = np.zeros((T,EBranch.nrows-1))
    Flag_E6 = np.zeros((T,EBranch.nrows-1))
    Flag_E7 = np.zeros((T,CHPnum))
    Flag_E8 = np.zeros(T)
    for i in range(1,T+1):
        for j in range(1,EBus.nrows):
            if EBus[j,1].value == 0:   #ENodePLoadeq
                Flag_E1[i-1,j-1] = Flag_E1[i-1,j-1] - EBus[j,2].value*EloadCurve[i-1]
            if EBus[j,1].value >= 1: #ENodePCHPeq
                Flag_E1[i-1,j-1] = Flag_E1[i-1,j-1] + CHP[i,int(EBus[j,1].value),'P'] - EBus[j,2].value*EloadCurve[i-1]
            if EBus[j,1].value == -1: #ENodePSlaeq
                Flag_E1[i-1,j-1] = Flag_E1[i-1,j-1] + mainGridP[i] - EBus[j,2].value*EloadCurve[i-1]
            for k in range(1,EBranch.nrows):
                mhn1 = int(EBranch[k,1].value)
                mhn2 = int(EBranch[k,2].value)
                if mhn2 == j:
                    Flag_E1[i-1,j-1] = Flag_E1[i-1,j-1] + (Pij[i,k]-EBranch[k,3].value*Iij[i,k]/1000)
                if mhn1 ==j:
                    Flag_E1[i-1,j-1] = Flag_E1[i-1,j-1] - Pij[i,k]

            if EBus[j,1].value == 0:   #ENodeQLoadeq
                Flag_E2[i-1,j-1] = Flag_E2[i-1,j-1] - EBus[j,3].value*EloadCurve[i-1]
            if EBus[j,1].value >= 1: #ENodeQCHPeq
                Flag_E2[i-1,j-1] = Flag_E2[i-1,j-1] + CHP[i,int(EBus[j,1].value),'Q'] - EBus[j,3].value*EloadCurve[i-1]
            if EBus[j,1].value == -1: #ENodeQSlaeq
                Flag_E2[i-1,j-1] = Flag_E2[i-1,j-1] + mainGridQ[i] - EBus[j,3].value*EloadCurve[i-1]
            for k in range(1,EBranch.nrows):
                mhn1 = int(EBranch[k,1].value)
                mhn2 = int(EBranch[k,2].value)
                if mhn2 == j:
                    Flag_E2[i-1,j-1] = Flag_E2[i-1,j-1] + (Qij[i,k]-EBranch[k,4].value*Iij[i,k]/1000)
                if mhn1 ==j:
                    Flag_E2[i-1,j-1] = Flag_E2[i-1,j-1] - Qij[i,k]

    for i in range(1,T+1):
        for j in range(1,EBranch.nrows):
            #EBranchPeq  
            Flag_E3[i-1,j-1] = Flag_E3[i-1,j-1] + Vi[i,int(EBranch[j,1].value)] - Vi[i,int(EBranch[j,2].value)] - 2/1000*(Pij[i,j]*EBranch[j,3].value + Qij[i,j]*EBranch[j,4].value) + EBranch[j,5].value*Iij[i,j]/1000/1000
            #EBranchPpositive  
            Flag_E4[i-1,j-1] = Flag_E4[i-1,j-1] + (Pij[i,j] - Iij[i,j]*EBranch[j,3].value/1000)*EBranchPpositive[i,j]  
            #EBranchQpositive  
            Flag_E5[i-1,j-1] = Flag_E5[i-1,j-1] + (Qij[i,j] - Iij[i,j]*EBranch[j,4].value/1000)*EBranchQpositive[i,j] 
            #SOCPeq      
            Flag_E6[i-1,j-1] = Flag_E6[i-1,j-1] + SOCPeq[i,j]*(np.power(Pij[i,j],2) + np.power(Qij[i,j],2) - Vi[i,int(EBranch[j,1].value)]*Iij[i,j])
    #CHPOutputLimit
    for i in range(1,T+1):
        for j in range(1,CHPnum+1):
            Flag_E7[i-1,j-1] = Flag_E7[i-1,j-1] + (np.power(CHP[i,j,'P'],2)+np.power(CHP[i,j,'Q'],2) - np.power(CHPMax[j-1],2))*CHPOutputLimit[i,j]
    #SlackBusVoltage
    for i in range(1,T+1):
        Flag_E8[i-1] = Vi[i,15] - np.power(6.6,2)
    
    #heat validate
    Flag_H1 = np.zeros((T,HBus.nrows-1))
    Flag_H2 = np.zeros((T,HBus.nrows-1))
    Flag_H3 = np.zeros((T,HBus.nrows-1))
    Flag_H4 = np.zeros((T,HBus.nrows-1))
    Flag_H5 = np.zeros((T,HBranch.nrows-1))
    Flag_H6 = np.zeros((T,HBranch.nrows-1))
    Flag_H7 = np.zeros((T,HBus.nrows-1))
    Flag_H8 = np.zeros((T,HBus.nrows-1))
    Flag_H9 = np.zeros((T,HBus.nrows-1))
    Flag_H10 = np.zeros((T,HBus.nrows-1))
    #HNodeLoadeq
    for i in range(1,T+1):
        for j in range(1,HBus.nrows):
            if HBus[j,2].value != 0:
                Flag_H1[i-1,j-1] = Flag_H1[i-1,j-1] + HBus[j,2].value*HloadCurve[i-1] - Cp*MassFlowL[i,j]*(TempBusS[i,j]-TempLoadout[i,j])
            
    for i in range(1,T+1):
        for j in range(1,HBus.nrows):
            if HBus[j,1].value >= 1:
                #HNodeCHPeq
                Flag_H2[i-1,j-1] = Flag_H2[i-1,j-1] + CHP[i,int(HBus[j,1].value),'H'] + GasBo[i,int(HBus[j,1].value),'H'] - Cp*MassFlowCHP[i,int(HBus[j,1].value)]*(TCHPout-TempBusR[i,j])
                #HKCLCHPS
                Flag_H3[i-1,j-1] = MassFlowCHP[i,int(HBus[j,1].value)] - MassFlowL[i,j]
                #HKCLCHPR
                Flag_H4[i-1,j-1] = MassFlowL[i,j] - MassFlowCHP[i,int(HBus[j,1].value)]
                for k in range(1,HBranch.nrows):
                    mhn1 = int(HBranch[k,1].value)
                    mhn2 = int(HBranch[k,2].value)
                    if mhn2 == j:
                        Flag_H3[i-1,j-1] = Flag_H3[i-1,j-1] + MassFlowS[i,k]
                        Flag_H4[i-1,j-1] = Flag_H4[i-1,j-1] - MassFlowR[i,k]  
                    if mhn1 == j:
                        Flag_H3[i-1,j-1] = Flag_H3[i-1,j-1] - MassFlowS[i,k]
                        Flag_H4[i-1,j-1] = Flag_H4[i-1,j-1] + MassFlowR[i,k]
            if HBus[j,1].value <= 0:
                #HKCLLoadS
                Flag_H3[i-1,j-1] = -MassFlowL[i,j] 
                #HKCLLoadR
                Flag_H4[i-1,j-1] = MassFlowL[i,j] 
                for k in range(1,HBranch.nrows):
                    mhn1 = int(HBranch[k,1].value)
                    mhn2 = int(HBranch[k,2].value)
                    if mhn2 == j:
                        Flag_H3[i-1,j-1] = Flag_H3[i-1,j-1] + MassFlowS[i,k]
                        Flag_H4[i-1,j-1] = Flag_H4[i-1,j-1] - MassFlowR[i,k]
                    if mhn1 == j:
                        Flag_H3[i-1,j-1] = Flag_H3[i-1,j-1] - MassFlowS[i,k]
                        Flag_H4[i-1,j-1] = Flag_H4[i-1,j-1] + MassFlowR[i,k]                     
    for i in range(1,T+1):
        for j in range(1,HBranch.nrows):
            #HBranchTempLossS
            Flag_H5[i-1,j-1] = TempBranEndS[i,j] - Toutside - (TempBusS[i,int(HBranch[j,1].value)] - Toutside)*np.exp(-HBranch[j,6].value*HBranch[j,3].value/Cp/1000/MassFlowS[i,j])
            #HBranchTempLossR
            Flag_H6[i-1,j-1] = TempBranEndR[i,j] - Toutside - (TempBusR[i,int(HBranch[j,2].value)] - Toutside)*np.exp(-HBranch[j,6].value*HBranch[j,3].value/Cp/1000/MassFlowR[i,j])

    for i in range(1,T+1):
        for j in range(1,HBus.nrows):
            if HBus[j,1].value >= 1:
                #HNodeMixCHPS
                Flag_H7[i-1,j-1] = TempBusS[i,j] - TCHPout
                #HNodeMixCHPR
                Flag_H8[i-1,j-1] = TempBusR[i,j]*MassFlowCHP[i,int(HBus[j,1].value)] - MassFlowL[i,j]*TempLoadout[i,j]
                for k in range(1,HBranch.nrows):
                    mhn1 = int(HBranch[k,1].value)
                    if mhn1 == j:
                        Flag_H8[i-1,j-1] = Flag_H8[i-1,j-1] - MassFlowR[i,k]*TempBranEndR[i,k]

            if HBus[j,1].value <= 0:
                #HNodeMixLoadS
                Flag_H7[i-1,j-1] = -TempBusS[i,j]*MassFlowL[i,j]
                #HNodeMixLoadR
                Flag_H8[i-1,j-1] = MassFlowL[i,j]*TempLoadout[i,j]
                for k in range(1,HBranch.nrows):
                    mhn1 = int(HBranch[k,1].value)
                    mhn2 = int(HBranch[k,2].value)
                    if mhn2 ==j:
                        Flag_H7[i-1,j-1] = Flag_H7[i-1,j-1] + MassFlowS[i,k]*TempBranEndS[i,k]
                        Flag_H8[i-1,j-1] = Flag_H8[i-1,j-1] - MassFlowR[i,k]*TempBusR[i,j]
                    if mhn1 ==j:
                        Flag_H7[i-1,j-1] = Flag_H7[i-1,j-1] - MassFlowS[i,k]*TempBusS[i,j]
                        Flag_H8[i-1,j-1] = Flag_H8[i-1,j-1] + MassFlowR[i,k]*TempBranEndR[i,k]

    for i in range(1,T+1):
        for j in range(1,HBus.nrows):
            #HLoadMassFlowFix
            if HBus[j,2].value != 0:
                Flag_H9[i-1,j-1] = MassFlowL[i,j] - MassFlowC
            #HnLoadMassFlowFix
            if HBus[j,2].value == 0:
                Flag_H9[i-1,j-1] = MassFlowL[i,j]

    for i in range(1,T+1):
        for j in range(1,HBus.nrows):
            if HBus[j,2].value == 0:
                Flag_H10[i-1,j-1] = TempLoadout[i,j]

    #heat validate
    Flag_G1 = np.zeros((T,GBus.nrows-1))
    Flag_G2 = np.zeros((T,GBranch.nrows-1))
    Flag_G3 = np.zeros((T,GBus.nrows-1))
    for i in range(1,T+1):
        for j in range(1,GBus.nrows):
            #GNodeLoadeq
            if GBus[j,1].value == 0:
                Flag_G1[i-1,j-1] = -GBus[j,2].value/GasHV*GloadCurve[i-1]
            #GNodeCHPeq
            if GBus[j,1].value >= 1:
                Flag_G1[i-1,j-1] = -CHP[i,int(GBus[j,1].value),'G'] - GasBo[i,int(GBus[j,1].value),'G']
            #GSlackBuseq
            if GBus[j,1].value == -1:
                Flag_G1[i-1,j-1] = GasSource[i] - GBus[j,2].value/GasHV*GloadCurve[i-1]
            for k in range(1,GBranch.nrows):
                mhn1 = int(GBranch[k,1].value)
                mhn2 = int(GBranch[k,2].value)
                if mhn2 == j:
                    Flag_G1[i-1,j-1] = Flag_G1[i-1,j-1] + GasFlow[i,k]
                if mhn1 == j:
                    Flag_G1[i-1,j-1] = Flag_G1[i-1,j-1] - GasFlow[i,k]
    #GWeymoutheq
    for i in range(1,T+1):
        for j in range(1,GBranch.nrows):
            Flag_G2[i-1,j-1] = GasPressure[i,int(GBranch[j,1].value)] - GasPressure[i,int(GBranch[j,2].value)] - K_g[j]*np.power(GasFlow[i,j],2)

    #GSlackBusPressure
    for i in range(1,T+1):
        for j in range(1,GBus.nrows):
            if GBus[j,1].value == -1:
                Flag_G3[i-1,j-1] = GasPressure[i,j] - 7

Flag_L=np.max(np.abs(LagrangeMatrix_mainGridP))+np.max(np.abs(LagrangeMatrix_mainGridQ))+np.max(np.abs(LagrangeMatrix_Pij))+np.max(np.abs(LagrangeMatrix_Qij))\
    +np.max(np.abs(LagrangeMatrix_Vi))+np.max(np.abs(LagrangeMatrix_Iij))+np.max(np.abs(LagrangeMatrix_CHP_P))+np.max(np.abs(LagrangeMatrix_CHP_Q))\
        +np.max(np.abs(LagrangeMatrix_CHP_H))+np.max(np.abs(LagrangeMatrix_CHP_G))+np.max(np.abs(LagrangeMatrix_GasBo_H))+np.max(np.abs(LagrangeMatrix_GasBo_G))\
            +np.max(np.abs(LagrangeMatrix_TempBusS))+np.max(np.abs(LagrangeMatrix_TempBranEndS))+np.max(np.abs(LagrangeMatrix_TempBusR))+np.max(np.abs(LagrangeMatrix_TempBranEndR))\
                +np.max(np.abs(LagrangeMatrix_TempLoadout))+np.max(np.abs(LagrangeMatrix_GasFlow))+np.max(np.abs(LagrangeMatrix_GasPressure))
Flageq=np.max(np.abs(Flag_E1))+np.max(np.abs(Flag_E2))+np.max(np.abs(Flag_E3))+np.max(np.abs(Flag_E4))+np.max(np.abs(Flag_E5))+np.max(np.abs(Flag_E6))+np.max(np.abs(Flag_E7))\
    +np.max(np.abs(Flag_E8))+np.max(np.abs(Flag_H1))+np.max(np.abs(Flag_H2))+np.max(np.abs(Flag_H3))+np.max(np.abs(Flag_H4))+np.max(np.abs(Flag_H5))+np.max(np.abs(Flag_H6))\
        +np.max(np.abs(Flag_H7))+np.max(np.abs(Flag_H8))+np.max(np.abs(Flag_H9))+np.max(np.abs(Flag_H10))+np.max(np.abs(Flag_G1))+np.max(np.abs(Flag_G2))+np.max(np.abs(Flag_G3))

if Flag_L+Flageq <= 0.01:
    Flag_result=1
if Flag_L+Flageq > 0.01:
    Flag_result=0

#print(np.max(np.abs(Flag_G3)))
#print(K_g)
#print(np.max(np.abs(LagrangeMatrix_mainGridP)))
#print(np.max(np.abs(LagrangeMatrix_mainGridQ)))
#print(np.max(np.abs(LagrangeMatrix_Pij)))
#print(np.max(np.abs(LagrangeMatrix_Qij)))
#print(np.max(np.abs(LagrangeMatrix_Vi)))
#print(np.max(np.abs(LagrangeMatrix_Iij)))
#print(np.max(np.abs(LagrangeMatrix_CHP_P)))
#print(np.max(np.abs(LagrangeMatrix_CHP_Q)))
#print(np.max(np.abs(LagrangeMatrix_CHP_H)))
#print(np.max(np.abs(LagrangeMatrix_CHP_G)))
#print(np.max(np.abs(LagrangeMatrix_GasBo_H)))
#print(np.max(np.abs(LagrangeMatrix_GasBo_G)))
#print(np.max(np.abs(LagrangeMatrix_TempBusS)))
#print(np.max(np.abs(LagrangeMatrix_TempBranEndS)))
#print(np.max(np.abs(LagrangeMatrix_TempBusR)))
#print(np.max(np.abs(LagrangeMatrix_TempBranEndR)))
#print(np.max(np.abs(LagrangeMatrix_TempLoadout)))
#print(np.max(np.abs(LagrangeMatrix_GasFlow)))
#print(np.max(np.abs(LagrangeMatrix_GasSource)))
#print(np.max(np.abs(LagrangeMatrix_GasPressure)))

