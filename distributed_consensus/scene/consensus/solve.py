from gams import *
import os
import sys
    

def get_model_text():
    return '''
 Sets
       SEBus             'Set of EBus row' /1*15/
       SEBran            'Set of EBranch row' /1*14/
       SCHP              'Set of CHP'   /1,2/
       SCHPj             'Set of CHP column'/P,Q,H,G/
       GasBoj            'Set of Gasboiler column' /H,G/
       SHBus             'Set of HBus row'/1*36/
       SHBranch          'Set of HBranch row'/1*35/
       SGBus             'Set of GBus row'   /1*37/
       SGBranch          'Set of GBranch row' /1*36/
       St                'Set of time period' /1*24/
       ;
Parameters
CHPMax(SCHP)   'CHP maximum output, kW'
/1   1000
 2   1000/
GasBoMax(SCHP) 'Gasboiler maximum output, MW'
/1   19.2
 2   4.8/
Cp        'Specific heat capacity of water,kJ/(kg.C)'     /4.2/
TCHPout   'Temperature output at CHP'                     /85/
Toutside  'Temperature outside'                           /15/
MassFlowC 'MassFlow constant at each load node kg/s'      /20/
GasHV     'Heat value of gas is 39MJ/m3 1m3/h=390/36kW'   /10.833/
CHPPeff   'CHP electric power efficiency'                 /0.277/
CHPHP     'CHP heat and electric ratio 1/0.66'            /1.5/
GasBoeff  'Gas boiler efficiency'                         /0.792/
;


Table EBus(SEBus, *)   'EBus data(PQ in kW)'
           Type       P       Q
   1          0     121      44
   2          0     246      89
   3          0      55      20
   4          0      89      32
   5          0      65      24
   6          0      97      35
   7          0      86      31
   8          0     265      96
   9          0      36      13
   10         0      50      18
   11         0     110      40
   12         0      31      11
   13         1       0       0
   14         2     660     240
   15        -1       0       0
        ;

Table EBranch(SEBran, *)   'EBranch data'
            Fbus        Tbus        r        x        z2
   1          15           1   0.0348   0.5227   0.27445
   2           1           2   0.0132   0.0101  0.000276
   3           2           3   0.0270   0.0208   0.00116
   4           3           4   0.0184 0.014168  0.000539
   5           4           5  0.00426  0.00328  0.000029
   6           5           6  0.01302 0.010025   0.00027
   7           8           7  0.02804 0.021591   0.00125
   8           9           8   0.0316 0.024332  0.001591
   9          10           9  0.00928  0.00715  0.000137
  10          11          10  0.02262 0.017417  0.000815
  11          12          11  0.01787  0.01376  0.000509
  12          15          12  0.03485  0.52272  0.274451
  13          13           3     0.01   0.0077  0.000159
  14          14           9     0.01   0.0077  0.000159
        ;

Table HBus(SHBus,*)      'HBus data(H in kW)'
            Type        H
  1            0      520
  2            0      363
  3            0      320
  4            0      258
  5            0      201
  6            0        2
  7            0      542
  8            0      194
  9            0       61
  10           0      201
  11           0      330
  12           0       34
  13           0       61
  14           0      725
  15           0       36
  16           0       36
  17           0      602
  18           0      209
  19           0      191
  20           0      743
  21          -1
  22          -1
  23          -1
  24          -1
  25          -1
  26          -1
  27          -1
  28          -1
  29          -1
  30          -1
  31          -1
  32          -1
  33          -1
  34          -1
  35           2      1000
  36           1
  ;

Table HBranch(SHBranch,*)   'HBranch data at supply side'
             Fbus        Tbus        Length        Diameter        Roughness        Coefficient
  1             1          21            40          0.2191           0.0004              0.455
  2            21           2            20          0.1683           0.0004              0.367
  3            21          22            70          0.2191           0.0004              0.455
  4            22           3            20          0.1397           0.0004              0.367
  5            22          23            70          0.2191           0.0004              0.455
  6            23           4            20          0.0889           0.0004              0.327
  7            23          24            70          0.2191           0.0004              0.455
  8            24           5            20          0.1143           0.0004              0.321
  9            24          11           130          0.2191           0.0004              0.455
  10           11          34            30          0.1683           0.0004              0.367
  11           11           9            70          0.0603           0.0004              0.236
  12           11          10           110          0.0889           0.0004              0.327
  13           11          25            80          0.1143           0.0004              0.321
  14           25          26            40          0.0761           0.0004              0.278
  15           25           6            40          0.0889           0.0004              0.327
  16           26           8            20          0.0483           0.0004              0.219
  17           26           7            40          0.0889           0.0004              0.327
  18           34          28            20          0.0603           0.0004              0.236
  19           28          12            10          0.0483           0.0004              0.219
  20           28          13            30          0.0603           0.0004              0.236
  21           29          34            20          0.1683           0.0004              0.367
  22           29          15            20          0.1683           0.0004              0.367
  23           27          29            40          0.1683           0.0004              0.367
  24           31          27            20          0.1683           0.0004              0.367
  25           31          18            20          0.0889           0.0004              0.327
  26           27          30            40          0.0889           0.0004              0.327
  27           30          14            40          0.0889           0.0004              0.327
  28           30          16            40          0.0424           0.0004               0.21
  29           32          31            20          0.1683           0.0004              0.367
  30           33          32            20          0.2191           0.0004              0.455
  31           33          17            40          0.0889           0.0004              0.327
  32           20          19           200          0.0761           0.0004              0.278
  33           20          33           100          0.2191           0.0004              0.455
  34           36           1            10          0.2191           0.0004              0.455
  35           35          20            10          0.2191           0.0004              0.455
  ;

Table GBus(SGBus,*)      'GBus data(G in kW)'
             Type           G
   1            1           0
   2            0           36.225
   3            0           220
   4            0           464
   5            0           226
   6            0           283
   7            0           296
   8            0           800
   9            0           867
  10            0           362
  11            0           377
  12            0           300
  13            0           4564
  14            0           191
  15            2
  16            0
  17            0
  18            0
  19            0
  20            0
  21            0
  22            0
  23            0
  24            0
  25            0
  26            0
  27            0
  28            0
  29            0
  30            0
  31            0
  32            0
  33            0
  34            0
  35            0
  36            0
  37           -1
  ;

Table GBranch(SGBranch,*)      'GBranch data'
             Fbus        Tbus        Length        Diameter
   1           16           1           240             100
   2           16          35           220            4100
   3           35          19           320            4100
   4           19          14            90             100
   5           35          36           260             100
   6           36          17            90             100
   7           17          18            20             100
   8           18           2            20             500
   9           18           3            80             100
  10           36          33           160             500
  11           33          34            20             500
  12           33          20           180             500
  13           20          15           110             500
  14           34          23            20             500
  15           23          22           150             100
  16           22           5            30             100
  17            5           6            90             100
  18           22          21            20             100
  19           21           4            20             100
  20           23          24           200             100
  21           24          25            60             100
  22           25           7            20             100
  23           25           8            20             500
  24           34          26            90             100
  25           26          27           130             100
  26           27          12            20             500
  27           27          28            40             100
  28           28          10            20             100
  29           28          29            40             100
  30           29          11           100             100
  31           29          30            40             100
  32           30           9            20             100
  33           30          31            20             100
  34           31          32           200            1100
  35           32          13           110             100
  36           37          16           100            4100
   ;

Parameter
K_g(SGBranch) 'coefficient K_g'
ELoadCurve(St) /1 0.76,2 0.77,3 0.78,4 0.79,5 0.8,6 0.81,7 0.82,8 0.83,9 0.84,10 0.85,11 0.86,12 0.87,13 0.88,14 0.89,15 0.9,16 0.91,17 0.92,18 0.93,19 0.94,20 0.95,21 0.96,22 0.97,23 0.98,24 0.99/
HLoadCurve(St) /1 0.76,2 0.77,3 0.78,4 0.79,5 0.8,6 0.81,7 0.82,8 0.83,9 0.84,10 0.85,11 0.86,12 0.87,13 0.88,14 0.89,15 0.9,16 0.91,17 0.92,18 0.93,19 0.94,20 0.95,21 0.96,22 0.97,23 0.98,24 0.99/
GLoadCurve(St) /1 0.76,2 0.77,3 0.78,4 0.79,5 0.8,6 0.81,7 0.82,8 0.83,9 0.84,10 0.85,11 0.86,12 0.87,13 0.88,14 0.89,15 0.9,16 0.91,17 0.92,18 0.93,19 0.94,20 0.95,21 0.96,22 0.97,23 0.98,24 0.99/
;
K_g(SGBranch)=11.7*GBranch(SGBranch,'Length')/GBranch(SGBranch,'Diameter')**5;

Variables
Obj                      'Objective Function'
;
Positive Variables
*electric variables
CHP(St,SCHP,SCHPj)          'CHP output, kW'
mainGridP(St)               'MainGrid P, kW'
mainGridQ(St)               'MainGrid Q, kVar'
Pij(St,SEBran)              'Active power on branchij, kW'
Qij(St,SEBran)              'Reactive power on branchij, kVar'
Vi(St,SEBus)                'Voltage of bus i in squared form,kV^2'
Iij(St,SEBran)              'Current of branch ij in squared form, A^2'
*heat variables
GasBo(St,SCHP,GasBoj)       'Gasboiler output, kW'
MassFlowL(St,SHBus)         'Node massFlow inject'
MassFlowS(St,SHBranch)      'Branch massFlow at supply side'
MassFlowR(St,SHBranch)      'Branch massFlow at return side'
MassFlowCHP(St,SCHP)        'CHP massFlow from return side to supply side'
TempBusS(St,SHBus)          'Node temperature at supply side'
TempBranEndS(St,SHBranch)   'Node temperature at supply side'
TempBusR(St,SHBus)          'Node temperature at return side'
TempBranEndR(St,SHBranch)   'Node temperature at return side'
TempLoadout(St,SHBus)       'Load output temperature'
*gas variables
GasFlow(St,SGBranch)        'Branch gasflow'
GasSource(St)               'Gas supply from source'
GasPressure(St,SGBus)       'Node gas pressure'
;

Vi.lo(St,SEBus)=sqr(0.95*6.6);
Vi.up(St,SEBus)=sqr(1.05*6.6);
MassFlowR.lo(St,SHBranch)=0.00001;
MassFlowS.lo(St,SHBranch)=0.00001;

Equations
ObjFunc                       'Objective Function'
*electric restrictions
ENodePLoadeq(St,SEBus)           'Load-node active power balance'
ENodePCHPeq(St,SEBus)            'CHP-node active power balance'
ENodePSlaeq(St,SEBus)            'Slack-node active power balance'
ENodeQLoadeq(St,SEBus)           'Load-node reactive power balance'
ENodeQCHPeq(St,SEBus)            'CHP-node reactive power balance'
ENodeQSlaeq(St,SEBus)            'Slack-node reactive power balance'
EBranchPeq(St,SEBran)            'Branch power balance'
EBranchPpositive(St,SEBran)      'Branch active power positive'
EBranchQpositive(St,SEBran)      'Branch reactive power positive'
SOCPeq(St,SEBran)                'Second-order-cone balance'
CHPOutputLimit(St,SCHP)          'CHP generation Limits'
SlackBusVoltage(St,SEBus)        'Voltage at slack bus is 1'

*heat restrictions
HNodeLoadeq(St,SHBus)            'load node heat balance'
HNodeCHPeq(St,SHBus)             'CHP node heat balance'
HKCLLoadS(St,SHBus)              'Load node KCL at supply side'
HKCLLoadR(St,SHBus)              'Load node KCL at return side'
HKCLCHPS(St,SHBus)               'CHP node KCL at supply side'
HKCLCHPR(St,SHBus)               'CHP node KCL at return side'
HBranchTempLossS(St,SHBranch)    'Branch heat loss at supply side'
HBranchTempLossR(St,SHBranch)    'Branch heat loss at return side'
HNodeMixLoadS(St,SHBus)          'Load node heat mix at supply side'
HNodeMixLoadR(St,SHBus)          'Load node heat mix at return side'
HNodeMixCHPS(St,SHBus)           'CHP node heat mix at supply side'
HNodeMixCHPR(St,SHBus)           'CHP node heat mix at return side'
HLoadMassFlowFix(St,SHBus)       'Load massflow inject is a constant'
HnLoadMassFlowFix(St,SHBus)      'nLoad massflow inject is 0'
HnLoadTempLoadout(St,SHBus)      'nLoad output temperatre is 0'

*gas restrictions
GNodeLoadeq(St,SGBus)            'Gas node gas load balance'
GNodeCHPeq(St,SGBus)             'CHP node gas load balance'
GSlackBuseq(St,SGBus)            'Gas source load balance'
GWeymoutheq(St,SGBranch)         'Gas Weymouth equation'
GSlackBusPressure(St,SGBus)      'Gas pressure at slack bus is 7bar'

*CHP restrictions
CHPEfficiencyeq1(St,SCHP)        'CHP efficiency restriction'
CHPEfficiencyeq2(St,SCHP)        'CHP efficiency restriction'
GasBoEfficiencyeq1(St,SCHP)      'GasBoiler efficiency restriction'
GasBoEfficiencyeq2(St,SCHP)      'GasBoiler efficiency restriction'
;

****************************************************************************************************************************************************************
ObjFunc                                            ..obj=E= sum(St,mainGridP(St))+sum(St,GasSource(St));
*+sum(St,sum(SCHP,(CHP(St,SCHP,'P')+CHP(St,SCHP,'H'))))
*electric restrictions
ENodePLoadeq(St,SEBus)$(EBus(SEBus,'Type') eq 0)      ..sum(SEBran$(EBranch(SEBran,'Tbus') eq ord(SEBus)),(Pij(St,SEBran)-EBranch(SEBran,'r')*Iij(St,SEBran)/1000)) =E= sum(SEBran$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Pij(St,SEBran))+EBus(SEBus,'P')*ELoadCurve(St);
ENodePCHPeq(St,SEBus)$(EBus(SEBus,'Type')  ge 1)      ..sum(SEBran$(EBranch(SEBran,'Tbus') eq ord(SEBus)),(Pij(St,SEBran)-EBranch(SEBran,'r')*Iij(St,SEBran)/1000))+sum(SCHP$(EBus(SEBus,'Type') eq ord (SCHP)),CHP(St,SCHP,'P')) =E= sum(SEBran$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Pij(St,SEBran))+EBus(SEBus,'P')*ELoadCurve(St);
ENodePSlaeq(St,SEBus)$(EBus(SEBus,'Type')  le -1)     ..sum(SEBran$(EBranch(SEBran,'Tbus') eq ord(SEBus)),(Pij(St,SEBran)-EBranch(SEBran,'r')*Iij(St,SEBran)/1000))+mainGridP(St) =E= sum(SEBran$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Pij(St,SEBran))+EBus(SEBus,'P')*ELoadCurve(St);
ENodeQLoadeq(St,SEBus)$(EBus(SEBus,'Type') eq 0)      ..sum(SEBran$(EBranch(SEBran,'Tbus') eq ord(SEBus)),(Qij(St,SEBran)-EBranch(SEBran,'x')*Iij(St,SEBran)/1000)) =E= sum(SEBran$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Qij(St,SEBran))+EBus(SEBus,'Q')*ELoadCurve(St);
ENodeQCHPeq(St,SEBus)$(EBus(SEBus,'Type')  ge 1)      ..sum(SEBran$(EBranch(SEBran,'Tbus') eq ord(SEBus)),(Qij(St,SEBran)-EBranch(SEBran,'x')*Iij(St,SEBran)/1000))+sum(SCHP$(EBus(SEBus,'Type') eq ord (SCHP)),CHP(St,SCHP,'Q')) =E= sum(SEBran$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Qij(St,SEBran))+EBus(SEBus,'Q')*ELoadCurve(St);
ENodeQSlaeq(St,SEBus)$(EBus(SEBus,'Type')  le -1)     ..sum(SEBran$(EBranch(SEBran,'Tbus') eq ord(SEBus)),(Qij(St,SEBran)-EBranch(SEBran,'x')*Iij(St,SEBran)/1000))+mainGridQ(St) =E= sum(SEBran$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Qij(St,SEBran))+EBus(SEBus,'Q')*ELoadCurve(St);
EBranchPeq(St,SEBran)                                 ..sum(SEBus$(EBRanch(SEBran,'Fbus') eq ord(SEBus)),Vi(St,SEBus))-sum(SEBus$(EBRanch(SEBran,'Tbus') eq ord(SEBus)),Vi(St,SEBus))=E= 2/1000*(Pij(St,SEBran)*EBranch(SEBran,'r')+Qij(St,SEBran)*EBranch(SEBran,'x'))-EBranch(SEBran,'z2')*Iij(St,SEBran)/1000/1000;
EBranchPpositive(St,SEBran)                           ..Pij(St,SEBran) =g= Iij(St,SEBran)*EBranch(SEBran,'r')/1000;
EBranchQpositive(St,SEBran)                           ..Qij(St,SEBran) =g= Iij(St,SEBran)*EBranch(SEBran,'x')/1000;
SOCPeq(St,SEBran)                                     ..sqr(sum(SEBus$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Vi(St,SEBus))+Iij(St,SEBran)) =G= sqr(2*Pij(St,SEBran))+sqr(2*Qij(St,SEBran))+sqr(sum(SEBus$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Vi(St,SEBus))-Iij(St,SEBran));
CHPOutputLimit(St,SCHP)                               ..CHP(St,SCHP,'P')**2+CHP(St,SCHP,'Q')**2 =l= CHPMax(SCHP)**2;
SlackBusVoltage(St,SEBus)$(EBus(SEBus,'Type') eq -1)  ..Vi(St,SEBus) =e= sqr(6.6);

*heat restrictions
HNodeLoadeq(St,SHBus)$(HBus(SHBus,'H') ne 0)         ..HBus(SHBus,'H')*HLoadCurve(St) =E= Cp*MassFlowL(St,SHBus)*(TempBusS(St,SHBus)-TempLoadout(St,SHBus));
HNodeCHPeq(St,SHBus)$(HBus(SHBus,'Type') ge 1)       ..sum(SCHP $(HBus(SHBus,'Type') eq ord(SCHP)),(CHP(St,SCHP,'H')+GasBo(St,SCHP,'H')))=E=Cp*sum(SCHP $(HBus(SHBus,'Type') eq ord(SCHP)),MassFlowCHP(St,SCHP))*(TCHPout-TempBusR(St,SHBus));
HKCLLoadS(St,SHBus)$(HBus(SHBus,'Type') le 0)        ..sum(SHBranch$(HBranch(SHBranch,'Tbus') eq ord(SHBus)),MassFlowS(St,SHBranch))=E=MassFlowL(St,SHBus)+sum(SHBranch$(HBranch(SHBranch,'Fbus') eq ord(SHBus)),MassFlowS(St,SHBranch));
HKCLLoadR(St,SHBus)$(HBus(SHBus,'Type') le 0)        ..sum(SHBranch$(HBranch(SHBranch,'Fbus') eq ord(SHBus)),MassFlowR(St,SHBranch))+MassFlowL(St,SHBus)=E=sum(SHBranch$(HBranch(SHBranch,'Tbus') eq ord(SHBus)),MassFlowR(St,SHBranch));
HKCLCHPS(St,SHBus)$(HBus(SHBus,'Type') ge 1)         ..sum(SHBranch$(HBranch(SHBranch,'Tbus') eq ord(SHBus)),MassFlowS(St,SHBranch))+sum(SCHP$(HBus(SHBus,'Type') eq ord(SCHP)),MassFlowCHP(St,SCHP))=E=MassFlowL(St,SHBus)+sum(SHBranch$(HBranch(SHBranch,'Fbus') eq ord(SHBus)),MassFlowS(St,SHBranch));
HKCLCHPR(St,SHBus)$(HBus(SHBus,'Type') ge 1)         ..sum(SHBranch$(HBranch(SHBranch,'Fbus') eq ord(SHBus)),MassFlowR(St,SHBranch))+MassFlowL(St,SHBus)=E=sum(SHBranch$(HBranch(SHBranch,'Tbus') eq ord(SHBus)),MassFlowR(St,SHBranch))+sum(SCHP$(HBus(SHBus,'Type') eq ord(SCHP)),MassFlowCHP(St,SCHP));
HBranchTempLossS(St,SHBranch)                        ..TempBranEndS(St,SHBranch)=E=Toutside+(sum(SHBus$(HBranch(SHBranch,'Fbus')eq ord(SHBus)),TempBusS(St,SHBus))-Toutside)*exp(-HBranch(SHBranch,'Coefficient')*HBranch(SHBranch,'Length')/Cp/1000/MassFlowS(St,SHBranch));
HBranchTempLossR(St,SHBranch)                        ..TempBranEndR(St,SHBranch)=E=Toutside+(sum(SHBus$(HBranch(SHBranch,'Tbus')eq ord(SHBus)),TempBusR(St,SHBus))-Toutside)*exp(-HBranch(SHBranch,'Coefficient')*HBranch(SHBranch,'Length')/Cp/1000/MassFlowR(St,SHBranch));
HNodeMixLoadS(St,SHBus)$(HBus(SHBus,'Type') le 0)    ..sum(SHBranch$(HBranch(SHBranch,'Tbus') eq ord(SHBus)),MassFlowS(St,SHBranch)*TempBranEndS(St,SHBranch))=E=(MassFlowL(St,SHBus)+sum(SHBranch$(HBranch(SHBranch,'Fbus') eq ord(SHBus)),MassFlowS(St,SHBranch)))*TempBusS(St,SHBus);
HNodeMixLoadR(St,SHBus)$(HBus(SHBus,'Type') le 0)    ..sum(SHBranch$(HBranch(SHBranch,'Fbus') eq ord(SHBus)),MassFlowR(St,SHBranch)*TempBranEndR(St,SHBranch))+MassFlowL(St,SHBus)*TempLoadout(St,SHBus)=E=sum(SHBranch$(HBranch(SHBranch,'Tbus') eq ord(SHBus)),MassFlowR(St,SHBranch))*TempBusR(St,SHBus);
HNodeMixCHPS(St,SHBus)$(HBus(SHBus,'Type') ge 1)     ..TempBusS(St,SHBus)=E=TCHPout;
HNodeMixCHPR(St,SHBus)$(HBus(SHBus,'Type') ge 1)     ..TempBusR(St,SHBus)*sum(SCHP$(HBus(SHBus,'Type') eq ord(SCHP)),MassFlowCHP(St,SCHP))=E=sum(SHBranch$(HBranch(SHBranch,'Fbus') eq ord (SHBus)),MassFlowR(St,SHBranch)*TempBranEndR(St,SHBranch))+MassFlowL(St,SHBus)*TempLoadout(St,SHBus);
HLoadMassFlowFix(St,SHBus)$(HBus(SHBus,'H') ne 0)    ..MassFlowL(St,SHBus) =e= MassFlowC;
HnLoadMassFlowFix(St,SHBus)$(HBus(SHBus,'H') eq 0)   ..MassFlowL(St,SHBus) =e= 0;
HnLoadTempLoadout(St,SHBus)$(HBus(SHBus,'H') eq 0)   ..TempLoadout(St,SHBus) =e= 0;

*gas restrictions
GNodeLoadeq(St,SGBus)$(GBus(SGBus,'Type') eq 0)      ..sum(SGBranch$(GBranch(SGBranch,'Tbus') eq ord(SGBus)),GasFlow(St,SGBranch))=e=sum(SGBranch$(GBranch(SGBranch,'Fbus') eq ord(SGBus)),GasFlow(St,SGBranch))+GBus(SGBus,'G')/GasHV*GLoadCurve(St);
GNodeCHPeq(St,SGBus)$(GBus(SGBus,'Type') ge 1)       ..sum(SGBranch$(GBranch(SGBranch,'Tbus') eq ord(SGBus)),GasFlow(St,SGBranch))=e=sum(SGBranch$(GBranch(SGBranch,'Fbus') eq ord(SGBus)),GasFlow(St,SGBranch))+sum(SCHP$(GBus(SGBus,'Type') eq ord(SCHP)),(CHP(St,SCHP,'G')+GasBo(St,SCHP,'G')));
GSlackBuseq(St,SGBus)$(GBus(SGBus,'Type') eq -1)     ..sum(SGBranch$(GBranch(SGBranch,'Tbus') eq ord(SGBus)),GasFlow(St,SGBranch))+GasSource(St)=E=sum(SGBranch$(GBranch(SGBranch,'Fbus') eq ord(SGBus)),GasFlow(St,SGBranch))+GBus(SGBus,'G')/GasHV*GLoadCurve(St);
GWeymoutheq(St,SGBranch)                             ..sum(SGBus$(GBranch(SGBranch,'Fbus') eq ord(SGBus)),GasPressure(St,SGBus))-sum(SGBus$(GBranch(SGBranch,'Tbus') eq ord(SGBus)),GasPressure(St,SGBus))=e=K_g(SGBranch)*GasFlow(St,SGBranch)**2;
GSlackBusPressure(St,SGBus)$(GBus(SGBus,'Type') eq -1)..GasPressure(St,SGBus)=e=7;

*CHP restrictions
CHPEfficiencyeq1(St,SCHP)                            ..CHP(St,SCHP,'P') =e= CHPPeff*CHP(St,SCHP,'G')*GasHV;
CHPEfficiencyeq2(St,SCHP)                            ..CHP(St,SCHP,'P')*CHPHP =e= CHP(St,SCHP,'H');
GasBoEfficiencyeq1(St,SCHP)                          ..GasBo(St,SCHP,'G')*GasHV*GasBoeff =e= GasBo(St,SCHP,'H');
GasBoEfficiencyeq2(St,SCHP)                          ..GasBo(St,SCHP,'H') =l= GasBoMax(SCHP)*1000;

model IES /ALL/;

option NLP=CONOPT;
*option DNLP=Baron  CONOPT  MINOS SNOPT

solve IES using NLP minimizing obj; '''


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ws = GamsWorkspace(system_directory = sys.argv[1])
    else:
        ws = GamsWorkspace()

    #file = open(os.path.join(ws.working_directory, "tdata.gms"), "w")
   # file.write(get_data_text())
   # file.close()
    
    t2 = ws.add_job_from_string(get_model_text())
    #opt = ws.add_options()
    #opt.defines["incname"] = "tdata"
    t2.run()
    #for rec in t2.out_db["CHP"]:
    #    print("MassFlowS(" + rec.key(0) + "," + rec.key(1) + ","+rec.key(2)+"): level=" + str(rec.level) + " marginal=" + str(rec.marginal))
    
    T=24
    CHPnum=2
    EBusnum=15 
    EBrannum=14 
    HBusnum=36   
    HBrannum=35
    GBusnum=37
    GBrannum=36
    PySt=[str(j) for j in range(1,T+1)]
    PySCHP=[str(j) for j in range(1,CHPnum+1)]
    PySCHPj=['P','Q','H','G']
    PySEBran=[str(j) for j in range(1,EBrannum+1)]
    PyEBus=[str(j) for j in range(1,EBusnum+1)]
    PyGasBoj=['H','G']
    PySHBus=[str(j) for j in range(1,HBusnum+1)]  
    PySHBran=[str(j) for j in range(1,HBrannum+1)] 
    PySGBus=[str(j) for j in range(1,GBusnum+1)] 
    PySGBran=[str(j) for j in range(1,GBrannum+1)] 
       
  
    db = ws.add_database()
    St = db.add_set("St", 1, "Set of time period")
    SCHP = db.add_set("SCHP", 1, "Set of CHP")
    SCHPj = db.add_set("SCHPj", 1, "Set of CHP column")
    SEBran = db.add_set("SEBran", 1, "Set of EBranch row")
    SEBus = db.add_set("SEBus", 1, "Set of EBus row")
    GasBoj = db.add_set("GasBoj", 1, "Set of Gasboiler column")
    SHBus = db.add_set("SHBus", 1, "Set of HBus row")
    SHBran = db.add_set("SHBran", 1, "Set of HBranch row") 
    SGBus = db.add_set("SGBus", 1, "Set of GBus row")    
    SGBran = db.add_set("SGBran", 1, "Set of GBranch row")  
    for i in PySt:
      St.add_record(i)
    for i in PySCHP:
      SCHP.add_record(i)
    for i in PySCHPj:
      SCHPj.add_record(i)
    for i in PySEBran:
      SEBran.add_record(i)
    for i in PyEBus:
      SEBus.add_record(i)
    for i in PyGasBoj:
      GasBoj.add_record(i)
    for i in PySHBus:
      SHBus.add_record(i)
    for i in PySHBran:
      SHBran.add_record(i)
    for i in PySGBus:
      SGBus.add_record(i)
    for i in PySGBran:
      SGBran.add_record(i)


