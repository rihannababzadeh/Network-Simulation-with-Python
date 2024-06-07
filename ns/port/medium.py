import random
import simpy

class Medium:
    """ Implements a medium that simulates the slotted Aloha access scheme.
        if a station misses out the allowed time, it must wait for the next time slot

        Parameters
        ----------
        env: simpy.Environment
            the simulation environment.
        slots: int
            the number of available time slots in each frame.
    """

    def __init__(self, env, slots):
        self.env = env
        self.slots = slots # Divide the shared channel into discrete time intervals
        self.packet_queue = [] # a queue to hold packets that are waiting to be transmitted
        self.transmitting = False  # Flag indicating if the medium is currently transmitting a packet

    def transmit(self):
        """
        Transmits packets in the packet queue according to the slotted Aloha access scheme.

        The transmission process occurs as follows:
        1. If the medium is not currently transmitting a packet and there are packets in the queue,
           the first packet in the queue is selected for transmission.
        2. The packet is transmitted and the transmission duration is determined by the propagation delay.
        3. After the transmission duration, the packet is removed from the queue.
        4. The medium checks if there are more packets in the queue and repeats the process.

        This method is executed as a continuous process in the simulation environment.
        """
        while True:
            if not self.transmitting and self.packet_queue:
                packet = self.packet_queue[0]  # Select the first packet in the queue for transmission
                self.transmitting = True  # Set the transmitting flag to indicate that the medium is busy
                if self.debug:
                    print("Transmitting packet:", packet)
                yield self.env.timeout(self.propagation_delay())  # Simulate the transmission duration
                self.packet_queue.pop(0)  # Remove the transmitted packet from the queue
                self.transmitting = False  # Set the transmitting flag to indicate that the medium is idle
            else:
                # If there are no packets in the queue or the medium is already transmitting,
                # yield to the simulation environment until a new packet arrives or the transmission completes
                yield self.env.timeout(0)


    def process_frame(self):
        """ Processes a frame of transmission slots and performs collision detection. """
        while len(self.packet_queue) > 0:
            frame = self.packet_queue[:self.slots]
            self.packet_queue = self.packet_queue[self.slots:]

            if len(frame) == 1:
                # Only one packet in the frame, no collision
                self.receive_packet(frame[0])
            else:
                # Collision detected
                self.handle_collision(frame)

            # Wait for the next frame
            yield self.env.timeout(1)

    def handle_collision(self, frame):
        """ Handles collision in a frame of packets.

            Parameters
            ----------
            frame: list
                the list of packets in the frame.
        """
        # Implement the collision resolution mechanism here (e.g., random backoff, exponential backoff, etc.)
        # For example, drop all the packets in the frame and notify the sender about the collision.
        for packet in frame:
            packet.sender.handle_collision(packet)

    def receive_packet(self, packet):
        """ Receives a successfully transmitted packet.

            Parameters
            ----------
            packet: Packet
                the received packet.
        """
        packet.receiver.receive_packet(packet)


    def enqueue_packet(self, packet):
        """
        Enqueues a packet in the packet queue.

        Parameters
        ----------
        packet : object
            The packet to be enqueued.
        """
        self.packet_queue.append(packet)  # Add the packet to the end of the packet queue
        if self.debug:
            print("Enqueued packet:", packet)