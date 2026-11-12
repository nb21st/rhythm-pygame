# @Todo:
#    Biggest problem we're having right now is the heavy computing works
#    are done every frame. Try to make a new system that only run transformation
#    as necessary. Text rendering is also expensive.
#

from pygame import Vector2, Surface, draw, transform, SRCALPHA, SCROLL_REPEAT
from utils import *
import entity

def drawEntities(screen: Surface, entities: list[entity.Entity], pos_offset=(0, 0), transformation_offset=(0, 0, 0)):
    for e in entities:
        drawEntity(screen, e, pos_offset, transformation_offset)

def drawEntity(screen: Surface, e: entity.Entity, pos_offset=(0, 0), transformation_offset=(1, 1, 0)):
    def calcPos(pos): return tupleAdd(tuple(Vector2(pos).rotate(transformation_offset[2])), pos_offset)
    match e:
        case entity.BackgroundColor(color=col):
            screen.fill(col)

        case entity.Rect(pos=pos, size=size, color=col):
            draw.rect(screen, col, (calcPos(pos), size))

        case entity.Circle(pos=pos, radius=rad, color=col):
            draw.circle(screen, col, calcPos(pos), rad)

        case entity.Text(pos=pos, font=f, content=text, color=col, outline_color=o_col, outline_width=o_w, center=center):
            text_surface = f.render(text, True, col)
            if o_w > 0:
                f.outline = o_w
                outline_text_surface = f.render(text, True, o_col)
                outline_text_surface.blit(text_surface, (f.outline, f.outline))
                text_surface = outline_text_surface
                f.outline = 0

            text_surface = transform.rotate(text_surface, transformation_offset[2])

            if center:
                text_rect = text_surface.get_rect(center=calcPos(pos))
                screen.blit(text_surface, text_rect)
            else:
                screen.blit(text_surface, calcPos(pos))

        case entity.Image(pos=pos, transformation=transformation, image=surface, center=center, scroll_rate=scroll, visible=visible):
            if not visible:
                return
            # @Bug, Todo: Where is delta time bro.
            surface.scroll(scroll[0], scroll[1], SCROLL_REPEAT)
            e.image = surface

            # @Bug, Todo: This is hella expensive. It's probably lerp job to do the surface transformation. Need to fix this.
            surface = transform.scale_by(surface, (transformation[0], transformation[1]))
            surface = transform.rotate(surface, transformation[2])

            if center:
                surface_pos = tupleSub(calcPos(pos), tupleIDiv(surface.get_size(), (2, 2)))
            else:
                surface_pos = calcPos(pos)

            screen.blit(surface, surface_pos)

        # @Note: Debatable if this animation iteration logic should be put somewhere else.
        case entity.Animation(pos=pos, transformation=transformation, animation=animation, delay_ms=delay_ms, center=center, clock=clock, frame_index=i, excess_ms=ms_left):
            ms_left += clock.tick()

            while ms_left >= delay_ms:
                ms_left -= delay_ms
                i = (i + 1) % len(animation)

            surface = animation[i]
            surface = transform.scale_by(surface, (transformation[0], transformation[1]))
            surface = transform.rotate(surface, transformation[2])

            if center:
                surface_pos = tupleSub(calcPos(pos), tupleIDiv(surface.get_size(), (2, 2)))
            else:
                surface_pos = calcPos(pos)

            screen.blit(surface, surface_pos)

            e.frame_index = i
            e.excess_ms = ms_left

        case entity.Container(pos=pos, transformation=transformation, entities=es, visible=visible):
            if visible:
                drawEntities(screen, es, calcPos(pos), tupleAdd(transformation, transformation_offset))