#electric variables  
    CHP = db.add_parameter_dc("CHP", [St,SCHP,SCHPj], "CHP output, kW")
    mainGridP = db.add_parameter_dc("mainGridP", [St], "Power bought from maingrid")
    mainGridQ = db.add_parameter_dc("mainGridQ", [St], "Power bought from maingrid")
    Pij = db.add_parameter_dc("Pij",[St,SEBran],'Active power on branchij, kW')
    Qij = db.add_parameter_dc("Qij",[St,SEBran],'Reactive power on branchij, kVar')
    Vi = db.add_parameter_dc("Vi",[St,SEBus],'Voltage of bus i in squared form,kV^2')   
    Iij = db.add_parameter_dc("Iij",[St,SEBran],'Current of branch ij in squared form, A^2')           
    for rec in t2.out_db["CHP"]:
      tmp=(rec.key(0),rec.key(1),rec.key(2))
      CHP.add_record(tmp).value = rec.level
    for rec in t2.out_db["mainGridP"]:
      mainGridP.add_record(rec.key(0)).value = rec.level
    for rec in t2.out_db["mainGridQ"]:
      mainGridQ.add_record(rec.key(0)).value = rec.level
    for rec in t2.out_db["Pij"]:
      tmp=(rec.key(0),rec.key(1))
      Pij.add_record(tmp).value = rec.level
    for rec in t2.out_db["Qij"]:
      tmp=(rec.key(0),rec.key(1))
      Qij.add_record(tmp).value = rec.level
    for rec in t2.out_db["Vi"]:
      tmp=(rec.key(0),rec.key(1))
      Vi.add_record(tmp).value = rec.level
    for rec in t2.out_db["Iij"]:
      tmp=(rec.key(0),rec.key(1))
      Iij.add_record(tmp).value = rec.level

