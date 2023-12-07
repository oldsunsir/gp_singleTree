from Simulator import FlowSimulator
from Simulator import Agent
from Simulator import NodeFreeFlowNet
from Simulator.Engine import leftlenth
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
module_path = os.path.join(current_dir, "..")
sys.path.append(module_path)
import GraphConstrut
import random
from typing import Callable
import pandas as pd
import time
import ast
import os

MyGraph = GraphConstrut.MyGraph
vertex_attrs = GraphConstrut.vertex_attrs
edge_attrs = GraphConstrut.edge_attrs


RESOURCE_FIELD = '_resource'
class simulate:
    def __init__(self) -> None:
        self.VDF_a = 1
        self.VDF_b = 1
        self.PopNum = 10        ##样例个数，控制每个样例对应的随机种子数
        self.M_CONST = 500       ##虚拟节点的容量，足够大即可
        self.RESOURCE_FIELD = RESOURCE_FIELD
        self.Speed = 900/60            ##以km/min为单位，因为延迟时间精确到分

        self.MyNet = NodeFreeFlowNet(n = MyGraph.vcount(), edges = MyGraph.get_edgelist(), 
                        directed = False, vertex_attrs = vertex_attrs, edge_attrs = edge_attrs)##构图
        self.MyNet.capacity_btw = self.capacity_btw
        self.MyNet.capacity_of = self.capacity_of
        self.MyNet.ett_seconds = self.ett_seconds
        self.MySim : FlowSimulator = None
        self.end : int
        self.discount : float
    def VDF(self, x:float)->float:
        return 1.6*x
    
    def rule(self, net,agent:Agent, )->int:
        mintmp = float('inf')
        current = agent.current
        next_node = -1
        if self.MyNet.vs[current]['True'] == "No":
            next_node = self.MyNet[current][0] if self.MyNet[current][0] not in agent.path else self.MyNet[current][1]
        else:
            for neighbor in self.MyNet[current]:
                eid = self.MyNet.get_eid(current, neighbor)
                Imp = round(self.MyNet.es[eid]['lenth']+leftlenth[neighbor][agent.dest], 2)
                priority = Imp
                if priority < mintmp:
                    mintmp = priority
                    next_node = neighbor
            assert next_node != -1
        return next_node



    def capacity_btw(self, u:int, v:int) -> int:
        assert vertex_attrs['True'][u] == 'Yes'##u一定是真实节点
        Neighbors = len(self.MyNet[u])
        return int(self.MyNet.vs[u][self.RESOURCE_FIELD].capacity/Neighbors)

    def capacity_of(self, node):

        # if vertex_attrs['True'][node] == 'Yes':
        #     seed = int(self.PopNum)
        #     random.seed(seed)
        #     Luckyguys = [random.randint(0, 166) for _ in range(50)]
        #     if node in Luckyguys:
        #         return 56*(1 - self.discount)+1
        #     else:
        #         return 56
        # else:
        #     return self.M_CONST
        if vertex_attrs['True'][node] == 'Yes':
            seed = int(self.PopNum*node+self.PopNum+node)
            random.seed(seed)
            return random.randint(20,120)
        else:
            return self.M_CONST
        
    def ett_seconds(self, u, v):
        f_u_v = self.MyNet.number_btw(u,v)
        eid = self.MyNet.get_eid(u,v)
        t0 = self.MyNet.es[eid]['lenth'] / self.Speed
        C_u_v = self.MyNet.es[eid][self.RESOURCE_FIELD].capacity
        t = self.VDF((1+self.VDF_a*((f_u_v/C_u_v)**self.VDF_b))*t0)
        return int(t)

    def addagents(self,sim:FlowSimulator):
        script_dir = os.path.dirname(__file__)
        path = os.path.join(script_dir, "..", "usectrajectory03.csv")
        
        df = pd.read_csv(path, encoding='gbk')
        for i in range(df.shape[0]):
            sim.add_agent(idx=i, start=df.iloc[i]['DepSector'], dest=df.iloc[i]['ArrSector'], delay=df.iloc[i]['TimeDelay'])
         

    def run(self):
        DoneAir = 0
        while self.PopNum >= 1:
            self.MySim = FlowSimulator(flow_net=self.MyNet)
            self.addagents(self.MySim)
            self.MySim.evaluate_run(rule = self.rule, end = self.end, log = False)
            DoneAir += self.MySim.reset_agents_num   
            self.PopNum -= 1
        self.PopNum = 10
        return int(DoneAir / self.PopNum)
    
if __name__ == '__main__':
    with open('输出记录/MUEGF.txt', 'w', encoding='utf-8') as f:
        for i in range(100, 901, 100):
            Env = simulate()
            Env.end = int(i)

            f.write(f'MUEGF仿真{i}min结果为:')
            f.write(str(Env.run())+'\n')
            f.flush()
            f.close
    # else:
    #     print("Invalid argument:", user_argument)
    pass
