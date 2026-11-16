# @Intro:
#     These entities co-work with the entire code including lerp and draw.
#     Every entity inherits from Entity and can draw itself via draw().
#     Entities with nothing to show (Line, buttons, Position2, ...) inherit the
#     do-nothing draw() from the base class.
# @Todo:
#     I am considering make simple shapes entity like Rect, Circle depecrated,
#     since most of what visible in the game should be drawn texture.
#

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TypeAlias
import pygame
import draw as d  # helpers + utils live there; use d.xxx at call time (avoids circular import trouble)

Point2f: TypeAlias = tuple[float, float]
Point3f: TypeAlias = tuple[float, float, float]

Point2i: TypeAlias = tuple[int, int]
Point3i: TypeAlias = tuple[int, int, int]

Color: TypeAlias = tuple[float, float, float]

# @Note: Special Type that is not compatible with lerp.
Index: TypeAlias = int
Millisecond: TypeAlias = int
Multiplier: TypeAlias = float


class Entity:
    """Base class of everything in a scene's entity list."""

    def draw(self, screen, pos_offset, transformation_offset) -> None:
        pass  # default: invisible (buttons, Line, Position2, ...)

    def calcPos(self, pos, pos_offset, transformation_offset):
        """Convert a position local to the parent container into screen space."""
        return d.toParentSpace(pos, pos_offset, transformation_offset)


@dataclass
class Position2(Entity):
    x: float = 0.0
    y: float = 0.0

@dataclass
class Position3(Entity):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

@dataclass
class BackgroundColor(Entity):
    color: Color

    def draw(self, screen, pos_offset, transformation_offset):
        screen.fill(self.color)

@dataclass
class Rect(Entity):
    pos: Point2f
    size: Point2f
    color: Color

    def draw(self, screen, pos_offset, transformation_offset):
        osx, osy, _ = transformation_offset
        pygame.draw.rect(screen, self.color,
                         (self.calcPos(self.pos, pos_offset, transformation_offset),
                          (self.size[0] * osx, self.size[1] * osy)))

@dataclass
class Circle(Entity):
    pos: Point2f
    radius: float
    color: Color

    def draw(self, screen, pos_offset, transformation_offset):
        osx, osy, _ = transformation_offset
        pygame.draw.circle(screen, self.color,
                           self.calcPos(self.pos, pos_offset, transformation_offset),
                           self.radius * (abs(osx) + abs(osy)) / 2)

@dataclass
class Text(Entity):
    pos: Point2f
    font: pygame.font.Font
    content: str
    color: Color = (255, 255, 255)
    outline_color: Color = (0, 0, 0)
    outline_width: int = 4
    center: bool = False

    def draw(self, screen, pos_offset, transformation_offset):
        osx, osy, oangle = transformation_offset
        color, o_color = tuple(self.color), tuple(self.outline_color)

        if d._isUnitScale(osx) and d._isUnitScale(osy):
            text_surface = d._renderText(self.font, self.content, color, o_color, self.outline_width)
        else:
            text_surface = d._scaledText(self.font, self.content, color, o_color, self.outline_width,
                                         d._quant(osx, d.SCALE_STEP), d._quant(osy, d.SCALE_STEP))

        angle = -oangle
        if not d._isZeroAngle(angle):
            text_surface = pygame.transform.rotate(text_surface, angle)

        pos = self.calcPos(self.pos, pos_offset, transformation_offset)
        if self.center:
            screen.blit(text_surface, text_surface.get_rect(center=pos))
        else:
            screen.blit(text_surface, pos)

@dataclass
class RectButton(Entity):
    pos: Point2f
    size: Point2f
    id: int
    center: bool = False

@dataclass
class CircleButton(Entity):
    pos: Point2f
    radius: float
    id: int
    center: bool = True

class TransformCache:
    """Scratch space draw.py uses to remember already-transformed surfaces.

    Not part of the public entity API: draw.py owns it, lerp ignores it
    (its field type is not one of the lerp-able types), and it is excluded
    from repr/eq/init on the entities that carry it.
    """
    __slots__ = ("source", "scale_key", "key", "scaled", "surface",
                 "scaled_frames", "frames", "scroll_x", "scroll_y")

    def __init__(self) -> None:
        self.source = None         # original surface (Image) / frame list (Animation)
        self.scale_key = None      # (sx, sy) the scaled stage was built for
        self.key = None            # (sx, sy, angle) the rotated stage was built for
        self.scaled = None         # Image: scaled surface
        self.surface = None        # Image: scaled + rotated surface
        self.scaled_frames = {}    # Animation: frame index -> scaled surface
        self.frames = {}           # Animation: frame index -> scaled + rotated surface
        self.scroll_x = 0          # Image: accumulated scroll, in source pixels
        self.scroll_y = 0

