from pygame import Vector2, Surface, draw, transform, SRCALPHA
from utils import *
import entity

def drawEntities(screen: Surface, entities: list[entity.Entity], pos_offset=(0, 0), rot_offset=0):
    for e in entities:
        drawEntity(screen, e, pos_offset, rot_offset)

def drawEntity(screen: Surface, e: entity.Entity, pos_offset=(0, 0), rot_offset=0):
    calcPos = lambda pos: tuple_add(tuple(Vector2(pos).rotate(rot_offset)), pos_offset)
    match e:
        case entity.BackgroundColor(color=col):
            screen.fill(col)

        case entity.Rect(rect=rect, color=col):
            x, y, w, h = rect
            pos, size = (x, y), (w, h)
            draw.rect(screen, col, (calcPos(pos), size))

        case entity.Circle(pos=pos, radius=rad, color=col):
            draw.circle(screen, col, calcPos(pos), rad)

        case entity.Text(pos=pos, font=f, content=text, color=col):
            text_surface = f.render(text, False, col)
            text_surface = transform.rotate(text_surface, rot_offset)
            text_rect = text_surface.get_rect(center=calcPos(pos))
            screen.blit(text_surface, text_rect)

        case entity.GIF(pos=pos, animation=animation, delay_ms=delay_ms, clock=clock, frame_index=i, excess_ms=ms_left):
            ms_left += clock.tick()

            while ms_left >= delay_ms:
                ms_left -= delay_ms
                i = (i + 1) % len(animation)

            screen.blit(animation[i], calcPos(pos))

            e.frame_index = i
            e.excess_ms = ms_left

        case entity.Container(pos=pos, rotation=rot, entities=es, visible=visible):
            if visible:
                drawEntities(screen, es, calcPos(pos), rot + rot_offset)
