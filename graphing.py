import matplotlib.pyplot as plt

class Graph:
    def __init__(self, title):
        self.title = title
        self.time = []
        self.val = []
        self.name = ''

    def add_point(self, time, value):
        self.time.append(time)
        self.val.append(value)

    def set_name(self, name):
        self.name = name

    def plot(self):
        plt.plot(self.time, self.val)
        plt.title(self.name + " " + self.title)
        plt.ylabel(self.title)
        plt.xlabel('time (ms)')
        plt.show()
