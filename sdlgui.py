import os
os.environ["PYSDL2_DLL_PATH"] = os.path.dirname(os.path.abspath(__file__))
import sdl2, sdl2.ext
from multiprocessing import Process


class GUI(Process):
    def __init__(self, conn):
        Process.__init__(self)
        self.window = None
        self.renderer = None
        self.factory = None
        self.font_manager = sdl2.ext.FontManager(font_path='fonts/OpenSans-Regular.ttf', size=90)
        self.conn = conn
        self.length = "Feet: 0, Inches: 0"
        self.counter = 0

    def render_length(self):
        feet, counter = divmod(self.counter, 600)
        inches = int(counter) / 50

        if self.counter < 0:
            return "Feet: %s, Inches: %s" % (0, 0)
        else:
            return "Feet: %s, Inches: %s" % (feet, inches)

    def start_sdl(self):
        sdl2.ext.init()
        self.window = sdl2.ext.Window("RotaryEncoder", size=(1280, 1024), flags=sdl2.SDL_WINDOW_FULLSCREEN)
        self.window.show()
        self.renderer = sdl2.ext.Renderer(self.window)
        self.factory = sdl2.ext.SpriteFactory(renderer=self.renderer)

    def run(self):
        print("SDL pid: %s" % os.getpid())
        self.start_sdl()
        while True:
            self.renderer.clear(sdl2.ext.Color(0, 0, 0))
            text = self.factory.from_text(self.length, fontmanager=self.font_manager)
            self.renderer.copy(text, dstrect=(0, 0, text.size[0], text.size[1]))
            self.renderer.present()
            self.length = self.conn.recv()