#heat variables
    GasBo = db.add_parameter_dc("GasBo", [St,SCHP,GasBoj], "Gasboiler output, kW")
    MassFlowL = db.add_parameter_dc("MassFlowL", [St,SHBus], "Node massFlow inject")
    MassFlowS = db.add_parameter_dc("MassFlowS", [St,SHBran], "Branch massFlow at supply side")
    MassFlowR = db.add_parameter_dc("MassFlowR", [St,SHBran], "Branch massFlow at return side")
    MassFlowCHP = db.add_parameter_dc("MassFlowCHP", [St,SCHP], "CHP massFlow from return side to supply side")
    TempBusS = db.add_parameter_dc("TempBusS", [St,SHBus], "Node temperature at supply side")
    TempBranEndS = db.add_parameter_dc("TempBranEndS", [St,SHBran], "Node temperature at supply side")
    TempBusR = db.add_parameter_dc("TempBusR", [St,SHBus], "Node temperature at return side")
    TempBranEndR = db.add_parameter_dc("TempBranEndR", [St,SHBran], "Node temperature at return side")
    TempLoadout = db.add_parameter_dc("TempLoadout", [St,SHBus], "Load output temperature")
    for rec in t2.out_db["GasBo"]:
      tmp=(rec.key(0),rec.key(1),rec.key(2))
      GasBo.add_record(tmp).value = rec.level
    for rec in t2.out_db["MassFlowL"]:
      tmp=(rec.key(0),rec.key(1))
      MassFlowL.add_record(tmp).value = rec.level
    for rec in t2.out_db["MassFlowS"]:
      tmp=(rec.key(0),rec.key(1))
      MassFlowS.add_record(tmp).value = rec.level
    for rec in t2.out_db["MassFlowR"]:
      tmp=(rec.key(0),rec.key(1))
      MassFlowR.add_record(tmp).value = rec.level
    for rec in t2.out_db["MassFlowCHP"]:
      tmp=(rec.key(0),rec.key(1))
      MassFlowCHP.add_record(tmp).value = rec.level
    for rec in t2.out_db["TempBusS"]:
      tmp=(rec.key(0),rec.key(1))
      TempBusS.add_record(tmp).value = rec.level
    for rec in t2.out_db["TempBranEndS"]:
      tmp=(rec.key(0),rec.key(1))
      TempBranEndS.add_record(tmp).value = rec.level
    for rec in t2.out_db["TempBusR"]:
      tmp=(rec.key(0),rec.key(1))
      TempBusR.add_record(tmp).value = rec.level
    for rec in t2.out_db["TempBranEndR"]:
      tmp=(rec.key(0),rec.key(1))
      TempBranEndR.add_record(tmp).value = rec.level
    for rec in t2.out_db["TempLoadout"]:
      tmp=(rec.key(0),rec.key(1))
      TempLoadout.add_record(tmp).value = rec.level

