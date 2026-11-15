import pygame
import math
import zipfile
from copy              import copy
from dataclasses       import dataclass
from enum              import IntEnum, auto
from mutagen.mp3       import MP3
from mutagen.oggvorbis import OggVorbis
from utils             import *
from draw              import drawEntities
import scenes.scenes as scenes
import oszloader       as osu
import entity
import data_io

@dataclass
class HitLighting:
    grade:     int
    lifetime:  float

class Judgement(IntEnum):
    PERFECT = 0
    GREAT   = auto()
    GOOD    = auto()
    OK      = auto()
    MEH     = auto()
    MISS    = auto()
    NONE    = auto()

judgement_text = [
    "PERFECT",
    "GREAT",
    "GOOD",
    "OK",
    "MEH",
    "MISS",
    "",
]

class KeyState(IntEnum):
    JUST_PRESSED  = 0
    PRESSED       = auto()
    JUST_RELEASED = auto()
    RELEASED      = auto()

KEY_STATE_TABLE = [[KeyState.JUST_RELEASED, KeyState.JUST_RELEASED, KeyState.RELEASED,     KeyState.RELEASED    ],
                   [KeyState.PRESSED,       KeyState.PRESSED,       KeyState.JUST_PRESSED, KeyState.JUST_PRESSED]]

JUDGEMENT_COLORS  = [ pygame.Color("lime")
                    , pygame.Color("green")
                    , pygame.Color("dodgerblue")
                    , pygame.Color("orange")
                    , pygame.Color("red")
                    , pygame.Color("purple")
                    , pygame.Color("white")
                    ]

HIT_OBJECT_COLORS = [ pygame.Color("tomato")
                    , pygame.Color("gold")
                    , pygame.Color("springgreen")
                    , pygame.Color("deepskyblue")
                    ]

HIT_LIGHTING_COLORS = JUDGEMENT_COLORS + HIT_OBJECT_COLORS

