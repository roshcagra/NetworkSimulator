class Graph:
    def __init__(self, title):
        self.title = title
        self.times = []  # x axis
        self.vals = []   # y axis

    def add_point(self, time, value):
        self.times.append(time)
        self.vals.append(value)