#gas variables
    GasFlow = db.add_parameter_dc("GasFlow", [St,SGBran], "Branch gasflow")
    GasSource = db.add_parameter_dc("GasSource", [St], "Gas supply from source")
    GasPressure = db.add_parameter_dc("GasPressure", [St,SGBus], "Node gas pressure")
    for rec in t2.out_db["GasFlow"]:
      tmp=(rec.key(0),rec.key(1))
      GasFlow.add_record(tmp).value = rec.level
    for rec in t2.out_db["GasSource"]:
      GasSource.add_record(rec.key(0)).value = rec.level
    for rec in t2.out_db["GasPressure"]:
      tmp=(rec.key(0),rec.key(1))
      GasPressure.add_record(tmp).value = rec.level

    db.export("C:/Users/miller/Desktop/ptry/Optimization_data.gdx")

#dual variables
    db = ws.add_database() 
    St = db.add_set("St", 1, "Set of time period")
    SCHP = db.add_set("SCHP", 1, "Set of CHP")
    SCHPj = db.add_set("SCHPj", 1, "Set of CHP column")
    SEBran = db.add_set("SEBran", 1, "Set of EBranch row")
    SEBus = db.add_set("SEBus", 1, "Set of EBus row")
    GasBoj = db.add_set("GasBoj", 1, "Set of Gasboiler column")
    SHBus = db.add_set("SHBus", 1, "Set of HBus row")
    SHBran = db.add_set("SHBran", 1, "Set of HBranch row") 
    SGBus = db.add_set("SGBus", 1, "Set of GBus row")    
    SGBran = db.add_set("SGBran", 1, "Set of GBranch row")  
    for i in PySt:
      St.add_record(i)
    for i in PySCHP:
      SCHP.add_record(i)
    for i in PySCHPj:
      SCHPj.add_record(i)
    for i in PySEBran:
      SEBran.add_record(i)
    for i in PyEBus:
      SEBus.add_record(i)
    for i in PyGasBoj:
      GasBoj.add_record(i)
    for i in PySHBus:
      SHBus.add_record(i)
    for i in PySHBran:
      SHBran.add_record(i)
    for i in PySGBus:
      SGBus.add_record(i)
    for i in PySGBran:
      SGBran.add_record(i)
