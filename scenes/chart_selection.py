# @Note: Standard library
from enum import IntEnum, auto
from copy import copy
# @Note: Third-Party library
import pygame
import pytweening
# @Note: Local library
from draw import drawEntities
import entity
import lerp
import scenes.scenes as scenes
from utils import *

def chartSelection(screen):
    next_scene = None

    debug_font = pygame.font.Font(None, 32)

    clock = pygame.time.Clock()
    running = True

    class button_id(IntEnum):
        CHART_SELECTION_BACK = auto()
        COUNT                = auto()

    camera_pos = entity.Position2(0, 1080 * 8)
    outer_background = entity.BackgroundColor(DARK_BACKGROUND_COLOR)
    introbg_png = pygame.image.load("assets/introbg.png", "introbg.png").convert()
    inner_background = entity.Image((16, 16), ((SCREEN_WIDTH - 32) / SCREEN_WIDTH, (SCREEN_HEIGHT - 32) / SCREEN_HEIGHT, 0), introbg_png, scroll_rate=(-1, 0))
    arrow_png = pygame.image.load("assets/ui/arrow.png", "arrow.png").convert_alpha()
    chart_selection_menu_back_arrow = entity.Container(
        pos = (100, 100),
        transformation = (1, 1, 0),
        entities = [
            entity.CircleButton((0, 0), 64, id=button_id.CHART_SELECTION_BACK),
            entity.Image((0, 0), (0.6, 0.6, 90), arrow_png, True),
        ],
    )

    entities: List[entity.Entity] = [
        outer_background,
        inner_background,
        chart_selection_menu_back_arrow
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

        if button_clicks[button_id.CHART_SELECTION_BACK]:
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

        lerp.processTransformationEvents(transformation_events, delta_time_s)
        drawEntities(screen, entities, (-camera_pos.x, -camera_pos.y))

        if debug_state.level >= 1:
            quick_debug_info = {}
            bulk_debug_info = {}
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
            drawDebugInfo(screen, debug_font, clock.get_fps(), quick_debug_info, bulk_debug_info)

        pygame.display.flip()

    return next_scene
