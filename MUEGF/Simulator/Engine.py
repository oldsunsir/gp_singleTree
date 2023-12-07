import json
import numpy as np
import os
from simpy import Environment
from simpy.core import StopSimulation, EmptySchedule
from typing import Callable
from queue import Queue
from .Agent import Agent
from .Network import NodeFreeFlowNet

script_dir = os.path.dirname(__file__)
file_path = os.path.join(script_dir, "..", "..", "ShortestLenth.txt")
leftlenth = []
with open(file_path, "r") as file:
    for line in file:
        line = line.strip()
        row_elements = line.split("\t")
        row = [float(element) for element in row_elements]
        leftlenth.append(row)
    file.close()

class ODsContainer(object):
    def __init__(self):
        self._d = dict()
        self._li = list()

    def add(self, item) -> int:
        if item not in self._d:
            self._d[item] = 0
            self._li.append(item)
        else:
            self._d[item] += 1
        return self._d[item]

    def sample(self, tabu_od):
        od = self._li[np.random.randint(len(self._li))]
        while od == tabu_od:
            od = self._li[np.random.randint(len(self._li))]
        self._d[od] += 1
        return od


class BaseFlowSimulator(Environment):
    def __init__(self, flow_net):
        super(BaseFlowSimulator, self).__init__()
        self.graph = flow_net
        self.graph.compile(self)

        self._seed = 666

        self.next_to_go: Callable = None
        self.agents = []

        self.OD_pairs = ODsContainer()

        self.reset_agents_num = 0

        self.simulation_history = []

    def toJson(self, path):
        d = {'nodes': list(self.graph.nodes), 'edges': list(self.graph.edges), 'simulation': self.simulation_history}
        with open(path, 'w') as f:
            f.write(json.dumps(d))

    def add_history(self, u, v, opt):
        self.simulation_history.append([
            self.now,
            int(u),
            int(v),
            opt,
            self.reset_agents_num,
        ])

    def _logs(self, u, v, change: int):
        self.add_history(u, v, change)
        pass

    def add_agent(self, idx, start, dest, delay = 0):
        self.agents.append(Agent(idx, start, dest))
        self.OD_pairs.add((start, dest))
        self.process(self.agent_proc(self.agents[-1], delay=delay))

    def agent_proc(self, agent, delay=0):
        raise NotImplementedError

    def delay_evaluate(self, delay):
        yield self.timeout(delay)
        self.reset_agents_num = 0

    def evaluate_run(self, rule: Callable, end, log=False):
        reserve_state = np.random.get_state()
        np.random.seed(self._seed)
        self.next_to_go = rule
        self.process(self.delay_evaluate(0))
        log_time = 0
        try:
            while self.now < end:
                self.step()
                if log and log_time < self.now:
                    log_time = self.now
                    print(f"\rTime Now: [{self.now:.1f}] | Finished: [{self.reset_agents_num}]", end='')
                    # print(self.graph.agents_counts())
            if log: print('')
        # except StopSimulation:
        #     pass
        except EmptySchedule:
            # deadlock by the damn routing
            pass
        np.random.set_state(reserve_state)
        # print(f"\rTime Now: [{self.now:.1f}] | Finished: [{self.reset_agents_num}]", end='')
        return self.reset_agents_num


class FlowSimulator(BaseFlowSimulator):
    """
    The numbers of the nodes means the total number agents
    on all its out edges
    """

    def __init__(self, flow_net):
        assert issubclass(flow_net.__class__, NodeFreeFlowNet)
        super(FlowSimulator, self).__init__(flow_net)

    def agent_proc(self, agent:Agent, delay=0, new_comer=True):
        if delay: yield self.timeout(delay)
        yield self.graph.resource_of(agent.start).put(1)
        while 1:
            if agent.is_finished():
                self.reset_agents_num += 1
                break
            reserve_state = np.random.get_state()
            next_node = self.next_to_go(self.graph, agent)
            np.random.set_state(reserve_state)
            if next_node == -1:
                agent.reset((agent.start, agent.dest))
                break
            with self.graph.resource_btw(agent.current, next_node).request(priority = -1*leftlenth[agent.current][agent.dest]) as req:
                yield req
                yield self.graph.resource_of(agent.current).get(1)
                self._logs(agent.current, next_node, 1)
                ett = self.graph.ett_seconds(agent.current, next_node)
                agent.pre = yield self.timeout(max(ett, 1), value=agent.current)
                agent.moveTo(next_node, travel_time=ett)
                
                self.graph.resource_btw(agent.pre, agent.current).release(req)
                if next_node != agent.dest:
                    self.graph.resource_of(next_node).put(1)
                    assert self.graph.resource_of(next_node).level <= self.graph.resource_of(next_node).capacity


