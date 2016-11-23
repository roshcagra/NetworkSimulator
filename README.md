# NetworkSimulator

## Language
Python 3

## Simulator
SimPy 3. It is built for simulations where there are many objects being simulated and they interact often. Network simulation using processes is very simple (our code is approximately 200 lines at the moment)

## Classes
### Packet
#### Variables
1. id: integer
2. source: Device
3. destination: Host

### Data_Packet
#### Variables

### Ack_Packet
#### Variables

### Routing_Packet (TODO)
#### Variables
1. distance_table: table of distances calculated by the sending router
2. time_sent: time that the routing packet was sent by the sending router

#### Methods
1. specify_link: set the link the router packet came from.

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
2. distance_table: { destination: distance }

#### Methods
1. receive_routing(Routing_Packet): update distance and routing table
2. send_routing(): send a routing packet to all immediated neighbors with the distance table

### Host -> Extension of Device
#### Outgoing Flow Variables (One for each outgoing flow)
1. unacknowledged_packets: number
2. window_size: number
3. slow_start: boolean
4. timer: number
5. retransmit_queue: map of retransmitted packets

#### Incoming Flow Variables (One for each incoming flow)
1. received: array of received packets

#### Methods
1. start_flow(data, destination): start a flow of data that is periodically stopped and started.
2. receive_ack(Ack_Packet): handle processing the acknowledgement. This involves interrupting the timer for the original packet, adjusting the window size, and restarting the flow.
3. receive_data(Data_Packet): handle processing data. This involves updating the list of received packets and generating the correct acknowledgement packet.

### Link
#### Variables
1. devices : [Device, Device, ...]
2. queue: [Packet, Packet, ...]
3. link_rate: number specifying the rate at which packets can be transmitted
4. link_delay: number specifying the travel time from one end of the link to the other
5. buffer_size: number specifying how many packets can sit in the queue before packets begin to be dropped

#### Methods
1. send(): send a packet, taking into out account buffer_size, the queue, and transmission delay.


### Flow
Defined as a function which is passed the following parameters:
1. Total amount of data to be sent
2. Source
3. Destination
4. Initial delay
