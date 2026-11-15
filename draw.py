# @Intro:
#     Immediate-mode drawing of entities.
#
# @Note on performance:
#     Surface transformations (scale/rotate) and text rendering are the expensive
#     parts, so nothing here redoes them unless its inputs actually changed:
#       * Identity transforms (scale 1, angle 0) are skipped entirely.
#       * Image / Animation remember their last transformed surface in
#         `entity._cache` and reuse it while (source, scale, angle) are unchanged.
#       * Rendered text is kept in a small LRU keyed by (font, text, colors, outline).
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

def _applyTransform(surface: Surface, key) -> Surface:
    """scale then rotate, skipping whichever step is a no-op.
    Returns `surface` itself (no copy) when the whole transform is the identity."""
    sx, sy, angle = key
    if not (_isUnitScale(sx) and _isUnitScale(sy)):
        surface = transform.scale_by(surface, (sx, sy))
    if not _isZeroAngle(angle):
        surface = transform.rotate(surface, angle)
    return surface

def _imageSurface(e: entity.Image, surface: Surface, key, animated_pixels: bool) -> Surface:
    if animated_pixels:
        # Pixels change every frame (scrolling), so a cache would go stale.
        return _applyTransform(surface, key)
    c = e._cache
    if c.source is not surface or c.key != key:
        c.source, c.key = surface, key
        c.surface = _applyTransform(surface, key)
    return c.surface

def _animationFrame(e: entity.Animation, frames, index: int, key) -> Surface:
    c = e._cache
    if c.source is not frames or c.key != key:
        c.source, c.key, c.frames = frames, key, {}
    s = c.frames.get(index)
    if s is None:
        s = c.frames[index] = _applyTransform(frames[index], key)
    return s

def invalidateTransformCache(e) -> None:
    """Call this if you edit the *pixels* of an Image / Animation frame in place
    while it has a non-identity transformation. Reassigning e.image, e.animation
    or e.transformation is detected automatically and needs no call."""
    if hasattr(e, "_cache"):
        e._cache.key = None

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
            text_surface = _renderText(f, text, tuple(col), tuple(o_col), o_w)

            angle = -transformation_offset[2]
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

            scrolling = scroll[0] != 0 or scroll[1] != 0
            if scrolling:
                # @Bug, Todo: Where is delta time bro.
                surface.scroll(scroll[0], scroll[1], SCROLL_REPEAT)

            key = _transformKey(transformation[0], transformation[1],
                                transformation[2] - transformation_offset[2])
            surface = _imageSurface(e, surface, key, scrolling)

            if center:
                surface_pos = tupleSub(calcPos(pos), tupleIDiv(surface.get_size(), (2, 2)))
            else:
                surface_pos = calcPos(pos)

            screen.blit(surface, surface_pos)

        # @Note: Debatable if this animation iteration logic should be put somewhere else.
        case entity.Animation(pos=pos, transformation=transformation, animation=animation, delay_ms=delay_ms, center=center, clock=clock, frame_index=i, excess_ms=ms_left, visible=visible):
            if not visible:
                return

            ms_left += clock.tick()

            while ms_left >= delay_ms:
                ms_left -= delay_ms
                i = (i + 1) % len(animation)

            # @Bug?: unlike Image, this ignores transformation_offset[2]. Kept as-is.
            key = _transformKey(transformation[0], transformation[1], transformation[2])
            surface = _animationFrame(e, animation, i, key)

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
