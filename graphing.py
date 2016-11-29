import matplotlib
matplotlib.use("TkAgg")
from matplotlib import pyplot as plt


# import matplotlib.pyplot as plt



class Graph:
    def __init__(self, title, filename):
        self.title = title
        self.time = []  # x axis
        self.val = []   # y axis
        self.name = ''
        self.filename = filename

    def add_point(self, time, value):
        # if self.time[-1] == time:
        #     self.val[-1] += value
        # else:
        #     self.time.append(time)
        #     self.val.append(value)

        self.time.append(time)
        self.val.append(value)

        # Write to external file for plotting on a seperate python script
        file = open("data/" + self.filename + ".txt","a")
        file.write(str(time) + "," + str(value) + "\n")
        file.close()

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
