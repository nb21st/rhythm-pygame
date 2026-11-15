# @Intro:
#     Collection of contants, global variables, useful functions,
#

import pygame
import entity

LIGHT_BACKGROUND_COLOR = tuple(pygame.Color("#f6b678"))
DARK_BACKGROUND_COLOR  = tuple(pygame.Color("#d98352"))
SCREEN_WIDTH  = 1920
SCREEN_HEIGHT = 1080
SCREEN_SIZE   = (SCREEN_WIDTH, SCREEN_HEIGHT)
MENU_FPS_LIMIT = 60
GAMEPLAY_FPS_LIMIT = 120

pygame.font.init()
class DebugState:
    font  = pygame.font.Font(None, 32)
    level = 0
    count = 4
debug_state = DebugState()

class custom_event:
    QUIT_SCENE = pygame.event.custom_type()

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

# @Note: Container transformation offsets are (scale_x, scale_y, angle_degrees).
#        The root offset is IDENTITY_OFFSET. Scales multiply down the tree, angles add.
IDENTITY_OFFSET = (1, 1, 0)

def composeTransformation(offset, t):
    return (offset[0] * t[0], offset[1] * t[1], offset[2] + t[2])

# @Note: Local position of a child -> position in the parent's space: scale, then rotate,
#        then translate. (Exact for uniform scale; with non-uniform scale inside rotated
#        containers it is an approximation, since there is no shear.)
def toParentSpace(pos, pos_offset, transformation_offset):
    sx, sy, angle = transformation_offset
    p = pygame.Vector2(pos[0] * sx, pos[1] * sy).rotate(angle)
    return (p.x + pos_offset[0], p.y + pos_offset[1])

# @Note: Camera zoom about the screen center. `camera_x/y` is the world position at the
#        screen's top-left when zoom == 1 (same meaning as before). Use the SAME returned
#        values for drawing and for hit-testing:
#            cam_pos, cam_tf = cameraTransform(camera.x, camera.y, camera.z)
#            detectButtonCollisions(clicks, hovers, entities, mouse_pos, cam_pos, cam_tf)
#            drawEntities(screen, entities, cam_pos, cam_tf)
def cameraTransform(camera_x, camera_y, zoom, screen_size=SCREEN_SIZE):
    cx, cy = screen_size[0] / 2, screen_size[1] / 2
    return ((-camera_x * zoom + cx * (1 - zoom),
             -camera_y * zoom + cy * (1 - zoom)),
            (zoom, zoom, 0))

def detectButtonCollisions(
    button_clicks, button_hovers, es, mouse_pos, offset_pos=(0, 0),
    transformation_offset=IDENTITY_OFFSET
):
    osx, osy, _ = transformation_offset

    for e in es:
        match e:
            # @Note: Did not consider rotated rect.
            case entity.RectButton(pos=pos, size=size, id=id, center=center):
                size = (size[0] * osx, size[1] * osy)
                rect_pos = tupleAdd((pos[0] * osx, pos[1] * osy), offset_pos)
                if center:
                    rect_pos = tupleSub(rect_pos, tupleIDiv(size, (2, 2)))
                rect = pygame.Rect(rect_pos, size)
                if rect.collidepoint(mouse_pos):
                    button_hovers[id] = True
                    if pygame.mouse.get_just_pressed()[0]:
                        button_clicks[id] = True

            case entity.CircleButton(pos=pos, radius=rad, id=id):
                rad = rad * (abs(osx) + abs(osy)) / 2
                if pygame.Vector2(toParentSpace(pos, offset_pos, transformation_offset)).distance_to(mouse_pos) <= rad:
                    button_hovers[id] = True
                    if pygame.mouse.get_just_pressed()[0]:
                        button_clicks[id] = True

            case entity.Container(pos=pos, transformation=transformation, entities=fs, visible=visible):
                if visible:
                    detectButtonCollisions(
                        button_clicks,
                        button_hovers,
                        fs, mouse_pos,
                        toParentSpace(pos, offset_pos, transformation_offset),
                        composeTransformation(transformation_offset, transformation)
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
