# @Intro:
#     Immediate-mode drawing of entities.
#
# @Note on performance:
#     Surface transformations (scale/rotate) and text rendering are the expensive
#     parts, so nothing here redoes them unless its inputs actually changed:
#       * Identity transforms (scale 1, angle 0) are skipped entirely.
#       * Image / Animation keep a two-stage cache in `entity._cache`:
#         scaled surface (keyed by scale) and rotated surface (keyed by scale+angle).
#         A spinning sprite therefore re-rotates but never re-scales.
#       * Scrolling images are never modified in place: the scale result is cached
#         and the wrap-around is done with up to 4 area-blits.
#       * Entities whose bounding box is fully off screen are skipped before any
#         transformation happens.
#       * Rendered text is kept in a small LRU keyed by (font, text, colors, outline).
#     Container offsets are (scale_x, scale_y, angle): scales multiply down the tree,
#     angles add, and everything inside a container is scaled by it (positions, sizes,
#     radii, sprites, text). The root offset is IDENTITY_OFFSET = (1, 1, 0).
#     Change detection happens here, at draw time, so it doesn't matter who
#     modified the entity (lerp, gameplay code, ...). No call site has to know.

from functools import lru_cache
from pygame import Vector2, Surface, draw, transform, SCROLL_REPEAT
from utils import *
import entity

# Optional quantization: while something is mid-lerp its transformation changes
# every frame, which defeats the cache. Setting a step (e.g. SCALE_STEP = 0.01,
# ANGLE_STEP = 0.5) snaps values so small per-frame changes reuse the cached
# surface, at the price of visible stepping on slow, large zooms. 0 = exact.
SCALE_STEP = 0
ANGLE_STEP = 0

_EPS_SCALE = 1e-3  # lerp's float output rarely lands exactly on 1.0 / 0.0
_EPS_ANGLE = 1e-2

def _quant(v, step): return round(v / step) * step if step else v
def _isUnitScale(s): return abs(s - 1.0) < _EPS_SCALE
def _isZeroAngle(a): return abs((a + 180.0) % 360.0 - 180.0) < _EPS_ANGLE

def _transformKey(sx, sy, angle):
    return (_quant(sx, SCALE_STEP), _quant(sy, SCALE_STEP), _quant(angle, ANGLE_STEP))

def _scale(surface: Surface, key) -> Surface:
    sx, sy = key[0], key[1]
    if _isUnitScale(sx) and _isUnitScale(sy):
        return surface
    return transform.scale_by(surface, (sx, sy))

def _rotate(surface: Surface, key) -> Surface:
    if _isZeroAngle(key[2]):
        return surface
    return transform.rotate(surface, key[2])

def _offscreen(screen: Surface, pos, size, key) -> bool:
    """Conservative bounding-box test, done before any surface work.
    d is the diagonal of the scaled sprite, which bounds the rotated sprite
    whichever corner/center it is anchored at."""
    d = (((size[0] * key[0]) ** 2 + (size[1] * key[1]) ** 2) ** 0.5)
    return (pos[0] + d < 0 or pos[0] - d > screen.get_width() or
            pos[1] + d < 0 or pos[1] - d > screen.get_height())

def _scaledImage(c, surface: Surface, key) -> Surface:
    sk = (key[0], key[1])
    if c.source is not surface or c.scale_key != sk:
        c.source, c.scale_key = surface, sk
        c.scaled = _scale(surface, key)
        c.key = None  # rotated stage is stale now
    return c.scaled

def _rotatedImage(c, scaled: Surface, key) -> Surface:
    if c.key != key:
        c.key = key
        c.surface = _rotate(scaled, key)
    return c.surface

def _animationFrame(e: entity.Animation, frames, index: int, key) -> Surface:
    c = e._cache
    sk = (key[0], key[1])
    if c.source is not frames or c.scale_key != sk:
        c.source, c.scale_key, c.key = frames, sk, key
        c.scaled_frames, c.frames = {}, {}
    elif c.key != key:
        c.key, c.frames = key, {}
    out = c.frames.get(index)
    if out is None:
        scaled = c.scaled_frames.get(index)
        if scaled is None:
            scaled = c.scaled_frames[index] = _scale(frames[index], key)
        out = c.frames[index] = _rotate(scaled, key)
    return out

def _blitWrapped(screen: Surface, src: Surface, pos, ox: int, oy: int) -> None:
    """Draw `src` at `pos` as if it had been Surface.scroll(ox, oy, SCROLL_REPEAT)'ed."""
    x, y = pos
    w, h = src.get_size()
    for dx, sx0, sw in ((ox, 0, w - ox), (0, w - ox, ox)):
        if sw <= 0: continue
        for dy, sy0, sh in ((oy, 0, h - oy), (0, h - oy, oy)):
            if sh <= 0: continue
            screen.blit(src, (x + dx, y + dy), (sx0, sy0, sw, sh))

def invalidateTransformCache(e) -> None:
    """Call this if you edit the *pixels* of an Image / Animation frame in place
    while it has a non-identity transformation. Reassigning e.image, e.animation
    or e.transformation is detected automatically and needs no call."""
    if hasattr(e, "_cache"):
        e._cache.source = None

