from threading import Thread
import time

class UpdateCounter(Thread):
    def __init__(self, lock, shared_counter, encoder):
        Thread.__init__(self)
        self.lock = lock
        self.encoder = encoder
        self.shared_counter = shared_counter

    def run(self):
        while True:
            self.lock.acquire()
            self.shared_counter.value = self.encoder.counter
            self.lock.release()
            time.sleep(0.5)