#electric restrictions
    ENodePeq = db.add_parameter_dc("ENodePeq", [St,SEBus], "Node active power balance")
    for rec in t2.out_db["ENodePLoadeq"]:
      tmp=(rec.key(0),rec.key(1))
      ENodePeq.add_record(tmp).value = rec.marginal
    for rec in t2.out_db["ENodePCHPeq"]:
      tmp=(rec.key(0),rec.key(1))
      ENodePeq.add_record(tmp).value = rec.marginal
    for rec in t2.out_db["ENodePSlaeq"]:
      tmp=(rec.key(0),rec.key(1))
      ENodePeq.add_record(tmp).value = rec.marginal
    ENodeQeq = db.add_parameter_dc("ENodeQeq", [St,SEBus], "Node reactive power balance")
    for rec in t2.out_db["ENodeQLoadeq"]:
      tmp=(rec.key(0),rec.key(1))
      ENodeQeq.add_record(tmp).value = rec.marginal
    for rec in t2.out_db["ENodeQCHPeq"]:
      tmp=(rec.key(0),rec.key(1))
      ENodeQeq.add_record(tmp).value = rec.marginal
    for rec in t2.out_db["ENodeQSlaeq"]:
      tmp=(rec.key(0),rec.key(1))
      ENodeQeq.add_record(tmp).value = rec.marginal
    EBranchPeq = db.add_parameter_dc("EBranchPeq", [St,SEBran], "Branch power balance")
    for rec in t2.out_db["EBranchPeq"]:
      tmp=(rec.key(0),rec.key(1))
      EBranchPeq.add_record(tmp).value = rec.marginal
    EBranchPpositive = db.add_parameter_dc("EBranchPpositive", [St,SEBran], "Branch active power positive")
    for rec in t2.out_db["EBranchPpositive"]:
      tmp=(rec.key(0),rec.key(1))
      EBranchPpositive.add_record(tmp).value = abs(rec.marginal)
    EBranchQpositive = db.add_parameter_dc("EBranchQpositive", [St,SEBran], "Branch reactive power positive")
    for rec in t2.out_db["EBranchQpositive"]:
      tmp=(rec.key(0),rec.key(1))
      EBranchQpositive.add_record(tmp).value = abs(rec.marginal)
    SOCPeq = db.add_parameter_dc("SOCPeq", [St,SEBran], "Second-order-cone balance")
    for rec in t2.out_db["SOCPeq"]:
      tmp=(rec.key(0),rec.key(1))
      SOCPeq.add_record(tmp).value = abs(rec.marginal)
    CHPOutputLimit = db.add_parameter_dc("CHPOutputLimit", [St,SCHP], "CHP generation Limits")
    for rec in t2.out_db["CHPOutputLimit"]:
      tmp=(rec.key(0),rec.key(1))
      CHPOutputLimit.add_record(tmp).value = abs(rec.marginal)

