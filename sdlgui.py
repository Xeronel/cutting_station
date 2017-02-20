import os
os.environ["PYSDL2_DLL_PATH"] = os.path.dirname(os.path.abspath(__file__))
import sdl2, sdl2.ext, time
from multiprocessing import Process


class GUI(Process):
    def __init__(self):
        Process.__init__(self)
        sdl2.ext.init()
        window = sdl2.ext.Window("RotaryEncoder", size=(1280, 1024), flags=sdl2.SDL_WINDOW_FULLSCREEN)
        window.show()
        factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
        sprite = factory.from_image("smile.png")
        spriterenderer = factory.create_sprite_render_system(window)
        spriterenderer.render(sprite)


sdl2.ext.init()
window = sdl2.ext.Window("RotaryEncoder", size=(1280, 1024), flags=sdl2.SDL_WINDOW_FULLSCREEN)
window.show()

renderer = sdl2.ext.Renderer(window)
managerfont = sdl2.ext.FontManager(font_path='fonts/OpenSans-Regular.ttf', size=50)
factory = sdl2.ext.SpriteFactory(renderer=renderer)

i = 0

while True:
    i += 1
    text = factory.from_text(str(i), fontmanager=managerfont)
    renderer.copy(text, dstrect=(0, 0, text.size[0], text.size[1]))
    renderer.present()
    time.sleep(1)
    renderer.clear(sdl2.ext.Color(0, 0, 0))
    #window.refresh()
