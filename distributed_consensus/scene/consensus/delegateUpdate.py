#代表根据所有普通节点发来的各能源需求量，更新各能源价格
#输入为3个数量十二元组和1个价格三元组+当前迭代期标号，即12个微网发来的各能源需求量，分别为气需求、电需求、热需求：(gd, ed, hd)；以及迭代至当前时计算出的新的各能源价格，分别为气价、电价、热价：(gp, ep, hp)
#输出为三元组，即本代表计算出的新的各能源价格，分别为气价、电价、热价：(gp, ep, hp)
##其中，代表计算出的热价hp本身也是一个三元组: 微网1-4共享hp[0], 微网5-8共享hp[1], 微网9-12共享hp[2]
#def delegate_update(gd,ed,hd, gp,ep,hp, round_id)
#   函数主体
#   return gp,ep,hp

#函数主体如下(当然，数据导入等预处理可以放在函数外部)
import pandas as pd
file0 = 'demand.xlsx'
file2 = 'price_ge.xlsx'

gasdemand_raw = pd.read_excel(file0, 'GasDemand')
elecdemand_raw = pd.read_excel(file0, 'ElecDemand')


gasdemand = gasdemand_raw.loc[12, 'T12']
elecdemand = elecdemand_raw.loc[12, 'T12']


price_raw = pd.read_excel(file2, 'Sheet1')
GasPrice = price_raw.loc[11, 'gas']
ElecPrice = price_raw.loc[11, 'elec']
CH = [206.1, 206.1, 206.1]
Qmax = [100, 0, 160]

#判断当前迭代价格与外部源价格比对
eps = 1e-2
#迭代气价与外部气源
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
if ep - ElecPrice > eps:
    elec_max = elecdemand + 500
    elec_min = elecdemand + 500
elif gp - GasPrice < -eps:
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






