from copy              import copy
from dataclasses       import dataclass
from enum              import IntEnum, auto
import math
import zipfile

import pygame
from mutagen.mp3       import MP3
from mutagen.oggvorbis import OggVorbis
import pytweening

from utils             import *
from draw              import drawEntities
import scenes.scenes as scenes
import oszloader       as osu
import entity
import lerp
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

class guy_state_id(IntEnum):
    DNOTE = 0
    FNOTE = auto()
    JNOTE = auto()
    KNOTE = auto()
    IDLE  = auto()

class KeyState(IntEnum):
    JUST_PRESSED  = 0
    PRESSED       = auto()
    JUST_RELEASED = auto()
    RELEASED      = auto()

KEY_STATE_TABLE = [[KeyState.JUST_RELEASED, KeyState.JUST_RELEASED, KeyState.RELEASED,     KeyState.RELEASED    ],
                   [KeyState.PRESSED,       KeyState.PRESSED,       KeyState.JUST_PRESSED, KeyState.JUST_PRESSED]]

JUDGEMENT_COLORS      = [ pygame.Color("lime")
                        , pygame.Color("green")
                        , pygame.Color("dodgerblue")
                        , pygame.Color("orange")
                        , pygame.Color("red")
                        , pygame.Color("purple")
                        , pygame.Color("white")
                        ]

HIT_OBJECT_COLORS     = [ pygame.Color("#d5c2a1")
                        , pygame.Color("#bf0003")
                        , pygame.Color("#d6a0ab")
                        , pygame.Color("#58652c")
                        ]

HIT_OBJECT_COLORS_ALT = [
    pygame.Color.from_hsla(h, s, l * 1.2, a)
    for h, s, l, a in map(lambda x: x.hsla , HIT_OBJECT_COLORS)
]

HIT_LIGHTING_COLORS = JUDGEMENT_COLORS + HIT_OBJECT_COLORS

MEH_TIMING     = 0.150
OK_TIMING      = 0.100
GOOD_TIMING    = 0.066
GREAT_TIMING   = 0.044
PERFECT_TIMING = 0.033