def gameplay(screen, context):
    next_scene = scenes.chartSelection
    beatmapset_filename, beatmap_filename, beatmap_id = context

    auto            = False
    beatmap_name    = ""
    song_filename   = ""

    track_pos_x     = SCREEN_WIDTH // 4

    beatmaps_directory = "songs/"

    hit_objects   = []
    total_notes   = 0

    health = 100

    running       = True
    clock         = pygame.time.Clock()
    counting_down = False
    time          = 0.0
    dt            = 0.0

    rewinding     = False

    music_time_base = 0.0
    music_pos_base  = 0

    HITBAR_Y      = SCREEN_HEIGHT // 10 * 9
    COLUMN_GAP    = 80

    hit_lightings       = [None, None, None, None]
    judgement_feedback  = None

    small_font = pygame.font.SysFont("Liberation Sans", 16)
    big_font   = pygame.font.Font(None, 64)

    MAX_SCORE        = 1_000_000.0
    mod_multiplier   = 1.0
    mod_divider      = 1.0
    combo            = 0
    score            = 0
    base_score       = 0
    bonus_score      = 0
    bonus            = 100
    accuracy_n       = 0
    accuracy_d       = 0
    accuracy         = 0

    accuracy_values  = [300, 300, 200, 100, 50,         0]
    hit_values       = [320, 300, 200, 100, 50,         0]
    hit_bonus_values = [32,   32,  16,   8,  4,         0]
    hit_bonuses      = [ 2,    1,   0,   0,  0,         0]
    hit_punishments  = [ 0,    0,   8,  24, 44, -math.inf]

    game_end = False

    # @Todo: Figure out how to implement difficulty.
    MEH_TIMING     = 0.150
    OK_TIMING      = 0.100
    GOOD_TIMING    = 0.066
    GREAT_TIMING   = 0.044
    PERFECT_TIMING = 0.033

    song_length         = 0.0
    song_length_minutes = 0
    song_length_seconds = 0

    pygame.mixer.set_num_channels(64)

    hitsounds  = [ pygame.mixer.Sound("sounds/hitsound_alt.wav")
                 , pygame.mixer.Sound("sounds/hitsound_whistle.wav")
                 , pygame.mixer.Sound("sounds/hitsound_finish.wav")
                 , pygame.mixer.Sound("sounds/hitsound_clap.wav")
                 , pygame.mixer.Sound("sounds/hitsound_normal.wav")
                 ]

    for hitsound, volume in zip(hitsounds, [0.05, 0.1, 0.1, 0.1, 0.05]):
        hitsound.set_volume(volume)

    music_volume_raw = 0.08
    pygame.mixer.music.set_volume(music_volume_raw)


    keys_state = [ KeyState.RELEASED
                 , KeyState.RELEASED
                 , KeyState.RELEASED
                 , KeyState.RELEASED
                 ]

    result = osu.load(beatmaps_directory, beatmapset_filename, beatmap_filename)

    if result == None:
        return None

    song_filename, bpm, hit_objects = result
    bps = bpm / 60
    total_notes = len(hit_objects) + sum(map(lambda x: x.end_time != 0, hit_objects))

    zf = zipfile.ZipFile(beatmaps_directory + '/' + beatmapset_filename, 'r')
    f  = zf.open(song_filename)

    if song_filename.endswith(".mp3"):
        song_length = MP3(f).info.length
    elif song_filename.endswith(".ogg"):
        song_length = OggVorbis(f).info.length

    song_length_minutes = int(song_length) // 60
    song_length_seconds = int(song_length) % 60

    f.seek(0)
    pygame.mixer.music.load(f)

    time = -2.0
    counting_down = True

    camera_pos = entity.Position2(0, 0)
    background = entity.Image(
        pos = (0, 0),
        transformation = (1, 1, 0),
        image = pygame.image.load("assets/background.png").convert(),
    )

    entities: List[entity.Entity] = [
        background,
    ]

    while running:
        if counting_down and time >= 0.0:
            pygame.mixer.music.play()
            music_time_base = 0.0
            music_pos_base  = pygame.mixer.music.get_pos()
            counting_down = False

        # @Note: End Game
        song_end = time >= song_length and song_length > 0.0
        if health <= 0:
            pygame.mixer.music.stop()
            running = False
        elif song_end and not game_end:
            # Write beatmap_id and score to files
            pygame.mixer.music.stop()
            data_io.write_data("data/score.txt", {beatmap_id:round(score)})
            pygame.time.set_timer(custom_event.QUIT_SCENE, 3000, 1)
            game_end = True

        for event in pygame.event.get():
            match event.type:
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_SPACE:
                            auto = not auto

                case pygame.QUIT:
                    import sys
                    pygame.quit()
                    sys.exit(0)
                case custom_event.QUIT_SCENE:
                    running = False

        keyboard_inputs = pygame.key.get_pressed()

        # @Note: Time Machine
        if keyboard_inputs[pygame.K_LEFT] or keyboard_inputs[pygame.K_RIGHT]:
            if not rewinding:
                pygame.mixer.music.set_volume(0.0)
                rewinding = True
            offset = (keyboard_inputs[pygame.K_RIGHT] - keyboard_inputs[pygame.K_LEFT]) * 2.0 * dt * (1 + keyboard_inputs[pygame.K_LSHIFT] * 3)
            time += offset

        elif rewinding:
            rewinding = False
            if pygame.mixer.music.get_busy():
                time = max(time, 0.0)
                pygame.mixer.music.rewind()
                pygame.mixer.music.set_pos(time)
                music_time_base = time
                music_pos_base  = pygame.mixer.music.get_pos()
            pygame.mixer.music.set_volume(music_volume_raw)


        config = data_io.read_data("data/config.txt")

        pressed_keys = [ keyboard_inputs[pygame.key.key_code(config["key1"])],
                         keyboard_inputs[pygame.key.key_code(config["key2"])],
                         keyboard_inputs[pygame.key.key_code(config["key3"])],
                         keyboard_inputs[pygame.key.key_code(config["key4"])],
                       ]

        # @Note: That's right. We're gonna cheat.
        if auto:
            for hit_object in hit_objects:
                margin = PERFECT_TIMING / 3 * 2
                begin_diff = abs(hit_object.timestamp - time)
                end_diff   = abs(hit_object.timestamp + hit_object.end_time - time)

                if hit_object.timestamp - time > margin:
                    break

                if begin_diff < margin:
                    pressed_keys[hit_object.key] = True
                elif hit_object.end_time > 0 and end_diff < margin:
                    pressed_keys[hit_object.key] = False
                elif (time + margin > hit_object.timestamp and hit_object.end_time > 0 and
                      (keys_state[hit_object.key] == KeyState.JUST_PRESSED or keys_state[hit_object.key] == KeyState.PRESSED)):
                    pressed_keys[hit_object.key] = True

        keys_state = [KEY_STATE_TABLE[press][state] for press, state in zip(pressed_keys, keys_state)]

        sawtooth_visual_wave = ((1/bps) - (time / 2) % (1/bps)) / (1/bps)

        for key, key_state in enumerate(keys_state):
            if ((key_state == KeyState.PRESSED or key_state == KeyState.JUST_PRESSED) and
                (hit_lightings[key] is None or hit_lightings[key].grade == Judgement.NONE)):
                hit_lighting = HitLighting(Judgement.NONE, 1.0)
                hit_lightings[key] = hit_lighting

        # @Note: Instead of deleting, we can use base index and keep the previous objects. This will make rewinding easier.
        hit_object_deletes = []
        key_hits = [False, False, False, False]
        for hit_object in hit_objects:
            begin_diff = abs(hit_object.timestamp - time)
            end_diff   = abs(hit_object.timestamp + hit_object.end_time - time)
            grade      = None

            if (keys_state[hit_object.key] == KeyState.JUST_PRESSED and begin_diff <= MEH_TIMING and
                hit_object.pressed == False and not key_hits[hit_object.key]):
                if   begin_diff < PERFECT_TIMING: grade = Judgement.PERFECT
                elif begin_diff < GREAT_TIMING:   grade = Judgement.GREAT
                elif begin_diff < GOOD_TIMING:    grade = Judgement.GOOD
                elif begin_diff < OK_TIMING:      grade = Judgement.OK
                else:                             grade = Judgement.MEH

                # @Note: Preventing holds object button mashing exploit.
                hit_object.pressed = True

                if hit_object.end_time == 0:
                    hit_object_deletes.append(hit_object)
                key_hits[hit_object.key] = True
            elif (hit_object.end_time > 0 and
                  keys_state[hit_object.key] == KeyState.JUST_RELEASED and end_diff <= MEH_TIMING and
                  not key_hits[hit_object.key]):
                if   end_diff < PERFECT_TIMING: grade = Judgement.PERFECT
                elif end_diff < GREAT_TIMING:   grade = Judgement.GREAT
                elif end_diff < GOOD_TIMING:    grade = Judgement.GOOD
                elif end_diff < OK_TIMING:      grade = Judgement.OK
                else:                           grade = Judgement.MEH

                hit_object_deletes.append(hit_object)
                key_hits[hit_object.key] = True
            elif (hit_object.timestamp + hit_object.end_time) < time - MEH_TIMING:
                grade = Judgement.MISS
                hit_object_deletes.append(hit_object)
            elif (time + 0.1 >= hit_object.timestamp and hit_object.end_time > 0 and
                  (keys_state[hit_object.key] == KeyState.JUST_PRESSED or keys_state[hit_object.key] == KeyState.PRESSED)):
                hit_lightings[key] = HitLighting(Judgement.NONE + 1 + hit_object.key, 1.0)

                continue
            elif hit_object.timestamp - time > MEH_TIMING:
                break
            else:
                continue

            combo += 1
            if grade < Judgement.MISS:
                if not any(hit_object.hitsounds):
                    hitsounds[-1].play()
                else:
                    for bit, hitsound in zip(hit_object.hitsounds, hitsounds):
                        if bit: hitsound.play()
            else:
                combo = 0

            bonus        = max(0, min(100, bonus + hit_bonuses[grade] - hit_punishments[grade] / mod_divider))
            base_score  += (MAX_SCORE * mod_multiplier * 0.5 / total_notes) * (hit_values[grade] / 320)
            bonus_score += (MAX_SCORE * mod_multiplier * 0.5 / total_notes) * (hit_bonus_values[grade] * math.sqrt(bonus) / 320)
            score        = base_score + bonus_score

            health += [4, 2, 1, 0, -2, -10, 0][grade]
            health = cramp(health, 0, 100)
            accuracy_n  += accuracy_values[grade]
            accuracy_d  += 300
            accuracy     = accuracy_n / accuracy_d

            hit_lighting = HitLighting(grade, 1.0)
            hit_lightings[hit_object.key] = hit_lighting
            judgement_feedback = copy(hit_lighting)
            judgement_feedback.lifetime = 3.0

        hit_objects = list(filter(lambda x: x not in hit_object_deletes, hit_objects))

        # @Section: Draw

        drawEntities(screen, entities, (-camera_pos.x, -camera_pos.y))

        # @Note: This seems inflexible
        sawtooth_color_light   = pygame.Color((255, 255, 255))
        sawtooth_color_dark    = pygame.Color((255, 255, 255))
        sawtooth_color_light.a = 100 + int(sawtooth_visual_wave * 155)
        sawtooth_color_dark.a  = int(sawtooth_visual_wave * 30)
        sawtooth_color_light   = sawtooth_color_light.premul_alpha()
        sawtooth_color_dark    = sawtooth_color_dark.premul_alpha()

        track_bg = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
        pygame.draw.rect(
            track_bg,
            pygame.Color((0, 0, 0)),
            (track_pos_x - (80 + 96), 0, (80 + 96) * 2, SCREEN_HEIGHT)
        )
        track_bg.set_alpha(200)
        screen.blit(track_bg)

        for column_track_i in range(4):
            pygame.draw.rect(
                screen,
                pygame.Color((0, 0, 0)),
                (track_pos_x + (column_track_i - 1.5) * COLUMN_GAP - 32, 0, 64, HITBAR_Y),
            )

        # @Note: Draw BPM guide lines.
        for i in range(3):
            three = 1
            line_pos_y = ((HITBAR_Y - (HITBAR_Y / three) * i) + (time / 2 * bps) * (HITBAR_Y / three)) % HITBAR_Y
            pygame.draw.line(screen, pygame.Color("gray20"), (track_pos_x - (80 + 96), line_pos_y), (track_pos_x + (80 + 96), line_pos_y), 2)

        for key, hit_lighting in filter(lambda xs: xs[1] is None, enumerate(hit_lightings)):
            pygame.draw.circle(
                screen,
                pygame.Color("black"),
                (track_pos_x + (key - 1.5) * COLUMN_GAP, HITBAR_Y),
                32,
            )

        for hit_object in hit_objects:
            SPEED = 1400
            size  = 32 # @Note: Radius
            pos   = HITBAR_Y - (hit_object.timestamp - time) * SPEED

            if pos < -32:
                break

            primary_color     = HIT_OBJECT_COLORS[hit_object.key]
            secondary_color   = primary_color
            secondary_color.a = 85
            secondary_color   = secondary_color.premul_alpha()

            is_long_note = hit_object.end_time > 0.0

            if is_long_note:
                end_pos = pos - hit_object.end_time * SPEED
                height  = max(0, min(HITBAR_Y - end_pos, pos - end_pos)) if keys_state[hit_object.key] == KeyState.PRESSED \
                          else hit_object.end_time * SPEED

                pygame.draw.rect(
                    screen,
                    secondary_color,
                    (track_pos_x + (hit_object.key - 1.5) * COLUMN_GAP - size, end_pos,
                     size * 2, height)
                )

            pygame.draw.circle(
                screen,
                primary_color,
                (track_pos_x + (hit_object.key - 1.5) * COLUMN_GAP, pos - int(hit_object.end_time * SPEED)),
                size,
            )

            if not is_long_note or (pos > HITBAR_Y and keys_state[hit_object.key] == KeyState.PRESSED):
                continue

            pygame.draw.circle(
                screen,
                primary_color,
                (track_pos_x + (hit_object.key - 1.5) * COLUMN_GAP, pos),
                size,
            )

        for key, hit_lighting in filter(lambda xs: xs[1] is not None, enumerate(hit_lightings)):
            color = HIT_LIGHTING_COLORS[hit_lighting.grade]
            color.a = int(255 * cramp(hit_lighting.lifetime, 0, 1))
            color = color.premul_alpha()

            pygame.draw.circle(
                screen,
                color,
                (track_pos_x + (key - 1.5) * COLUMN_GAP, HITBAR_Y),
                32,
            )
            hit_lighting.lifetime -= dt * 3 * (1 + 2 * (hit_lighting.grade == Judgement.NONE))
            if hit_lighting.lifetime <= 0.0:
                hit_lightings[key] = None

        for key_guide_x in [0, 1, 2, 3]:
            pygame.draw.circle(
                screen,
                sawtooth_color_light,
                (track_pos_x + (key_guide_x - 1.5) * COLUMN_GAP, HITBAR_Y),
                8,
            )

        if judgement_feedback is not None:
            judgement_feedback.lifetime -= dt * 3 * (1 + 2 * (judgement_feedback.grade == Judgement.NONE))

            if judgement_feedback.lifetime <= 0.0:
                judgement_feedback = None
            else:
                text = judgement_text[judgement_feedback.grade]
                combo_text = str(combo)
                feedback_surface = big_font.render(text, True, JUDGEMENT_COLORS[judgement_feedback.grade])
                feedback_surface_rect = feedback_surface.get_rect(center=(track_pos_x, SCREEN_HEIGHT // 2 - 48))
                big_font.outline = 2
                outline_surface = big_font.render(text, True, (0, 0, 0))
                outline_surface.blit(feedback_surface, (2, 2))
                feedback_surface = outline_surface
                big_font.outline = 0

                combo_feedback_surface = big_font.render(combo_text, True, (255, 255, 255))
                combo_feedback_surface_rect = combo_feedback_surface.get_rect(center=(track_pos_x, SCREEN_HEIGHT // 2))
                big_font.outline = 2
                combo_outline_surface = big_font.render(combo_text, True, (0, 0, 0))
                combo_outline_surface.blit(combo_feedback_surface, (2, 2))
                combo_feedback_surface = combo_outline_surface
                big_font.outline = 0
    
                screen.blit(feedback_surface, feedback_surface_rect)
                screen.blit(combo_feedback_surface, combo_feedback_surface_rect)


        pygame.draw.line(screen, "red", (track_pos_x + 220, SCREEN_HEIGHT // 2 + 400), (track_pos_x + 220, SCREEN_HEIGHT // 2 + 400 * ((100 - health) / 100)), 32)

        cramped_time  = cramp(time, 0, song_length)
        cramped_time_minutes = math.trunc(cramped_time / 60)
        cramped_time_seconds = math.floor(math.fmod(cramped_time, 60))
        auto_text     = big_font.render("AUTO", True, pygame.Color("yellow"))
        score_text    = big_font.render(f'{score:.0f}', True, pygame.Color("white"))
        combo_text    = big_font.render(f'{combo}x', True, pygame.Color("white"))
        accuracy_text = small_font.render(f'{accuracy * 100:.2f}%', True, pygame.Color("white"))
        time_percent  = cramped_time / song_length * 100
        time_text     = small_font.render(
            f'{cramped_time_minutes}:{cramped_time_seconds:02}/{song_length_minutes}:{song_length_seconds:02} ({time_percent:.0f}%)',
            True,
            pygame.Color("white"),
        )
        screen.blit(score_text,    (track_pos_x + 200, SCREEN_HEIGHT - 128 + 00))
        screen.blit(combo_text,    (track_pos_x + 200, SCREEN_HEIGHT - 128 + 48))
        screen.blit(accuracy_text, (track_pos_x + 200, SCREEN_HEIGHT - 128 + 96))
        screen.blit(time_text,     (8, SCREEN_HEIGHT - 32))
        if auto: screen.blit(auto_text, (SCREEN_WIDTH - 134, SCREEN_HEIGHT - 48))
        pygame.draw.rect(screen, pygame.Color("yellow"), (0, SCREEN_HEIGHT - 4, int(SCREEN_WIDTH * (time / song_length)), 4))


        if debug_state.level >= 1:
            quick_debug_info = {}
            bulk_debug_info = {}
        if debug_state.level >= 2:
            quick_debug_info.update({
                "camera pos": (f"({camera_pos.x:.2f}, {camera_pos.y:.2f})"),
                "mouse pos": mouse_pos,
                "waiting for key id": waiting_for_key_id
            })
        if debug_state.level >= 3:
            bulk_debug_info.update({
                "entities": entities_text,
                "keybinds": keybinds,
            })
        if debug_state.level >= 1:
            drawDebugInfo(screen,clock.get_fps(), quick_debug_info,bulk_debug_info)

        pygame.display.flip()

        dt = clock.tick(GAMEPLAY_FPS_LIMIT) / 1000
        if pygame.mixer.music.get_busy() and not rewinding:
            time = music_time_base + (pygame.mixer.music.get_pos() - music_pos_base) / 1000
        else:
            time += dt

    return next_scene, context
