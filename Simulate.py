from Simulator import FlowSimulator
from Simulator import Agent
from Simulator import NodeFreeFlowNet
from GraphConstrut import MyGraph, vertex_attrs, edge_attrs
import random
from typing import Callable
import pandas as pd
import time
import sys
import ast
import networkx as nx


RoutePath = 'resource/Dijkstra.txt'
with open(RoutePath, 'r') as f:
    lines = f.readlines()
for i in range(len(lines)):
    lines[i] = ast.literal_eval(lines[i])

file_path = "resource/ShortestLenth.txt"
leftlenth = []
with open(file_path, "r") as file:
    for line in file:
        line = line.strip()
        row_elements = line.split("\t")
        row = [float(element) for element in row_elements]
        leftlenth.append(row)

file_path = 'resource/HistoryTra.txt'
HistroyTra = []
with open(file_path, 'r') as file:
    for line in file:
        line = line.strip()
        row_elements = line.split("\t")
        row = [int(element) for element in row_elements]
        HistroyTra.append(row)


RESOURCE_FIELD = '_resource'
class simulate:
    def __init__(self) -> None:
        self.VDF_a = 1
        self.VDF_b = 1
        self.PopNum = 101        ##样例个数，控制每个样例对应的随机种子数
        self.M_CONST = 500       ##虚拟节点的容量，足够大即可
        self.RESOURCE_FIELD = RESOURCE_FIELD
        self.Speed = 900/60            ##以km/min为单位，因为延迟时间精确到分
        self.gpfunc : Callable = None

        self.MyNet = NodeFreeFlowNet(n = MyGraph.vcount(), edges = MyGraph.get_edgelist(), 
                        directed = False, vertex_attrs = vertex_attrs, edge_attrs = edge_attrs)##构图
        self.MyNet.capacity_btw = self.capacity_btw
        self.MyNet.capacity_of = self.capacity_of
        self.MyNet.ett_seconds = self.ett_seconds

        self.MySim : FlowSimulator = None
        self.MyNet2 : nx.Graph = None
        self.RuleChoice = "GP"         ##选择哪一个rule，GP，Dijkstra, CASPER..
        self.discount = 0
        self.end = 500                 ##默认为500min仿真

    def VDF(self, x:float)->float:
        return 1.6*x
    
    def rule(self, net,agent:Agent, )->int:
        if self.RuleChoice == 'GP':
            mintmp = float('inf')
            current = agent.current
            if self.MyNet.vs[current]['True'] == "No":
                next_node = self.MyNet[current][0] if self.MyNet[current][0] not in agent.path else self.MyNet[current][1]
            else:
                next_node = -1
                for neighbor in self.MyNet[current]:
                    eid = self.MyNet.get_eid(current, neighbor)
                    L = round(self.MyNet.es[eid]['lenth'], 2)
                    S = round(leftlenth[neighbor][agent.dest], 2)
                    P = self.MyNet.number_btw(current, neighbor) / self.MyNet.resource_btw(current, neighbor).capacity+1e-7
                    P_ = 0
                    for neighbor2 in self.MyNet[neighbor]:
                        if neighbor2 != current:
                            P_ += self.MyNet.number_btw(neighbor, neighbor2) / self.MyNet.resource_btw(neighbor,
                                                                                                    neighbor2).capacity
                    P_ = P_ / len(self.MyNet[neighbor])+1e-7
                    ##添加预计耗时
                    Esti_time = self.ett_seconds(current, neighbor) + 1e-3
                    ###指派到该点的飞机数量
                    Plane2node = (self.MySim.will2node[neighbor] + self.MyNet.number_of(neighbor)) + 1e-5
                    priority = self.gpfunc(L, S, P, P_, Esti_time, Plane2node)
                    if priority < mintmp:
                        mintmp = priority
                        next_node = neighbor
                assert next_node != -1
            return next_node

        elif self.RuleChoice == 'CASPER':
            mintmp = float('inf')
            current = agent.current
            next_node = -1
            if self.MyNet.vs[current]['True'] == "No":
                next_node = self.MyNet[current][0] if self.MyNet[current][0] not in agent.path else self.MyNet[current][1]
            else:
                for neighbor in self.MyNet[current]:
                    eid = self.MyNet.get_eid(current, neighbor)
                    Imp = round(self.MyNet.es[eid]['lenth']+leftlenth[neighbor][agent.dest], 2)
                    Flow = self.MyNet.number_btw(current, neighbor)
                    Cap = self.MyNet.resource_btw(current, neighbor).capacity
                    T_f_c = 1 - Flow/(1.2 * Cap)
                    priority = Imp / T_f_c
                    if priority < mintmp:
                        mintmp = priority
                        next_node = neighbor
                assert next_node != -1
            return next_node
        elif self.RuleChoice == 'Dijkstra':
            idx = agent.idx
            current = agent.current
            next_idx = lines[idx].index(current)+1
            next_node = lines[idx][next_idx]
            return next_node
        elif self.RuleChoice == 'D_Lite':
            if self.MyNet2 == None:
                self.MyNet2 = nx.Graph()
                for vertex in self.MyNet.vs:
                    self.MyNet2.add_node(vertex.index)
                for idx,edge in enumerate(self.MyNet.edges):
                    self.MyNet2.add_edge(edge[0], edge[1], weight = self.MyNet.es[idx]['lenth'])
            for u, v, data in self.MyNet2.edges(data = True):
                data['weight'] = self.ett_seconds(u, v)
            path = nx.astar_path(self.MyNet2, agent.current, agent.dest, weight="weight")
            next_node = path[1]
            return next_node
        elif self.RuleChoice == 'Greedy':
            mintmp = float('inf')
            current = agent.current
            next_node = -1
            if self.MyNet.vs[current]['True'] == "No":
                next_node = self.MyNet[current][0] if self.MyNet[current][0] != agent.path[-1] else self.MyNet[current][1]
            else:
                for neighbor in self.MyNet[current]:
                    eid = self.MyNet.get_eid(current, neighbor)
                    Imp = round(self.MyNet.es[eid]['lenth'], 2)
                    priority = Imp
                    if priority < mintmp:
                        mintmp = priority
                        next_node = neighbor
            return next_node
        elif self.RuleChoice == 'History':
            idx = agent.idx
            current = agent.current
            next_idx = HistroyTra[idx].index(current)+1
            next_node = HistroyTra[idx][next_idx]
            return next_node
        else:
            pass


    def capacity_btw(self, u:int, v:int) -> int:
        assert vertex_attrs['True'][u] == 'Yes'##u一定是真实节点
        Neighbors = len(self.MyNet[u])
        return int(self.MyNet.vs[u][self.RESOURCE_FIELD].capacity/Neighbors)

    def capacity_of(self, node):
        if vertex_attrs['True'][node] == 'Yes':
            seed = int(self.PopNum*node+self.PopNum+node)
            random.seed(seed)   
            low_bound = [20, 60, 90][self.discount % 3]     ##对应不同的波动幅度
            return random.randint(low_bound,120)
        else:
            return self.M_CONST
        
    def ett_seconds(self, u, v):
        '''
        VDF时间,与车道容量与目前人数有关
        可以先用线性的试一试
        '''
        f_u_v = self.MyNet.number_btw(u,v)
        eid = self.MyNet.get_eid(u,v)
        t0 = self.MyNet.es[eid]['lenth'] / self.Speed
        C_u_v = self.MyNet.es[eid][self.RESOURCE_FIELD].capacity
        t = self.VDF((1+self.VDF_a*((f_u_v/C_u_v)**self.VDF_b))*t0)
        return int(t)

    def addagents(self,sim:FlowSimulator):
        path = 'resource/usedtrajectory03.csv'
        df = pd.read_csv(path, encoding='gbk')
        for i in range(df.shape[0]):
            sim.add_agent(idx=i, start=df.iloc[i]['DepSector'], dest=df.iloc[i]['ArrSector'], delay=df.iloc[i]['TimeDelay'])
         

    def run(self, discount = -1):
        DoneAir = 0
        while self.PopNum >= 90:
            self.discount = self.PopNum if discount == -1 else discount
            self.MySim = FlowSimulator(flow_net=self.MyNet)
            self.addagents(self.MySim)
            self.MySim.evaluate_run(rule = self.rule, end = self.end, log = False)
            DoneAir += self.MySim.reset_agents_num   
            self.PopNum -= 1

        self.PopNum = 101
        return int(DoneAir)

def protectedDiv(left, right):
    try:
        return left / right
    except ZeroDivisionError:
        return 1
    





if __name__ == '__main__':
    expr = []   ##用来测试
    expr.append("add(add(mul(Max(P2N, mul(add(S, P_), P)), add(Min(P, L), mul(P_, P2N))), L),"
            "Max(Max(S, Max(S, S)), Max(S, Max(add(Max(P_, S), mul(P, P_)), S))))")
    import GP    
    for i in range(100, 901, 100):  ##修改仿真时间
        for rule in ['GP']: #'History', 'CASPER', 'Dijkstra', 'Greedy'
            Env = simulate()
            Env.gpfunc = GP.my_compile(expr[-1].strip())    ##直接用GP里面的compile函数，不用自己再写
            Env.end = int(i)
            Env.RuleChoice = rule
            with open('输出记录/Test.txt', 'a', encoding='utf-8') as f:
                f.write(f'{rule}在20~120仿真{i}min结果为:\t{str(Env.run(discount=-1))}\n')  ##discount 0, 1, 2 -->20% 60% 90%
                f.flush()
                f.close

