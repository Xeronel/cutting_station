import RPi.GPIO as GPIO
from multiprocessing import Process


class RotaryEncoder(Process):
    def __init__(self, a_pin, b_pin):
        Process.__init__(self)

        # Pins
        self.a_pin = a_pin
        self.b_pin = b_pin

        # Initial pin states
        self.a_phase = bool(GPIO.input(a_pin))
        self.b_phase = bool(GPIO.input(b_pin))

        self.last_delta = 0
        self.last_seq = 0
        self.last_seq = self.rotation_sequence()

        self.last_rotation = 0
        self.rotation = 0
        self.running = False

    def rotation_sequence(self):
        # SEQ | A | B | SEQ
        #  0  | 0 | 0 |  0
        #  1  | 1 | 0 |  1
        #  2  | 1 | 1 |  2
        #  3  | 0 | 1 |  3
        return (int(self.a_phase) ^ int(self.b_phase)) | int(self.b_phase) << 1

    def get_delta(self):
        curr_seq = self.rotation_sequence()
        delta = self.last_delta
        if curr_seq != self.last_seq:
            # print("A: %s, B: %s, SEQ: %s" % (int(self.a_phase), int(self.b_phase), curr_seq))
            # 0 | No Change
            # 1 | Clockwise
            # 2 | Missed a step
            # 3 | Counter clockwise
            delta = (curr_seq - self.last_seq) % 4

            # print("Curr: %s, Last: %s, Delta: %s" % (curr_seq, self.last_seq, delta))
            # If clockwise set a positive rotation
            # If counter clockwise set a negative rotation
            # If 0 rotation or missed steps keep the same rotation
            if delta == 1:
                self.rotation = -1
            elif delta == 3:
                self.rotation = 1
        self.last_seq = curr_seq
        self.last_delta = delta
        self.last_rotation = self.rotation

    def phase_change(self, channel):
        self.a_phase = GPIO.input(self.a_pin)
        self.b_phase = GPIO.input(self.b_pin)
        self.get_delta()

    def run(self):
        self.running = True
        GPIO.add_event_callback(self.a_pin, self.phase_change)
        GPIO.add_event_callback(self.b_pin, self.phase_change)

    def stop(self):
        self.running = False
