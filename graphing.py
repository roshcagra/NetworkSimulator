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
        self.avgwindow = 100
        self.curwindow = 0

    def add_point(self, time, value):

        # Add to average
        if self.curwindow < self.avgwindow:
            self.time.append(time)
            self.val.append(value)
            self.curwindow += 1
        else :
            # If it hits the number of points to avg, plot it
            avg_x = 0
            avg_y = 0
            for i in range(1, self.avgwindow):
                avg_x = self.time.pop(len(self.time) - 1)
                avg_y = self.val.pop(len(self.val) - 1)


            avg_val = 0
            if (time - avg_x):
                avg_val = abs(value - avg_y)/(time - avg_x)
            else:
                avg_val = abs(value - avg_y)/1

            if avg_val < -0.5 or avg_val > 0.5:
                self.time.append(time)
                self.val.append(avg_val)

                # Write to external file for plotting on a seperate python script
                file = open("data/" + self.filename + ".txt","a")
                #file.write(str(time) + "," + str(value) + "\n")
                file.write(str(time) + "," + str(avg_val) + "\n")
                file.close()

                # Log
                file = open("log/" + self.filename + ".txt","a")
                #file.write(str(time) + "," + str(value) + "\n")
                file.write(str(time) + "," + str(avg_val) + "\n")
                file.close()

            self.curwindow = 0

    def set_name(self, name):
        self.name = name

    def plot(self):
        plt.plot(self.time, self.val)
        plt.title(self.name + " " + self.title)
        plt.ylabel(self.title)
        plt.xlabel('time (ms)')
        plt.show()
