import pygame
from dataclasses import dataclass, field

USE_MUSIC_POS = True

@dataclass
class HitObject:
    time_ms: int

@dataclass
class App:
    screen: pygame.Surface
    clock:  pygame.Clock
    font:   pygame.Font

    hit_objects: HitObject = field(default_factory=list)
    judge_feedback: Tuple[str, int] = None
    time_ms: int = 0
    score: int = 0

    running: bool = True

def button(draw_objects_container, label, pos, font):
    x, y = pos
    width, height = font.size(label)
    button_rect = pygame.Rect(x, y, width, height)
    mouse_pos = pygame.mouse.get_pos()
    focused = button_rect.collidepoint(mouse_pos)
    activated = focused and pygame.mouse.get_just_pressed()[0]

    result_surface = font.render(label, False, "white", "black")
    draw_objects_container.append((result_surface, pos))

    return activated

def game_init(app):
    SONG_PATH = "/Users/nb21st/programming/rhythm-pygame/music/overdoser.mp3"
    app.hit_objects = [HitObject(round(x * 1000)) for x in [0.5, 1.0, 2.0, 2.5, 3.0, 4.0, 5.0, 5.1, 5.2]]
    app.time_ms = 0
    pygame.mixer.music.load(SONG_PATH)
    pygame.mixer.music.set_volume(0.1)
    pygame.mixer.music.play()
    return game_loop

def game_loop(app):
    next_loop = game_loop

    just_pressed_keys = pygame.key.get_just_pressed()
    key_hit = just_pressed_keys[pygame.K_SPACE]

    delta_time_ms = app.clock.tick(60)
    if USE_MUSIC_POS: new_time_ms = pygame.mixer.music.get_pos()
    else:             new_time_ms = app.time_ms + delta_time_ms
    app.time_ms = new_time_ms

    for i, hit_object in enumerate(app.hit_objects):
        VALID_TIME_WINDOW_MS = 100

        if abs(app.time_ms - hit_object.time_ms) <= VALID_TIME_WINDOW_MS:
            if key_hit:
                app.score += 1
                app.hit_objects.pop(i)
                app.judge_feedback = ("HIT!", 500)
                break
        elif app.time_ms - hit_object.time_ms > VALID_TIME_WINDOW_MS:
            app.hit_objects.pop(i)
            app.judge_feedback = ("MISSED!", 500)
        elif app.time_ms - hit_object.time_ms < VALID_TIME_WINDOW_MS:
            break

    if len(app.hit_objects) == 0:
        next_loop = score_loop

    app.screen.fill("white")
    pygame.draw.line(
        app.screen,
        "green",
        (app.screen.get_width() // 2 - 200, app.screen.get_height() // 2),
        (app.screen.get_width() // 2 + 200, app.screen.get_height() // 2),
        2,
    )
    for hit_object in app.hit_objects:
        NOTE_RADIUS = 32
        position = (app.screen.get_width() // 2,
                    app.screen.get_height() // 2 + (app.time_ms - hit_object.time_ms) // 2)
        if position[1] + NOTE_RADIUS < 0:
            break
        pygame.draw.circle(app.screen, "black", position, NOTE_RADIUS)

    if app.judge_feedback is not None:
        text, lifetime_ms = app.judge_feedback
        if lifetime_ms > 0:
            text_surface = app.font.render(text, False, "red", "yellow")
            app.screen.blit(text_surface, (app.screen.get_width() // 2, app.screen.get_height() // 2))
        app.judge_feedback = (text, lifetime_ms - delta_time_ms)

    return next_loop

def menu_loop(app):
    next_loop = menu_loop

    immediate_draw_objects = []
    if button(immediate_draw_objects, "Play", (100, 100), app.font):
        next_loop = game_init
    if button(immediate_draw_objects, "Setting", (100, 200), app.font):
        next_loop = setting_loop
    if button(immediate_draw_objects, "Exit", (100, 300), app.font):
        app.running = False

    app.screen.fill((255, 255, 255))
    app.screen.blits(immediate_draw_objects)

    app.clock.tick(60)

    return next_loop

def setting_loop(app):
    next_loop = setting_loop

    app.screen.fill((0, 0, 0))
    text = app.font.render("yo", False, "white")

    immediate_draw_objects = []
    if button(immediate_draw_objects, "Back", (100, 100), app.font):
        next_loop = menu_loop

    app.screen.blit(text)
    app.screen.blits(immediate_draw_objects)

    app.clock.tick(60)

    return next_loop

def score_loop(app):
    next_loop = score_loop

    text = app.font.render(f"Score: {app.score}", False, "white")

    immediate_draw_objects = []
    if button(immediate_draw_objects, "Main Menu", (100, 200), app.font):
        pygame.mixer.music.stop()
        app.score = 0
        next_loop = menu_loop

    app.screen.fill((0, 0, 0))
    app.screen.blit(text, (100, 100))
    app.screen.blits(immediate_draw_objects)

    app.clock.tick(60)

    return next_loop

def main():
    pygame.init()
    screen    = pygame.display.set_mode((1280, 720))
    clock     = pygame.time.Clock()
    font      = pygame.font.Font(None, 32)
    game_loop = menu_loop

    app = App(
        screen,
        clock,
        font,
    )

    while app.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                app.running = False

        game_loop = game_loop(app)

        fps = clock.get_fps() or 1.0
        fps_text = font.render(f"{fps:.0f} FPS ({1000 / fps:.1f} MS)", False, "green", "black")
        screen.blit(fps_text)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
