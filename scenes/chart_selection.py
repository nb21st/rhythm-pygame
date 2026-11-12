# @Note: Standard library
from enum import IntEnum, auto
from copy import copy
# @Note: Third-Party library
import pygame
import pytweening
# @Note: Local library
from utils import *
import scenes.scenes as scenes
from draw import drawEntities
import entity
import lerp
import oszloader
import data_io

def chartSelection(screen, context):
    next_scene = None
    context    = None

    clock = pygame.time.Clock()
    running = True
    camera_pos = entity.Position2(0, 1080 * 8)

    class button_id(IntEnum):
        CHART_BACK    = 0
        CHART_PREV    = auto()
        CHART_NEXT    = auto()
        CHART_SELECT  = auto()
        VERSION_PREV = auto()
        VERSION_NEXT = auto()
        CHART_PLAY    = auto()
        COUNT         = auto()

    # @Todo, @Note: This is perfect of OOP but let's stick to procedural copy & paste for now.
    charts = oszloader.directory_preview("songs/")
    charts_count = len(charts)
    current_chart_index = 0
    def chart_inc(amount=1):
        nonlocal current_chart_index
        current_chart_index = (current_chart_index + amount) % charts_count
    def chart_dec(amount=1): chart_inc(-amount)
    def get_current_chart(): return charts[current_chart_index]
    def get_current_chart_text():
        current_chart = get_current_chart()
        return current_chart.title + "\nby " + current_chart.artist

    versions = get_current_chart().versions
    versions_count = len(versions)
    current_version_index = 0
    def update_versions():
        nonlocal versions, versions_count
        versions = get_current_chart().versions
        versions_count = len(versions)
    def version_inc(amount=1):
        nonlocal current_version_index
        current_version_index = (current_version_index + amount) % versions_count
    def version_dec(amount=1): version_inc(-amount)
    def get_current_version(): return versions[current_version_index]
    def get_current_version_highscore():
        id = get_current_version()[3]
        scores = data_io.read_data("data/score.txt")
        highscore = scores[id] if id in scores else 0
        return highscore
    def get_current_version_text():
        highscore = int(get_current_version_highscore())
        return get_current_version()[0] + (f"\n[HIGHSCORE: {highscore:,}]" if highscore > 0 else "")

    outer_background = entity.BackgroundColor(DARK_BACKGROUND_COLOR)
    decoration = entity.Image((0, 0), (1, 1, 0), pygame.image.load("assets/redwood.png", "redwood.png").convert_alpha())
    introbg_png = pygame.image.load("assets/introbg.png", "introbg.png").convert()
    inner_background = entity.Image((16, 16), ((SCREEN_WIDTH - 32) / SCREEN_WIDTH, (SCREEN_HEIGHT - 32) / SCREEN_HEIGHT, 0), introbg_png, scroll_rate=(-1, 0))
    arrow_png = pygame.image.load("assets/arrow.png", "arrow.png").convert_alpha()
    chart_back_arrow = entity.Container(
        pos = (100, 100),
        transformation = (1, 1, 0),
        entities = [
            entity.CircleButton((0, 0), 64, id=button_id.CHART_BACK),
            entity.Image((0, 0), (0.6, 0.6, 90), arrow_png, True),
        ],
    )
    prev_arrow_image       = entity.Image((0, 0), (0.6, 0.6, 0), arrow_png, True)
    prev_arrow_image_small = entity.Image((0, 0), (0.4, 0.4, 0), arrow_png, True)
    chart_prev_arrow = entity.Container(
        pos = (SCREEN_WIDTH - 512, SCREEN_HEIGHT // 2 - 256),
        transformation = (1, 1, 0),
        entities = [
            entity.CircleButton((0, 0), 64, id=button_id.CHART_PREV),
            prev_arrow_image,
        ],
        visible = False,
    )
    next_arrow_image       = entity.Image((0, 0), (0.6, 0.6, 180), arrow_png, True)
    next_arrow_image_small = entity.Image((0, 0), (0.4, 0.4, 180), arrow_png, True)
    chart_next_arrow = entity.Container(
        pos = (SCREEN_WIDTH - 512, SCREEN_HEIGHT // 2 + 256),
        transformation = (1, 1, 0),
        entities = [
            entity.CircleButton((0, 0), 64, id=button_id.CHART_NEXT),
            next_arrow_image,
        ],
        visible = bool(charts_count),
    )
    chart_select_arrow = entity.Container(
        pos = (SCREEN_WIDTH - 512 - 256, SCREEN_HEIGHT // 2),
        transformation = (1, 1, 0),
        entities = [
            entity.CircleButton((0, 0), 64, id=button_id.CHART_SELECT),
            entity.Image((0, 0), (0.6, 0.6, 90), arrow_png, True)
        ],
        visible = True,
    )
    linchuck_png = pygame.image.load("assets/linchuck.png", "linchuck.png").convert_alpha()
    linchuck_image = entity.Image((-80, 0), (0.8, 0.8, 0), linchuck_png, True)
    current_chart_text = entity.Text((-280, -32), pygame.font.Font(None, 42), get_current_chart_text())
    current_chart_display = entity.Container(
        pos = (SCREEN_WIDTH - 256, SCREEN_HEIGHT // 2),
        transformation = (1, 1, 0),
        entities = [
            linchuck_image,
            current_chart_text,
        ],
    )
    paper_png    = pygame.image.load("assets/paper.png", "paper.png").convert_alpha()
    play_png     = pygame.image.load("assets/play.png", "play.png").convert_alpha()
    paper_image  = entity.Image((500, 540), (1, 1, 0), paper_png, True)
    play_image   = entity.Image((500, 780), (1, 1, 0), play_png, True)
    play_button  = entity.RectButton(play_image.pos, play_image.image.get_size(), id=button_id.CHART_PLAY, center=True)
    version_text = entity.Text((500, 540), pygame.font.Font(None, 48), get_current_version()[0], (0, 0, 0), outline_width=0, center=True)

    current_chart_info = entity.Container(
        pos = (0, 1080),
        transformation = (1, 1, 0),
        entities = [
            paper_image,
            play_image,
            play_button,
            entity.Text((500, 260), pygame.font.Font(None, 64), "Difficulty:", (0, 0, 0), outline_width=0, center=True),
            version_text,
        ],
        visible = False
    )
    version_prev_arrow = entity.Container(
        pos = (500, 420),
        transformation = (1, 1, 0),
        entities = [
            entity.CircleButton((0, 0), 64, id=button_id.VERSION_PREV),
            prev_arrow_image_small,
        ],
        visible = False,
    )
    version_next_arrow = entity.Container(
        pos = (500, 640),
        transformation = (1, 1, 0),
        entities = [
            entity.CircleButton((0, 0), 64, id=button_id.VERSION_NEXT),
            next_arrow_image_small,
        ],
        visible = False,
    )

    transition = entity.Circle((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 0, (0, 0, 0))

    entities: List[entity.Entity] = [
        outer_background,
        inner_background,
        current_chart_display,
        current_chart_info,
        decoration,
        chart_back_arrow,
        chart_prev_arrow,
        chart_next_arrow,
        chart_select_arrow,
        version_prev_arrow,
        version_next_arrow,
        transition,
    ]

    entities_text = "[\n"
    for e in entities:
        entities_text += "    " + type(e).__name__ + ",\n"
    entities_text += "]"

    transformation_events: List[lerp.TransformationEvent] = [
        lerp.TransformationEvent(
            camera_pos,
            copy(camera_pos),
            entity.Position2(0, 0),
            pytweening.easeOutCirc,
            0.6,
        ),
    ]

    while running:
        delta_time_ms = clock.tick(not (debug_state.level > 0) and MENU_FPS_LIMIT)
        delta_time_s  = delta_time_ms / 1000

        events = pygame.event.get()
        for event in events:
            match event.type:
                case pygame.QUIT:
                    import sys
                    pygame.quit()
                    sys.exit(0)
                case custom_event.QUIT_SCENE:
                    running = False
                case pygame.KEYDOWN:
                    if event.key == pygame.K_F1:
                        debug_state.level = (debug_state.level + 1) % debug_state.count

        mouse_pos = pygame.mouse.get_pos()
        button_clicks = [False for _ in range(button_id.COUNT)]
        button_hovers = [False for _ in range(button_id.COUNT)]
        detectButtonCollisions(button_clicks, button_hovers, entities, mouse_pos, (-camera_pos.x, -camera_pos.y))
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if any(button_hovers) else pygame.SYSTEM_CURSOR_ARROW)

        if button_clicks[button_id.CHART_BACK]:
            transformation_events.append(
                    lerp.TransformationEvent(
                        camera_pos,
                        copy(camera_pos),
                        entity.Position2(-1080 * 10, 0),
                        pytweening.easeInOutCirc,
                        1.0,
                    )
            )
            next_scene = scenes.mainMenu
            pygame.time.set_timer(custom_event.QUIT_SCENE, 500, 1)
        elif button_clicks[button_id.CHART_PREV]:
            chart_dec()
            current_chart_text.content = get_current_chart_text()
            chart_prev_arrow.visible = current_chart_index > 0
            chart_next_arrow.visible = True
        elif button_clicks[button_id.CHART_NEXT]:
            chart_inc()
            current_chart_text.content = get_current_chart_text()
            chart_prev_arrow.visible = True
            chart_next_arrow.visible = current_chart_index < charts_count - 1
        elif button_clicks[button_id.CHART_SELECT]:
            update_versions()
            version_text.content = get_current_version_text()
            chart_prev_arrow.visible   = False
            chart_next_arrow.visible   = False
            chart_select_arrow.visible = False
            version_prev_arrow.visible = False
            version_next_arrow.visible = True
            transformation_events.append(
                lerp.TransformationEvent(
                    current_chart_display,
                    copy(current_chart_display),
                    entity.Container(
                        pos = (SCREEN_WIDTH - 512, SCREEN_HEIGHT // 2),
                        transformation = (1, 1, 0),
                        entities = current_chart_display.entities
                    ),
                    pytweening.easeOutExpo,
                    0.5,
                )
            )
            current_chart_info.visible = True
            transformation_events.append(
                lerp.TransformationEvent(
                    current_chart_info,
                    copy(current_chart_info),
                    entity.Container(
                        pos = (0, 0),
                        transformation = (1, 1, 0),
                        entities = current_chart_info.entities
                    ),
                    pytweening.easeOutExpo,
                    1.0,
                )
            )
        elif button_clicks[button_id.VERSION_PREV]:
            version_dec()
            version_prev_arrow.visible = current_version_index > 0
            version_next_arrow.visible = True
            version_text.content = get_current_version_text()
        elif button_clicks[button_id.VERSION_NEXT]:
            version_inc()
            version_prev_arrow.visible = True
            version_next_arrow.visible = current_version_index < versions_count - 1
            version_text.content = get_current_version_text()
        elif button_clicks[button_id.CHART_PLAY]:
            version_prev_arrow.visible = False
            version_next_arrow.visible = False
            transformation_events.append(
                lerp.TransformationEvent(
                    inner_background,
                    copy(inner_background),
                    entity.Image((0, 0), (1, 1, 0), inner_background.image),
                    pytweening.easeOutCirc,
                    0.5,
                ),
            )
            transformation_events.append(
                lerp.TransformationEvent(
                    current_chart_display,
                    copy(current_chart_display),
                    entity.Container(
                        pos = (SCREEN_WIDTH + 512, SCREEN_HEIGHT // 2),
                        transformation = (1, 1, 0),
                        entities = current_chart_display.entities
                    ),
                    pytweening.easeOutExpo,
                    1.4,
                )
            )
            transformation_events.append(
                lerp.TransformationEvent(
                    current_chart_info,
                    copy(current_chart_info),
                    entity.Container(
                        pos = (0, 1080),
                        transformation = (1, 1, 0),
                        entities = current_chart_info.entities
                    ),
                    pytweening.easeOutExpo,
                    1.4,
                )
            )
            transformation_events.append(
                lerp.TransformationEvent(
                    transition,
                    copy(transition),
                    entity.Circle(
                        pos = transition.pos,
                        radius = 1200,
                        color = transition.color,
                    ),
                    pytweening.easeInExpo,
                    0.8,
                )
            )
            context = (get_current_chart().filename, get_current_version()[2], get_current_version()[3])
            next_scene = scenes.gameplay
            pygame.time.set_timer(custom_event.QUIT_SCENE, 800, 1)


        lerp.processTransformationEvents(transformation_events, delta_time_s)
        drawEntities(screen, entities, (-camera_pos.x, -camera_pos.y))

        if debug_state.level >= 1:
            quick_debug_info = {}
            bulk_debug_info  = {}
        if debug_state.level >= 2:
            quick_debug_info.update({
                "camera pos": f"({camera_pos.x:.2f}, {camera_pos.y:.2f})",
                "mouse pos": mouse_pos,
            })
        if debug_state.level >= 3:
            bulk_debug_info.update({
                "entities": entities_text,
            })

        if debug_state.level >= 1:
            drawDebugInfo(screen, clock.get_fps(), quick_debug_info, bulk_debug_info)

        pygame.display.flip()

    return next_scene, context
