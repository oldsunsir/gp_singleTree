from abc import ABC
import igraph
import numpy as np
import random
from simpy import PriorityResource, Container

class FlowNet(igraph.Graph):
    RESOURCE_FIELD = '_resource'

    def __init__(self, *args, **kwargs):
        super(FlowNet, self).__init__(*args, **kwargs)
    
    @property
    def edges(self):
        return self.get_edgelist()##返回边列表，每个元素是od tuple形式

    @property
    def nodes(self):
        return [i.index for i in self.vs]##vs:vertex sequence

    def __getitem__(self, item):##item是一个vertex
        return self.neighbors(item, mode='out')##返回该节点item的所有下一个可以到达的节点
    

    def compile(self, eng):
        for node in self.vs:
            node[FlowNet.RESOURCE_FIELD] = \
                Container(eng, capacity=self.capacity_of(node.index))##每个节点，即路口，是一个container
        for edge in self.es:
            edge[FlowNet.RESOURCE_FIELD] = \
                PriorityResource(eng, capacity=self.capacity_btw(*edge.tuple)+1)##每个边，即道路，是一个resource


    def number_btw(self, u, v):
        return self.resource_btw(u, v).count##Resource.count返回目前使用资源的人数

    def resource_btw(self, u, v)->PriorityResource:
        eid = self.get_eid(u, v)
        return self.es[eid][FlowNet.RESOURCE_FIELD]##返回u->v这条道路的流量状况

    def capacity_btw(self, u, v) -> int:
        raise NotImplementedError                   ##每个道路的capacity是看具体情况

    def number_of(self, node):
        return self.resource_of(node).level         ##container.level是The current amount，路口的车辆数

    def resource_of(self, node):
        return self.vs[node][FlowNet.RESOURCE_FIELD]##返回一个container
    def capacity_of(self, node) -> int:             ##从下面来看，作者将路口的容量设定为所有出度道路的容量和
        raise NotImplementedError

    def ett_seconds(self, u, v) -> int:
        raise NotImplementedError

    # debug function
    def agents_counts(self):
        r = 0
        for u, v in self.get_edgelist():
            r += self.number_btw(u, v)
        for node in self.nodes:
            r += self.resource_of(node).level
        # return r
        return [self.number_of(node) for node in self.nodes], r


class NodeFreeFlowNet(FlowNet, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def capacity_of(self, node):
        tmp = sum([self.capacity_btw(node, nbrs)
                    for nbrs in self[node]])
        return tmp
    
