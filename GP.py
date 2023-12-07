from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from deap import gp
import operator
from Simulate import simulate


import multiprocessing
import random
import numpy
import matplotlib.pyplot as plt
import multiprocessing
import time
import traceback


def protectedDiv(left, right):
    try:
        return left / right
    except ZeroDivisionError:
        return 1
    
def Max(left, right):
    return left if left >= right else right

def Min(left, right):
    return left if left <= right else right

def target(individual):
    Env = simulate()
    func = toolbox.compile(expr=individual)
    Env.gpfunc = func
    Env.end = 500
    return Env.run(),




popnum = 500
pset = gp.PrimitiveSetTyped("MAIN",in_types=[float]*6,ret_type=float)
pset.addPrimitive(operator.add, [float,float], float)
pset.addPrimitive(operator.sub, [float,float], float)
pset.addPrimitive(operator.mul, [float,float], float)
pset.addPrimitive(protectedDiv, [float,float], float)
pset.addPrimitive(Max, [float, float], float)
pset.addPrimitive(Min, [float, float], float)
pset.renameArguments(ARG0 = 'L',ARG1 = 'S',ARG2 = 'P',ARG3 = 'P_',\
                     ARG4 = 'T', ARG5 = 'P2N')

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

toolbox = base.Toolbox()
toolbox.register("expr", gp.genHalfAndHalf, pset=pset, min_=1, max_=2)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("compile", gp.compile, pset=pset)
toolbox.register("evaluate", target)
toolbox.register('select', tools.selLexicase)

toolbox.register("mate", gp.cxOnePoint)
toolbox.decorate("mate", gp.staticLimit(key=operator.attrgetter("height"), max_value=8))    ##最大高度设置为8
toolbox.decorate("mate", gp.staticLimit(key=len, max_value=35))                             ##最长限制为35

toolbox.register("expr_mut", gp.genFull, min_=0, max_=2)
toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)
toolbox.decorate("mutate", gp.staticLimit(key=operator.attrgetter("height"), max_value=8))    ##最大高度设置为8
toolbox.decorate("mutate", gp.staticLimit(key=len, max_value=35))  



def my_compile(expression):
    try:
        func = gp.compile(expression, pset=pset)
        return func
    except SyntaxError as e:
        print(f"SyntaxError in expression: {expression}")
        print("Error message:", str(e))
        traceback.print_exc()
        return None
        

def main():

    random.seed(10)
    pop = toolbox.population(n=popnum)
    hof = tools.HallOfFame(1)
    stats_fit = tools.Statistics(lambda ind: ind.fitness.values)
    stats_size = tools.Statistics(len)
    stats = tools.MultiStatistics(fitness=stats_fit, size=stats_size)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
    pool = multiprocessing.Pool(processes=10)
    toolbox.register("map", pool.map)

    _, log = algorithms.eaSimple(pop, toolbox, 0.85, 0.1, 52, stats, halloffame=hof)

    pool.close()
    pool.join()

    max_fit = log.chapters['fitness'].select('max')
    # 绘制收敛曲线
    plt.figure(figsize=(10, 5))
    plt.plot(range(len(max_fit)), max_fit, label="Maximum Fitness")
    plt.xlabel("Generation")
    plt.ylabel("Fitness Value")
    plt.legend()
    plt.title("Convergence Plot")
    plt.grid(True)
    output_file = "./输出记录/tmp.png"
    plt.savefig(output_file, format="png")

    return pop, stats, hof

if __name__ == "__main__":
    pop, stats, hof = main()
    print(hof[0])
    nodes, edges, labels = gp.graph(hof[0])

    import networkx as nx 
    import pygraphviz as pgv
    pgv.AGraph(prog='C:/Program Files/Graphviz/bin/dot.exe')  # 将路径替换为您的dot.exe的实际路径
    g  = nx.Graph()
    g.add_nodes_from(nodes)
    g.add_edges_from(edges)
    pos = nx.nx_agraph.graphviz_layout(g, prog = "dot")
    nx.draw_networkx_nodes(g, pos)
    nx.draw_networkx_edges(g, pos)
    nx.draw_networkx_labels(g, pos, labels)
    plt.show()
    