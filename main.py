# @Note: Standard library
from enum import IntEnum, auto
from copy import copy
from math import pi
# @Note: Third-Party library
import pygame
import pytweening
# @Note: Local library
from utils import *
import entity
import lerp
from draw import drawEntities

LIGHT_BACKGROUND_COLOR = tuple(pygame.Color("#f6b678"))
DARK_BACKGROUND_COLOR = tuple(pygame.Color("#d98352"))
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
FPS_LIMIT = 0

def detectButtonCollisions(button_clicks, button_hovers, es, mouse_pos, offset_pos=(0, 0), rot_offset=0):
    for e in es:
        match e:
            case entity.RectButton(rect=rect, id=id):
                x, y, w, h = rect
                pos, size = (x, y), (w, h)
                rect = pygame.Rect(tuple_add(pos, offset_pos), (w, h))
                # @Todo: What about rotated rect.
                if rect.collidepoint(mouse_pos):
                    button_hovers[id] = True
                    if pygame.mouse.get_just_pressed()[0]:
                        button_clicks[id] = True
            case entity.CircleButton(pos=pos, radius=rad, id=id):
                if (pygame.Vector2(pos).rotate(rot_offset) + offset_pos).distance_to(mouse_pos) <= rad:
                    button_hovers[id] = True
                    if pygame.mouse.get_just_pressed()[0]:
                        button_clicks[id] = True
            case entity.Container(pos=pos, rotation=rot, entities=fs, visible=visible):
                if visible:
                    detectButtonCollisions(button_clicks, button_hovers, fs, mouse_pos, pygame.Vector2(pos).rotate(rot_offset) + offset_pos, rot + rot_offset)

