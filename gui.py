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
		self.canvas = tk.Canvas(width=700, height=700)
		self.canvas.pack(fill="both", expand=True)
		self.simulate = tk.Button(text="Simulate", command=self.run)
		self.simulate.pack(side=tk.RIGHT)
		self.create_flow = tk.Button(text="Create Flow", command=self.create_flow)
		self.create_flow.pack(side=tk.RIGHT)
		self.set_ip = 0
		self.clicked_flow = -1
		self.clicked_idx = -1
		self.increment = 5
		info = Tk()
		info.title("ReadMe")
		inf = "This is a GUI for the Network Simulator.\n\nLeft Click: Create a device (host=blue, router=green)\nRight Click(on device): Create a link betweeen two devices\n'q': Quit the app\n'c': Clear canvas"
		text = Text(info)
		text.insert(INSERT, inf)
		text.pack()
		def done():
			info.destroy()
		button1=Button(info, text="OK", command=done)
		button1.pack()

	def create_flow(self):
		global devices
		global devices_id
		device_ip = [item.ip for item in devices]
		master = Tk()
		master.title("Create Flow")
		label = Label(master, text="Amount(MB)", font=10)
		label.grid(row=0)
		entry1 = Entry(master)
		entry1.grid(row=0, column=1)
		label = Label(master, text="Start Time(s)", font=10)
		label.grid(row=1)
		entry2 = Entry(master)
		entry2.grid(row=1, column=1)
		entry3 = StringVar(master)
		entry3.set(device_ip[0])
		w = OptionMenu(master, entry3, *device_ip)
		w.grid()
		entry4 = StringVar(master)
		entry4.set(device_ip[0])
		w = OptionMenu(master, entry4, *device_ip)
		w.grid()
		entry5 = StringVar(master)
		entry5.set("FAST")
		w = OptionMenu(master, entry5, "FAST", "Reno")
		w.grid()

		def create_flow_for_real():
			if (devices[int(entry3.get())].type and devices[int(entry4.get())].type == "host") and (entry3.get() != entry4.get()) and (entry1.get().replace('.','',1).isdigit() and entry2.get().replace('.','',1).isdigit()):
				env.process(flow(float(entry1.get()) * 10**6, float(entry2.get()) * 10**3, devices[int(entry3.get())], devices[int(entry4.get())].ip, env, entry5.get()))
				flow_text = entry5.get() + " flow from " + entry3.get() + " --> " + entry4.get() + "\nAmount(MB):" + entry1.get() + ", Start Time(s):" + entry2.get()
				text_id = self.canvas.create_text(5, self.increment, anchor=NW, text=flow_text)
				self.increment += 40
				master.destroy()

		button1=Button(master, text="Create", command=create_flow_for_real)
		button1.grid(row=5, column=1)

	def run(self):
		global devices
		r = env.process(dynamic_routing(devices, 500, env))
		env.run()
		for device in devices:
		    device_name = "Device " + str(device.ip)
		    device.graph_wsize.set_name(device_name)
		    device.graph_wsize.plot()
		    device.graph_flowrate.set_name(device_name)
		    device.graph_flowrate.plot()

		for i in range(0, len(links)):
		    link = links[i]
		    link.graph_dropped.set_name("Link " + str(i))
		    link.graph_dropped.plot()
		    link.graph_buffocc.set_name("Link " + str(i))
		    link.graph_buffocc.plot()
		    link.graph_buffocc.plot()
		    link.graph_linkrate.set_name("Link " + str(i))
		    link.graph_linkrate.plot()
		    link.graph_delay.set_name("Link " + str(i))
		    link.graph_delay.plot()

	def key_handler(self, event):
		global devices
		global device_id
		global links
		global link_id
		if event.keysym == 'q':
			quit()
		elif event.keysym == 'c':
			self.canvas.delete("all")
			devices = []
			links = []
			device_id = []
			link_id = []
			self.set_ip = 0
			self.clicked_flow = -1
			self.clicked_idx = -1
			self.increment = 5

	def button_handler_l(self, event):
		global devices
		global device_id

		master = Tk()
		master.title("Create Device")
		label = StringVar(master)
		label.set("host")
		w = OptionMenu(master, label, "host", "router")
		w.grid()

		def callback():
			if label.get() == "host":
				device = self.canvas.create_oval(event.x - 10, event.y - 10, event.x + 10, event.y + 10, fill="blue")
				device_id.append([device, 0])
				devices.append(Host(ip=self.set_ip))
				text_id = self.canvas.create_text(event.x, event.y, text=self.set_ip, fill="white")
				self.set_ip += 1
				master.destroy()
			elif label.get() == "router":
				device = self.canvas.create_oval(event.x - 10, event.y - 10, event.x + 10, event.y + 10, fill="green")
				device_id.append([device, 1])
				devices.append(Router(ip=self.set_ip))
				text_id = self.canvas.create_text(event.x, event.y, text=self.set_ip, fill="white")
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
				if self.clicked_idx != -1 and self.clicked_idx != idx:
					master = Tk()
					master.title("Create Link")
					label = Label(master, text="Link Rate(Mbps)", font=10)
					label.grid(row=0)
					entry1 = Entry(master)
					entry1.grid(row=0, column=1)

					label=Label(master, text="Link Delay(ms)", font=10)
					label.grid(row=1)
					entry2 = Entry(master)
					entry2.grid(row=1, column=1)

					label=Label(master, text="Max Buffer Size(KB)", font=10)
					label.grid(row=2)
					entry3 = Entry(master)
					entry3.grid(row=2, column=1)

					cor1_x = self.canvas.coords(device_id[self.clicked_idx][0])[0] + 10
					cor1_y = self.canvas.coords(device_id[self.clicked_idx][0])[1] + 10
					cor2_x = self.canvas.coords(device_id[idx][0])[0] + 10
					cor2_y = self.canvas.coords(device_id[idx][0])[1] + 10
					link = self.canvas.create_line(cor1_x, cor1_y, cor2_x, cor2_y, fill="red")

					def create_link():
						if entry1.get().replace('.','',1).isdigit() and entry2.get().replace('.','',1).isdigit() and entry3.get().replace('.','',1).isdigit():
							link_text = "LR:" + entry1.get() + "\nLD:" + entry2.get() + "\nMBS:" + entry3.get()
							text_id = self.canvas.create_text((cor1_x + cor2_x) / 2, (cor1_y + cor2_y) / 2, text=link_text)
							link_val = Link(link_rate=float(entry1.get()) * 1.25 * 10**5, link_delay=float(entry2.get()), max_buffer_size=float(entry3.get()) * 10**3, env=env)
							links.append(link_val)
							link_id.append(link)

							link_val.add_device(devices[self.clicked_idx])
							link_val.add_device(devices[idx])
							devices[self.clicked_idx].add_link(link_val)
							devices[idx].add_link(link_val)

							self.clicked_idx = -1
							master.destroy()

					button1=Button(master, text="Create", command=create_link)
					button1.grid(row=4, column=1)
					break

				elif self.clicked_idx == idx:
					pass
				else:
					self.clicked_idx = idx
					break

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
