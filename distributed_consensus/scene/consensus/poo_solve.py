import xlrd
import xlwt
import numpy as np
from gams import *
import sys
import subprocess
import os
from .sheet_wrapper import SheetWrapper

class PooSolve:
    def __init__(self):
        super().__init__()
    def solve_error_optimization(self,dual_filename,optimization_filename):
        self.solve_optimization(dual_filename,optimization_filename,error = True)
    # 获取可行解，改方法用来获取非最优解
    def solve_feasible_optimization(self,dual_filename,optimization_filename):
        self.solve_optimization(dual_filename,optimization_filename,conopt = "CONOPT")
    # 获取可行解（conopt为默认值时是最优解）
    def solve_optimization(self,dual_filename,optimization_filename,conopt="CONOPT4",error=False):
        #if len(sys.argv) > 1:
        #    ws = GamsWorkspace(system_directory = sys.argv[1])
        #else:
        #    ws = GamsWorkspace()
        ws = GamsWorkspace()

        #file = open(os.path.join(ws.working_directory, "tdata.gms"), "w")
      # file.write(get_data_text())
      # file.close()
        t2 = ws.add_job_from_string(self.get_model_text(conopt,error))
        #opt = ws.add_options()
        #opt.defines["incname"] = "tdata"
        t2.run()
        #for rec in t2.out_db["CHP"]:
        #    print("MassFlowS(" + rec.key(0) + "," + rec.key(1) + ","+rec.key(2)+"): level=" + str(rec.level) + " marginal=" + str(rec.marginal))
        
        T=24
        CHPnum=8
        EBusnum=15 
        EBrannum=14 
        HBusnum=36   
        HBrannum=35
        GBusnum=37
        GBrannum=36
        PySt=[str(j) for j in range(1,T+1)]
        PySCHP=[str(j) for j in range(1,CHPnum+1)]
        PySCHPj=['P','Q','H','G']
        PySEStoj=['P','Pi','Po']
        PySHStoj=['H','Hi','Ho']
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
        SEStoj = db.add_set("SEStoj", 1, "Set of Estorage column")
        SHStoj = db.add_set("SHStoj", 1, "Set of Estorage column")
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
        for i in PySEStoj:
          SEStoj.add_record(i)
        for i in PySHStoj:
          SHStoj.add_record(i)
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
        Esto = db.add_parameter_dc("Esto",[St,SCHP,SEStoj],'Electirc storage') 

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
        for rec in t2.out_db["Esto"]:
          tmp=(rec.key(0),rec.key(1),rec.key(2))
          Esto.add_record(tmp).value = rec.level

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
        Hsto = db.add_parameter_dc("Hsto",[St,SCHP,SHStoj],'Heat storage')
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
        for rec in t2.out_db["Hsto"]:
          tmp=(rec.key(0),rec.key(1),rec.key(2))
          Hsto.add_record(tmp).value = rec.level

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
        #db.export("D:\punlish\ptry\Optimization_data.gdx")
        db.export(optimization_filename)

    #dual variables
        db = ws.add_database() 
        St = db.add_set("St", 1, "Set of time period")
        SCHP = db.add_set("SCHP", 1, "Set of CHP")
        SCHPj = db.add_set("SCHPj", 1, "Set of CHP column")
        SEStoj = db.add_set("SEStoj", 1, "Set of Estorage column")
        SHStoj = db.add_set("SHStoj", 1, "Set of Estorage column")
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
        for i in PySEStoj:
          SEStoj.add_record(i)
        for i in PySHStoj:
          SHStoj.add_record(i)
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
        EstoragePowereq = db.add_parameter_dc("EstoragePowereq", [St,SCHP], "Estorage power equation")
        for rec in t2.out_db["EstoragePowereq"]:
          tmp=(rec.key(0),rec.key(1))
          EstoragePowereq.add_record(tmp).value = abs(rec.marginal)
        EstorageStarteqEnd = db.add_parameter_dc("EstorageStarteqEnd", [SCHP], "Initial power equals end power")
        for rec in t2.out_db["EstorageStarteqEnd"]:
          tmp=rec.key(0)
          EstorageStarteqEnd.add_record(tmp).value = abs(rec.marginal)
        EstorageInitial = db.add_parameter_dc("EstorageInitial", [SCHP], "Initialize storage power")
        for rec in t2.out_db["EstorageInitial"]:
          tmp=rec.key(0)
          EstorageInitial.add_record(tmp).value = abs(rec.marginal)

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
        HstoragePowereq = db.add_parameter_dc("HstoragePowereq", [St,SCHP], "Hstorage power equation")   
        for rec in t2.out_db["HstoragePowereq"]:
          tmp=(rec.key(0),rec.key(1))
          HstoragePowereq.add_record(tmp).value = abs(rec.marginal)
        HstorageStarteqEnd = db.add_parameter_dc("HstorageStarteqEnd", [SCHP], "Initial power equals end power")
        for rec in t2.out_db["HstorageStarteqEnd"]:
          tmp=rec.key(0)
          HstorageStarteqEnd.add_record(tmp).value = abs(rec.marginal)
        HstorageInitial = db.add_parameter_dc("HstorageInitial", [SCHP], "Initialize storage power")
        for rec in t2.out_db["HstorageInitial"]:
          tmp=rec.key(0)
          HstorageInitial.add_record(tmp).value = abs(rec.marginal)

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
        #CHPEfficiencyeq1 = db.add_parameter_dc("CHPEfficiencyeq1", [St,SCHP], "CHP efficiency restriction")
        #for rec in t2.out_db["CHPEfficiencyeq1"]:
          #tmp=(rec.key(0),rec.key(1))
          #CHPEfficiencyeq1.add_record(tmp).value = rec.marginal
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
        # db.export("D:\punlish\ptry\dual_data.gdx")   
        db.export(dual_filename)      

    def validate_optimization(self,dual_filename,optimization_filename,ies_filename):
        #if len(sys.argv) > 1:
        #    ws = GamsWorkspace(system_directory = sys.argv[1])
        #else:
        #    ws = GamsWorkspace()
        ws = GamsWorkspace()
        T= 24
        CHPnum = 8
        CHPHP = 1.5
        CHPPeff = 0.277
        GasHV = 10.833
        GasBoeff = 0.792
        Cp = 4.2
        TCHPout = 85
        Toutside = 15
        MassFlowC = 20

        #data = xlrd.open_workbook('D:\punlish\ptry\IES_data.xls')
        data = xlrd.open_workbook(ies_filename)
        EBus = SheetWrapper(data.sheet_by_name('EBus'))
        EBranch = SheetWrapper(data.sheet_by_name('EBranch'))
        HBus = SheetWrapper(data.sheet_by_name('HBus'))
        HBranch = SheetWrapper(data.sheet_by_name('HBranch'))
        GBus = SheetWrapper(data.sheet_by_name('GBus'))
        GBranch = SheetWrapper(data.sheet_by_name('GBranch'))
        CHPcost = SheetWrapper(data.sheet_by_name('CHPcost'))
        EStoragedata = SheetWrapper(data.sheet_by_name('EStoragedata'))
        HStoragedata = SheetWrapper(data.sheet_by_name('HStoragedata'))
        CHPMax=[1000,1000,1000,1000,1000,1000,1000,1000]
        GasBoMax=[6,6,1,1,1,1,1,1]
        K_g=np.zeros(GBranch.nrows)
        for i in range(1,GBranch.nrows):
            K_g[i] = 11.7*GBranch[i,3].value/np.power(GBranch[i,4].value*1000,5)
        EloadCurve=np.zeros(T)
        HloadCurve=np.zeros(T)
        GloadCurve=np.zeros(T)
        mainGridPrice=np.zeros(T) 
        EloadCurve=[0.78,0.77,0.76,0.79,0.80,0.83,0.84,0.86,0.82,0.85,0.87,0.93,0.91,0.90,0.89,0.94,0.98,1,0.99,0.97,0.92,0.88,0.84,0.80]
        HloadCurve=[0.78,0.77,0.76,0.79,0.80,0.83,0.84,0.86,0.82,0.85,0.87,0.93,0.91,0.90,0.89,0.94,0.98,1,0.99,0.97,0.92,0.88,0.84,0.80]
        GloadCurve=[0.78,0.77,0.76,0.79,0.80,0.83,0.84,0.86,0.82,0.85,0.87,0.93,0.91,0.90,0.89,0.94,0.98,1,0.99,0.97,0.92,0.88,0.84,0.80]
        mainGridPrice=[0.012,0.012,0.010,0.011,0.009,0.010,0.030,0.060,0.050,0.045,0.032,0.031,0.015,0.032,0.035,0.020,0.058,0.050,0.047,0.012,0.011,0.031,0.009,0.010]
        db = ws.add_database_from_gdx(optimization_filename)
        CHP = { tuple((int(rec.key(0)),int(rec.key(1)),rec.key(2))):rec.value for rec in db["CHP"] }
        mainGridP = { int(rec.key(0)):rec.value for rec in db["mainGridP"] }
        mainGridQ = { int(rec.key(0)):rec.value for rec in db["mainGridQ"] }
        Pij = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["Pij"] }
        Qij = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["Qij"] }
        Iij = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["Iij"] }
        Vi = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["Vi"] }
        Esto = { tuple((int(rec.key(0)),int(rec.key(1)),rec.key(2))):rec.value for rec in db["Esto"] }
        
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
        Hsto = { tuple((int(rec.key(0)),int(rec.key(1)),rec.key(2))):rec.value for rec in db["Hsto"] }

        GasFlow = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GasFlow"] }
        GasSource = { int(rec.key(0)):rec.value for rec in db["GasSource"] }
        GasPressure = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GasPressure"] }    

        #db = ws.add_database_from_gdx("D:\punlish\ptry\dual_data.gdx")
        db = ws.add_database_from_gdx(dual_filename)
        #electric restrictions
        ENodePeq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["ENodePeq"] }
        ENodeQeq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["ENodeQeq"] }
        EBranchPeq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["EBranchPeq"] }
        EBranchPpositive = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["EBranchPpositive"] }
        EBranchQpositive = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["EBranchQpositive"] }
        SOCPeq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["SOCPeq"] }
        CHPOutputLimit = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["CHPOutputLimit"] }
        EstoragePowereq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["EstoragePowereq"] }
        EstorageStarteqEnd = { (int(rec.key(0))):rec.value for rec in db["EstorageStarteqEnd"] }
        EstorageInitial = { (int(rec.key(0))):rec.value for rec in db["EstorageInitial"] }

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
        HstoragePowereq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["HstoragePowereq"] }
        HstorageStarteqEnd = { (int(rec.key(0))):rec.value for rec in db["HstorageStarteqEnd"] }
        HstorageInitial = { (int(rec.key(0))):rec.value for rec in db["HstorageInitial"] }

        #Gas restrictions
        GNodeLoadeq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GNodeLoadeq"] }
        GNodeCHPeq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GNodeCHPeq"] }
        GSlackBuseq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GSlackBuseq"] }
        GWeymoutheq = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GWeymoutheq"] }
        GSlackBusPressure = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GSlackBusPressure"] }

        #CHP restrictions
        #CHPEfficiencyeq1 = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["CHPEfficiencyeq1"] }
        CHPEfficiencyeq2 = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["CHPEfficiencyeq2"] }
        GasBoEfficiencyeq1 = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GasBoEfficiencyeq1"] }
        GasBoEfficiencyeq2 = { tuple((int(rec.key(0)),int(rec.key(1)))):rec.value for rec in db["GasBoEfficiencyeq2"] }


        #deltaL/CHP(P)
        LagrangeMatrix_CHP_P = np.zeros((T,CHPnum))
        for i in range(1,T+1):
            LagrangeMatrix_CHP_P[i-1,0] = GNodeCHPeq[i,1]/CHPPeff/GasHV+ENodePeq[i,13] - 2*CHP[i,1,'P']*CHPOutputLimit[i,1]  + CHPEfficiencyeq2[i,1]*CHPHP -2*CHPcost[1,1].value*CHP[i,1,'P']/1000/1000-CHPcost[1,2].value/1000-CHPcost[1,5].value*CHP[i,1,'H']/1000/1000
            LagrangeMatrix_CHP_P[i-1,1] = GNodeCHPeq[i,15]/CHPPeff/GasHV+ENodePeq[i,14] - 2*CHP[i,2,'P']*CHPOutputLimit[i,2]  + CHPEfficiencyeq2[i,2]*CHPHP -2*CHPcost[2,1].value*CHP[i,2,'P']/1000/1000-CHPcost[2,2].value/1000-CHPcost[2,5].value*CHP[i,2,'H']/1000/1000
            LagrangeMatrix_CHP_P[i-1,2] = GNodeCHPeq[i,17]/CHPPeff/GasHV+ENodePeq[i,12] - 2*CHP[i,3,'P']*CHPOutputLimit[i,3]  + CHPEfficiencyeq2[i,3]*CHPHP -2*CHPcost[3,1].value*CHP[i,3,'P']/1000/1000-CHPcost[3,2].value/1000-CHPcost[3,5].value*CHP[i,3,'H']/1000/1000
            LagrangeMatrix_CHP_P[i-1,3] = GNodeCHPeq[i,27]/CHPPeff/GasHV+ENodePeq[i,5] - 2*CHP[i,4,'P']*CHPOutputLimit[i,4]  + CHPEfficiencyeq2[i,4]*CHPHP -2*CHPcost[4,1].value*CHP[i,4,'P']/1000/1000-CHPcost[4,2].value/1000-CHPcost[4,5].value*CHP[i,4,'H']/1000/1000
            LagrangeMatrix_CHP_P[i-1,4] = GNodeCHPeq[i,35]/CHPPeff/GasHV+ENodePeq[i,10] - 2*CHP[i,5,'P']*CHPOutputLimit[i,5]  + CHPEfficiencyeq2[i,5]*CHPHP -2*CHPcost[5,1].value*CHP[i,5,'P']/1000/1000-CHPcost[5,2].value/1000-CHPcost[5,5].value*CHP[i,5,'H']/1000/1000
            LagrangeMatrix_CHP_P[i-1,5] = GNodeCHPeq[i,24]/CHPPeff/GasHV+ENodePeq[i,1] - 2*CHP[i,6,'P']*CHPOutputLimit[i,6]  + CHPEfficiencyeq2[i,6]*CHPHP -2*CHPcost[6,1].value*CHP[i,6,'P']/1000/1000-CHPcost[6,2].value/1000-CHPcost[6,5].value*CHP[i,6,'H']/1000/1000
            LagrangeMatrix_CHP_P[i-1,6] = GNodeCHPeq[i,22]/CHPPeff/GasHV+ENodePeq[i,4] - 2*CHP[i,7,'P']*CHPOutputLimit[i,7]  + CHPEfficiencyeq2[i,7]*CHPHP -2*CHPcost[7,1].value*CHP[i,7,'P']/1000/1000-CHPcost[7,2].value/1000-CHPcost[7,5].value*CHP[i,7,'H']/1000/1000
            LagrangeMatrix_CHP_P[i-1,7] = GNodeCHPeq[i,21]/CHPPeff/GasHV+ENodePeq[i,6] - 2*CHP[i,8,'P']*CHPOutputLimit[i,8]  + CHPEfficiencyeq2[i,8]*CHPHP -2*CHPcost[8,1].value*CHP[i,8,'P']/1000/1000-CHPcost[8,2].value/1000-CHPcost[8,5].value*CHP[i,8,'H']/1000/1000
        
        #deltaL/CHP(Q)
        LagrangeMatrix_CHP_Q = np.zeros((T,CHPnum))
        for i in range(1,T+1):
            LagrangeMatrix_CHP_Q[i-1,0] = ENodeQeq[i,13] - 2*CHP[i,1,'Q']*CHPOutputLimit[i,1] 
            LagrangeMatrix_CHP_Q[i-1,1] = ENodeQeq[i,14] - 2*CHP[i,2,'Q']*CHPOutputLimit[i,2] 
            LagrangeMatrix_CHP_Q[i-1,2] = ENodeQeq[i,12] - 2*CHP[i,3,'Q']*CHPOutputLimit[i,3] 
            LagrangeMatrix_CHP_Q[i-1,3] = ENodeQeq[i,5] - 2*CHP[i,4,'Q']*CHPOutputLimit[i,4] 
            LagrangeMatrix_CHP_Q[i-1,4] = ENodeQeq[i,10] - 2*CHP[i,5,'Q']*CHPOutputLimit[i,5] 
            LagrangeMatrix_CHP_Q[i-1,5] = ENodeQeq[i,1] - 2*CHP[i,6,'Q']*CHPOutputLimit[i,6] 
            LagrangeMatrix_CHP_Q[i-1,6] = ENodeQeq[i,4] - 2*CHP[i,7,'Q']*CHPOutputLimit[i,7] 
            LagrangeMatrix_CHP_Q[i-1,7] = ENodeQeq[i,6] - 2*CHP[i,8,'Q']*CHPOutputLimit[i,8] 

        #deltaL/CHP(H)
        LagrangeMatrix_CHP_H = np.zeros((T,CHPnum))
        for i in range(1,T+1):
            LagrangeMatrix_CHP_H[i-1,0] = HNodeCHPeq[i,35] - CHPEfficiencyeq2[i,1] + 2*CHPcost[1,3].value*CHP[i,1,'H']/1000/1000+CHPcost[1,4].value/1000+CHPcost[1,5].value*CHP[i,1,'P']/1000/1000 
            LagrangeMatrix_CHP_H[i-1,1] = HNodeCHPeq[i,36] - CHPEfficiencyeq2[i,2] + 2*CHPcost[2,3].value*CHP[i,2,'H']/1000/1000+CHPcost[2,4].value/1000+CHPcost[2,5].value*CHP[i,2,'P']/1000/1000 
            LagrangeMatrix_CHP_H[i-1,2] = HNodeCHPeq[i,5] - CHPEfficiencyeq2[i,3] +2*CHPcost[3,3].value*CHP[i,3,'H']/1000/1000+CHPcost[3,4].value/1000+CHPcost[3,5].value*CHP[i,3,'P']/1000/1000 
            LagrangeMatrix_CHP_H[i-1,3] = HNodeCHPeq[i,15] - CHPEfficiencyeq2[i,4]+2*CHPcost[4,3].value*CHP[i,4,'H']/1000/1000+CHPcost[4,4].value/1000+CHPcost[4,5].value*CHP[i,4,'P']/1000/1000 
            LagrangeMatrix_CHP_H[i-1,4] = HNodeCHPeq[i,3] - CHPEfficiencyeq2[i,5] +2*CHPcost[5,3].value*CHP[i,5,'H']/1000/1000+CHPcost[5,4].value/1000+CHPcost[5,5].value*CHP[i,5,'P']/1000/1000 
            LagrangeMatrix_CHP_H[i-1,5] = HNodeCHPeq[i,16] - CHPEfficiencyeq2[i,6]+2*CHPcost[6,3].value*CHP[i,6,'H']/1000/1000+CHPcost[6,4].value/1000+CHPcost[6,5].value*CHP[i,6,'P']/1000/1000 
            LagrangeMatrix_CHP_H[i-1,6] = HNodeCHPeq[i,17] - CHPEfficiencyeq2[i,7] +2*CHPcost[7,3].value*CHP[i,7,'H']/1000/1000+CHPcost[7,4].value/1000+CHPcost[7,5].value*CHP[i,7,'P']/1000/1000 
            LagrangeMatrix_CHP_H[i-1,7] = HNodeCHPeq[i,19] - CHPEfficiencyeq2[i,8]+2*CHPcost[8,3].value*CHP[i,8,'H']/1000/1000+CHPcost[8,4].value/1000+CHPcost[8,5].value*CHP[i,8,'P']/1000/1000 
        
        #deltaL/CHP(G)
        #LagrangeMatrix_CHP_G = np.zeros((T,CHPnum))
        #for i in range(1,T+1):
            #LagrangeMatrix_CHP_G[i-1,0] = GNodeCHPeq[i,1] - CHPEfficiencyeq1[i,1]*CHPPeff*GasHV 
            #LagrangeMatrix_CHP_G[i-1,1] = GNodeCHPeq[i,15] - CHPEfficiencyeq1[i,2]*CHPPeff*GasHV
            #LagrangeMatrix_CHP_G[i-1,2] = GNodeCHPeq[i,17] - CHPEfficiencyeq1[i,3]*CHPPeff*GasHV 
            #LagrangeMatrix_CHP_G[i-1,3] = GNodeCHPeq[i,27] - CHPEfficiencyeq1[i,4]*CHPPeff*GasHV
            #LagrangeMatrix_CHP_G[i-1,4] = GNodeCHPeq[i,35] - CHPEfficiencyeq1[i,5]*CHPPeff*GasHV 
            #LagrangeMatrix_CHP_G[i-1,5] = GNodeCHPeq[i,24] - CHPEfficiencyeq1[i,6]*CHPPeff*GasHV
            #LagrangeMatrix_CHP_G[i-1,6] = GNodeCHPeq[i,22] - CHPEfficiencyeq1[i,7]*CHPPeff*GasHV 
            #LagrangeMatrix_CHP_G[i-1,7] = GNodeCHPeq[i,21] - CHPEfficiencyeq1[i,8]*CHPPeff*GasHV
            
        #deltaL/mainGridP
        LagrangeMatrix_mainGridP = np.zeros(T)
        for i in range(1,T+1):
            LagrangeMatrix_mainGridP[i-1] = mainGridPrice[i-1] - ENodePeq[i,15]

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
            LagrangeMatrix_GasBo_H[i-1,0] = HNodeCHPeq[i,36] - GasBoEfficiencyeq1[i,1] - GasBoEfficiencyeq2[i,1] + CHPcost[1,6].value
            LagrangeMatrix_GasBo_H[i-1,1] = HNodeCHPeq[i,35] - GasBoEfficiencyeq1[i,2] - GasBoEfficiencyeq2[i,2] + CHPcost[2,6].value
            LagrangeMatrix_GasBo_H[i-1,2] = HNodeCHPeq[i,5] - GasBoEfficiencyeq1[i,3] - GasBoEfficiencyeq2[i,3] + CHPcost[3,6].value
            LagrangeMatrix_GasBo_H[i-1,3] = HNodeCHPeq[i,15] - GasBoEfficiencyeq1[i,4] - GasBoEfficiencyeq2[i,4] + CHPcost[4,6].value
            LagrangeMatrix_GasBo_H[i-1,4] = HNodeCHPeq[i,3] - GasBoEfficiencyeq1[i,5] - GasBoEfficiencyeq2[i,5] + CHPcost[5,6].value
            LagrangeMatrix_GasBo_H[i-1,5] = HNodeCHPeq[i,16] - GasBoEfficiencyeq1[i,6] - GasBoEfficiencyeq2[i,6] + CHPcost[6,6].value
            LagrangeMatrix_GasBo_H[i-1,6] = HNodeCHPeq[i,17] - GasBoEfficiencyeq1[i,7] - GasBoEfficiencyeq2[i,7] + CHPcost[7,6].value
            LagrangeMatrix_GasBo_H[i-1,7] = HNodeCHPeq[i,19] - GasBoEfficiencyeq1[i,8] - GasBoEfficiencyeq2[i,8] + CHPcost[8,6].value
        
        #deltaL/deltaGasBo(G)
        LagrangeMatrix_GasBo_G = np.zeros((T,CHPnum))
        for i in range(1,T+1):
            LagrangeMatrix_GasBo_G[i-1,0] = -GNodeCHPeq[i,1] + GasBoEfficiencyeq1[i,1]*GasHV*GasBoeff
            LagrangeMatrix_GasBo_G[i-1,1] = -GNodeCHPeq[i,15] + GasBoEfficiencyeq1[i,2]*GasHV*GasBoeff
            LagrangeMatrix_GasBo_G[i-1,2] = -GNodeCHPeq[i,17] + GasBoEfficiencyeq1[i,3]*GasHV*GasBoeff
            LagrangeMatrix_GasBo_G[i-1,3] = -GNodeCHPeq[i,27] + GasBoEfficiencyeq1[i,4]*GasHV*GasBoeff
            LagrangeMatrix_GasBo_G[i-1,4] = -GNodeCHPeq[i,35] + GasBoEfficiencyeq1[i,5]*GasHV*GasBoeff
            LagrangeMatrix_GasBo_G[i-1,5] = -GNodeCHPeq[i,24] + GasBoEfficiencyeq1[i,6]*GasHV*GasBoeff
            LagrangeMatrix_GasBo_G[i-1,6] = -GNodeCHPeq[i,22] + GasBoEfficiencyeq1[i,7]*GasHV*GasBoeff
            LagrangeMatrix_GasBo_G[i-1,7] = -GNodeCHPeq[i,21] + GasBoEfficiencyeq1[i,8]*GasHV*GasBoeff

        #deltaL/Esto(P)
        LagrangeMatrix_Esto_P = np.zeros((T,CHPnum)) 
        for i in range(1,T+1):
            for j in range(1,CHPnum+1):
                if i==1:
                    LagrangeMatrix_Esto_P[i-1,j-1] = -EstorageStarteqEnd[j]-EstorageInitial[j]+EStoragedata[j,4].value*EstoragePowereq[i+1,j]
                if (i>1)& (i<24):
                    LagrangeMatrix_Esto_P[i-1,j-1] = -EstoragePowereq[i,j]+EstoragePowereq[i+1,j]*EStoragedata[j,4].value
                if i==24:
                    LagrangeMatrix_Esto_P[i-1,j-1] = -EstoragePowereq[i,j] - EstorageStarteqEnd[j]*EStoragedata[j,4].value

        #deltaL/Esto(Pi) 
        LagrangeMatrix_Esto_Pi = np.zeros((T,CHPnum)) 
        for i in range(1,T):
            LagrangeMatrix_Esto_Pi[i-1,0]=ENodePeq[i,13]/EStoragedata[1,3].value-EstoragePowereq[i+1,1]
            LagrangeMatrix_Esto_Pi[i-1,1]=ENodePeq[i,14]/EStoragedata[2,3].value-EstoragePowereq[i+1,2]
            LagrangeMatrix_Esto_Pi[i-1,2]=ENodePeq[i,12]/EStoragedata[3,3].value-EstoragePowereq[i+1,3]
            LagrangeMatrix_Esto_Pi[i-1,3]=ENodePeq[i,5]/EStoragedata[4,3].value-EstoragePowereq[i+1,4]
            LagrangeMatrix_Esto_Pi[i-1,4]=ENodePeq[i,10]/EStoragedata[5,3].value-EstoragePowereq[i+1,5]
            LagrangeMatrix_Esto_Pi[i-1,5]=ENodePeq[i,1]/EStoragedata[6,3].value-EstoragePowereq[i+1,6]
            LagrangeMatrix_Esto_Pi[i-1,6]=ENodePeq[i+1,4]/EStoragedata[7,3].value-EstoragePowereq[i+1,7]
            LagrangeMatrix_Esto_Pi[i-1,7]=ENodePeq[i,6]/EStoragedata[8,3].value-EstoragePowereq[i+1,8]
            LagrangeMatrix_Esto_Pi[23,0]=ENodePeq[1,13]/EStoragedata[1,3].value-EstorageStarteqEnd[1]
            LagrangeMatrix_Esto_Pi[23,1]=ENodePeq[1,14]/EStoragedata[2,3].value-EstorageStarteqEnd[2]
            LagrangeMatrix_Esto_Pi[23,2]=ENodePeq[1,12]/EStoragedata[3,3].value-EstorageStarteqEnd[3]
            LagrangeMatrix_Esto_Pi[23,3]=ENodePeq[1,5]/EStoragedata[4,3].value-EstorageStarteqEnd[4]
            LagrangeMatrix_Esto_Pi[23,4]=ENodePeq[1,10]/EStoragedata[5,3].value-EstorageStarteqEnd[5]
            LagrangeMatrix_Esto_Pi[23,5]=ENodePeq[1,1]/EStoragedata[6,3].value-EstorageStarteqEnd[6]
            LagrangeMatrix_Esto_Pi[23,6]=ENodePeq[1,4]/EStoragedata[7,3].value-EstorageStarteqEnd[7]
            LagrangeMatrix_Esto_Pi[23,7]=ENodePeq[1,6]/EStoragedata[8,3].value-EstorageStarteqEnd[8]
        
        #deltaL/Esto(Po) 
        LagrangeMatrix_Esto_Po = np.zeros((T,CHPnum)) 
        for i in range(1,T):
            LagrangeMatrix_Esto_Po[i-1,0]=ENodePeq[i,13]*EStoragedata[1,3].value-EstoragePowereq[i+1,1]
            LagrangeMatrix_Esto_Po[i-1,1]=ENodePeq[i,14]*EStoragedata[2,3].value-EstoragePowereq[i+1,2]
            LagrangeMatrix_Esto_Po[i-1,2]=ENodePeq[i,12]*EStoragedata[3,3].value-EstoragePowereq[i+1,3]
            LagrangeMatrix_Esto_Po[i-1,3]=ENodePeq[i,5]*EStoragedata[4,3].value-EstoragePowereq[i+1,4]
            LagrangeMatrix_Esto_Po[i-1,4]=ENodePeq[i,10]*EStoragedata[5,3].value-EstoragePowereq[i+1,5]
            LagrangeMatrix_Esto_Po[i-1,5]=ENodePeq[i,1]*EStoragedata[6,3].value-EstoragePowereq[i+1,6]
            LagrangeMatrix_Esto_Po[i-1,6]=ENodePeq[i,4]*EStoragedata[7,3].value-EstoragePowereq[i+1,7]
            LagrangeMatrix_Esto_Po[i-1,7]=ENodePeq[i,6]*EStoragedata[8,3].value-EstoragePowereq[i+1,8]
            LagrangeMatrix_Esto_Po[23,0]=ENodePeq[1,13]*EStoragedata[1,3].value+EstorageStarteqEnd[1]
            LagrangeMatrix_Esto_Po[23,1]=ENodePeq[1,14]*EStoragedata[2,3].value+EstorageStarteqEnd[2]
            LagrangeMatrix_Esto_Po[23,2]=ENodePeq[1,12]*EStoragedata[3,3].value+EstorageStarteqEnd[3]
            LagrangeMatrix_Esto_Po[23,3]=ENodePeq[1,5]*EStoragedata[4,3].value+EstorageStarteqEnd[4]
            LagrangeMatrix_Esto_Po[23,4]=ENodePeq[1,10]*EStoragedata[5,3].value+EstorageStarteqEnd[5]
            LagrangeMatrix_Esto_Po[23,5]=ENodePeq[1,1]*EStoragedata[6,3].value+EstorageStarteqEnd[6]
            LagrangeMatrix_Esto_Po[23,6]=ENodePeq[1,4]*EStoragedata[7,3].value+EstorageStarteqEnd[7]
            LagrangeMatrix_Esto_Po[23,7]=ENodePeq[1,6]*EStoragedata[8,3].value+EstorageStarteqEnd[8]

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
                for k in range(1,HBus.nrows):
                    if HBranch[j,2].value ==k:
                        LagrangeMatrix_TempBranEndS[i-1,j-1] = LagrangeMatrix_TempBranEndS[i-1,j-1] - HNodeMixLoadS[i,k]*MassFlowS[i,j] 
        
        #deltaL/deltaTempBusR
        LagrangeMatrix_TempBusR = np.zeros((T,HBus.nrows-1))
        for i in range(1,T+1):
            for j in range(1,HBus.nrows):
                if HBus[j,1].value >= 1:
                    LagrangeMatrix_TempBusR[i-1,j-1] = Cp*MassFlowCHP[i,HBus[j,1].value]*HNodeCHPeq[i,j]
                for k in range(1,HBranch.nrows):
                    if HBranch[k,2].value == j:
                        LagrangeMatrix_TempBusR[i-1,j-1] = LagrangeMatrix_TempBusR[i-1,j-1] + HBranchTempLossR[i,k]*np.exp(-HBranch[k,6].value*HBranch[k,3].value/Cp/1000/MassFlowR[i,k])
                if HBus[j,1].value <= 0:
                    LagrangeMatrix_TempBusR[i-1,j-1] = LagrangeMatrix_TempBusR[i-1,j-1] + HNodeMixLoadR[i,j]*(sum(MassFlowR[i,k] for k in range(1,HBranch.nrows) if (HBranch[k,2].value == j)))
                if HBus[j,1].value >= 1:
                    LagrangeMatrix_TempBusR[i-1,j-1] = LagrangeMatrix_TempBusR[i-1,j-1] + MassFlowCHP[i,HBus[j,1].value]*HNodeMixCHPR[i,j]
        
        #deltaL/deltaTempBranEndR
        LagrangeMatrix_TempBranEndR = np.zeros((T,HBranch.nrows-1))
        EHnum=np.array([3,5,15,16,17,19,35,36])
        for i in range(1,T+1):
            for j in range(1,HBranch.nrows):
                LagrangeMatrix_TempBranEndR[i-1,j-1] = - HBranchTempLossR[i,j]
                for k in range(1,HBus.nrows):
                    if (HBranch[j,1].value ==k)&(np.isin(k,EHnum,invert=True)):
                        LagrangeMatrix_TempBranEndR[i-1,j-1] = LagrangeMatrix_TempBranEndR[i-1,j-1] - HNodeMixLoadR[i,k]*MassFlowR[i,j]
                    if (HBranch[j,1].value ==k)&(np.isin(k,EHnum,invert=False)):
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
        
        #deltaL/Hsto(H)
        LagrangeMatrix_Hsto_H = np.zeros((T,CHPnum)) 
        for i in range(1,T+1):
            for j in range(1,CHPnum+1):
                if i==1:
                    LagrangeMatrix_Hsto_H[i-1,j-1] = -HstorageStarteqEnd[j]-HstorageInitial[j]+HStoragedata[j,4].value*HstoragePowereq[i+1,j]
                if (i>1)& (i<24):
                    LagrangeMatrix_Hsto_H[i-1,j-1] = -HstoragePowereq[i,j]+HstoragePowereq[i+1,j]*HStoragedata[j,4].value
                if i==24:
                    LagrangeMatrix_Hsto_H[i-1,j-1] = -HstoragePowereq[i,j] - HstorageStarteqEnd[j]*HStoragedata[j,4].value
        
        #deltaL/Hsto(Hi) 
        LagrangeMatrix_Hsto_Hi = np.zeros((T,CHPnum)) 
        for i in range(1,T):
            LagrangeMatrix_Hsto_Hi[i-1,0]=HNodeCHPeq[i,36]/HStoragedata[1,3].value-HstoragePowereq[i+1,1]
            LagrangeMatrix_Hsto_Hi[i-1,1]=HNodeCHPeq[i,35]/HStoragedata[2,3].value-HstoragePowereq[i+1,2]
            LagrangeMatrix_Hsto_Hi[i-1,2]=HNodeCHPeq[i,5]/HStoragedata[3,3].value-HstoragePowereq[i+1,3]
            LagrangeMatrix_Hsto_Hi[i-1,3]=HNodeCHPeq[i,15]/HStoragedata[4,3].value-HstoragePowereq[i+1,4]
            LagrangeMatrix_Hsto_Hi[i-1,4]=HNodeCHPeq[i,3]/HStoragedata[5,3].value-HstoragePowereq[i+1,5]
            LagrangeMatrix_Hsto_Hi[i-1,5]=HNodeCHPeq[i,16]/HStoragedata[6,3].value-HstoragePowereq[i+1,6]
            LagrangeMatrix_Hsto_Hi[i-1,6]=HNodeCHPeq[i,17]/HStoragedata[7,3].value-HstoragePowereq[i+1,7]
            LagrangeMatrix_Hsto_Hi[i-1,7]=HNodeCHPeq[i,19]/HStoragedata[8,3].value-HstoragePowereq[i+1,8]
            LagrangeMatrix_Hsto_Hi[23,0]=HNodeCHPeq[1,36]/HStoragedata[1,3].value-HstorageStarteqEnd[1]
            LagrangeMatrix_Hsto_Hi[23,1]=HNodeCHPeq[1,35]/HStoragedata[2,3].value-HstorageStarteqEnd[2]
            LagrangeMatrix_Hsto_Hi[23,2]=HNodeCHPeq[1,5]/HStoragedata[3,3].value-HstorageStarteqEnd[3]
            LagrangeMatrix_Hsto_Hi[23,3]=HNodeCHPeq[1,15]/HStoragedata[4,3].value-HstorageStarteqEnd[4]
            LagrangeMatrix_Hsto_Hi[23,4]=HNodeCHPeq[1,3]/HStoragedata[5,3].value-HstorageStarteqEnd[5]
            LagrangeMatrix_Hsto_Hi[23,5]=HNodeCHPeq[1,16]/HStoragedata[6,3].value-HstorageStarteqEnd[6]
            LagrangeMatrix_Hsto_Hi[23,6]=HNodeCHPeq[1,17]/HStoragedata[7,3].value-HstorageStarteqEnd[7]
            LagrangeMatrix_Hsto_Hi[23,7]=HNodeCHPeq[1,19]/HStoragedata[8,3].value -HstorageStarteqEnd[8]
        
        #deltaL/Hsto(Ho) 
        LagrangeMatrix_Hsto_Ho = np.zeros((T,CHPnum)) 
        for i in range(1,T):
            LagrangeMatrix_Hsto_Ho[i-1,0]=HNodeCHPeq[i,36]*HStoragedata[1,3].value-HstoragePowereq[i+1,1]
            LagrangeMatrix_Hsto_Ho[i-1,1]=HNodeCHPeq[i,35]*HStoragedata[2,3].value-HstoragePowereq[i+1,2]
            LagrangeMatrix_Hsto_Ho[i-1,2]=HNodeCHPeq[i,5]*HStoragedata[3,3].value-HstoragePowereq[i+1,3]
            LagrangeMatrix_Hsto_Ho[i-1,3]=HNodeCHPeq[i,15]*HStoragedata[4,3].value-HstoragePowereq[i+1,4]
            LagrangeMatrix_Hsto_Ho[i-1,4]=HNodeCHPeq[i,3]*HStoragedata[5,3].value-HstoragePowereq[i+1,5]
            LagrangeMatrix_Hsto_Ho[i-1,5]=HNodeCHPeq[i,16]*HStoragedata[6,3].value-HstoragePowereq[i+1,6]
            LagrangeMatrix_Hsto_Ho[i-1,6]=HNodeCHPeq[i,17]*HStoragedata[7,3].value-HstoragePowereq[i+1,7]
            LagrangeMatrix_Hsto_Ho[i-1,7]=HNodeCHPeq[i,19]*HStoragedata[8,3].value-HstoragePowereq[i+1,8]
            LagrangeMatrix_Hsto_Ho[23,0]=HNodeCHPeq[1,36]*HStoragedata[1,3].value+HstorageStarteqEnd[1]
            LagrangeMatrix_Hsto_Ho[23,1]=HNodeCHPeq[1,35]*HStoragedata[2,3].value+HstorageStarteqEnd[2]
            LagrangeMatrix_Hsto_Ho[23,2]=HNodeCHPeq[1,5]*HStoragedata[3,3].value+HstorageStarteqEnd[3]
            LagrangeMatrix_Hsto_Ho[23,3]=HNodeCHPeq[1,15]*HStoragedata[4,3].value+HstorageStarteqEnd[4]
            LagrangeMatrix_Hsto_Ho[23,4]=HNodeCHPeq[1,3]*HStoragedata[5,3].value+HstorageStarteqEnd[5]
            LagrangeMatrix_Hsto_Ho[23,5]=HNodeCHPeq[1,16]*HStoragedata[6,3].value+HstorageStarteqEnd[6]
            LagrangeMatrix_Hsto_Ho[23,6]=HNodeCHPeq[1,17]*HStoragedata[7,3].value+HstorageStarteqEnd[7]
            LagrangeMatrix_Hsto_Ho[23,7]=HNodeCHPeq[1,19]*HStoragedata[8,3].value+HstorageStarteqEnd[8]
        
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
            LagrangeMatrix_GasSource[i-1] = GSlackBuseq[i,37]

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
        Flag_E9 = np.zeros((T,CHPnum))
        Flag_E10 = np.zeros(CHPnum)
        Flag_E11 = np.zeros(CHPnum)
        for i in range(1,T+1):
            for j in range(1,EBus.nrows):
                if EBus[j,1].value == 0:   #ENodePLoadeq
                    Flag_E1[i-1,j-1] = Flag_E1[i-1,j-1] - EBus[j,2].value*EloadCurve[i-1]
                if EBus[j,1].value >= 1: #ENodePCHPeq
                    Flag_E1[i-1,j-1] = Flag_E1[i-1,j-1] + CHP[i,int(EBus[j,1].value),'P']+Esto[i,int(EBus[j,1].value),'Po']*EStoragedata[int(EBus[j,1].value),3].value-Esto[i,int(EBus[j,1].value),'Pi']/EStoragedata[int(EBus[j,1].value),3].value - EBus[j,2].value*EloadCurve[i-1]
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
        
        #EstoragePowereq
        for i in range(2,T+1):
            for j in range(1,CHPnum+1):
                Flag_E9[i-1,j-1]= Esto[i,j,'P'] - Esto[i-1,j,'P']*EStoragedata[j,4].value-Esto[i-1,j,'Pi']+Esto[i-1,j,'Po']
        #EstorageStarteqEnd
        for i in range(1,CHPnum+1):
            Flag_E10[i-1]=Esto[1,i,'P']-Esto[24,i,'P']*EStoragedata[i,4].value-Esto[24,i,'Pi']+Esto[24,i,'Po']
        #EstorageInitial
        for i in range(1,CHPnum+1):
            Flag_E11[i-1]=Esto[1,i,'P']-EStoragedata[i,2].value/2
        
        
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
        Flag_H11 = np.zeros((T,CHPnum))
        Flag_H12 = np.zeros(CHPnum)
        Flag_H13 = np.zeros(CHPnum)
        #HNodeLoadeq
        for i in range(1,T+1):
            for j in range(1,HBus.nrows):
                if HBus[j,2].value != 0:
                    Flag_H1[i-1,j-1] = Flag_H1[i-1,j-1] + HBus[j,2].value*HloadCurve[i-1] - Cp*MassFlowL[i,j]*(TempBusS[i,j]-TempLoadout[i,j])
            
        for i in range(1,T+1):
            for j in range(1,HBus.nrows):
                if HBus[j,1].value >= 1:
                    #HNodeCHPeq
                    Flag_H2[i-1,j-1] = Flag_H2[i-1,j-1] + CHP[i,int(HBus[j,1].value),'H'] + GasBo[i,int(HBus[j,1].value),'H']+Hsto[i,int(HBus[j,1].value),'Ho']*HStoragedata[int(HBus[j,1].value),3].value-Hsto[i,int(HBus[j,1].value),'Hi']/HStoragedata[int(HBus[j,1].value),3].value - Cp*MassFlowCHP[i,int(HBus[j,1].value)]*(TCHPout-TempBusR[i,j])
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
        #HstoragePowereq
        for i in range(2,T+1):
            for j in range(1,CHPnum+1):
                Flag_H11[i-1,j-1]= Hsto[i,j,'H'] - Hsto[i-1,j,'H']*HStoragedata[j,4].value-Hsto[i,j,'Hi']+Hsto[i,j,'Ho']
        #HstorageStarteqEnd
        for i in range(1,CHPnum+1):
            Flag_H12[i-1]=Hsto[1,i,'H']-Hsto[24,i,'H']*HStoragedata[i,4].value-Hsto[24,i,'Hi']+Hsto[24,i,'Ho']
        #HstorageInitial
        for i in range(1,CHPnum+1):
            Flag_H13[i-1]=Hsto[1,i,'H']-HStoragedata[i,2].value/2

        #gas validate
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
                    Flag_G1[i-1,j-1] =  - GasBo[i,int(GBus[j,1].value),'G']-CHP[i,int(GBus[j,1].value),'P']/CHPPeff/GasHV
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
        
        #CHP validate
        #Flag_CHP1 = np.zeros((T,CHPnum))
        Flag_CHP2 = np.zeros((T,CHPnum))
        Flag_CHP3 = np.zeros((T,CHPnum))
        Flag_CHP4 = np.zeros((T,CHPnum))
        #for i in range(1,T+1):
        #    for j in range(1,CHPnum+1):
        #        Flag_CHP1[i-1,j-1]=CHP[i,j,'P']-CHPPeff*CHP[i,j,'G']*GasHV
        for i in range(1,T+1):
            for j in range(1,CHPnum+1):
                Flag_CHP2[i-1,j-1]=(CHP[i,j,'P']*CHPHP-CHPPeff*CHP[i,j,'H'])*CHPEfficiencyeq2[i,j]
        for i in range(1,T+1):
            for j in range(1,CHPnum+1):
                Flag_CHP3[i-1,j-1]=GasBo[i,j,'G']*GasHV*GasBoeff-GasBo[i,j,'H']
        for i in range(1,T+1):
            for j in range(1,CHPnum+1):
                Flag_CHP4[i-1,j-1]=(GasBo[i,j,'H']-GasBoMax[j-1]*1000)*GasBoEfficiencyeq2[i,j]

        Flag_L=np.max([np.max(np.abs(LagrangeMatrix_mainGridP)),np.max(np.abs(LagrangeMatrix_mainGridQ)),np.max(np.abs(LagrangeMatrix_Pij)),np.max(np.abs(LagrangeMatrix_Qij)),\
            np.max(np.abs(LagrangeMatrix_Vi)),np.max(np.abs(LagrangeMatrix_Iij)),np.max(np.abs(LagrangeMatrix_CHP_P)),np.max(np.abs(LagrangeMatrix_CHP_Q)),\
                np.max(np.abs(LagrangeMatrix_CHP_H)),np.max(np.abs(LagrangeMatrix_GasBo_H)),np.max(np.abs(LagrangeMatrix_GasBo_G)),\
                    np.max(np.abs(LagrangeMatrix_TempBusS)),np.max(np.abs(LagrangeMatrix_TempBranEndS)),np.max(np.abs(LagrangeMatrix_TempBusR)),np.max(np.abs(LagrangeMatrix_TempBranEndR)),\
                        np.max(np.abs(LagrangeMatrix_TempLoadout)),np.max(np.abs(LagrangeMatrix_GasFlow)),np.max(np.abs(LagrangeMatrix_GasPressure))])
        Flageq=np.max([np.max(np.abs(Flag_E1)),np.max(np.abs(Flag_E2)),np.max(np.abs(Flag_E3)),np.max(np.abs(Flag_E4)),np.max(np.abs(Flag_E5)),np.max(np.abs(Flag_E6)),np.max(np.abs(Flag_E7)),\
            np.max(np.abs(Flag_E8)),np.max(np.abs(Flag_E9)),np.max(np.abs(Flag_E10)),np.max(np.abs(Flag_E11)),np.max(np.abs(Flag_H1)),np.max(np.abs(Flag_H2)),np.max(np.abs(Flag_H3)),\
                np.max(np.abs(Flag_H4)),np.max(np.abs(Flag_H5)),np.max(np.abs(Flag_H6)),np.max(np.abs(Flag_H7)),np.max(np.abs(Flag_H8)),np.max(np.abs(Flag_H9)),np.max(np.abs(Flag_H10)),\
                    np.max(np.abs(Flag_H11)),np.max(np.abs(Flag_H12)),np.max(np.abs(Flag_H13)),np.max(np.abs(Flag_G1)),np.max(np.abs(Flag_G2)),np.max(np.abs(Flag_G3))])

        Objective=0
        for i in range(1,T+1):
            Objective = Objective+mainGridP[i]*mainGridPrice[i-1]
        for i in range(1,T+1):
            for j in range(1,CHPnum+1):
                Objective=Objective+CHPcost[j,1].value*CHP[i,j,'P']*CHP[i,j,'P']/1000/1000+CHPcost[j,2].value*CHP[i,j,'P']/1000+CHPcost[j,3].value*CHP[i,j,'H']*CHP[i,j,'H']/1000/1000+CHPcost[j,4].value*CHP[i,j,'H']/1000+CHPcost[j,5].value*CHP[i,j,'H']*CHP[i,j,'P']/1000/1000+CHPcost[j,6].value*GasBo[i,j,'H']

        if Flag_L+Flageq <= 0.05:
            Flag_result=1
        if Flag_L+Flageq > 0.05:
            Flag_result=0
        return (Flag_result,Objective)
    # 计算错误结果把1136行
    # ObjFunc                                            ..obj=E= sum(St,mainGridP(St))+sum(St,GasSource(St));
    # 更改为
    #ObjFunc                                            ..obj=E= sum(St,GasSource(St));
    def get_model_text(self,conopt="CONOPT4",error=False):
        return f'''
Sets
       SEBus             'Set of EBus row' /1*15/
       SEBran            'Set of EBranch row' /1*14/
       SCHP              'Set of CHP'   /1*8/
       SCHPj             'Set of CHP column'/P,Q,H,G/
       GasBoj            'Set of Gasboiler column' /H,G/
       SEStoj             'Set of electric storage' /P,Pi,Po/
       SHStoj             'Set of electric storage' /H,Hi,Ho/
       SHBus             'Set of HBus row'/1*36/
       SHBranch          'Set of HBranch row'/1*35/
       SGBus             'Set of GBus row'   /1*37/
       SGBranch          'Set of GBranch row' /1*36/
       St                'Set of time period' /1*24/
       ;
Parameters
CHPMax(SCHP)   'CHP maximum output, kW'
/1   1000
 2   1000
 3   1000
 4   1000
 5   1000
 6   1000
 7   1000
 8   1000/
GasBoMax(SCHP) 'Gasboiler maximum output, MW'
/1   6
 2   6
 3   1
 4   1
 5   1
 6   1
 7   1
 8   1/
Cp        'Specific heat capacity of water,kJ/(kg.C)'     /4.2/
TCHPout   'Temperature output at CHP'                     /85/
Toutside  'Temperature outside'                           /15/
MassFlowC 'MassFlow constant at each load node kg/s'      /20/
GasHV     'Heat value of gas is 39MJ/m3 1m3/h=390/36kW'   /10.833/
CHPPeff   'CHP electric power efficiency'                 /0.277/
CHPHP     'CHP heat and electric ratio 1/0.66'            /1.5/
GasBoeff  'Gas boiler efficiency'                         /0.792/
;
Table CHPcost(SCHP,*)      'CHP: aP^2+bP+cH^2+dH+ePH, $,MW  GasBoiler: fH  comes from Zhang Jinhui'
            a        b         c        d           e         f     
   1        0.0575   10.6     0.027    0.92      0.012    0.001
   2        0.0590   12.5     0.030    1.28      0.015    0.001
   3        0.0835   22.6     0.035    2.36      0.032    0.001
   4        0.0865   21.4     0.042    3.23      0.026    0.001
   5        0.0865   21.4     0.042    3.23      0.026    0.001   
   6        0.1035   41.8     0.072    7.80      0.052    0.001   
   7        0.1035   41.8     0.072    7.80      0.052    0.001   
   8        0.1035   41.8     0.072    7.80      0.052    0.001
   ;

Table EStoragedata(SCHP,*)
            ramp       Pmax    Conver      loss      
   1          60        300       0.9      0.95     
   2          60        300       0.9      0.95     
   3          60        300       0.9      0.95     
   4          60        300       0.9      0.95     
   5          60        300       0.9      0.95     
   6          60        300       0.9      0.95     
   7          60        300       0.9      0.95     
   8          60        300       0.9      0.95
   ;
Table HStoragedata(SCHP,*)
            ramp       Pmax    Conver      loss      
   1          50        300       0.9      0.95     
   2          50        300       0.9      0.95     
   3          50        300       0.9      0.95     
   4          50        300       0.9      0.95     
   5          50        300       0.9      0.95     
   6          50        300       0.9      0.95     
   7          50        300       0.9      0.95     
   8          50        300       0.9      0.95
   ;
   
Table EBus(SEBus, *)   'EBus data(PQ in kW)'
           Type       P       Q
   1          6     121      44
   2          0     246      89
   3          0      55      20
   4          7      89      32
   5          4      65      24
   6          8      97      35
   7          0      86      31
   8          0     265      96
   9          0      36      13
   10         5      50      18
   11         0     110      40
   12         3      31      11
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
  3            5      320
  4            0      258
  5            3      201
  6            0        2
  7            0      542
  8            0      194
  9            0       61
  10           0      201
  11           0      330
  12           0       34
  13           0       61
  14           0      725
  15           4       36
  16           6       36
  17           7      602
  18           0      209
  19           8      191
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
*4 8 22 28 31 32changed
Table HBranch(SHBranch,*)   'HBranch data at supply side'
             Fbus        Tbus        Length        Diameter        Roughness        Coefficient
  1             1          21            40          0.2191           0.0004              0.455
  2            21           2            20          0.1683           0.0004              0.367
  3            21          22            70          0.2191           0.0004              0.455
  4             3          22            20          0.1397           0.0004              0.367
  5            22          23            70          0.2191           0.0004              0.455
  6            23           4            20          0.0889           0.0004              0.327
  7            23          24            70          0.2191           0.0004              0.455
  8             5          24            20          0.1143           0.0004              0.321
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
  22           15          29            20          0.1683           0.0004              0.367
  23           27          29            40          0.1683           0.0004              0.367
  24           31          27            20          0.1683           0.0004              0.367
  25           31          18            20          0.0889           0.0004              0.327
  26           27          30            40          0.0889           0.0004              0.327
  27           30          14            40          0.0889           0.0004              0.327
  28           16          30            40          0.0424           0.0004               0.21
  29           32          31            20          0.1683           0.0004              0.367
  30           33          32            20          0.2191           0.0004              0.455
  31           17          33            40          0.0889           0.0004              0.327
  32           19          20           200          0.0761           0.0004              0.278
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
  17            3
  18            0
  19            0
  20            0
  21            8
  22            7
  23            0
  24            6
  25            0
  26            0
  27            4
  28            0
  29            0
  30            0
  31            0
  32            0
  33            0
  34            0
  35            5
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
mainGridPrice(St)/1 0.012,2 0.012,3 0.010,4 0.011,5 0.009,6 0.010,7 0.030,8 0.060,9 0.050,10 0.045,11 0.032,12 0.031,13 0.015,14 0.032,15 0.035,16 0.020,17 0.058,18 0.050,19 0.047,20 0.012,21 0.011,22 0.031,23 0.009,24 0.010/
ELoadCurve(St) /1 0.78,2 0.77,3 0.76,4 0.79,5 0.80,6 0.83,7 0.84,8 0.86,9 0.82,10 0.85,11 0.87,12 0.93,13 0.91,14 0.90,15 0.89,16 0.94,17 0.98,18 1,19 0.99,20 0.97,21 0.92,22 0.88,23 0.84,24 0.80/
HLoadCurve(St) /1 0.78,2 0.77,3 0.76,4 0.79,5 0.80,6 0.83,7 0.84,8 0.86,9 0.82,10 0.85,11 0.87,12 0.93,13 0.91,14 0.90,15 0.89,16 0.94,17 0.98,18 1,19 0.99,20 0.97,21 0.92,22 0.88,23 0.84,24 0.80/
GLoadCurve(St) /1 0.78,2 0.77,3 0.76,4 0.79,5 0.80,6 0.83,7 0.84,8 0.86,9 0.82,10 0.85,11 0.87,12 0.93,13 0.91,14 0.90,15 0.89,16 0.94,17 0.98,18 1,19 0.99,20 0.97,21 0.92,22 0.88,23 0.84,24 0.80/;
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
Esto(St,SCHP,SEStoj)         'Electric storage, kW'

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
Hsto(St,SCHP,SHStoj)         'Electric storage, kW'

*gas variables
GasFlow(St,SGBranch)        'Branch gasflow'
GasSource(St)               'Gas supply from source'
GasPressure(St,SGBus)       'Node gas pressure'
;

Vi.lo(St,SEBus)=sqr(0.9*6.6);
Vi.up(St,SEBus)=sqr(1.1*6.6);
Esto.up(St,SCHP,'P')=EStoragedata(SCHP,'Pmax');
Esto.lo(St,SCHP,'P')=EStoragedata(SCHP,'Pmax')/10;
Esto.up(St,SCHP,'Pi')=EStoragedata(SCHP,'ramp');
Esto.up(St,SCHP,'Po')=EStoragedata(SCHP,'ramp');
Hsto.up(St,SCHP,'H')=HStoragedata(SCHP,'Pmax');
Hsto.lo(St,SCHP,'H')=HStoragedata(SCHP,'Pmax')/10;
Hsto.up(St,SCHP,'Hi')=HStoragedata(SCHP,'ramp');
Hsto.up(St,SCHP,'Ho')=HStoragedata(SCHP,'ramp');
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
EstoragePowereq(St,SCHP)         'Estorage power equation'
EstorageStarteqEnd(SCHP)         'Initial power equals end power'
EstorageInitial(SCHP)            'Initialize storage power'

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
HstoragePowereq(St,SCHP)         'Hstorage power equation'
HstorageStarteqEnd(SCHP)         'Initial power equals end power'
HstorageInitial(SCHP)            'Initialize storage power'

*gas restrictions
GNodeLoadeq(St,SGBus)            'Gas node gas load balance'
GNodeCHPeq(St,SGBus)             'CHP node gas load balance'
GSlackBuseq(St,SGBus)            'Gas source load balance'
GWeymoutheq(St,SGBranch)         'Gas Weymouth equation'
GSlackBusPressure(St,SGBus)      'Gas pressure at slack bus is 7bar'

*CHP restrictions
*CHPEfficiencyeq1(St,SCHP)        'CHP efficiency restriction'
CHPEfficiencyeq2(St,SCHP)        'CHP efficiency restriction'
*CHPEfficiencyeq3(St,SCHP)        'CHP efficiency restriction'
*CHPEfficiencyeq4(St,SCHP)        'CHP efficiency restriction'
GasBoEfficiencyeq1(St,SCHP)      'GasBoiler efficiency restriction'
GasBoEfficiencyeq2(St,SCHP)      'GasBoiler efficiency restriction'
;

****************************************************************************************************************************************************************
ObjFunc                                            ..obj=E={"sum(St,-CHP(St,'3','P')-Esto(St,'3','Po')+Esto(St,'3','Pi'))+1.5*sum(St,mainGridP(St)*mainGridPrice(St))+sum(St,sum(SCHP,CHPcost(SCHP,'a')*(CHP(St,SCHP,'P')/1000)**2+CHPcost(SCHP,'b')*CHP(St,SCHP,'P')/1000+CHPcost(SCHP,'c')*(CHP(St,SCHP,'H')/1000)**2+CHPcost(SCHP,'d')*CHP(St,SCHP,'H')/1000+CHPcost(SCHP,'e')*CHP(St,SCHP,'H')/1000*CHP(St,SCHP,'P')/1000+GasBo(St,SCHP,'H')*CHPcost(SCHP,'f')));" if error else "sum(St,mainGridP(St)*mainGridPrice(St))+sum(St,sum(SCHP,CHPcost(SCHP,'a')*(CHP(St,SCHP,'P')/1000)**2+CHPcost(SCHP,'b')*CHP(St,SCHP,'P')/1000+CHPcost(SCHP,'c')*(CHP(St,SCHP,'H')/1000)**2+CHPcost(SCHP,'d')*CHP(St,SCHP,'H')/1000+CHPcost(SCHP,'e')*CHP(St,SCHP,'H')/1000*CHP(St,SCHP,'P')/1000+GasBo(St,SCHP,'H')*CHPcost(SCHP,'f')));"}

*electric restrictions
ENodePLoadeq(St,SEBus)$(EBus(SEBus,'Type') eq 0)      ..sum(SEBran$(EBranch(SEBran,'Tbus') eq ord(SEBus)),(Pij(St,SEBran)-EBranch(SEBran,'r')*Iij(St,SEBran)/1000)) =E= sum(SEBran$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Pij(St,SEBran))+EBus(SEBus,'P')*ELoadCurve(St);
ENodePCHPeq(St,SEBus)$(EBus(SEBus,'Type')  ge 1)      ..sum(SEBran$(EBranch(SEBran,'Tbus') eq ord(SEBus)),(Pij(St,SEBran)-EBranch(SEBran,'r')*Iij(St,SEBran)/1000))+sum(SCHP$(EBus(SEBus,'Type') eq ord (SCHP)),CHP(St,SCHP,'P')+Esto(St,SCHP,'Po')*EStoragedata(SCHP,'Conver')-Esto(St,SCHP,'Pi')/EStoragedata(SCHP,'Conver')) =E= sum(SEBran$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Pij(St,SEBran))+EBus(SEBus,'P')*ELoadCurve(St);
ENodePSlaeq(St,SEBus)$(EBus(SEBus,'Type')  le -1)     ..sum(SEBran$(EBranch(SEBran,'Tbus') eq ord(SEBus)),(Pij(St,SEBran)-EBranch(SEBran,'r')*Iij(St,SEBran)/1000))+mainGridP(St) =E= sum(SEBran$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Pij(St,SEBran))+EBus(SEBus,'P')*ELoadCurve(St);
ENodeQLoadeq(St,SEBus)$(EBus(SEBus,'Type') eq 0)      ..sum(SEBran$(EBranch(SEBran,'Tbus') eq ord(SEBus)),(Qij(St,SEBran)-EBranch(SEBran,'x')*Iij(St,SEBran)/1000)) =E= sum(SEBran$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Qij(St,SEBran))+EBus(SEBus,'Q')*ELoadCurve(St);
ENodeQCHPeq(St,SEBus)$(EBus(SEBus,'Type')  ge 1)      ..sum(SEBran$(EBranch(SEBran,'Tbus') eq ord(SEBus)),(Qij(St,SEBran)-EBranch(SEBran,'x')*Iij(St,SEBran)/1000))+sum(SCHP$(EBus(SEBus,'Type') eq ord (SCHP)),CHP(St,SCHP,'Q')) =E= sum(SEBran$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Qij(St,SEBran))+EBus(SEBus,'Q')*ELoadCurve(St);
ENodeQSlaeq(St,SEBus)$(EBus(SEBus,'Type')  le -1)     ..sum(SEBran$(EBranch(SEBran,'Tbus') eq ord(SEBus)),(Qij(St,SEBran)-EBranch(SEBran,'x')*Iij(St,SEBran)/1000))+mainGridQ(St) =E= sum(SEBran$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Qij(St,SEBran))+EBus(SEBus,'Q')*ELoadCurve(St);
EBranchPeq(St,SEBran)                                 ..sum(SEBus$(EBRanch(SEBran,'Fbus') eq ord(SEBus)),Vi(St,SEBus))-sum(SEBus$(EBRanch(SEBran,'Tbus') eq ord(SEBus)),Vi(St,SEBus))=E= 2/1000*(Pij(St,SEBran)*EBranch(SEBran,'r')+Qij(St,SEBran)*EBranch(SEBran,'x'))-EBranch(SEBran,'z2')*Iij(St,SEBran)/1000/1000;
EBranchPpositive(St,SEBran)                           ..Pij(St,SEBran) =g= Iij(St,SEBran)*EBranch(SEBran,'r')/1000;
EBranchQpositive(St,SEBran)                           ..Qij(St,SEBran) =g= Iij(St,SEBran)*EBranch(SEBran,'x')/1000;
*SOCPeq(St,SEBran)                                     ..sqr(sum(SEBus$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Vi(St,SEBus))+Iij(St,SEBran)) =G= sqr(2*Pij(St,SEBran))+sqr(2*Qij(St,SEBran))+sqr(sum(SEBus$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Vi(St,SEBus))-Iij(St,SEBran));
SOCPeq(St,SEBran)                                     ..sum(SEBus$(EBranch(SEBran,'Fbus') eq ord(SEBus)),Vi(St,SEBus))*Iij(St,SEBran) =e= sqr(Pij(St,SEBran))+sqr(Qij(St,SEBran));
CHPOutputLimit(St,SCHP)                               ..CHP(St,SCHP,'P')**2+CHP(St,SCHP,'Q')**2 =l= CHPMax(SCHP)**2;
SlackBusVoltage(St,SEBus)$(EBus(SEBus,'Type') eq -1)  ..Vi(St,SEBus) =e= sqr(6.6);
EstoragePowereq(St,SCHP)$(ord(St) ge 2)               ..Esto(St,SCHP,'P')=e=Esto(St-1,SCHP,'P')*EStoragedata(SCHP,'loss')+Esto(St-1,SCHP,'Pi')-Esto(St-1,SCHP,'Po');
EstorageStarteqEnd(SCHP)                              ..Esto('1',SCHP,'P')=e=Esto('24',SCHP,'P')*EStoragedata(SCHP,'loss')+Esto('24',SCHP,'Pi')-Esto('24',SCHP,'Po');
EstorageInitial(SCHP)                                 ..Esto('1',SCHP,'P')=e=EStoragedata(SCHP,'Pmax')/2;

*heat restrictions
HNodeLoadeq(St,SHBus)$(HBus(SHBus,'H') ne 0)         ..HBus(SHBus,'H')*HLoadCurve(St) =E= Cp*MassFlowL(St,SHBus)*(TempBusS(St,SHBus)-TempLoadout(St,SHBus));
HNodeCHPeq(St,SHBus)$(HBus(SHBus,'Type') ge 1)       ..sum(SCHP $(HBus(SHBus,'Type') eq ord(SCHP)),(CHP(St,SCHP,'H')+GasBo(St,SCHP,'H')+Hsto(St,SCHP,'Ho')*HStoragedata(SCHP,'Conver')-Hsto(St,SCHP,'Hi')/HStoragedata(SCHP,'Conver')))=E=Cp*sum(SCHP $(HBus(SHBus,'Type') eq ord(SCHP)),MassFlowCHP(St,SCHP))*(TCHPout-TempBusR(St,SHBus));
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
HstoragePowereq(St,SCHP)$(ord(St) ge 2)               ..Hsto(St,SCHP,'H')=e=Hsto(St-1,SCHP,'H')*HStoragedata(SCHP,'loss')+Hsto(St,SCHP,'Hi')-Hsto(St,SCHP,'Ho');
HstorageStarteqEnd(SCHP)                              ..Hsto('1',SCHP,'H')=e=Hsto('24',SCHP,'H')*HStoragedata(SCHP,'loss')+Hsto('24',SCHP,'Hi')-Hsto('24',SCHP,'Ho');
HstorageInitial(SCHP)                                 ..Hsto('1',SCHP,'H')=e=HStoragedata(SCHP,'Pmax')/2
;

*gas restrictions
GNodeLoadeq(St,SGBus)$(GBus(SGBus,'Type') eq 0)      ..sum(SGBranch$(GBranch(SGBranch,'Tbus') eq ord(SGBus)),GasFlow(St,SGBranch))=e=sum(SGBranch$(GBranch(SGBranch,'Fbus') eq ord(SGBus)),GasFlow(St,SGBranch))+GBus(SGBus,'G')/GasHV*GLoadCurve(St);
GNodeCHPeq(St,SGBus)$(GBus(SGBus,'Type') ge 1)       ..sum(SGBranch$(GBranch(SGBranch,'Tbus') eq ord(SGBus)),GasFlow(St,SGBranch))=e=sum(SGBranch$(GBranch(SGBranch,'Fbus') eq ord(SGBus)),GasFlow(St,SGBranch))+sum(SCHP$(GBus(SGBus,'Type') eq ord(SCHP)),(CHP(St,SCHP,'P')/CHPPeff/GasHV+GasBo(St,SCHP,'G')));
GSlackBuseq(St,SGBus)$(GBus(SGBus,'Type') eq -1)     ..sum(SGBranch$(GBranch(SGBranch,'Tbus') eq ord(SGBus)),GasFlow(St,SGBranch))+GasSource(St)=E=sum(SGBranch$(GBranch(SGBranch,'Fbus') eq ord(SGBus)),GasFlow(St,SGBranch))+GBus(SGBus,'G')/GasHV*GLoadCurve(St);
GWeymoutheq(St,SGBranch)                             ..sum(SGBus$(GBranch(SGBranch,'Fbus') eq ord(SGBus)),GasPressure(St,SGBus))-sum(SGBus$(GBranch(SGBranch,'Tbus') eq ord(SGBus)),GasPressure(St,SGBus))=e=K_g(SGBranch)*GasFlow(St,SGBranch)**2;
GSlackBusPressure(St,SGBus)$(GBus(SGBus,'Type') eq -1)..GasPressure(St,SGBus)=e=7;

*CHP restrictions
*CHPEfficiencyeq1(St,SCHP)                            ..CHP(St,SCHP,'P')-CHPcoeff('1','P') =l= -(CHPcoeff('1','P')-CHPcoeff('2','P'))/(CHPcoeff('2','H')-CHPcoeff('1','H'))*(CHP(St,SCHP,'H')-CHPcoeff('1','H'));
*CHPEfficiencyeq2(St,SCHP)                            ..CHP(St,SCHP,'P')-CHPcoeff('2','P') =g= (CHPcoeff('2','P')-CHPcoeff('3','P'))/(CHPcoeff('2','H')-CHPcoeff('3','H'))*(CHP(St,SCHP,'H')-CHPcoeff('2','H'));
*CHPEfficiencyeq3(St,SCHP)                            ..CHP(St,SCHP,'P')-CHPcoeff('3','P') =l= -(CHPcoeff('4','P')-CHPcoeff('3','P'))/(CHPcoeff('3','H')-CHPcoeff('4','H'))*(CHP(St,SCHP,'H')-CHPcoeff('3','H'));
*CHPEfficiencyeq4(St,SCHP)                            ..CHP(St,SCHP,'G')*GasHV*0.88=e=(sqrt(CHP(St,SCHP,'P')**2+CHP(St,SCHP,'Q')**2)+CHP(St,SCHP,'H'));

*CHPEfficiencyeq1(St,SCHP)                            ..CHP(St,SCHP,'P') =e= CHPPeff*CHP(St,SCHP,'G')*GasHV;
CHPEfficiencyeq2(St,SCHP)                            ..CHP(St,SCHP,'P')*CHPHP =e= CHP(St,SCHP,'H');
GasBoEfficiencyeq1(St,SCHP)                          ..GasBo(St,SCHP,'G')*GasHV*GasBoeff =e= GasBo(St,SCHP,'H');
GasBoEfficiencyeq2(St,SCHP)                          ..GasBo(St,SCHP,'H') =l= GasBoMax(SCHP)*1000;

model IES /ALL/;

option NLP={conopt};
*option DNLP=Baron  CONOPT  MINOS SNOPT 

solve IES using NLP minimizing obj; '''
