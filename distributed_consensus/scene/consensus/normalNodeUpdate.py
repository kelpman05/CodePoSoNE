#普通节点根据代表发来价格，更新自身多能源需求量
#输入为三元组，即三个价格，分别为气价、电价、热价：(gp, ep, hp)
#输出为四元组，即本普通节点（微网）在该价格下的各能源的最优需求量，分别为气需求、电需求、热需求：(gd, ed, hd)，以及此时的最低成本cost_min
#def normal_node_update(gp,ep,hp)
#   函数主体
#   return gd,ed,hd,cost_min

#函数主体如下（当然，数据导入等预处理可以放在函数外部）

#以下为普通节点（微网）1的案例。如无特别说明，则其代码也适用于其余普通节点（微网）
from scipy.optimize import minimize
import pandas as pd
import numpy as np

file0 = 'demand.xlsx'
file2 = 'price_ge.xlsx'

##特别说明：file1为每个微网独有的文件，此处微网1的文件即为HUB1.xlsx##
file1 = 'HUB1.xlsx'
####################################################################

node = pd.read_excel(file1, 'node')
branch = pd.read_excel(file1, 'branch')
NodeInOut = pd.read_excel(file1, 'NodeInOut')
renewerable_energy_raw = pd.read_excel(file1, 'Renewable_Energy')

gasdemand_raw = pd.read_excel(file0, 'GasDemand')
elecdemand_raw = pd.read_excel(file0, 'ElecDemand')
heatdemand_raw = pd.read_excel(file0, 'HeatDemand')
cooldemand_raw = pd.read_excel(file0, 'CoolDemand')

price_raw = pd.read_excel(file2, 'Sheet1')

#时段12负荷（目前仿真只做时段12，其他时段原理相同）
##特别说明：第一个参数0表示微网1，微网2,3...依次类推##
gasdemand = gasdemand_raw.loc[0, 'T12']
elecdemand = elecdemand_raw.loc[0, 'T12']
heatdemand = heatdemand_raw.loc[0, 'T12']
cooldemand = cooldemand_raw.loc[0, 'T12']
#####################################################

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
fun = lambda x : (x[7]*hp + x[2]*ep + x[1]*gp + plant_b * x[27]**2 + plant_c * x[27])
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
x0 = np.array((0,319.999999505356,-250.003001096491,100,1.11046426604397,100,4.99999999615589,75.9477313666888,0,25.0696544011388,72.8521359323478,1.39999998291272,3.98999994207841,3.98999994224326,119.999996997767,91.1999995463381,159.999999757731,60.7999999826104,68.3999999597335,0,0,0,0,159.999999757731,60.7999999826104,68.3999999597335,100,329.999999987477))
#########################################################################

res = minimize(fun, x0, method='SLSQP', constraints=cons, options={'disp': True, 'maxiter': 300})
##  gd = res.x[1]
##  ed = res.x[2]
##  hd = res.x[7]
##  cost_min = res.fun

# print('最小值：',res.fun)
# print('最优解：',res.x)
# print('迭代终止是否成功：', res.success)
# print('迭代终止原因：', res.message)




