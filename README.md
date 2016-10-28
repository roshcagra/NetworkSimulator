# NetworkSimulator

## Language
Python

## Simulator
SimPy 3. It is built for simulations where there are many objects being simulated and they interact often. Simulating a network falls under this, so SimPy seems like a good fit. It's also allows Process Based Simulation, which is also cool.

## Classes
### Packet
#### Variables
1. id: integer
2. source: Host
3. destination: Host

### Data_Packet
#### Variables
1. payload

### Ack_Packet
#### Variables
3. original_packet

### Routing_Packet
#### Variables
1. source: Router
2. distance: number
	
### Device
#### Variables
1. ip: integer
2. links : [Link, Link, ...]

#### Methods
1. send_data()
2. receive_data()

### Router -> Extension of Device
#### Variables
1. routing_table: { destination: next_hop }

#### Methods	
1. receive_routing()
2. send_routing()

### Host -> Extension of Device
#### Variables
1. window_size: number

#### Methods
1. send_ack()
2. receive_ack()

### Reno_Host -> Extension of Host
### Fast_Host -> Extension of Host

### Link
#### Variables
1. devices : [Device, Device, ...]
2. queue: [Packet, Packet, ...]
3. capacity: integer
4. transmission_delay: number
5. buffer_size: number

#### Methods
1. send_data()