def judgeTiming(diff: float) -> Judgement:
    """Grade a hit by how far (in seconds) it was from the note's head/tail."""
    if   diff < PERFECT_TIMING: return Judgement.PERFECT
    elif diff < GREAT_TIMING:   return Judgement.GREAT
    elif diff < GOOD_TIMING:    return Judgement.GOOD
    elif diff < OK_TIMING:      return Judgement.OK
    else:                       return Judgement.MEH

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
    delta_time_s  = 0.0

    rewinding     = False

    music_time_base = 0.0
    music_pos_base  = 0

    HITBAR_Y          = SCREEN_HEIGHT // 10 * 9
    HIT_OBJECT_RADIUS = 48
    COLUMN_GAP        = HIT_OBJECT_RADIUS * 2 + 16

    hit_lightings       = [None, None, None, None]
    judgement_feedback  = HitLighting(None, 0.0)

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

    song_length         = 0.0
    song_length_minutes = 0
    song_length_seconds = 0

    pygame.mixer.set_num_channels(32)

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

    camera_pos = entity.Position3(0, 0, 1)
    background = entity.Image(
        pos = (0, 0),
        transformation = (1, 1, 0),
        image = pygame.image.load("assets/background.png").convert(),
    )
    
    transition = entity.Circle((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 1100, (0, 0, 0))
    
    game = entity.Image(
        pos = (0, 0),
        transformation = (1, 1, 0),
        image = None,
    )

    auto_text = entity.Text((SCREEN_WIDTH - 134, SCREEN_HEIGHT - 48), big_font, "")
    score_text = entity.Text((track_pos_x + 240, SCREEN_HEIGHT - 128 + 00), big_font, "")
    combo_text = entity.Text((track_pos_x + 240, SCREEN_HEIGHT - 128 + 48), big_font, "")
    accuracy_text = entity.Text((track_pos_x + 240, SCREEN_HEIGHT - 128 + 96), small_font, "")
    time_text = entity.Text((8, SCREEN_HEIGHT - 32), small_font, "")
    combo_feedback_text = entity.Text((track_pos_x, SCREEN_HEIGHT // 2), big_font, "", center=True)
    grade_feedback_text = entity.Text((track_pos_x, SCREEN_HEIGHT // 2 - 48), big_font, "", center=True)

    guy_animations = [
        [
            pygame.image.load(
                "assets/" + codename + "000" + str(i) + ".png",
                codename + "000" + str(i) + ".png",
            ).convert_alpha()
            for i in range(4)
        ] for codename in ["Dnote", "Fnote", "Jnote", "Knote", "idle"]
    ]
    guy_animations = [
        [
            pygame.transform.flip(img, flip, False)
            for img in anim
        ] for anim, flip in zip(guy_animations, [True, False, True, False, False])
    ]
    guy = entity.Animation(
        pos = (800, 200),
        transformation = (1, 1, 0),
        animation = guy_animations[guy_state_id.IDLE],
    )
    guy_animation_durations = [
        guy.delay_ms * len(anim)
        for anim in guy_animations
    ]

    # @Note: Hit object sprites. Pre-scaled once to the note's on-screen diameter so draw.py
    #         sees an identity transform and just blits them.
    HIT_OBJECT_DIAMETER = HIT_OBJECT_RADIUS * 2.2
    note_images = [
        pygame.transform.smoothscale(
            pygame.image.load("assets/" + key_name + "-note.png").convert_alpha(),
            (HIT_OBJECT_DIAMETER, HIT_OBJECT_DIAMETER),
        ) for key_name in ["D", "F", "J", "K"]
    ]
    # Rebuilt every frame from the hit objects on screen; drawn on top of `game`.
    note_entities: List[entity.Entity] = []
    notes_layer = entity.Container(pos = (0, 0), transformation = (1, 1, 0), entities = note_entities)

    art_entities: List[entity.Entity] = [
        background,
        guy,
    ]

    game_entities: List[entity.Entity] = [
        game,
        notes_layer,
        auto_text,
        score_text,
        combo_text,
        accuracy_text,
        time_text,
        grade_feedback_text,
        combo_feedback_text,
        transition,
    ]

    transformation_events: List[lerp.TransformationEvent] = [
        lerp.TransformationEvent(
            transition,
            copy(transition),
            entity.Circle((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 0, (0, 0, 0)),
            pytweening.easeInExpo,
            0.8,
        ),
    ]

    # @Note: Guy animation state. Priority: short-note animation > held long note > idle.
    #        A short-note animation lasts guy_animation_durations[key]; a hold animation lasts
    #        exactly as long as a long note is actually being held (head hit, key still down).
    guy_state           = guy_state_id.IDLE
    guy_short_key       = None
    guy_short_time_left = 0.0
    guy_hold_key        = None
    dropped_holds       = set()  # id()s of long notes whose hold was broken (released early)

    clock.tick()

    while running:
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    import sys
                    pygame.quit()
                    sys.exit(0)
                case custom_event.QUIT_SCENE:
                    running = False
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_SPACE:
                            auto = not auto
                        case pygame.K_F1:
                            debug_state.level = (debug_state.level + 1) % debug_state.count

        delta_time_s = clock.tick(GAMEPLAY_FPS_LIMIT) / 1000
        if pygame.mixer.music.get_busy() and not rewinding:
            time = music_time_base + (pygame.mixer.music.get_pos() - music_pos_base) / 1000
        else:
            time += delta_time_s

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

        keyboard_inputs = pygame.key.get_pressed()

        # @Note: Time Machine
        if keyboard_inputs[pygame.K_LEFT] or keyboard_inputs[pygame.K_RIGHT]:
            if not rewinding:
                pygame.mixer.music.set_volume(0.0)
                rewinding = True
            offset = (keyboard_inputs[pygame.K_RIGHT] - keyboard_inputs[pygame.K_LEFT]) * 2.0 * delta_time_s * (1 + keyboard_inputs[pygame.K_LSHIFT] * 3)
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
                margin = PERFECT_TIMING
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
        camera_pos.z = 1.0 + pytweening.easeInCirc(sawtooth_visual_wave) / 20

        for key, key_state in enumerate(keys_state):
            if ((key_state == KeyState.PRESSED or key_state == KeyState.JUST_PRESSED) and
                (hit_lightings[key] is None or hit_lightings[key].grade == Judgement.NONE)):
                hit_lighting = HitLighting(Judgement.NONE, 1.0)
                hit_lightings[key] = hit_lighting

        # @Note: Instead of deleting, we can use base index and keep the previous objects. This will make rewinding easier.
        hit_object_deletes  = []
        key_hits            = [False, False, False, False]
        held_keys           = []  # columns with a long note being held this frame
        guy_restart         = False
        guy_short_time_left = max(0.0, guy_short_time_left - delta_time_s)

        for hit_object in hit_objects:
            key         = hit_object.key
            state       = keys_state[key]
            is_long     = hit_object.end_time > 0
            end_time    = hit_object.timestamp + hit_object.end_time
            begin_diff  = abs(hit_object.timestamp - time)
            end_diff    = abs(end_time - time)
            key_is_down = state == KeyState.JUST_PRESSED or state == KeyState.PRESSED
            key_is_free = not key_hits[key]  # one hit per key per frame
            grade       = None

            if (state == KeyState.JUST_PRESSED and begin_diff <= MEH_TIMING and
                not hit_object.pressed and key_is_free):
                # Head of the note (the whole note, if it is a short one).
                grade = judgeTiming(begin_diff)

                # @Note: Preventing holds object button mashing exploit.
                hit_object.pressed = True
                key_hits[key] = True
                if is_long:
                    held_keys.append(key)
                else:
                    hit_object_deletes.append(hit_object)

            elif (is_long and hit_object.pressed and state == KeyState.JUST_RELEASED and
                  end_diff <= MEH_TIMING and key_is_free):
                # Tail of a long note whose head was hit.
                grade = judgeTiming(end_diff)
                hit_object_deletes.append(hit_object)
                key_hits[key] = True

            elif end_time < time - MEH_TIMING:
                grade = Judgement.MISS
                hit_object_deletes.append(hit_object)

            else:
                # Not judged this frame. A long note counts as *held* only if its own head was
                # hit and the key is still down; letting go early breaks the hold for good,
                # pressing the key again does not revive it.
                if is_long and hit_object.pressed and id(hit_object) not in dropped_holds:
                    if key_is_down:
                        held_keys.append(key)
                        hit_lightings[key] = HitLighting(Judgement.NONE + 1 + key, 1.0)
                    else:
                        dropped_holds.add(id(hit_object))

                if hit_object.timestamp - time > MEH_TIMING:
                    break
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

            health += [4, 2, 1, 0, -10, -20, 0][grade]
            health = cramp(health, 0, 100)
            accuracy_n  += accuracy_values[grade]
            accuracy_d  += 300
            accuracy     = accuracy_n / accuracy_d

            hit_lighting = HitLighting(grade, 1.0)
            hit_lightings[key] = hit_lighting

            judgement_feedback = copy(hit_lighting)
            judgement_feedback.lifetime = 3.0

            # @Note: Only a *hit* short note triggers its (timed) animation. Long-note heads start
            #        the hold animation through `held_keys`, and tails/misses just end it.
            if not is_long and grade < Judgement.MISS:
                guy_short_key       = key
                guy_short_time_left = guy_animation_durations[key] / 1000
                guy_restart         = True

        hit_objects = list(filter(lambda x: x not in hit_object_deletes, hit_objects))

        # @Section: Guy
        # Keep showing the same held note while it is still held, otherwise pick the latest one.
        if guy_hold_key not in held_keys:
            guy_hold_key = held_keys[-1] if held_keys else None

        if guy_short_time_left > 0.0:
            guy_wanted_state = guy_short_key
        elif guy_hold_key is not None:
            guy_wanted_state = guy_hold_key
        else:
            guy_wanted_state = guy_state_id.IDLE

        if guy_restart or guy_wanted_state != guy_state:
            guy_state       = guy_wanted_state
            guy.animation   = guy_animations[guy_state]
            guy.frame_index = 0
            guy.excess_ms   = 0

        # @Section: Draw

        game.image = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)

        # @Note: This seems inflexible
        sawtooth_color_light   = pygame.Color((255, 255, 255))
        sawtooth_color_dark    = pygame.Color((255, 255, 255))
        sawtooth_color_light.a = 100 + int(sawtooth_visual_wave * 155)
        sawtooth_color_dark.a  = 55 + int(sawtooth_visual_wave * 35)
        sawtooth_color_light   = sawtooth_color_light.premul_alpha()
        sawtooth_color_dark    = sawtooth_color_dark.premul_alpha()
        sawtooth_color_light.a = 255
        sawtooth_color_dark.a  = 255

        pygame.draw.rect(
            game.image,
            pygame.Color((0, 0, 0, 155)),
            (track_pos_x + -1.5 * COLUMN_GAP - HIT_OBJECT_RADIUS - 16, 0, 3 * COLUMN_GAP + 2 * HIT_OBJECT_RADIUS + 32, SCREEN_HEIGHT),
        )

        for column_track_i in range(4):
            pygame.draw.rect(
                game.image,
                pygame.Color((0, 0, 0, 200)),
                (track_pos_x + (column_track_i - 1.5) * COLUMN_GAP - HIT_OBJECT_RADIUS, 0, (HIT_OBJECT_RADIUS * 2), HITBAR_Y),
            )

        # @Note: Draw BPM guide lines.
        bpm_line_pos_y = ((HITBAR_Y - (HITBAR_Y)) + (time / 2 * bps) * (HITBAR_Y)) % HITBAR_Y
        bpm_line_pos_x_start = track_pos_x + -1.5 * COLUMN_GAP - HIT_OBJECT_RADIUS - 16
        bpm_line_pos_x_end   = bpm_line_pos_x_start + 3 * COLUMN_GAP + 2 * HIT_OBJECT_RADIUS + 32
        pygame.draw.line(game.image, pygame.Color("gray20"), (bpm_line_pos_x_start, bpm_line_pos_y), (bpm_line_pos_x_end, bpm_line_pos_y), 8)

        for key, hit_lighting in filter(lambda xs: xs[1] is None, enumerate(hit_lightings)):
            pygame.draw.circle(
                game.image,
                pygame.Color("black"),
                (track_pos_x + (key - 1.5) * COLUMN_GAP, HITBAR_Y),
                HIT_OBJECT_RADIUS,
            )

        note_entities.clear()
        for hit_object in hit_objects:
            SPEED = 1800
            pos   = HITBAR_Y - (hit_object.timestamp - time) * SPEED

            if pos < -HIT_OBJECT_RADIUS:
                break

            secondary_color   = HIT_OBJECT_COLORS_ALT[hit_object.key]
            note_x            = round(track_pos_x + (hit_object.key - 1.5) * COLUMN_GAP)

            is_long_note = hit_object.end_time > 0.0

            if is_long_note:
                end_pos = pos - hit_object.end_time * SPEED
                height  = max(0, min(HITBAR_Y - end_pos, pos - end_pos)) if keys_state[hit_object.key] == KeyState.PRESSED \
                          else hit_object.end_time * SPEED

                pygame.draw.rect(
                    game.image,
                    secondary_color,
                    (track_pos_x + (hit_object.key - 1.5) * COLUMN_GAP - HIT_OBJECT_RADIUS, end_pos,
                     HIT_OBJECT_RADIUS * 2, height)
                )

            # The far end of the note (for a short note that is the note itself).
            note_entities.append(entity.Image(
                (note_x, round(pos - hit_object.end_time * SPEED)), (1, 1, 0), note_images[hit_object.key], True))

            if not is_long_note or (pos > HITBAR_Y and keys_state[hit_object.key] == KeyState.PRESSED):
                continue

            # The head of a long note.
            note_entities.append(entity.Image(
                (note_x, round(pos)), (1, 1, 0), note_images[hit_object.key], True))

        for key, hit_lighting in filter(lambda xs: xs[1] is not None, enumerate(hit_lightings)):
            h, s, v, a = HIT_LIGHTING_COLORS[hit_lighting.grade].hsva
            color = pygame.Color.from_hsva(h, s, v * hit_lighting.lifetime, a)

            pygame.draw.circle(
                game.image,
                color,
                (track_pos_x + (key - 1.5) * COLUMN_GAP, HITBAR_Y),
                HIT_OBJECT_RADIUS,
            )
            hit_lighting.lifetime -= delta_time_s * 3 * (1 + 2 * (hit_lighting.grade == Judgement.NONE))
            if hit_lighting.lifetime <= 0.0:
                hit_lightings[key] = None

        for key_guide_x in [0, 1, 2, 3]:
            pygame.draw.circle(
                game.image,
                sawtooth_color_dark,
                (track_pos_x + (key_guide_x - 1.5) * COLUMN_GAP, HITBAR_Y),
                HIT_OBJECT_RADIUS + 4,
                4,
            )

        judgement_feedback.lifetime -= delta_time_s * 3 * (1 + 2 * (judgement_feedback.grade == Judgement.NONE))

        if judgement_feedback.lifetime <= 0.0:
            grade_feedback_text.content = ""
            combo_feedback_text.content = ""
        else:
            grade_feedback_text.color   = JUDGEMENT_COLORS[judgement_feedback.grade]
            grade_feedback_text.content = judgement_text[judgement_feedback.grade]
            combo_feedback_text.content = str(combo)

        pygame.draw.line(game.image, (0, 0, 0),   (track_pos_x + 260, SCREEN_HEIGHT // 2 + 400), (track_pos_x + 260, SCREEN_HEIGHT // 2), 32)
        pygame.draw.line(game.image, (200, 0, 0), (track_pos_x + 260, SCREEN_HEIGHT // 2 + 398), (track_pos_x + 260, SCREEN_HEIGHT // 2 + 2 + 400 * ((100 - health) / 100)), 28)

        cramped_time  = cramp(time, 0, song_length)
        cramped_time_minutes = math.trunc(cramped_time / 60)
        cramped_time_seconds = math.floor(math.fmod(cramped_time, 60))

        auto_text.content     = "AUTO"
        score_text.content    = f'{score:.0f}'
        combo_text.content    = f'{combo}x'
        accuracy_text.content = f'{accuracy * 100:.2f}%'
        time_text.content     = f'{cramped_time_minutes}:{cramped_time_seconds:02}/{song_length_minutes}:{song_length_seconds:02} ({cramped_time / song_length * 100:.0f}%)'
        auto_text.content     = "AUTO" * auto # @Note: It's funny
            
        pygame.draw.rect(game.image, (0, 0, 0), (0, SCREEN_HEIGHT - 4, SCREEN_WIDTH, 4))
        pygame.draw.rect(game.image, (255, 255, 0), (0, SCREEN_HEIGHT - 4, int(SCREEN_WIDTH * (time / song_length)), 4))

        lerp.processTransformationEvents(transformation_events, delta_time_s)
        cam_pos, cam_tf = cameraTransform(camera_pos.x, camera_pos.y, camera_pos.z)
        drawEntities(screen, art_entities, cam_pos, cam_tf)
        drawEntities(screen, game_entities)

        if debug_state.level >= 1:
            quick_debug_info = {}
            bulk_debug_info = {}
        if debug_state.level >= 2:
            quick_debug_info.update({
                "camera pos": (f"({camera_pos.x:.2f}, {camera_pos.y:.2f})"),
            })
        if debug_state.level >= 3:
            pass
        if debug_state.level >= 1:
            drawDebugInfo(screen, clock.get_fps(), quick_debug_info, bulk_debug_info)

        pygame.display.flip()

    return next_scene, context
