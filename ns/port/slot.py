import simpy

class Slot:
    def __init__(self, env, rate, packet_size):
        self.env = env
        self.rate = rate
        self.packet_size = packet_size
        self.packets_in_slot = []
        self.out = None  # Add out attribute to connect the Slot to the wire

        # Start the slot scheduling process
        self.env.process(self.schedule_slots())

    def schedule_slots(self):
        slot_duration = 0.9 # 1.0 / self.rate
        print("Slot duration is: ", slot_duration)
        while True:
            self.current_slot_start = self.env.now
            self.current_slot_end = self.current_slot_start + slot_duration
            print("New slot begins at {:.3f}".format(self.env.now))
            yield self.env.timeout(slot_duration)

            # Transmit one packet from the slot if it's not empty
            if self.packets_in_slot:
                packet = self.packets_in_slot.pop(0)
                #print("Packet sent from slot to wire: ", self.env.now)
                if self.rate > 0:
                    packet.begin_transmission = self.env.now  # Record the begin_transmission time
                    print("Begins slot transmission at: {:.3f}, Packet ID: {}, flow ID: {}".format(packet.begin_transmission, packet.packet_id, packet.flow_id))
                    # Calculate the transmission time based on the rate
                    transmission_time = packet.size * 8.0 / self.rate
                    yield self.env.timeout(transmission_time)
                    print("Ends slot transmission at: {} , Packet ID: {}, flow ID: {}".format(self.env.now, packet.packet_id, packet.flow_id))
                self.out.put(packet)  # Send packet to the out attribute (wire)
    
    def put(self, packet):
        # If a packet arrives, it will be queued
        print("Adding the packet with id: {} in flow: {} to the slot buffer.".format(packet.packet_id, packet.flow_id))
        self.packets_in_slot.append(packet)
