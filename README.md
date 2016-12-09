# NetworkSimulator

## Language
Python 3

## Simulator
SimPy 3. It is built for simulations where there are many objects being simulated and they interact often.

## Classes
### `Packet`
#### Variables
- `id`: packet id
- `source`: Source Device ip
- `destination`: Destination Device ip

### `DataPacket` -> Extension of `Packet`
DataPacket has no additional variables or methods

### `AckPacket` -> Extension of `Packet`
AckPacket has no additional variables or methods

### `RoutingPacket` -> Extension of `Packet`
#### Variables
- `distance_table`: table of distances calculated by the sending router
- `buffer_occ`: occupancy of the buffer the packet is being sent down
- `link`: the link the packet is being sent down

#### Methods
- `specify_link(link)`: set the `link` the router packet came from.

### `Device`
#### Variables
- `ip`: the ip address of the device
- `links` : an array of links attached to the device as [Link, Link, ...]

#### Methods
- `add_link(link)`: add the link to `links`
- `receive_packet(Packet)`: different implementations for Router and Host, but depending on the packet, call a handler function.

### `Router` -> Extension of `Device`
#### Variables
- `distance_table`: maps each destination ip to the cost it takes to get there
- `routing_table`: maps each destination ip to the next hop the packet must take to get

#### Methods
- `route(Packet)`: if the packet is not a `RouterPacket`, then send it along. Otherwise pass it to `receive_router(packet)`
- `send_router()`: send `distance_table` in a `RouterPacket` to all neighbors
- `receive_router(RoutingPacket -> (neighbor_distance_table, link, buff_occ))`:
  1. For each `device` in `neighbor_distance_table`:
    - If `device` is not in `routing_table`, update `routing_table` and `distance_table` with `link` and `neighbor_distance_table[device]`
    - If `routing_table[device] == link` (i.e. we already use this link to get to `device`), update `distance_table` using `neighbor_distance_table` and `buff_occ`
    - If `neighbor_distance_table[device] + buff_occ < distance_table[device]` (i.e. there is a new, better path), then update `routing_table` and `distance_table` to include this
  2. If `routing_table` has changed, call `send_router()`

### `Host` -> Extension of `Device`
#### Sender (General)
##### Variables (One for each outgoing flow)
- `window`: the current flight stored as [start, end)
- `window_size`: the maximum flight size
- `last_acknowledged`: the last packet id acknowledged and the number of times it was acknowledged stored as (id, count)

##### Methods
- `send_data(packet_id, destination)`: send the packet down the attached link
- `retransmit()`: send the last unacknowledged packet
- `start_flow(data, destination, tcp_type)`: depending on the `tcp_type`, call the tcp specific flow function

#### Sender (Reno)
##### Variables
- `ss_thresh`: the slow start threshold past which the flow enters congestion control
- `timeout_clock`: stores the average travel time and deviation as (travel_time, deviation)
- `timer`: a separate process waiting for a timeout to occur

##### Methods
- `get_timeout()`: returns how long the current timer should wait

- `reset_timer()`:
  1. Wait for however long `get_timeout()` says and
    - If interrupted before completion, set `timer = reset_timer()` (i.e. reset the timer)
    - If not interrupted, assume failure and
      1. Call `retransmit()`
      2. Set `ss_thresh = window_size / 2`
      3. Set `window_size = 1`
      4. Set `window = [window.start, window.start + 1)`
      5. Set `timer = reset_timer()` (i.e. reset the timer)

- `start_reno_flow(data, destination)`:
  1. Initializes `window_size = 1`
  2. Initializes `window = [start = 0, end = 0)`
  3. Initializes `ss_thresh = inf`
  4. Initializes `last_acknowledged = (id = 0, count = 0)`
  4. Sends a packet, sets `window = [0, 1)`, sets `timer = reset_timer()` (i.e. starts the timer), and waits for reactivation
  5. Each time the function is reactivated, it sends `window_size - len(window)` number of data packets to `destination` if there is any `data` left to send

- `update_timeout_clock(send_time, arrival_time)`: update the average travel time and deviation stored in `timeout_clock`

