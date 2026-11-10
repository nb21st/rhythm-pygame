def todo(msg=""):
    raise RuntimeError("@Todo: " + msg)

def cramp(x, mn, mx):
    return min(max(x, mn), mx)

def tuple_add(xs, ys):
    return tuple(x + y for x, y in zip(xs, ys))

def tuple_sub(xs, ys):
    return tuple(x - y for x, y in zip(xs, ys))

def tuple_cramp(xs, mn, mx):
    return tuple(cramp(x, mn, mx) for x in xs)

def drawFPS(screen, clock, font):
    fps = clock.get_fps() or 1
    frametime = 1000 / fps
    text_surface = font.render(f"{fps:.0f} FPS ({frametime:.1f} MS)", False, (0, 255, 0), (0, 0, 0))
    screen.blit(text_surface)
