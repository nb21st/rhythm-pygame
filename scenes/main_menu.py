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

def mainMenu(screen):
    next_scene = None

    debug_font = pygame.font.Font(None, 32)

    clock = pygame.time.Clock()
    running = True

    class button_id(IntEnum):
        MAIN_MENU_NEXT       = 0
        MAIN_MENU_PREV       = auto()
        MAIN_MENU_PLAY       = auto()
        MAIN_MENU_EDITOR     = auto()
        MAIN_MENU_SETTING    = auto()
        MAIN_MENU_EXIT       = auto()
        COUNT                = auto()

    camera_pos = entity.Position2(0, -1080 * 2)
    outer_background = entity.BackgroundColor(DARK_BACKGROUND_COLOR)
    inner_background = entity.Image((16, 16), (0, 0, 0), pygame.image.load("assets/introbg.png", "introbg.png").convert(), scroll_rate=(1, 0))
    game_title = entity.Image((512 + 64, 256), (1, 1, 0), pygame.image.load("assets/game_title.png").convert_alpha(), True)
    main_menu_selection_target_rotation = -60
    main_menu_selection = entity.Container(
        pos = (SCREEN_WIDTH, SCREEN_HEIGHT),
        transformation = (1, 1, 90),
        entities = [
            entity.Circle((0, 0), 512, DARK_BACKGROUND_COLOR),
            entity.Container(
                pos = (0, -(512 + 256)),
                transformation = (1, 1, 60 + 90 * 0),
                entities = [
                    entity.CircleButton((0, 0), 256, id=button_id.MAIN_MENU_PLAY),
                    entity.Circle((0, 0), 256, DARK_BACKGROUND_COLOR),
                    entity.Text((0, 0), pygame.font.Font(None, 128), "Play", (255, 255, 255))
                ],
            ),
            entity.Container(
                pos = (512 + 256, 0),
                transformation = (1, 1, 60 + 90 * 1),
                entities = [
                    entity.CircleButton((0, 0), 256, id=button_id.MAIN_MENU_EDITOR),
                    entity.Circle((0, 0), 256, DARK_BACKGROUND_COLOR),
                    entity.Text((0, 0), pygame.font.Font(None, 128), "Editor", (255, 255, 255))
                ],
            ),
            entity.Container(
                pos = (0, (512 + 256)),
                transformation = (1, 1, 60 + 90 * 2),
                entities = [
                    entity.CircleButton((0, 0), 256, id=button_id.MAIN_MENU_SETTING),
                    entity.Circle((0, 0), 256, DARK_BACKGROUND_COLOR),
                    entity.Text((0, 0), pygame.font.Font(None, 128), "Setting", (255, 255, 255)) 
                ],
            ),
            entity.Container(
                pos = (-(512 + 256), 0),
                transformation = (1, 1, 60 + 90 * 3),
                entities = [
                    entity.CircleButton((0, 0), 256, id=button_id.MAIN_MENU_EXIT),
                    entity.Circle((0, 0), 256, DARK_BACKGROUND_COLOR),
                    entity.Text((0, 0), pygame.font.Font(None, 128), "Exit", (255, 255, 255))
                ],
            ),
        ],
    )
    arrow_png = pygame.image.load("assets/ui/arrow.png", "arrow.png").convert_alpha()
    main_menu_next_arrow = entity.Container(
        pos = (SCREEN_WIDTH - 256, 512 - 128),
        transformation = (1, 1, 0),
        entities = [
            entity.CircleButton((0, 0), 64, id=button_id.MAIN_MENU_NEXT),
            entity.Image((0, 0), (0.6, 0.6, -60), arrow_png, True),
        ],
    )
    main_menu_prev_arrow = entity.Container(
        pos = (SCREEN_WIDTH - 512 - 128, SCREEN_HEIGHT - 64 - 32),
        transformation = (1, 1, 0),
        entities = [
            entity.CircleButton((0, 0), 64, id=button_id.MAIN_MENU_PREV),
            entity.Image((0, 0), (0.6, 0.6, 160), arrow_png, True),
        ],
    )

    main_menu_animation_guy = entity.Animation(
        pos = (-1920, 1000),
        transformation = (1, 1, 0),
        animation = [
            pygame.image.load("assets/idle0.png", "idle0.png").convert_alpha(),
            pygame.image.load("assets/idle1.png", "idle1.png").convert_alpha(),
            pygame.image.load("assets/idle2.png", "idle2.png").convert_alpha(),
            pygame.image.load("assets/idle3.png", "idle3.png").convert_alpha(),
        ],
        center = True,
    )

    entities: List[entity.Entity] = [
        outer_background,
        inner_background,
        game_title,
        main_menu_animation_guy,
        main_menu_selection,
        main_menu_next_arrow,
        main_menu_prev_arrow,
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
            1.2,
        ),
        lerp.TransformationEvent(
            main_menu_animation_guy,
            copy(main_menu_animation_guy),
            entity.Animation(
                pos = (620, 700),
                transformation = main_menu_animation_guy.transformation,
                animation = main_menu_animation_guy.animation,
                delay_ms = 1000 // 8,
            ),
            pytweening.easeOutCirc,
            1.2,
        ),
        lerp.TransformationEvent(
            inner_background,
            copy(inner_background),
            entity.Image(
                (16, 16),
                ((SCREEN_WIDTH - 32) / SCREEN_WIDTH, (SCREEN_HEIGHT - 32) / SCREEN_HEIGHT, 0),
                inner_background.image),
            pytweening.easeInOutCirc,
            0.8,
        ),
        lerp.TransformationEvent(
            main_menu_selection,
            copy(main_menu_selection),
            entity.Container(
                pos = (SCREEN_WIDTH + 128, SCREEN_HEIGHT - 64),
                transformation = (1, 1, main_menu_selection_target_rotation),
                entities = main_menu_selection.entities
            ),
            pytweening.easeOutCirc,
            1.4,
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

        if button_clicks[button_id.MAIN_MENU_NEXT]:
           main_menu_selection_target_rotation += 90
           transformation_events.append(
              lerp.TransformationEvent(
                 main_menu_selection,
                 copy(main_menu_selection),
                 entity.Container(
                    pos = main_menu_selection.pos,
                    transformation = (1, 1, main_menu_selection_target_rotation),
                    entities = main_menu_selection.entities,
                 ),
                 pytweening.easeOutBack,
                 0.4,
              )
           )
        elif button_clicks[button_id.MAIN_MENU_PREV]:
           main_menu_selection_target_rotation -= 90
           transformation_events.append(
              lerp.TransformationEvent(
                 main_menu_selection,
                 copy(main_menu_selection),
                 entity.Container(
                    pos = main_menu_selection.pos,
                    transformation = (1, 1, main_menu_selection_target_rotation),
                    entities = main_menu_selection.entities,
                 ),
                 pytweening.easeOutBack,
                 0.4,
              )
           )
        else:
            if button_clicks[button_id.MAIN_MENU_PLAY]:
                transformation_events.append(
                    lerp.TransformationEvent(
                        camera_pos,
                        copy(camera_pos),
                        entity.Position2(0, -1080 * 10),
                        pytweening.easeInOutCirc,
                        1.0,
                    )
                )
                next_scene = scenes.chartSelection
                pygame.time.set_timer(custom_event.QUIT_SCENE, 300, 1)
            if button_clicks[button_id.MAIN_MENU_EXIT]:
                pygame.event.post(pygame.QUIT)

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