@dataclass
class Image(Entity):
    pos: Point2f
    transformation: Point3f
    image: pygame.Surface
    center: bool = False
    scroll_rate: Point2i = (0, 0)
    visible: bool = True
    # @Note: Extra render-time scale on top of `transformation` (hover/press feedback, ...).
    #        Typed `Multiplier` on purpose so lerp leaves it alone while it animates `transformation`.
    scale: Multiplier = 1.0
    _cache: TransformCache = field(default_factory=TransformCache, init=False, repr=False, compare=False)

    def draw(self, screen, pos_offset, transformation_offset):
        if not self.visible:
            return

        osx, osy, oangle = transformation_offset
        surface, transformation, scroll = self.image, self.transformation, self.scroll_rate

        key = d._transformKey(transformation[0] * osx * self.scale, transformation[1] * osy * self.scale,
                              transformation[2] - oangle)
        draw_pos = self.calcPos(self.pos, pos_offset, transformation_offset)
        if d._offscreen(screen, draw_pos, surface.get_size(), key):
            return

        c = self._cache
        scaled = d._scaledImage(c, surface, key)

        if scroll[0] == 0 and scroll[1] == 0:
            out = d._rotatedImage(c, scaled, key)
            if self.center:
                draw_pos = d.tupleSub(draw_pos, d.tupleIDiv(out.get_size(), (2, 2)))
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

        if d._isZeroAngle(key[2]):
            if self.center:
                draw_pos = d.tupleSub(draw_pos, d.tupleIDiv((w, h), (2, 2)))
            d._blitWrapped(screen, scaled, draw_pos, ox, oy)
        else:
            # Rare: scrolling *and* rotated. Scroll a copy, then rotate it.
            tmp = scaled.copy()
            tmp.scroll(ox, oy, pygame.SCROLL_REPEAT)
            out = pygame.transform.rotate(tmp, key[2])
            if self.center:
                draw_pos = d.tupleSub(draw_pos, d.tupleIDiv(out.get_size(), (2, 2)))
            screen.blit(out, draw_pos)

@dataclass
class Animation(Entity):
    pos: Point2f
    transformation: Point3f
    animation: list[tuple[pygame.Surface, float]]
    delay_ms: int = 80
    center: bool = False
    clock: pygame.time.Clock = field(default_factory=pygame.time.Clock)
    frame_index: Index = 0
    excess_ms: Millisecond = 0
    visible: bool = True
    _cache: TransformCache = field(default_factory=TransformCache, init=False, repr=False, compare=False)

    # @Note: Debatable if this animation iteration logic should be put somewhere else.
    def draw(self, screen, pos_offset, transformation_offset):
        if not self.visible:
            return

        osx, osy, _ = transformation_offset
        i = self.frame_index
        ms_left = self.excess_ms + self.clock.tick()

        while ms_left >= self.delay_ms:
            ms_left -= self.delay_ms
            i = (i + 1) % len(self.animation)

        self.frame_index = i
        self.excess_ms = ms_left

        # @Bug?: unlike Image, this ignores transformation_offset[2]. Kept as-is.
        t = self.transformation
        key = d._transformKey(t[0] * osx, t[1] * osy, t[2])
        draw_pos = self.calcPos(self.pos, pos_offset, transformation_offset)
        if d._offscreen(screen, draw_pos, self.animation[i].get_size(), key):
            return

        surface = d._animationFrame(self, self.animation, i, key)

        if self.center:
            draw_pos = d.tupleSub(draw_pos, d.tupleIDiv(surface.get_size(), (2, 2)))
        screen.blit(surface, draw_pos)

@dataclass
class Container(Entity):
    pos: Point2f
    transformation: Point3f
    entities: list[Entity]
    visible: bool = True

    def draw(self, screen, pos_offset, transformation_offset):
        if self.visible:
            d.drawEntities(screen, self.entities,
                           self.calcPos(self.pos, pos_offset, transformation_offset),
                           d.composeTransformation(transformation_offset, self.transformation))
