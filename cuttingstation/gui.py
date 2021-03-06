import sdl2, sdl2.ext, time
from multiprocessing import Process


class GUI(Process):
    def __init__(self, length):
        Process.__init__(self)
        self.window = None
        self.renderer = None
        self.factory = None
        self.font_manager = sdl2.ext.FontManager(font_path='fonts/OpenSans-Regular.ttf', size=90)
        self.last_length = ""
        self.length = length
        self.counter = 0

    def start_sdl(self):
        sdl2.ext.init()
        self.window = sdl2.ext.Window("RotaryEncoder", size=(1280, 1024), flags=sdl2.SDL_WINDOW_FULLSCREEN)
        self.window.show()
        self.renderer = sdl2.ext.Renderer(self.window)
        self.factory = sdl2.ext.SpriteFactory(renderer=self.renderer)
        sdl2.SDL_ShowCursor(0)

    def run(self):
        try:
            self.start_sdl()
            while True:
                # Try to get length from shared memory
                try:
                    length = self.length.value
                except IOError:
                    # If the memory manager has closed this process can not operate
                    break

                # If it's changed render the new length
                if length != self.last_length:
                    self.renderer.clear(sdl2.ext.Color(0, 0, 0))
                    text = self.factory.from_text(length, fontmanager=self.font_manager)
                    self.renderer.copy(text, dstrect=(0, 0, text.size[0], text.size[1]))
                    self.renderer.present()

                self.last_length = length
                time.sleep(0.1)
        except KeyboardInterrupt:
            return
