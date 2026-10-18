import pygame
from dataclasses import dataclass, field

USE_MUSIC_POS = True

@dataclass
class HitObject:
    time_ms: int

class Scene:
    def init(self, app):
        pass
    def uninit(self, app):
        pass
    def update(self, app):
        pass
    def draw(self, app):
        pass

class MainMenuScene(Scene):
    def update(self, app):
        self.immediate_draw_objects = []
        if button(self.immediate_draw_objects, "Play", (100, 100), app.font):
            app.scene_transition(GameplayScene())
        if button(self.immediate_draw_objects, "Setting", (100, 200), app.font):
            app.scene_transition(SettingScene())
        if button(self.immediate_draw_objects, "Exit", (100, 300), app.font):
            app.running = False
        app.clock.tick(60)

    def draw(self, app):
        app.screen.fill((255, 255, 255))
        app.screen.blits(self.immediate_draw_objects)

class GameplayScene(Scene):
    def init(self, app):
        SONG_PATH = "/Users/nb21st/programming/rhythm-pygame/music/overdoser.mp3"
        self.judge_feedback: list[str, int] = [None, 0]
        self.time_ms: int = 0
        self.score: int = 0
        self.hit_objects = (
            [HitObject(round(x * 1000)) for x in [0.5, 1.0, 2.0, 2.5, 3.0, 4.0, 5.0, 5.1, 5.3]],
            [HitObject(round(x * 1000)) for x in [0.6, 1.0, 1.8, 2.5, 3.0, 4.0, 5.0, 5.2, 5.4]],
            [HitObject(round(x * 1000)) for x in [0.7, 1.1, 1.8, 2.5, 3.0, 4.0, 5.0, 5.3, 5.6]],
            [HitObject(round(x * 1000)) for x in [0.8, 1.1, 2.0, 2.5, 3.0, 4.0, 5.0, 5.4, 5.5]],
        )
        pygame.mixer.music.load(SONG_PATH)
        pygame.mixer.music.set_volume(0.1)
        pygame.mixer.music.play()

    def update(self, app):
        just_pressed_keys = pygame.key.get_just_pressed()
        key_hits = (
            just_pressed_keys[pygame.K_d],
            just_pressed_keys[pygame.K_f],
            just_pressed_keys[pygame.K_j],
            just_pressed_keys[pygame.K_k],
        )
                    

        delta_time_ms = app.clock.tick(30)
        if USE_MUSIC_POS: new_time_ms = pygame.mixer.music.get_pos()
        else:             new_time_ms = self.time_ms + delta_time_ms
        self.time_ms = new_time_ms
        for row_i, hit_objects_row in enumerate(self.hit_objects):
            for i, hit_object in enumerate(hit_objects_row):
                VALID_TIME_WINDOW_MS = 100
                if abs(self.time_ms - hit_object.time_ms) <= VALID_TIME_WINDOW_MS:
                    if key_hits[row_i]:
                        self.score += 1
                        self.hit_objects[row_i].pop(i)
                        self.judge_feedback = ["HIT!", 500]
                        break
                elif self.time_ms - hit_object.time_ms > VALID_TIME_WINDOW_MS:
                    self.hit_objects[row_i].pop(i)
                    self.judge_feedback = ["MISSED!", 500]
                elif self.time_ms - hit_object.time_ms < VALID_TIME_WINDOW_MS:
                    break
        if sum(map(len, self.hit_objects)) == 0:
            app.latest_score = self.score
            app.scene_transition(ScoreScene())

        self.judge_feedback[1] -= delta_time_ms


    def draw(self, app):
        app.screen.fill("white")
        pygame.draw.line(
            app.screen,
            "green",
            (app.screen.get_width() // 2 - 200, app.screen.get_height() // 2),
            (app.screen.get_width() // 2 + 200, app.screen.get_height() // 2),
            2,
        )
        for row_i, hit_objects_row in enumerate(self.hit_objects):
            for hit_object in hit_objects_row:
                SPEED = 1.0
                NOTE_RADIUS = 32
                ROW_COUNT = len(self.hit_objects)
                position = (app.screen.get_width() // 2 - (NOTE_RADIUS * 2 * ROW_COUNT) // 2 + (NOTE_RADIUS * 2 * row_i) + NOTE_RADIUS,
                            app.screen.get_height() // 2 + (self.time_ms - hit_object.time_ms) * SPEED)

                if position[1] + NOTE_RADIUS < 0:
                    break

                pygame.draw.circle(app.screen, "black", position, NOTE_RADIUS)
        if self.judge_feedback[1] > 0:
            text_surface = app.font.render(self.judge_feedback[0], False, "red", "yellow")
            app.screen.blit(text_surface, (app.screen.get_width() // 2, app.screen.get_height() // 2 + self.judge_feedback[1] // 20))
    

class SettingScene(Scene):
    def update(self, app):
        app.screen.fill((0, 0, 0))

        self.immediate_draw_objects = []
        if button(self.immediate_draw_objects, "Back", (100, 100), app.font):
            app.scene_transition(MainMenuScene())

    def draw(self, app):
        app.screen.blits(self.immediate_draw_objects)

        app.clock.tick(60)

class ScoreScene(Scene):
    def update(self, app):
        self.immediate_draw_objects = []
        if button(self.immediate_draw_objects, "Main Menu", (100, 200), app.font):
            pygame.mixer.music.stop()
            app.scene_transition(MainMenuScene())

    def draw(self, app):
        score_text = app.font.render(f"Score: {app.latest_score}", False, "white")
        app.screen.fill((0, 0, 0))
        app.screen.blit(score_text, (100, 100))
        app.screen.blits(self.immediate_draw_objects)
        app.clock.tick(60)

class App:
    def __init__(self):
        pygame.init()
        self.screen        = pygame.display.set_mode((1280, 720))
        self.clock         = pygame.time.Clock()
        self.font          = pygame.font.Font(None, 32)
        self.current_scene = MainMenuScene()
        self.next_scene    = MainMenuScene()
        self.latest_score  = None
        self.running       = True
        self.main()

    def main(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.current_scene.update(self)
            self.current_scene.draw(self)
            self.current_scene = self.next_scene

            fps = self.clock.get_fps() or 1.0
            fps_text = self.font.render(f"{fps:.0f} FPS ({1000 / fps:.1f} MS)", False, "green", "black")
            self.screen.blit(fps_text)

            pygame.display.flip()

        pygame.quit()

    def scene_transition(self, next_scene):
        self.current_scene.uninit(self)
        next_scene.init(self)
        self.next_scene = next_scene

def button(draw_objects_container, label, pos, font):
    x, y = pos
    width, height = font.size(label)
    button_rect = pygame.Rect(x, y, width, height)
    mouse_pos = pygame.mouse.get_pos()
    focused = button_rect.collidepoint(mouse_pos)
    activated = focused and pygame.mouse.get_just_pressed()[0]
    color = "yellow" if focused else "white"

    result_surface = font.render(label, False, color, "black")
    draw_objects_container.append((result_surface, pos))

    return activated

if __name__ == "__main__":
    App()
