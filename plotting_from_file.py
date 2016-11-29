# https://pythonprogramming.net/python-matplotlib-live-updating-graphs/
# Plots data text files as it gets updated
# Run this in a separate terminal window as the simulator is running
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time

fig = plt.figure(figsize=(8, 10))
#fig.tight_layout()
fig.set_tight_layout(True)


# ax1 = fig.add_subplot(1,2,2)
# ax2 = fig.add_subplot(1,2,1)
axes = {}
axes["wsize"] = fig.add_subplot(6,1,1)
axes["flowrate"] = fig.add_subplot(6,1,2)
axes["linkrate"] = fig.add_subplot(6,1,3)
axes["delay"] = fig.add_subplot(6,1,4)
axes["dropped"] = fig.add_subplot(6,1,5)
axes["buffocc"] = fig.add_subplot(6,1,6)

def animate(i):
    for filename, ax in axes.items():
        #ax.ylabel("packets")
        #ax.xlabel('time (ms)')
        path = "data/" + filename + ".txt"
        try:
            pullData = open(path ,"r").read()
            dataArray = pullData.split('\n')
            xar = []
            yar = []
            # if len(xar) > 50:
            #     ax.set_xlim([xar[0], max(xar[0],xar[49])])
            for eachLine in dataArray:
                if len(eachLine)>1:
                    x,y = eachLine.split(',')
                    xar.append(float(x))
                    yar.append(float(y))
                    if len(xar) > 1000:
                        xar.pop(0)
                        yar.pop(0)

            ax.clear()
            ax.set_ylabel(filename)
            ax.set_xlabel("time")

            if len(yar) > 0:
                ax.set_ylim([0, max(yar)])
            ax.plot(xar,yar)
        except IOError as e:
            continue


ani = animation.FuncAnimation(fig, animate, interval=10)
plt.show()