def main():
    pygame.init()
    debug_font = pygame.font.Font(None, 16)
    screen = pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN)
    clock = pygame.time.Clock()
    running = True

    camera_pos = entity.Position(0, 0)
    outer_background = entity.BackgroundColor((0, 0, 0))
    inner_background1 = entity.Rect((0, 0, *SCREEN_SIZE), (0, 0, 0))
    inner_background2 = entity.Rect((32, - 1080 * 10 + 32, SCREEN_WIDTH - 64, SCREEN_HEIGHT - 64), LIGHT_BACKGROUND_COLOR)
    game_title = entity.Text((512 + 126, 126 + 64), pygame.font.Font(None, 128), "we're cooked beta (real)", (0, 0, 0))
    main_menu_selection_target_rotation = -60
    main_menu_selection = entity.Container(
        pos = (SCREEN_WIDTH + 512, SCREEN_HEIGHT + 512),
        rotation = 0,
        entities = [
            entity.Circle((0, 0), 512, DARK_BACKGROUND_COLOR),
            entity.Container(
                pos = (0, -(512 + 256)),
                rotation = 60 - 90 * 0,
                entities = [
                    entity.CircleButton((0, 0), 256, id=2),
                    entity.Circle((0, 0), 256, DARK_BACKGROUND_COLOR),
                    entity.Text((0, 0), pygame.font.Font(None, 128), "Play", (255, 255, 255))
                ]
            ),
            entity.Container(
                pos = (-(512 + 256), 0),
                rotation = 60 - 90 * 1,
                entities = [
                    entity.CircleButton((0, 0), 256, id=3),
                    entity.Circle((0, 0), 256, DARK_BACKGROUND_COLOR),
                    entity.Text((0, 0), pygame.font.Font(None, 128), "Editor", (255, 255, 255))
                ]
            ),
            entity.Container(
                pos = (0, 512 + 256),
                rotation = 60 - 90 * 2,
                entities = [
                    entity.CircleButton((0, 0), 256, id=4),
                    entity.Circle((0, 0), 256, DARK_BACKGROUND_COLOR),
                    entity.Text((0, 0), pygame.font.Font(None, 128), "Setting", (255, 255, 255)) 
                ]
            ),
            entity.Container(
                pos = (512 + 256, 0),
                rotation = 60 - 90 * 3,
                entities = [
                    entity.CircleButton((0, 0), 256, id=5),
                    entity.Circle((0, 0), 256, DARK_BACKGROUND_COLOR),
                    entity.Text((0, 0), pygame.font.Font(None, 128), "Exit", (255, 255, 255))
                ]
            ),
        ]
    )
    main_menu_next_arrow = entity.Container(
        pos = (SCREEN_WIDTH - 64, 240),
        rotation = 0,
        entities = [
            entity.CircleButton((0, 0), 128, id=0),
            entity.Circle((0, 0), 32, (255, 0, 0)),
            entity.Circle((0, 0), 16, (255, 255, 255)),
        ]
    )
    main_menu_prev_arrow = entity.Container(
        pos = (SCREEN_WIDTH - 512 - 64, SCREEN_HEIGHT - 64),
        rotation = 0,
        entities = [
            entity.CircleButton((0, 0), 128   , id=1),
            entity.Circle((0, 0), 32, (255, 0, 0)),
            entity.Circle((0, 0), 16, (255, 255, 255)),
        ]
    )

    main_menu_animation_guy = entity.GIF(
        pos = (-400, 100),
        animation = [
            pygame.image.load("assets/guy_hold0", "guy_hold0.png").convert_alpha(),
            pygame.image.load("assets/guy_hold1", "guy_hold1.png").convert_alpha(),
            pygame.image.load("assets/guy_hold2", "guy_hold2.png").convert_alpha(),
            pygame.image.load("assets/guy_hold3", "guy_hold3.png").convert_alpha(),
        ]
    )

    entities: List[entity.Entity] = [
        outer_background,
        inner_background1,
        inner_background2,
        main_menu_animation_guy,
        game_title,
        main_menu_selection,
        main_menu_next_arrow,
        main_menu_prev_arrow,
    ]

    transformation_events: List[lerp.TransformationEvent] = [
        lerp.TransformationEvent(
            outer_background,
            copy(outer_background),
            entity.BackgroundColor(DARK_BACKGROUND_COLOR),
            pytweening.easeInOutCirc,
            0.8,
        ),
        lerp.TransformationEvent(
            inner_background1,
            copy(inner_background1),
            entity.Rect((32, 32, SCREEN_WIDTH - 64, SCREEN_HEIGHT - 64), LIGHT_BACKGROUND_COLOR),
            pytweening.easeInOutCirc,
            0.8,
        ),
        lerp.TransformationEvent(
            main_menu_selection,
            copy(main_menu_selection),
            entity.Container(
                pos = (SCREEN_WIDTH + 128, SCREEN_HEIGHT - 64),
                rotation = main_menu_selection_target_rotation,
                entities = main_menu_selection.entities
            ),
            pytweening.easeInOutCirc,
            0.8,
        ),
    ]

    class ButtonID(IntEnum):
        MAIN_MENU_SELECTION_NEXT = 0
        MAIN_MENU_SELECTION_PREV = auto()
        MAIN_MENU_PLAY = auto()
        MAIN_MENU_EDITOR = auto()
        MAIN_MENU_SETTING = auto()
        MAIN_MENU_EXIT = auto()
        COUNT = auto()

    while running:
        delta_time_ms = clock.tick(FPS_LIMIT)
        delta_time_s  = delta_time_ms / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                print("\n[EXIT: Signal Exit]")

        mouse_pos = pygame.mouse.get_pos()
        button_clicks = [False for _ in range(ButtonID.COUNT)]
        button_hovers = [False for _ in range(ButtonID.COUNT)]
        detectButtonCollisions(button_clicks, button_hovers, entities, mouse_pos)
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if any(button_hovers) else pygame.SYSTEM_CURSOR_ARROW)

        if button_clicks[ButtonID.MAIN_MENU_SELECTION_NEXT]:
           main_menu_selection_target_rotation += 90
           transformation_events.append(
              lerp.TransformationEvent(
                 main_menu_selection,
                 copy(main_menu_selection),
                 entity.Container(
                    pos = main_menu_selection.pos,
                    rotation = main_menu_selection_target_rotation,
                    entities = main_menu_selection.entities,
                 ),
                 pytweening.easeOutBack,
                 0.4,
              )
           )
        elif button_clicks[ButtonID.MAIN_MENU_SELECTION_PREV]:
           main_menu_selection_target_rotation -= 90
           transformation_events.append(
              lerp.TransformationEvent(
                 main_menu_selection,
                 copy(main_menu_selection),
                 entity.Container(
                    pos = main_menu_selection.pos,
                    rotation = main_menu_selection_target_rotation,
                    entities = main_menu_selection.entities,
                 ),
                 pytweening.easeOutBack,
                 0.4,
              )
           )
        else:
            if button_clicks[ButtonID.MAIN_MENU_PLAY]:
                transformation_events.append(
                    lerp.TransformationEvent(
                        camera_pos,
                        copy(camera_pos),
                        entity.Position(0, -1080 * 10),
                        pytweening.easeInOutExpo,
                        1.0,
                    )
                )
            if button_clicks[ButtonID.MAIN_MENU_EXIT]:
                running = False
                print("\n[EXIT: Menu Exit]")

        lerp.processTransformationEvents(transformation_events, delta_time_s)
        drawEntities(screen, entities, (-camera_pos.x, -camera_pos.y))
        drawFPS(screen, clock, debug_font)
        pygame.display.flip()

if __name__ == "__main__":
    main()
