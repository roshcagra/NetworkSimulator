try:
    import Tkinter as tk
    from Tkinter import *
    from tkSimpleDialog import askstring
except ImportError:
    import tkinter as tk
    from tkinter import *
    from tkinter.simpledialog import askstring

import simpy
from device import Host
from device import Router
from link import Link
from utils import flow
from utils import dynamic_routing
env = simpy.Environment()

class NetworkGUI(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("Network Simulator")
        self.canvas = tk.Canvas(width=500, height=500)
        self.canvas.pack(fill="both", expand=True)
        self.simulate = tk.Button(text="Simulate", command=self.run)
        self.simulate.pack(side=tk.RIGHT)
        self.set_ip = 0
        self.clicked_flow = -1
        self.clicked_idx = -1
        self.found = False

    def run(self):
        global devices
        r = env.process(dynamic_routing(devices, 500, env))
        env.run()
        for device in devices:
            device_name = "Device " + str(device.ip)
            device.graph_wsize.set_name(device_name)
            device.graph_wsize.plot()
            for l in range(0, len(device.links)):
                link = device.links[l]
                link.graph_buffocc.set_name(device_name + " " + "Link " + str(l))
                link.graph_buffocc.plot()

    def key_handler(self, event):
        global devices
        global device_id
        global links
        global link_id
        if event.keysym == 'q':
            quit()
        elif event.keysym == 'c':
            devices = []
            links = []
            for item in device_id:
                self.canvas.delete(item)
            for item in link_id:
                self.canvas.delete(item)
            device_id = []
            link_id = []

    def button_handler_double(self, event):
        for idx in range(len(devices)):
            coord = self.canvas.coords(device_id[idx][0])
            print(event.x, event.y)
            print(coord)
            if coord[0] < event.x < coord[2] and coord[1] < event.y < coord[3] and device_id[idx][1] == 0:
                print(device_id[idx][1])
                if self.clicked_flow != -1:
                    master = Tk()
                    master.title("Create Flow")
                    label = Label(master, text="Amount", font=10)
                    label.grid(row=0)
                    entry1 = Entry(master)
                    entry1.grid(row=0, column=1)
                    label = Label(master, text="Start Time", font=10)
                    label.grid(row=1)
                    entry2 = Entry(master)
                    entry2.grid(row=1, column=1)

                    def create_flow():
                        cor1_x = self.canvas.coords(device_id[self.clicked_idx][0])[0] + 10
                        cor1_y = self.canvas.coords(device_id[self.clicked_idx][0])[1] + 10
                        cor2_x = self.canvas.coords(device_id[idx][0])[0] + 10
                        cor2_y = self.canvas.coords(device_id[idx][0])[1] + 10
                        link = self.canvas.create_line(cor1_x, cor1_y, cor2_x, cor2_y, fill="red")


                        if (self.clicked_flow != idx) and (self.clicked_flow != -1) and (idx != -1):
                            print('creating flow from', self.clicked_flow, 'to', idx)
                            env.process(flow(int(entry1.get()), int(entry2.get()), devices[self.clicked_flow], devices[idx].ip, env))


                        self.found = False
                        self.clicked_flow = -1
                        master.destroy()

                    button1=Button(master, text="Create", command=create_flow)
                    button1.grid(row=2, column=1)
                else:
                    self.clicked_flow = idx
                    break
                self.found == True

    def button_handler_l(self, event):
        global devices
        global device_id

        master = Tk()
        master.title("Create Device")
        label = Label(master, text="Device", font=10)
        label.grid(row=0)
        entry1 = Entry(master)
        entry1.grid(row=0, column=1)

        def callback():
            if entry1.get() == "host":
                device = self.canvas.create_oval(event.x - 10, event.y - 10, event.x + 10, event.y + 10, fill="blue")
                device_id.append([device, 0])
                devices.append(Host(ip=self.set_ip))
                self.set_ip += 1
                master.destroy()
            elif entry1.get() == "router":
                device = self.canvas.create_oval(event.x - 10, event.y - 10, event.x + 10, event.y + 10, fill="green")
                device_id.append([device, 1])
                devices.append(Router(ip=self.set_ip))
                self.set_ip += 1
                master.destroy()

        button1=Button(master, text="Create", command=callback)
        button1.grid(row=2, column=1)

    def button_handler_r(self, event):
        global devices
        global device_id
        global links
        global link_id

        for idx in range(len(devices)):
            coord = self.canvas.coords(device_id[idx][0])
            if coord[0] < event.x < coord[2] and coord[1] < event.y < coord[3]:
                if self.clicked_idx != -1:
                    master = Tk()
                    master.title("Create Link")
                    label = Label(master, text="Link Rate", font=10)
                    label.grid(row=0)
                    entry1 = Entry(master)
                    entry1.grid(row=0, column=1)

                    label=Label(master, text="Link Delay", font=10)
                    label.grid(row=1)
                    entry2 = Entry(master)
                    entry2.grid(row=1, column=1)

                    label=Label(master, text="Max Buffer Size", font=10)
                    label.grid(row=2)
                    entry3 = Entry(master)
                    entry3.grid(row=2, column=1)

                    cor1_x = self.canvas.coords(device_id[self.clicked_idx][0])[0] + 10
                    cor1_y = self.canvas.coords(device_id[self.clicked_idx][0])[1] + 10
                    cor2_x = self.canvas.coords(device_id[idx][0])[0] + 10
                    cor2_y = self.canvas.coords(device_id[idx][0])[1] + 10
                    link = self.canvas.create_line(cor1_x, cor1_y, cor2_x, cor2_y)

                    def create_link():
                        link_val = Link(link_rate=int(entry1.get()), link_delay=int(entry2.get()), max_buffer_size=int(entry3.get()), env=env)
                        links.append(link_val)
                        link_id.append(link)

                        devices[self.clicked_idx].add_link(link_val)
                        devices[idx].add_link(link_val)
                        link_val.add_device(devices[self.clicked_idx])
                        link_val.add_device(devices[idx])

                        if (device_id[self.clicked_idx][1] == 0 and device_id[idx][1] == 1) or (device_id[self.clicked_idx][1] == 1 and device_id[idx][1] == 0):
                            if device_id[self.clicked_idx][1] == 0:
                                devices[idx].routing_table = {devices[self.clicked_idx].ip:link_val}
                                devices[idx].distance_table = {devices[self.clicked_idx].ip:0}
                            else:
                                devices[self.clicked_idx].routing_table = {devices[idx].ip:link}
                                devices[self.clicked_idx].distance_table = {devices[idx].ip:0}

                        self.found = False
                        self.clicked_idx = -1
                        master.destroy()

                    button1=Button(master, text="Create", command=create_link)
                    button1.grid(row=4, column=1)

                else:
                    self.clicked_idx = idx
                    break
                self.found ==True

if __name__ == "__main__":
    root = NetworkGUI()
    root.bind('<Key>', root.key_handler)
    root.canvas.bind('<Button-1>', root.button_handler_l)
    root.canvas.bind('<Button-2>', root.button_handler_r)
    root.canvas.bind('<Double-Button-1>', root.button_handler_double)
    devices = []
    device_id = []
    links = []
    link_id = []
    root.mainloop()