#heat restrictions
    HNodeLoadeq = db.add_parameter_dc("HNodeLoadeq", [St,SHBus], "load node heat balance")
    for rec in t2.out_db["HNodeLoadeq"]:
      tmp=(rec.key(0),rec.key(1))
      HNodeLoadeq.add_record(tmp).value = rec.marginal
    HNodeCHPeq = db.add_parameter_dc("HNodeCHPeq", [St,SHBus], "CHP node heat balance")
    for rec in t2.out_db["HNodeCHPeq"]:
      tmp=(rec.key(0),rec.key(1))
      HNodeCHPeq.add_record(tmp).value = rec.marginal
    HBranchTempLossS = db.add_parameter_dc("HBranchTempLossS", [St,SHBran], "Branch heat loss at supply side")
    for rec in t2.out_db["HBranchTempLossS"]:
      tmp=(rec.key(0),rec.key(1))
      HBranchTempLossS.add_record(tmp).value = rec.marginal 
    HBranchTempLossR = db.add_parameter_dc("HBranchTempLossR", [St,SHBran], "Branch heat loss at return side")
    for rec in t2.out_db["HBranchTempLossR"]:
      tmp=(rec.key(0),rec.key(1))
      HBranchTempLossR.add_record(tmp).value = rec.marginal
    HNodeMixLoadS = db.add_parameter_dc("HNodeMixLoadS", [St,SHBus], "Load node heat mix at supply side")
    for rec in t2.out_db["HNodeMixLoadS"]:
      tmp=(rec.key(0),rec.key(1))
      HNodeMixLoadS.add_record(tmp).value = rec.marginal 
    HNodeMixLoadR = db.add_parameter_dc("HNodeMixLoadR", [St,SHBus], "Load node heat mix at return side")
    for rec in t2.out_db["HNodeMixLoadR"]:
      tmp=(rec.key(0),rec.key(1))
      HNodeMixLoadR.add_record(tmp).value = rec.marginal  
    HNodeMixCHPS = db.add_parameter_dc("HNodeMixCHPS", [St,SHBus], "CHP node heat mix at supply side")
    for rec in t2.out_db["HNodeMixCHPS"]:
      tmp=(rec.key(0),rec.key(1))
      HNodeMixCHPS.add_record(tmp).value = rec.marginal
    HNodeMixCHPR = db.add_parameter_dc("HNodeMixCHPR", [St,SHBus], "CHP node heat mix at return side")
    for rec in t2.out_db["HNodeMixCHPR"]:
      tmp=(rec.key(0),rec.key(1))
      HNodeMixCHPR.add_record(tmp).value = rec.marginal
    HnLoadTempLoadout = db.add_parameter_dc("HnLoadTempLoadout", [St,SHBus], "nLoad output temperatre is 0")
    for rec in t2.out_db["HnLoadTempLoadout"]:
      tmp=(rec.key(0),rec.key(1))
      HnLoadTempLoadout.add_record(tmp).value = rec.marginal
      

