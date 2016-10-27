# NetworkSimulator

Project Meeting 2 (Beer Room)

Event based simulation

Link
Fields:
	Hosts : [Host, Host, …]
	Routers : [Router, Router, ….]
	Queue of packets
	Capacity  // Is there max capacity for buffer on links?
	Transmission delay
Methods:
	send_data()
	drop_packets()
	
Device
Fields:
IP
Links : [Link, Link, ….]

Methods:
send_data()
receive_data()

Router
Fields:
	Routing table
	
Methods:	
	receive_routing()
	send_routing()

Host
Fields:
	References to links that are attached to it
	Window size
Methods:
	send_ack()
	receive_ack()
Subclasses:
	Reno_Host
	Reno_window_size()
	Fast_Host
	Fast_window_size()

Packet
Fields:
ID	// To keep track of which ones were acknowledged
Subclasses:
	Data
		Payload
	Ack
		[Destination, Source, original packet]
	Routing
		[Root, Distance]


