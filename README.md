# NetworkSimulator

## Language
Python 3

## Simulator
SimPy 3. It is built for simulations where there are many objects being simulated and they interact often. Network simulation using processes is very simple (our code is approximately 200 lines at the moment)

## Classes
### Packet
#### Variables
1. id: integer
2. source: Host
3. destination: Host

### Data_Packet
#### Variables
1. on_receive: an event to be passed onto the corresponding acknowledgement packet

### Ack_Packet
#### Variables
3. on_receive: an event to be triggered when the acknowledgement is received to interrupt the timer and prevent a timeout

### Routing_Packet (TODO)
#### Variables
1. source: Router
2. distance: number
	
### Device
#### Variables
1. ip: integer
2. links : [Link, Link, ...]

#### Methods
1. send(Packet): different implementations for Router and Host, but once the correct link is determined, call Link.send();
2. receive(Packet): different implementations for Router and Host, but depending on the packet, call a handler function.

### Router -> Extension of Device
#### Variables
1. routing_table: { destination: next_hop }

#### Methods
1. handle_routing(Routing_Packet): run the routing algorithm and send a routing packet.

### Host -> Extension of Device
#### Variables
1. window_size: number

#### Methods
1. receive_ack(Ack_Packet): handle processing the acknowledgement. This involves interrupting the timer for the original packet, adjusting the window size, and performing error correction.
2. receive_data(Data_Packet): handle processing data. This involves updating the list of received packets and generating the correct acknowledgement packet

### Link
#### Variables
1. devices : [Device, Device, ...]
2. queue: [Packet, Packet, ...]
3. capacity: integer
4. transmission_delay: number # doesnt capacity = transmission delay?!
5. buffer_size: number

#### Methods
1. send(): send a packet, taking into out account capacity, the queue, transmission delay, and buffer size.


### Flow
Defined as a function which is passed the following parameters:
1. Total amount of data to be sent
2. Source
3. Destination
4. Initial delay