#Gas restrictions
    GNodeLoadeq = db.add_parameter_dc("GNodeLoadeq", [St,SGBus], "Gas node gas load balance")
    for rec in t2.out_db["GNodeLoadeq"]:
      tmp=(rec.key(0),rec.key(1))
      GNodeLoadeq.add_record(tmp).value = rec.marginal  
    GNodeCHPeq = db.add_parameter_dc("GNodeCHPeq", [St,SGBus], "CHP node gas load balance")
    for rec in t2.out_db["GNodeCHPeq"]:
      tmp=(rec.key(0),rec.key(1))
      GNodeCHPeq.add_record(tmp).value = rec.marginal  
    GSlackBuseq = db.add_parameter_dc("GSlackBuseq", [St,SGBus], "Gas source load balance")
    for rec in t2.out_db["GSlackBuseq"]:
      tmp=(rec.key(0),rec.key(1))
      GSlackBuseq.add_record(tmp).value = rec.marginal  
    GWeymoutheq = db.add_parameter_dc("GWeymoutheq", [St,SGBran], "Gas Weymouth equation")
    for rec in t2.out_db["GWeymoutheq"]:
      tmp=(rec.key(0),rec.key(1))
      GWeymoutheq.add_record(tmp).value = rec.marginal 
    GSlackBusPressure = db.add_parameter_dc("GSlackBusPressure", [St,SGBus], "Gas pressure at slack bus is 7bar")
    for rec in t2.out_db["GSlackBusPressure"]:
      tmp=(rec.key(0),rec.key(1))
      GSlackBusPressure.add_record(tmp).value = rec.marginal