@lru_cache(maxsize=256)
def _scaledText(font, text, color, outline_color, outline_width, sx, sy) -> Surface:
    return transform.scale_by(_renderText(font, text, color, outline_color, outline_width), (sx, sy))

@lru_cache(maxsize=512)
def _renderText(font, text, color, outline_color, outline_width) -> Surface:
    surface = font.render(text, True, color)
    if outline_width > 0:
        font.outline = outline_width
        outlined = font.render(text, True, outline_color)
        outlined.blit(surface, (font.outline, font.outline))
        font.outline = 0
        surface = outlined
    return surface  # shared between callers: blit it, never draw on it

def drawEntities(screen: Surface, entities: list[entity.Entity], pos_offset=(0, 0), transformation_offset=IDENTITY_OFFSET):
    for e in entities:
        drawEntity(screen, e, pos_offset, transformation_offset)

def drawEntity(screen: Surface, e: entity.Entity, pos_offset=(0, 0), transformation_offset=IDENTITY_OFFSET):
    osx, osy, oangle = transformation_offset
    def calcPos(pos): return toParentSpace(pos, pos_offset, transformation_offset)
    match e:
        case entity.BackgroundColor(color=col):
            screen.fill(col)

        case entity.Rect(pos=pos, size=size, color=col):
            draw.rect(screen, col, (calcPos(pos), (size[0] * osx, size[1] * osy)))

        case entity.Circle(pos=pos, radius=rad, color=col):
            draw.circle(screen, col, calcPos(pos), rad * (abs(osx) + abs(osy)) / 2)

        case entity.Text(pos=pos, font=f, content=text, color=col, outline_color=o_col, outline_width=o_w, center=center):
            if _isUnitScale(osx) and _isUnitScale(osy):
                text_surface = _renderText(f, text, tuple(col), tuple(o_col), o_w)
            else:
                text_surface = _scaledText(f, text, tuple(col), tuple(o_col), o_w,
                                           _quant(osx, SCALE_STEP), _quant(osy, SCALE_STEP))

            angle = -oangle
            if not _isZeroAngle(angle):
                text_surface = transform.rotate(text_surface, angle)

            if center:
                text_rect = text_surface.get_rect(center=calcPos(pos))
                screen.blit(text_surface, text_rect)
            else:
                screen.blit(text_surface, calcPos(pos))

        case entity.Image(pos=pos, transformation=transformation, image=surface, center=center, scroll_rate=scroll, visible=visible):
            if not visible:
                return

            key = _transformKey(transformation[0] * osx, transformation[1] * osy,
                                transformation[2] - oangle)
            draw_pos = calcPos(pos)
            if _offscreen(screen, draw_pos, surface.get_size(), key):
                return

            c = e._cache
            scaled = _scaledImage(c, surface, key)

            if scroll[0] == 0 and scroll[1] == 0:
                out = _rotatedImage(c, scaled, key)
                if center:
                    draw_pos = tupleSub(draw_pos, tupleIDiv(out.get_size(), (2, 2)))
                screen.blit(out, draw_pos)
                return

            # @Bug, Todo: Where is delta time bro. (scroll is still "per frame")
            # Scroll is accumulated in source pixels; the source is never modified.
            w, h = scaled.get_size()
            if w == 0 or h == 0:
                return
            c.scroll_x = (c.scroll_x + scroll[0]) % surface.get_width()
            c.scroll_y = (c.scroll_y + scroll[1]) % surface.get_height()
            ox = round(c.scroll_x * key[0]) % w
            oy = round(c.scroll_y * key[1]) % h

            if _isZeroAngle(key[2]):
                if center:
                    draw_pos = tupleSub(draw_pos, tupleIDiv((w, h), (2, 2)))
                _blitWrapped(screen, scaled, draw_pos, ox, oy)
            else:
                # Rare: scrolling *and* rotated. Scroll a copy, then rotate it.
                tmp = scaled.copy()
                tmp.scroll(ox, oy, SCROLL_REPEAT)
                out = transform.rotate(tmp, key[2])
                if center:
                    draw_pos = tupleSub(draw_pos, tupleIDiv(out.get_size(), (2, 2)))
                screen.blit(out, draw_pos)

        # @Note: Debatable if this animation iteration logic should be put somewhere else.
        case entity.Animation(pos=pos, transformation=transformation, animation=animation, delay_ms=delay_ms, center=center, clock=clock, frame_index=i, excess_ms=ms_left, visible=visible):
            if not visible:
                return

            ms_left += clock.tick()

            while ms_left >= delay_ms:
                ms_left -= delay_ms
                i = (i + 1) % len(animation)

            e.frame_index = i
            e.excess_ms = ms_left

            # @Bug?: unlike Image, this ignores transformation_offset[2]. Kept as-is.
            key = _transformKey(transformation[0] * osx, transformation[1] * osy, transformation[2])
            draw_pos = calcPos(pos)
            if _offscreen(screen, draw_pos, animation[i].get_size(), key):
                return

            surface = _animationFrame(e, animation, i, key)

            if center:
                draw_pos = tupleSub(draw_pos, tupleIDiv(surface.get_size(), (2, 2)))
            screen.blit(surface, draw_pos)

        case entity.Container(pos=pos, transformation=transformation, entities=es, visible=visible):
            if visible:
                drawEntities(screen, es, calcPos(pos), composeTransformation(transformation_offset, transformation))
