# NetworkSimulator

## Language
Python

## Simulator
SimPy 3. It is built for simulations where there are many objects being simulated and they interact often. Simulating a network falls under this, so SimPy seems like a good fit.

## Classes
### Link
#### Variables
1. devices : [Device, Device, …]
2. queue
3. capacity
4. transmission_delay

#### Methods
1. send_data()
2. drop_packets()
	
### Device
#### Variables
1. ip
2. links : [Link, Link, ….]

#### Methods
1. send_data()
2. receive_data()

### Router -> Extension of Device
#### Variables
1. routing_table

#### Methods	
1. receive_routing()
2. send_routing()

### Host -> Extension of Device
#### Variables
1. References to links that are attached to it
2. window_size

#### Methods
1. send_ack()
2. receive_ack()

### Reno_Host -> Extension of Host
### Fast_Host -> Extension of Host

### Packet
#### Variables
1. id

### Data_Packet
#### Variables
1. payload

### Ack_Packet
#### Variables
1. destination
2. source
3. original_packet

### Routing_Packet
#### Variables
1. source
2. distance
