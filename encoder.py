import RPi.GPIO as GPIO
from threading import Thread
import time


class RotaryEncoder(Thread):
    def __init__(self, a_pin, b_pin):
        Thread.__init__(self)
        self.a_pin = a_pin
        self.b_pin = b_pin
        self.last_delta = 0
        self.last_seq = self.rotation_sequence()
        self.rotation = 1
        self.running = False

    def rotation_sequence(self):
        # SEQ | A | B
        #  0  | 0 | 0
        #  1  | 1 | 0
        #  2  | 1 | 1
        #  3  | 0 | 1
        a_state = GPIO.input(self.a_pin)
        b_state = GPIO.input(self.b_pin)
        return (a_state ^ b_state) | b_state << 1

    def get_delta(self):
        curr_seq = self.rotation_sequence()

        # 0 | No Change
        # 1 | Clockwise
        # 2 | Missed a step
        # 3 | Counter clockwise
        delta = (curr_seq - self.last_seq) % 4

        # If clockwise set a positive rotation
        # If counter clockwise set a negative rotation
        # If 0 rotation or missed steps keep the same rotation
        if delta == 1:
            self.rotation = 1
        elif delta == 3:
            self.rotation = -1

        self.last_seq = curr_seq
        self.last_delta = delta

    def run(self):
        self.running = True
        while self.running:
            self.get_delta()
            time.sleep(0.01)

    def stop(self):
        self.running = False
