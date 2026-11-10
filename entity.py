from __future__ import annotations
from dataclasses import dataclass, field
from typing import TypeAlias
import pygame

Point2: TypeAlias = tuple[float, float]
Rect2: TypeAlias = tuple[float, float, float, float]
Color: TypeAlias = tuple[float, float, float]

@dataclass
class Position:
    x: float
    y: float

@dataclass
class BackgroundColor:
    color: Color

@dataclass
class Line:
    pos1: Point2
    pos2: Point2
    color: Color
    width: float = 1.0

@dataclass
class Rect:
    rect: Rect2
    color: Color

@dataclass
class Circle:
    pos: Point2
    radius: float
    color: Color

@dataclass
class Text:
    pos: Point2
    font: pygame.font.Font
    content: str
    color: Color

@dataclass
class RectButton:
    rect: Rect2
    id: int

@dataclass
class CircleButton:
    pos: Point2
    radius: float
    id: int

@dataclass
class GIF:
    pos: Point2
    animation: list[tuple[pygame.Surface, float]]
    delay_ms: int = 80
    clock: pygame.time.Clock = field(default_factory=pygame.time.Clock) # @Note: This is probably a bad idea
    frame_index: int = 0
    excess_ms: int = 0 

@dataclass
class Container:
    pos: Point2
    rotation: float # @Note: Degree, maybe naming it `rot` to keep consistency with `pos`?
    entities: list[Entity] # @Note: `from __future__ import annotations`
                           #        needed for this to work
    visible: bool = True

Entity: TypeAlias = Position | BackgroundColor | Line | Rect | Circle | Text | RectButton | CircleButton | GIF | Container

