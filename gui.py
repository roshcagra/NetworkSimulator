import Tkinter as tk
from Tkinter import *
from tkSimpleDialog import askstring

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
		self.canvas = tk.Canvas(width=1000, height=1000)
		self.canvas.pack(fill="both", expand=True)
		self.simulate = tk.Button(text="Simulate", command=self.run)
		self.simulate.pack(side=tk.RIGHT)

	def run(self):
		global devices
		r = env.process(dynamic_routing(devices, env))
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
		if even.keysym == 'q':
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
			return

	def button_handler_l(self, event):
		global devices
		global device_id

		master = Tk()
		master.title("Create Device")
		label = Label(master, text="Device", font=10)
		label.grid(row=0)
		entry1 = Entry(master)
		entry1.grid(row=0, column=1)

		label=Label(master, text="IP", font=10)
		label.grid(row=1)
		entry2 = Entry(master)
		entry2.grid(row=1, column=1)

		def callback():
			if entry2.get():
				if entry1.get() == "host":
					device = self.canvas.create_oval(event.x - 10, event.y - 10, event.x + 10, event.y + 10, fill="blue")
					device_id.append([device, 0])
					devices.append(Host(ip=entry2.get()))
					master.destroy()
				elif entry2.get() == "router":
					device = self.canvas.create_oval(event.x - 10, event.y - 10, event.x + 10, event.y + 10, fill="green")
					device_id.append([device, 1])
					devices.append(Router(ip=entry2.get()))
					master.destroy()

		button1=Button(master, text="Create", command=callback)
		button1.grid(row=2, column=1)

	def button_handler_r(self, event):
		global devices
		global device_id
		global links
		global link_id

		clicked_idx = -1
		print event.x, event.y
		for idx in range(len(devices)):
			coord = self.canvas.coords(device_id[idx][0])
			if coord[0] < event.x < coord[2] and coord[1] < event.y < coord[3]:
				if clicked_idx != -1:
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
					label.grid(row=1)
					entry3 = Entry(master)
					entry3.grid(row=1, column=1)

					cor1_x = self.canvas.coords(device_id[clicked_idx][0])[0] + 10
					cor1_y = self.canvas.coords(device_id[clicked_idx][0])[1] + 10
					cor2_x = self.canvas.coords(device_id[idx][0])[0] + 10
					cor2_y = self.canvas.coords(device_id[idx][0])[1] + 10
					link = self.canvas.create_line(cor1_x, cor1_y, cor2_x, cor2_y)
					link_val = Link(link_rate=int(entry1.get()), link_delay=int(entry2.get()), max_buffer_size=int(entry3.get()), env=env)
					links.append(link_val)
					link_id.append(link)

					devices[clicked_idx].add_link(link_val)
					devices[idx].add_link(link_val)
					link_val.add_device(devices[clicked_idx])
					link_val.add_device(devices[idx])
					if (device_id[clicked_idx][1] == 0 and device_id[idx][1] == 1) or (device_id[clicked_idx][1] == 1 and device_id[idx][1] == 0):
						if device_id[clicked_idx][1] == 0:
							devices[idx].routing_table = {devices[clicked_idx].ip:link}
							devices[idx].distance_table = {devices[clicked_idx].ip:0}
						else:
							devices[clicked_idx].routing_table = {devices[idx].ip:link}
							devices[clicked_idx].distance_table = {devices[idx].ip:0}
				else:
					clicked_idx = idx
					print clicked_idx
					break
			else:
				clicked_idx = -1
		print clicked_idx

if __name__ == "__main__":
	root = NetworkGUI()
	root.bind('<Key>', root.key_handler)
	root.canvas.bind('<Button-1>', root.button_handler_l)
	root.canvas.bind('<Button-2>', root.button_handler_r)
	devices = []
	device_id = []
	links = []
	link_id = []
	root.mainloop()
