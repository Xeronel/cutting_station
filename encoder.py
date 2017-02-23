import RPi.GPIO as GPIO
from multiprocessing import Process
from subprocess import call
from os import devnull


class RotaryEncoder(Process):
    def __init__(self, a_pin, b_pin, ok_button, cancel_button, pipe):
        Process.__init__(self)

        self.running = False
        self.pipe = pipe

        # Buttons that should reset the count
        self.ok = ok_button
        self.cancel = cancel_button

        # Set A and B phase pins
        self.a_pin = a_pin
        self.b_pin = b_pin

        # Set initial values for A and B phases
        self.a_phase = 0
        self.b_phase = 0
        self.last_a_phase = 0
        self.last_b_phase = 0
        self.count = 0

    def run(self):
        self.running = True
        print("Encoder: %s" % self.pid)

        # Set priority to real-time and scheduler to fifo
        call(['chrt', '-f', '-p', '99', '%s' % self.pid],
             stdout=open(devnull, 'w'),
             close_fds=True)

        # Initialize variables to the encoder's current state
        self.a_phase = GPIO.input(self.a_pin)
        self.b_phase = GPIO.input(self.b_pin)
        self.last_a_phase = self.a_phase
        self.last_b_phase = self.b_phase

        while self.running:
            # Get the encoder's current state
            self.a_phase = GPIO.input(self.a_pin)
            self.b_phase = GPIO.input(self.b_pin)

            # Clockwise rotation
            if not self.a_phase and self.a_phase != self.last_a_phase:
                if not self.b_phase:
                    self.count += 1

            # Counter clockwise rotation
            if not self.b_phase and self.b_phase != self.last_b_phase:
                if not self.a_phase:
                    self.count -= 1

            self.last_a_phase = self.a_phase
            self.last_b_phase = self.b_phase

            if self.count == 50 or self.count == -50:
                self.pipe.send(self.count)
                self.count = 0

            if GPIO.input(self.ok) or GPIO.input(self.cancel):
                self.count = 0

            # If a message is received then exit
            if self.pipe.poll():
                self.running = False
