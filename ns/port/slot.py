"""
Slot Class
This class represents a slotted system in a network simulation. Each slot has a fixed duration
and can potentially contain packets waiting for transmission. 
Each sourse has its own slot instance. It schedules the transmission of packets based on the specified rate and packet size.
Packets are transmitted one by one from a slot to the connected medium (Wire).
"""

class Slot:
    def __init__(self, env, rate, packet_size):
        self.env = env
        self.rate = rate
        self.packet_size = packet_size
        self.packets_in_slot = []
        self.out = None  # Add out attribute to connect the Slot to the wire
        self.env.process(self.schedule_slots()) # Start the slot scheduling process

    def schedule_slots(self):
        # Schedule time slots with a fixed duration. This method controls the transmission
        # of packets in each slot
        print("initial delay in Slot: ",0)
        yield self.env.timeout(0) 
        slot_duration = 1.5 #1.0 / self.rate # # 
        while True:
            self.current_slot_start = self.env.now
            print("current slot time: ", self.env.now)
            self.current_slot_end = self.current_slot_start + slot_duration
            yield self.env.timeout(slot_duration)
            print("now is after yielding for slot duration: ", self.env.now)

            # Transmit one packet from the slot if it's not empty
            # So here we send only one packet to the wire as we are in one instance of slot each time
            if self.packets_in_slot:
                packet = self.packets_in_slot.pop(0) 
                if self.rate > 0:
                    packet.begin_transmission = self.env.now  # Record the begin_transmission time
                    print("Begins slot transmission at: {:.3f}, Packet ID: {}, flow ID: {}".format(packet.begin_transmission, packet.packet_id, packet.flow_id))
                    # Calculate the transmission time based on the rate
                    # MOVED TO WIRE AFTER NO COLLISION
                    # transmission_time = 1.5 # packet.size * 8.0 / self.rate
                    # yield self.env.timeout(transmission_time)
                    print("Ends slot transmission at: {} , Packet ID: {}, flow ID: {}".format(self.env.now, packet.packet_id, packet.flow_id))
                self.out.put(packet)  # Send packet to the out attribute (wire)

    def put(self, packet):
        # If a packet arrives, it will be queued
        print("Adding the packet with id: {} with flow_id: {} to the slot buffer at time {}.".format(packet.packet_id, packet.flow_id, self.env.now))
        self.packets_in_slot.append(packet)
