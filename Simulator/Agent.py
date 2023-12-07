class Agent(object):
    """docstring for Agent"""
    
    def __init__(self, idx, start, dest, expected):
        super(Agent, self).__init__()
        self.idx = idx
        self.start = start
        self.dest = dest
        self.current = self.start
        self.pre = self.start

        self.repeated_run = 0
        self.travel_time = 0
        self.expected = expected
        self.path = [self.start]

    def moveTo(self, node, travel_time=None):
        self.path.append(node)
        self.current = node
        if travel_time is not None:
            self.travel_time += travel_time

    def reset(self, od_pair:tuple = None):
        if od_pair is not None:
            self.start,self.dest = od_pair

        self.current = self.start
        self.pre = self.start
        self.repeated_run += 1

        self.path = [self.start]

    def is_finished(self):
        return self.current == self.dest


    def __str__(self):
        return f'Agent[{self.idx}]({self.start} => {self.dest})'