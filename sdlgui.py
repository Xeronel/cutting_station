import os
os.environ["PYSDL2_DLL_PATH"] = os.path.dirname(os.path.abspath(__file__))

import sdl2, sdl2.ext, time

sdl2.ext.init()
window = sdl2.ext.Window("test", size=(1920, 1080), flags=sdl2.SDL_WINDOW_FULLSCREEN)
window.show()
factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
sprite = factory.from_image("smile.png")

spriterenderer = factory.create_sprite_render_system(window)
spriterenderer.render(sprite)

while True:
    time.sleep(0.1)
    #window.refresh()