- `receive_reno_ack(Ack_Packet -> (p_id))`:
  1. If the acknowledgment is the next expected one, call `update_timeout_clock(Ack_Packet.send_time, current_time)`
  2. If the acknowledgment is higher than the last ack received, set `last_acknowledged = (p_id, 1)` and `window = [p_id, window.end)` and reset `timer`
    - If in fast recovery (`last_acknowledged.number >= 4`), set `window_size = ss_thresh`
    - If in slow-start (`window_size <= ss_thresh`), set `window_size += 1`
    - If in congestion control (`window_size > ss_thresh`), set `window_size += 1 / window_size`
  3. If it is equal to the last ack received, set `last_acknowledged = (p_id, last_acknowledged.number + 1)`
    - If this is less than the fourth duplicate acknowledgment
      - If currently in slow-start, set `window_size += 1`
      - If currently in congestion control, set `window_size += 1 / window_size`
    - If this is the fourth duplicate acknowledgment
      1. Call `retransmit()`
      2. Set `ss_thresh = window_size / 2`
      3. Set `window_size = window_size / 2 + 3`
      4. reset `timer`
    - If this is more than the fourth duplicate acknowledgment
      1. Set `window_size += 1`
  4. If it is less than the last ack received, ignore it
  4. If `len(window) < window_size` (i.e. the current flight size is less than the maximum allowed), then reactivate `start_reno_flow`

#### Sender (FAST)
##### Variables
- `fast_RTT`: the smallest and most recent round-trip-time stored as (smallest, most_recent)
- `timer`: a separate process that updates the window size

##### Methods
- `update_window()`:
  1. every 20 milliseconds, update the window size based on `fast_RTT.smallest` and `fast_RTT.most_recent`
  2. If `len(window) < window_size` (i.e. the current flight size is less than the maximum allowed), then reactivate `start_fast_flow`

- `start_fast_flow(data, destination)`
  1. Initializes `window_size = 1`
  2. Initializes `window = [start = 0, end = 0)`
  3. Initializes `fast_RTT = (smallest = inf, most_recent = inf)`
  4. Initializes `last_acknowledged = (id = 0, count = 0)`
  4. Sends a packet, sets `window = [0, 1)`, sets `timer = update_window()` (i.e. starts the window updater), and waits for reactivation
  5. Each time the function is reactivated, it sends `window_size - len(window)` number of data packets to `destination` if there is any `data` left to send

- `update_rtt(send_time, arrival_time)`: update `fast_RTT` based on the new RTT

- `receive_fast_ack(Ack_Packet -> (p_id))`:
  1. If the acknowledgment is the next expected one, call `update_rtt(Ack_Packet.send_time, current_time)`
  2. If the acknowledgment is higher than the last one received, set `last_acknowledged = (p_id, 1)` and `window = [p_id, window.end)`
  3. If `len(window) < window_size` (i.e. the current flight size is less than the maximum allowed), then reactivate `start_fast_flow`

#### Receiver (General)
##### Variables
- `received`: array of received packets stored as [id_1, id_2, ...]

##### Methods
- `send_ack(p_id, source)`: send an acknowledgment packet down the link back to the source

- `get_next_ack():` find the first hole in the acknowledgment sequence and return that id

- `receive_data(DataPacket -> p_id)`:
  - If `p_id` is not in `received`
    1. Add it to `received`
    2. Get `next_id = get_next_ack()`
    3. Call `send_ack(next_id, DataPacket.source)`
  - If `p_id` is in `received`, ignore it

#### Receiver (Reno)
Reno has no additional variables or methods for the receiver.

#### Receiver (FAST)
FAST has no additional variables or methods for the receiver.

### `Link`
#### Variables
- `devices`: a list of attached to this link as [Device, Device]
- `buffer`: a queue of packets
- `link_rate`: number specifying the rate at which packets can be transmitted
- `link_delay`: number specifying the travel time from one end of the link to the other
- `buffer_size`: number specifying how many packets can sit in the queue before packets begin to be dropped

#### Methods
- `add_device(device)`: add `device` to `devices`
- `insert_into_buffer(packet)`: add the packet to the buffer
- `remove_from_buffer(packet)`: remove the packet to the buffer
- `send_packet(packet, source)`:
  - If there is any room in the buffer, add the packet to the buffer using `insert_into_buffer(packet)`
    1. When the packet is at the top of the buffer, pass it onto the device at the other end and remove it from the buffer using `remove_from_buffer(packet)`
  - If there isn't any room, drop the packet


## Process Functions
### `Flow(data, start, source, destination, tcp_type)`
After waiting for `start`, call `source.start_flow(data, destination, tcp_type)`


### `dynamic_routing(devices, interval)`:
While there is a flow running, wait for `interval` and for each `router` in `devices`, call `router.send_router()`