#CHP restrictions
    CHPEfficiencyeq1 = db.add_parameter_dc("CHPEfficiencyeq1", [St,SCHP], "CHP efficiency restriction")
    for rec in t2.out_db["CHPEfficiencyeq1"]:
      tmp=(rec.key(0),rec.key(1))
      CHPEfficiencyeq1.add_record(tmp).value = rec.marginal
    CHPEfficiencyeq2 = db.add_parameter_dc("CHPEfficiencyeq2", [St,SCHP], "CHP efficiency restriction")
    for rec in t2.out_db["CHPEfficiencyeq2"]:
      tmp=(rec.key(0),rec.key(1))
      CHPEfficiencyeq2.add_record(tmp).value = rec.marginal
    GasBoEfficiencyeq1 = db.add_parameter_dc("GasBoEfficiencyeq1", [St,SCHP], "GasBoiler efficiency restriction")
    for rec in t2.out_db["GasBoEfficiencyeq1"]:
      tmp=(rec.key(0),rec.key(1))
      GasBoEfficiencyeq1.add_record(tmp).value = rec.marginal
    GasBoEfficiencyeq2 = db.add_parameter_dc("GasBoEfficiencyeq2", [St,SCHP], "GasBoiler efficiency restriction")
    for rec in t2.out_db["GasBoEfficiencyeq2"]:
      tmp=(rec.key(0),rec.key(1))
      GasBoEfficiencyeq2.add_record(tmp).value = abs(rec.marginal)

    db.export("C:/Users/miller/Desktop/ptry/dual_data.gdx")   

