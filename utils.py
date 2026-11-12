# @Intro:
#     Collection of custom useful functions.
#

# @Note: CONSTANTS
import pygame
import entity

LIGHT_BACKGROUND_COLOR = tuple(pygame.Color("#f6b678"))
DARK_BACKGROUND_COLOR  = tuple(pygame.Color("#d98352"))
SCREEN_WIDTH  = 1920
SCREEN_HEIGHT = 1080
SCREEN_SIZE   = (SCREEN_WIDTH, SCREEN_HEIGHT)
MENU_FPS_LIMIT = 60
GAMEPLAY_FPS_LIMIT = 120

# @Note: GLOBAL VARIABLES
pygame.font.init()
class DebugState:
    font  = pygame.font.Font(None, 32)
    level = 0
    count = 4
debug_state = DebugState()

class custom_event:
    QUIT_SCENE = pygame.event.custom_type()

def todo(msg=""): raise RuntimeError("@Todo: " + msg)

# @Note: This function actually exists in pygame.math but this is more fun.
def cramp(x, mn, mx): return min(max(x, mn), mx)

# @Note: Element-wise operations on tuple.
#        Unless the profiler calls out, using operator library should be fine.
import operator
def tupleOp(xs, ys, op):    return tuple(op(x, y) for x, y in zip(xs, ys))
def tupleAdd(xs, ys):       return tupleOp(xs, ys, operator.add)
def tupleSub(xs, ys):       return tupleOp(xs, ys, operator.sub)
def tupleMul(xs, ys):       return tupleOp(xs, ys, operator.mul)
def tupleFDiv(xs, ys):      return tupleOp(xs, ys, operator.truediv)
def tupleIDiv(xs, ys):      return tupleOp(xs, ys, operator.floordiv)
def tupleCramp(xs, mn, mx): return tuple(cramp(x, mn, mx) for x in xs)

def detectButtonCollisions(
    button_clicks, button_hovers, es, mouse_pos, offset_pos=(0, 0),
    transformation_offset=(1, 1, 0)
):

    for e in es:
        match e:
            # @Note: Did not consider rotated rect.
            case entity.RectButton(pos=pos, size=size, id=id, center=center):
                rect_pos = tupleAdd(pos, offset_pos)
                if center:
                    rect_pos = tupleSub(rect_pos, tupleIDiv(size, (2, 2)))
                rect = pygame.Rect(rect_pos, size)
                if rect.collidepoint(mouse_pos):
                    button_hovers[id] = True
                    if pygame.mouse.get_just_pressed()[0]:
                        button_clicks[id] = True

            case entity.CircleButton(pos=pos, radius=rad, id=id):
                if (pygame.Vector2(pos).rotate(transformation_offset[2]) +
                    offset_pos).distance_to(mouse_pos) <= rad:
                    button_hovers[id] = True
                    if pygame.mouse.get_just_pressed()[0]:
                        button_clicks[id] = True

            case entity.Container(pos=pos, transformation=transformation, entities=fs, visible=visible):
                if visible:
                    detectButtonCollisions(
                        button_clicks,
                        button_hovers,
                        fs, mouse_pos,
                        pygame.Vector2(pos).rotate(transformation_offset[2]) + offset_pos,
                        transformation + transformation_offset
                    )

# @Note: `drawDebugInfo` also happens to tank the FPS because
#        text rendering is expensive.
def drawDebugInfo(screen, fps, quick_variables, bulk_variables):
    font = debug_state.font
    fps = fps or 1.0
    frametime = 1000 / fps
    quick_text = (f"{fps:.0f} FPS {frametime:.1f} MS\n" +
                  "\n".join(f"{name}: {val}" for name, val in quick_variables.items()))
    bulk_text  =  "\n".join(f"{name}: {val}" for name, val in bulk_variables.items())

    quick_text_surface = font.render(quick_text, True, (255, 255, 255))
    bulk_text_surface  = font.render(bulk_text, True, (255, 255, 255))

    font.outline = 2
    quick_text_surface_surf = font.render(quick_text, True, (0, 0, 0))
    bulk_text_surface_surf  = font.render(bulk_text, True, (0, 0, 0))
    quick_text_surface_surf.blit(quick_text_surface, (2, 2))
    bulk_text_surface_surf.blit(bulk_text_surface, (2, 2))
    font.outline = 0

    from pygame import draw, Surface, SRCALPHA

    quick_pos = (screen.get_width() // 2, screen.get_height() // 6 * 5)
    quick_rect = quick_text_surface_surf.get_rect()
    quick_bg = Surface(quick_rect.size, SRCALPHA)
    draw.rect(quick_bg, (0, 0, 0, 255 // 3), quick_rect)
    screen.blit(quick_bg, quick_pos)
    screen.blit(quick_text_surface_surf, (screen.get_width() // 2, screen.get_height() // 6 * 5))

    bulk_rect = bulk_text_surface_surf.get_rect()
    bulk_bg = Surface(bulk_rect.size, SRCALPHA)
    draw.rect(bulk_bg, (0, 0, 0, 255 // 3), bulk_rect)
    screen.blit(bulk_bg, (0, 0))
    screen.blit(bulk_text_surface_surf, (0, 0))
