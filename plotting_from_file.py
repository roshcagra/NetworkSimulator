# https://pythonprogramming.net/python-matplotlib-live-updating-graphs/
# Plots data text files as it gets updated
# Run this in a separate terminal window as the simulator is running
import matplotlib.pyplot as plt
import matplotlib.animation as animation

fig = plt.figure(figsize=(8, 10))
#fig.tight_layout()
fig.set_tight_layout(True)


# ax1 = fig.add_subplot(1,2,2)
# ax2 = fig.add_subplot(1,2,1)
axes = {}
axes["wsize"] = fig.add_subplot(6,1,1)
axes["flowrate"] = fig.add_subplot(6,1,2)
# axes["delay"] = fig.add_subplot(6,1,3)
# axes["linkrate"] = fig.add_subplot(6,1,4)
# axes["dropped"] = fig.add_subplot(6,1,5)
# axes["buffocc"] = fig.add_subplot(6,1,6)

data = {}
data["wsize"] = [[], []]
data["flowrate"] = [[], []]
# data["delay"] = [[], []]
# data["linkrate"] = [[], []]
# data["dropped"] = [[], []]
# data["buffocc"] = [[], []]

gid = "0"

def animate(i):
    for filename, ax in axes.items():
        #ax.ylabel("packets")
        #ax.xlabel('time (ms)')
        path = "data/" + filename + gid + ".txt"
        try:
            f = open(path ,"r")
            pullData = f.read()
            dataArray = pullData.split('\n')
            xar = data[filename][0]
            yar = data[filename][1]

            for eachLine in dataArray:
                if len(eachLine)>1:
                    x,y = eachLine.split(',')
                    xar.append(float(x))
                    yar.append(float(y))

            f.close()
            open(path ,"w").close() # Clear text file

            ax.clear()
            ax.set_ylabel(filename)
            ax.set_xlabel("time")

            ax.plot(xar,yar)
        except IOError as e:
            continue

# Initial clearing
for filename, ax in axes.items():
    path = "data/" + filename + gid + ".txt"
    open(path ,"w").close() # Clear text file

ani = animation.FuncAnimation(fig, animate, interval=10)
#ani = animation.FuncAnimation(fig2, animate, interval=10)
plt.show()
