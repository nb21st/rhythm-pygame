# @Note: Standard library
from enum import IntEnum, auto
from copy import copy
# @Note: Third-Party library
import pygame
import pytweening
# @Note: Local library
import data_io
from draw import drawEntities
import entity
import lerp
import scenes.scenes as scenes
from utils import *

def setting(screen, context):
    next_scene = None
    small_font = pygame.font.Font(None, 96)
    clock = pygame.time.Clock()
    running = True

    class button_id(IntEnum):
        CHART_SELECTION_BACK = auto()
        KEY1_KEYBIND = auto()
        KEY2_KEYBIND = auto()
        KEY3_KEYBIND = auto()
        KEY4_KEYBIND = auto()
        COUNT = auto()

    # Load config
    config = data_io.read_data("data/config.txt")

    class key_id(IntEnum):
        KEY1 = 0
        KEY2 = auto()
        KEY3 = auto()
        KEY4 = auto()
    key_labels = ["key1", "key2", "key3", "key4"]
    keybinds = [config[key] for key in key_labels]

    waiting_for_key_id = None

    # Create keybind entity for like cus i lwk don't know how to update the text
    def create_key_binder(x, key_id, button):
        display_key = "___" if waiting_for_key_id == key_id else keybinds[key_id]
        return entity.Container(
            pos = (x, 670),
            transformation = (1, 1, 0),
            entities = [
                entity.CircleButton((228, 228), 128, id=button),
                entity.Rect((100, 100),(256, 256),DARK_BACKGROUND_COLOR),
                entity.Text((228, 228),small_font,display_key,outline_width=6,center=True),
            ]
        )

    arrow_png = pygame.image.load("assets/arrow.png").convert_alpha()
    camera_pos = entity.Position2(0, 0)
    outer_background = entity.BackgroundColor(DARK_BACKGROUND_COLOR)
    inner_background = entity.Rect((16, 16),(SCREEN_WIDTH - 32, SCREEN_HEIGHT - 32), LIGHT_BACKGROUND_COLOR)

    pos1 = 420
    # Keybind buttons maker cus holyF### am too lazy to write that shit
    Key1_binder = create_key_binder(100, key_id.KEY1, button_id.KEY1_KEYBIND)
    Key2_binder = create_key_binder(100 + pos1, key_id.KEY2, button_id.KEY2_KEYBIND)
    Key3_binder = create_key_binder(100 + pos1 * 2, key_id.KEY3, button_id.KEY3_KEYBIND)
    Key4_binder = create_key_binder(100 + pos1 * 3, key_id.KEY4, button_id.KEY4_KEYBIND)
    chart_selection_menu_back_arrow = entity.Container(
        pos = (100, 100),
        transformation = (1, 1, 0),
        entities = [
            entity.CircleButton((0, 0), 64,id=button_id.CHART_SELECTION_BACK),
            entity.Image((0, 0),(0.6, 0.6, 90),arrow_png,True),
        ],
    )
    entities = [
        outer_background,
        inner_background,
        chart_selection_menu_back_arrow,
        Key1_binder,
        Key2_binder,
        Key3_binder,
        Key4_binder
    ]

    entities_text = "[\n"
    for e in entities:
        entities_text += "    " + type(e).__name__ + ",\n"
    entities_text += "]"
    transformation_events = []

    while running:
        delta_time_ms = clock.tick(not (debug_state.level > 0) and MENU_FPS_LIMIT)
        delta_time_s = delta_time_ms / 1000
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
                        debug_state.level = (
                            debug_state.level + 1
                        ) % debug_state.count
                        
                    elif waiting_for_key_id is not None:
                        # Cancel rebinding
                        if event.key == pygame.K_ESCAPE:
                            waiting_for_key_id = None
                        else:
                            new_key = pygame.key.name(event.key).upper()
                            existing_keys = [key.upper() for key in keybinds]

                            # Swap key if duplicated
                            if new_key in existing_keys:
                                keybinds[existing_keys.index(new_key)] = keybinds[waiting_for_key_id]

                            keybinds[waiting_for_key_id] = new_key

                            # Save config
                            config.update(dict(zip(key_labels, keybinds)))
                            data_io.write_data("data/config.txt", config)
                            waiting_for_key_id = None


        mouse_pos = pygame.mouse.get_pos()
        button_clicks = [False for _ in range(button_id.COUNT)]
        button_hovers = [False for _ in range(button_id.COUNT)]
        detectButtonCollisions(
            button_clicks,
            button_hovers,
            entities,
            mouse_pos,
            (-camera_pos.x, -camera_pos.y))
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if any(button_hovers) else pygame.SYSTEM_CURSOR_ARROW)

        if button_clicks[button_id.CHART_SELECTION_BACK]:
            next_scene = scenes.mainMenu
            pygame.event.post(pygame.event.Event(custom_event.QUIT_SCENE))

        for i, condition in enumerate(button_clicks[button_id.KEY1_KEYBIND:button_id.KEY4_KEYBIND + 1]):
            if condition:
                waiting_for_key_id = i
                break

        entities[3] = create_key_binder(100, key_id.KEY1, button_id.KEY1_KEYBIND)
        entities[4] = create_key_binder(100 + pos1, key_id.KEY2, button_id.KEY2_KEYBIND)
        entities[5] = create_key_binder(100 + pos1 * 2, key_id.KEY3, button_id.KEY3_KEYBIND)
        entities[6] = create_key_binder(100 + pos1 * 3, key_id.KEY4, button_id.KEY4_KEYBIND)
        lerp.processTransformationEvents(transformation_events,delta_time_s)
        drawEntities(screen,entities,(-camera_pos.x, -camera_pos.y))

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

    return next_scene, None
