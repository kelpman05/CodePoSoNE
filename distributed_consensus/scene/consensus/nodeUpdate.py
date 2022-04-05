import logging
from scipy.optimize import minimize
import pandas as pd
import numpy as np
import typing

from ...core.node import Node

L = logging.getLogger(__name__)
class NodeUpdate:
    gasdemand_raw: object
    elecdemand_raw: object
    heatdemand_raw: object
    cooldemand_raw: object
    initial_raw: object
    price_raw: object
    node_raw: object
    branch_raw: object
    NodeInOut_raw: object
    renewerable_energy_raw: object
    logger: logging.Logger
    local: Node
    def __init__(self,demand: str,price_ge: str,initial: str, local: Node):
        super().__init__()
        self.local = local
        self.gasdemand_raw = pd.read_excel(demand, 'GasDemand')
        self.elecdemand_raw = pd.read_excel(demand, 'ElecDemand')
        self.heatdemand_raw = pd.read_excel(demand, 'HeatDemand')
        self.cooldemand_raw = pd.read_excel(demand, 'CoolDemand')

        self.price_raw = pd.read_excel(price_ge, 'Sheet1')

        self.initial_raw = pd.read_excel(initial,'Sheet1')

        self.node_raw = pd.read_excel(local.hub, 'node')
        self.branch_raw = pd.read_excel(local.hub, 'branch')
        self.NodeInOut_raw = pd.read_excel(local.hub, 'NodeInOut')
        self.renewerable_energy_raw = pd.read_excel(local.hub, 'Renewable_Energy')
        self.logger = L.getChild(f'{self.__class__.__name__}-{self.local.id}')
    #输入为两个三元组，分别为上一轮迭代的各能源价格与更新后的价格
    def delegate_checkEnd(self,gp1,ep1,hp1, gp2, ep2, hp2):
        flag_end = 0
        eps = 1e-3
        norm = ((gp2-gp1)**2 + (ep2-ep1)**2 + (hp2[0]-hp1[0])**2 + (hp2[1]-hp1[1])**2 + (hp2[2]-hp1[2])**2)**0.5

        self.logger.warning(f'pre data {(gp1,ep1,hp1)},next data {(gp2,ep2,hp2)}')
        self.logger.warning(f'norm {norm},eps {eps}')
        if norm < eps:
            flag_end = 1
        else:
            flag_end = 0
        return flag_end

    #普通节点根据代表发来价格，更新自身多能源需求量
    #输入为三元组，即三个价格，分别为气价、电价、热价：(gp, ep, hp)
    #输出为四元组，即本普通节点（微网）在该价格下的各能源的最优需求量，分别为气需求、电需求、热需求：(gd, ed, hd)，以及此时的最低成本cost_min
    def normal_node_update(self,gp,ep,hp):
        node = self.node_raw
        branch = self.branch_raw
        NodeInOut = self.NodeInOut_raw
        renewerable_energy_raw = self.renewerable_energy_raw
        #时段12负荷（目前仿真只做时段12，其他时段原理相同）
        ##特别说明：第一个参数0表示微网1，微网2,3...依次类推##
        gasdemand =  self.gasdemand_raw.loc[self.local.id-1, 'T12']
        elecdemand = self.elecdemand_raw.loc[self.local.id-1, 'T12']
        heatdemand = self.heatdemand_raw.loc[self.local.id-1, 'T12']
        cooldemand = self.cooldemand_raw.loc[self.local.id-1, 'T12']
        #电厂成本
        plant_node = node.loc[node['节点类型'] == 14]['节点序号'].values[0]
        plant_b = node.loc[plant_node - 1, 'b']
        plant_c = node.loc[plant_node - 1, 'c']
        if (np.isnan(plant_b)):
            plant_b = 0
        if (np.isnan(plant_c)):
            plant_c = 0

        #单输入单输出设备拓扑信息
        SS_row = node.loc[(node['节点类型'] == 4) | (node['节点类型'] == 5) | (node['节点类型'] == 6) | (node['节点类型'] == 7)]['节点序号'].values
        SS_inbran = NodeInOut.loc[SS_row-1, 'in'].values
        SS_outbran = NodeInOut.loc[SS_row-1, 'out1'].values

        #单输入多输出设备拓扑信息
        SM_row = node.loc[(node['节点类型'] == 1) | (node['节点类型'] == 2) | (node['节点类型'] == 3) | (node['节点类型'] == 8)]['节点序号'].values
        SM_inbran = NodeInOut.loc[SM_row-1, 'in']
        SM_outbran1 = NodeInOut.loc[SM_row-1, 'out1'].values
        SM_outbran2 = NodeInOut.loc[SM_row-1, 'out2'].values

        #储能拓扑信息
        Store_row = node.loc[(node['节点类型'] == 10) | (node['节点类型'] == 11)]['节点序号'].values
        Store_inbran = NodeInOut.loc[Store_row-1, 'in'].values
        Store_outbran = NodeInOut.loc[Store_row-1, 'out1'].values

        #光伏与风机拓扑信息
        PV_row = node.loc[(node['节点类型'] == 12)]['节点序号'].values
        PV_outbran = NodeInOut.loc[PV_row-1, 'out1']
        WT_row = node.loc[(node['节点类型'] == 13)]['节点序号'].values
        WT_outbran = NodeInOut.loc[WT_row-1, 'out1']

        #自备电厂拓扑信息
        plant_outbran = NodeInOut.loc[plant_node-1, 'out1']

        #函数依赖
        def _sum(a, b):
            if(len(b) == 1):
                return a[b[0]]
            else:
                s = a[b[0]]
                for i in range(1, len(b)):
                    s += a[b[i]]
                return s

        #目标函数   (x即为微网1支路潮流向量，长度为28。其中x[0]无意义)
        ##特别说明：由于不同微网的支路数目不同。以下目标函数中的x[27]为微网1独有##
        ##其余微网的该数据分别如下：
        ##微网2：x[24]
        ##微网3：x[27]
        ##微网4：x[27]
        ##微网5：x[24]
        ##微网6：x[20]
        ##微网7：x[26]
        ##微网8：x[26]
        ##微网9：x[27]
        ##微网10：x[24]
        ##微网11：x[24]
        ##微网12：x[24]

        xindex = [27,24,27,27,24,20,26,26,27,24,24,24]
        
        fun = lambda x : (x[7]*hp + x[2]*ep + x[1]*gp + plant_b * x[xindex[self.local.id-1]]**2 + plant_c * x[xindex[self.local.id-1]])
        #self.logger.debug(f'local_{self.local.id-1} fun = lambda x : (x[7]*hp + x[2]*ep + x[1]*gp + plant_b * x[{xindex[self.local.id-1]}]**2 + plant_c * x[{xindex[self.local.id-1]}])')
        
        # fun = lambda x : (x[7]*hp + x[2]*ep + x[1]*gp + plant_b * x[24]**2 + plant_c * x[24])
        #########################################################################

        #约束
        cons = (#外部源输入平衡，节点1234
                #{'type': 'eq', 'fun': lambda x: x[1] - _sum(x, branch.loc[branch['起始节点'] == 1]['支路编号'].values)},
                #{'type': 'eq', 'fun': lambda x: x[2] - _sum(x, branch.loc[branch['起始节点'] == 2]['支路编号'].values)},
                #{'type': 'eq', 'fun': lambda x: x[7] - _sum(x, branch.loc[branch['起始节点'] == 3]['支路编号'].values)},
                #{'type': 'eq', 'fun': lambda x: x[8] - _sum(x, branch.loc[branch['起始节点'] == 4]['支路编号'].values)},
                
                {'type': 'eq', 'fun': lambda x: x[8]},

                #总线平衡，节点5678
                {'type': 'eq', 'fun': lambda x: _sum(x, branch.loc[branch['起始节点'] == 5]['支路编号'].values) - _sum(x, branch.loc[branch['终止节点1'] == 5]['支路编号'].values) + gasdemand},
                {'type': 'eq', 'fun': lambda x: _sum(x, branch.loc[branch['起始节点'] == 6]['支路编号'].values) - _sum(x, branch.loc[branch['终止节点1'] == 6]['支路编号'].values) + elecdemand},
                {'type': 'eq', 'fun': lambda x: _sum(x, branch.loc[branch['起始节点'] == 7]['支路编号'].values) - _sum(x, branch.loc[branch['终止节点1'] == 7]['支路编号'].values) + heatdemand},
                {'type': 'eq', 'fun': lambda x: _sum(x, branch.loc[branch['起始节点'] == 8]['支路编号'].values) - _sum(x, branch.loc[branch['终止节点1'] == 8]['支路编号'].values) + cooldemand},

                #单输入单输出设备平衡，节点类型4567
                {'type': 'eq', 'fun': lambda x: node.loc[SS_row-1, 'b'].values * x[SS_inbran]**2 + node.loc[SS_row-1, 'c'].values * x[SS_inbran] + node.loc[SS_row-1, 'd'].values - x[SS_outbran]},
                {'type': 'ineq', 'fun': lambda x: x[SS_inbran]},
                {'type': 'ineq', 'fun': lambda x: node.loc[SS_row-1, 'In_max'].values - x[SS_inbran]},
                {'type': 'ineq', 'fun': lambda x: x[SS_outbran]},
                {'type': 'ineq', 'fun': lambda x: node.loc[SS_row-1, 'Out1_max'].values - x[SS_outbran]},

                #单输入多输出设备平衡，节点类型1238
                {'type': 'eq', 'fun': lambda x: node.loc[SM_row-1, 'a'].values * x[SM_inbran]**2 + node.loc[SM_row-1, 'c'].values * x[SM_inbran] + node.loc[SM_row-1, 'e'].values - x[SM_outbran1]},
                {'type': 'eq', 'fun': lambda x: node.loc[SM_row-1, 'b'].values * x[SM_inbran]**2 + node.loc[SM_row-1, 'd'].values * x[SM_inbran] + node.loc[SM_row-1, 'f'].values - x[SM_outbran2]},
                {'type': 'ineq', 'fun': lambda x: x[SM_inbran]},
                {'type': 'ineq', 'fun': lambda x: node.loc[SM_row-1, 'In_max'].values - x[SM_inbran]},
                {'type': 'ineq', 'fun': lambda x: x[SM_outbran1]},
                {'type': 'ineq', 'fun': lambda x: node.loc[SM_row-1, 'Out1_max'].values - x[SM_outbran1]},
                {'type': 'ineq', 'fun': lambda x: x[SM_outbran2]},
                {'type': 'ineq', 'fun': lambda x: node.loc[SM_row-1, 'Out2_max'].values - x[SM_outbran2]},

                #储能(CS和HS), 节点类型10，11
                #本场景中未考虑使用储能，因此约束其流入、流出支路的功率均为0
                {'type': 'eq', 'fun': lambda x: x[Store_inbran]},
                {'type': 'eq', 'fun': lambda x: x[Store_outbran]},

                #光伏与风机(PV与WT), 节点类型12，13
                {'type': 'ineq', 'fun': lambda x: x[PV_outbran]},
                {'type': 'ineq', 'fun': lambda x: renewerable_energy_raw.loc[11, 'PV_max(MW)'] - x[PV_outbran]},
                {'type': 'ineq', 'fun': lambda x: x[WT_outbran]},
                {'type': 'ineq', 'fun': lambda x: renewerable_energy_raw.loc[11, 'WT_max(MW)'] - x[WT_outbran]},

                #自备电厂, 节点类型14
                {'type': 'ineq', 'fun': lambda x: x[plant_outbran] - node.loc[plant_node-1, 'Out1_max']},
                {'type': 'ineq', 'fun': lambda x: node.loc[plant_node-1, 'In_max'] - x[plant_outbran]}
                )

        #设定初始值
        #其中，x0的第一位无效，可填任意值。
        ##特别说明：以下初值为微网1独有，其余微网初值具体见initialValue.xlsx文件##
        # x0 = np.array((0,319.999999505356,-250.003001096491,100,1.11046426604397,100,4.99999999615589,75.9477313666888,0,25.0696544011388,72.8521359323478,1.39999998291272,3.98999994207841,3.98999994224326,119.999996997767,91.1999995463381,159.999999757731,60.7999999826104,68.3999999597335,0,0,0,0,159.999999757731,60.7999999826104,68.3999999597335,100,329.999999987477))
        # x0 = np.array((0, 239.9999999,59.37759995,100,1.110464267,100,4.999999997,-11.97423777,0,25.78387405,74.85859171,0.799999982,2.165999955,2.165999956,39.99999974,28.49999986,239.9999999,90.05999999,101.004,0,0,0,0,100,0))
        #########################################################################

        # 去除nan值，会影响结果
        data = self.initial_raw.loc[:,self.local.id]
        notnan_data =[
          d
          for d in data
          if not np.isnan(d)
        ]
        x0 = np.array((0,*notnan_data))
        # x0[~pd.isnull(x0)]
        res = minimize(fun, x0, method='SLSQP', constraints=cons, options={'disp': True, 'maxiter': 300})
        ##  gd = res.x[1]
        ##  ed = res.x[2]
        ##  hd = res.x[7]
        ##  cost_min = res.fun
        gd = res.x[1]
        ed = res.x[2]
        hd = res.x[7]
        cost_min = res.fun
        # print('最小值：',res.fun)
        # print('最优解：',res.x)
        # print('迭代终止是否成功：', res.success)
        # print('迭代终止原因：', res.message)
        return gd,ed,hd,cost_min
    islog=False
    def log_x(self,xindex,x):
        if not self.islog:
            self.logger.debug(f'local_{self.local.id} x {x}')
            self.logger.debug(f'local_{self.local.id} plan{x[xindex[self.local.id-1]]}')
            self.islog = True
    #代表根据所有普通节点发来的各能源需求量，更新各能源价格
    #输入为3个数量十二元组和1个价格三元组+当前迭代期标号，即12个微网发来的各能源需求量，分别为气需求、电需求、热需求：(gd, ed, hd)；以及迭代至当前时计算出的新的各能源价格，分别为气价、电价、热价：(gp, ep, hp)
    #输出为三元组，即本代表计算出的新的各能源价格，分别为气价、电价、热价：(gp, ep, hp)
    ##其中，代表计算出的热价hp本身也是一个三元组: 微网1-4共享hp[0], 微网5-8共享hp[1], 微网9-12共享hp[2]
    def delegate_update(self,gd,ed,hd, gp,ep,hp, round_id):
        gasdemand = self.gasdemand_raw.loc[12, 'T12'] # sum
        elecdemand = self.elecdemand_raw.loc[12, 'T12'] # sum

        GasPrice = self.price_raw.loc[11, 'gas'] # 时段12(下标为11)的数据
        ElecPrice = self.price_raw.loc[11, 'elec'] # 时段12(下标为11)的数据
        CH = [206.1, 206.1, 206.1]
        Qmax = [100, 0, 160]
        #判断当前迭代价格与外部源价格比对
        eps = 1e-2
        #迭代气价与外部气源
        flag_gas = 0
        if gp - GasPrice > eps:
            gas_max = 2*(gasdemand + 4480)
            gas_min = 2*(gasdemand + 4480)
        elif gp - GasPrice < -eps:
            gas_max = 0
            gas_min = 0
        else:
            gas_max = 2*(gasdemand + 4480)
            gas_min = 0
            flag_gas = 1

        #迭代电价与外部电源
        flag_elec = 0
        if ep - ElecPrice > eps:
            elec_max = elecdemand + 500
            elec_min = elecdemand + 500
        elif ep - ElecPrice < -eps:
            elec_max = 0
            elec_min = 0
        else:
            elec_max = elecdemand + 500
            elec_min = 0
            flag_elec = 1

        #迭代热价与外部热源
        heat_max = [0,0,0]
        heat_min = [0,0,0]
        flag_heat = [0,0,0]
        for i in range(3):
            if hp[i] - CH[i] > eps:
                heat_max[i] = Qmax[i]
                heat_min[i] = Qmax[i]
            elif hp[i] - CH[i] < -eps:
                heat_max[i] = 0
                heat_min[i] = 0
            else:
                heat_max[i] = Qmax[i]
                heat_min[i] = 0
                flag_heat[i] = 1

        #对所有微网需求量按能源类型求和
        net_gas = sum(gd)
        net_elec = sum(ed)
        net_heat = [0,0,0]
        net_heat[0] = sum(hd[0:4])
        net_heat[1] = sum(hd[4:8])
        net_heat[2] = sum(hd[8:12])

        #计算各能源供给差量
        #气
        if flag_gas == 0:
            SG_gas = -gas_min + net_gas
        elif flag_gas == 1 and gas_min > net_gas:
            SG_gas = -gas_min + net_gas
        else:
            SG_gas = 0
        #电
        if flag_elec == 0:
            SG_elec = -elec_min + net_elec
        elif flag_elec == 1 and elec_min > net_elec:
            SG_elec = -elec_min + net_elec
        else:
            SG_elec = 0
        #热
        SG_heat = [0,0,0]
        for i in range(3):
            if flag_heat[i] == 0:
                SG_heat[i] = -heat_min[i] + net_heat[i]
            elif flag_heat[i] == 1 and heat_min[i] > net_heat[i]:
                SG_heat[i] = -heat_min[i] + net_heat[i]
            else:
                SG_heat[i] = 0

        #更新各能源新价格
        A = 20
        B = 0.1
        gp = GasPrice
        ep = ep + 1/(A+B*round_id)*SG_elec
        for i in range(3):
            hp[i] = hp[i] + 1/(A+B*round_id)*SG_heat[i]
        return gp,ep,hp
    
    # 初始化第一轮的需求
    def init_demand(self):       
        gp,ep,hp = self.init_price()
        gd,ed,hd,cost_min = self.normal_node_update(gp,ep,hp[0])
        return [gd,ed,hd]
    
    # 初始化第一轮的价格   
    def init_price(self):
        GasPrice = self.price_raw.loc[11, 'gas'] # 时段12(下标为11)的数据
        ElecPrice = self.price_raw.loc[11, 'elec'] # 时段12(下标为11)的数据
        gp = 0.9 * GasPrice
        ep = 0.5 * ElecPrice
        hp = [200,200,200]
        return gp,ep,hp

