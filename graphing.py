import matplotlib.pyplot as plt

class Graph:
    def __init__(self, title):
        self.title = title
        self.time = []  # x axis
        self.val = []   # y axis
        self.name = ''

    def add_point(self, time, value):
        self.time.append(time)
        self.val.append(value)

        # if len(self.time) > 50: # Arbitrary graph scrolling window size
        #     self.time.pop(0)
        #     self.val.pop(0)

    def set_name(self, name):
        self.name = name

    def plot(self):
        plt.plot(self.time, self.val)
        plt.title(self.name + " " + self.title)
        plt.ylabel(self.title)
        plt.xlabel('time (ms)')
        plt.show()

# class BigGraph(Graph):
#     def __init__(self):
#         self.subplots = []
#         ax1 = fig.add_subplot(2,1,2)
#
#     def plot_all():
#         for sub in self.subplots:
#             ax1 = fig.add_subplot(2,1,2)
