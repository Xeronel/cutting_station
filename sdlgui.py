import os
os.environ["PYSDL2_DLL_PATH"] = os.path.dirname(os.path.abspath(__file__))

import sys, sdl2, sdl2.ext, time

sdl2.ext.init()
window = sdl2.ext.Window("test", size=(800, 600), flags=sdl2.SDL_WINDOW_FULLSCREEN)
window.show()
factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
sprite = factory.from_image("smile.png")

spriterenderer = factory.create_sprite_render_system(window)

while True:
    begin = time.time()
    for i in xrange(100):
        spriterenderer.render(sprite)
    print time.time() - begin
    window.refresh()
