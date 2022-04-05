#代表根据更新后的价格和上一轮迭代的价格，检测迭代是否终止(价格是否收敛)
#输入为两个三元组，分别为上一轮迭代的各能源价格与更新后的价格
#def delegate_checkEnd(gp1,ep1,hp1, gp2, ep2, hp2)
#   函数主体
#   return flag_end

#函数主体如下

eps = 1e-3
norm = ((gp2-gp1)**2 + (ep2-ep1)**2 + (hp2[0]-hp1[0])**2 + (hp2[1]-hp1[1])**2 + (hp2[2]-hp1[2])**2)**0.5
if norm < eps:
    flag_end = 1
else:
    flag_end = 0