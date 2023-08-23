import simpy

class Slot:
    instances = []  # Class-level attribute to store references to all instances
    # Class-level variable to keep track of the condition
    at_least_two_slots_with_packets = False

    def __init__(self, env, rate, packet_size):
        self.env = env
        self.rate = rate
        self.packet_size = packet_size
        self.packets_in_slot = []
        self.out = None  # Add out attribute to connect the Slot to the wire

        # Add the current instance to the class-level instances list
        self.instances.append(self)

        # Start the slot scheduling process
        self.env.process(self.schedule_slots())

    def schedule_slots(self):
        slot_duration = 1.5 #1.0 / self.rate # # 
        print("Slot duration is: ", slot_duration)
        while True:
            self.current_slot_start = self.env.now
            print("now is: ", self.env.now)
            self.current_slot_end = self.current_slot_start + slot_duration
            # print("New slot begins at {:.3f}".format(self.env.now))
            yield self.env.timeout(slot_duration)

            # Check if at least two slots have at least one packet queued
            print("now is: ", self.env.now)
            if sum(slot.has_packets_queued() for slot in self.instances) >= 2:
                Slot.at_least_two_slots_with_packets = True
                print("At least two slots have at least one packet queued:")
                for slot in self.instances:
                    if slot.has_packets_queued():
                        print(f"Slot instance {Slot.instances.index(slot)} - Packet IDs: {[packet.packet_id for packet in slot.packets_in_slot]}")

            # Transmit one packet from the slot if it's not empty
            if self.packets_in_slot:
                packet = self.packets_in_slot.pop(0)

                if self.rate > 0:
                    packet.begin_transmission = self.env.now  # Record the begin_transmission time
                    print("Begins slot transmission at: {:.3f}, Packet ID: {}, flow ID: {}".format(packet.begin_transmission, packet.packet_id, packet.flow_id))
                    # Calculate the transmission time based on the rate
                    transmission_time = 1.5 # packet.size * 8.0 / self.rate
                    yield self.env.timeout(transmission_time)
                    print("Ends slot transmission at: {} , Packet ID: {}, flow ID: {}".format(self.env.now, packet.packet_id, packet.flow_id))

                self.out.put(packet)  # Send packet to the out attribute (wire)

    def put(self, packet):
        # If a packet arrives, it will be queued
        print("Adding the packet with id: {} in flow: {} to the slot buffer at time {}.".format(packet.packet_id, packet.flow_id, self.env.now))
        self.packets_in_slot.append(packet)

    def has_packets_queued(self):
        return len(self.packets_in_slot) >= 1 # Is there a packet queued in this slot?
    
    @staticmethod
    def has_at_least_two_slots_with_packets():
        return Slot.at_least_two_slots_with_packets
