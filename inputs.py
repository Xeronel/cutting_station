from threading import Thread
import RPi.GPIO as GPIO
from os import system, devnull
from time import sleep
from subprocess import call
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont


class Inputs(Thread):
    def __init__(self, ok, cancel, buttons, sounds, length, lock):
        Thread.__init__(self)

        # Uline 3in x 1in direct thermal label
        self.lblSize = (216, 72)

        # Register fonts
        fonts = ['OpenSans-Bold', 'OpenSans-Regular']
        for font in fonts:
            f = TTFont(font, 'fonts/' + font + '.ttf')
            registerFont(f)

        self.ok = ok
        self.cancel = cancel
        self.buttons = buttons
        self.sounds = sounds
        self.counter = 0
        self.length = length
        self.lock = lock

    def beep(self, channel):
        if channel in self.sounds:
            system('mpg123 -q %s &' % self.sounds[channel])

    def update_gui(self):
        # Update GUI
        feet, counter = divmod(self.counter, 600)
        inches = int(counter) / 50
        self.lock.acquire()
        self.length.value = "Feet: %s, Inches %s" % (feet, inches)
        self.lock.release()

    def add_count(self, count):
        self.counter += count
        self.update_gui()

    def print_label(self):
        c = canvas.Canvas('/tmp/examplelabel.pdf', pagesize=self.lblSize)
        width = self.lblSize[0]
        x_offset = 4

        # Draw Footage
        c.setFont('OpenSans-Bold', 16)
        c.drawString(x_offset, 56, "30'")

        # Draw description and part number
        c.setFont('OpenSans-Regular', 12)
        c.drawString(x_offset, 32, '12/2 ROMEX')
        c.drawString(x_offset, 6, '93512230R')

        # Draw serial number
        lc_width = c.stringWidth('L1C1', 'OpenSans-Regular', 12)
        c.drawString(width - lc_width - 6, 32, "L1C1")

        # Finalize page and save file
        c.showPage()
        c.save()
        call(['/usr/bin/lp', '/tmp/examplelabel.pdf'],
             stdout=open(devnull, 'w'),
             close_fds=True)

    def run(self):
        while True:
            for button, prev_state in self.buttons.items():
                pressed = GPIO.input(button)
                if pressed and prev_state is False:
                    self.counter = 0
                    self.update_gui()
                    self.buttons[button] = True
                    self.beep(button)
                    if button == self.ok:
                        self.print_label()
                elif not pressed and prev_state is True:
                    self.buttons[button] = False
            sleep(0.1)
