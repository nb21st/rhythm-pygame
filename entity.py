# @Intro:
#     These entities co-work with the entire code including lerp and draw.
# @Todo:
#     I am considering make simple shapes entity like Rect, Circle depecrated,
#     since most of what visible in the game should be drawn texture.
#

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TypeAlias
import pygame

Point2f: TypeAlias = tuple[float, float]
Point3f: TypeAlias = tuple[float, float, float]

Point2i: TypeAlias = tuple[int, int]
Point3i: TypeAlias = tuple[int, int, int]

Color: TypeAlias = tuple[float, float, float]

# @Note: Special Type that is not compatible with lerp.
Index: TypeAlias = int
Millisecond: TypeAlias = int

@dataclass
class Position2:
    x: float
    y: float

@dataclass
class BackgroundColor:
    color: Color

@dataclass
class Line:
    pos1: Point2f
    pos2: Point2f
    color: Color
    width: float = 1.0

@dataclass
class Rect:
    pos: Point2f
    size: Point2f
    color: Color

@dataclass
class Circle:
    pos: Point2f
    radius: float
    color: Color

@dataclass
class Text:
    pos: Point2f
    font: pygame.font.Font
    content: str
    color: Color

@dataclass
class RectButton:
    pos: Point2f
    size: Point2f
    id: int

@dataclass
class CircleButton:
    pos: Point2f
    radius: float
    id: int

@dataclass
class Image:
    pos: Point2f
    transformation: Point3f
    image: pygame.Surface
    center: bool = False
    scroll_rate: Point2i = (0, 0)

@dataclass
class Animation:
    pos: Point2f
    transformation: Point3f
    animation: list[tuple[pygame.Surface, float]]
    delay_ms: int = 80
    center: bool = False
    # @Note: This is probably a bad idea
    clock: pygame.time.Clock = field(default_factory=pygame.time.Clock)
    frame_index: Index = 0
    excess_ms: Millisecond = 0 

@dataclass
class Container:
    pos: Point2f
    transformation: Point3f
    entities: list[Entity]

Entity: TypeAlias = (
    Position2 | BackgroundColor | Line | Rect | Circle | Text | RectButton |
    CircleButton | Image | Animation | Container
)

