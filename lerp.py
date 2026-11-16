from copy import copy
from dataclasses import dataclass, fields
from collections.abc import Callable
import pytweening
from utils import *
from entity import Entity

@dataclass
class TransformationEvent:
    target_entity: Entity
    entity_a: Entity
    entity_b: Entity
    tween: Callable[[float], float] = pytweening.linear
    duration: float = 1.0
    elapsed: float = 0.0

    @classmethod
    def fromCurrent(cls, target: Entity, end: Entity,
                    tween: Callable[[float], float] = pytweening.linear,
                    duration: float = 1.0) -> "TransformationEvent":
        """Start from whatever `target` looks like right now and move to `end`.
        Same as TransformationEvent(target, copy(target), end, tween, duration),
        which is how nearly every scene was building its events."""
        return cls(target, copy(target), end, tween, duration)

    def update(self, delta_time_s: float) -> bool:
        """Advance the event and write the interpolated values into the target.
        Returns True once the event has finished."""
        finished = False

        self.elapsed += delta_time_s
        if self.elapsed >= self.duration:
            finished = True
            self.elapsed = self.duration
        t = self.elapsed / self.duration

        for f in fields(self.target_entity):
            if f.type not in (
                    "int", "float",
                    "Point2f", "Point3f",
                    "Color",
            ):
                continue

            value = lerp(
                getattr(self.entity_a, f.name),
                getattr(self.entity_b, f.name),
                self.tween(t),
            )

            # @Note: Type specific adjustment.
            match f.type:
                case "Color":
                    value = tupleCramp(value, 0, 255)

            setattr(self.target_entity, f.name, value)

        return finished

def lerp(a, b, t):
    if isinstance(a, tuple):
        return tuple(lerp(x, y, t) for x, y in zip(a, b))
    return a + (b - a) * t

def processTransformationEvents(transformation_events: list[TransformationEvent], delta_time_s: float) -> None:
    for event in transformation_events.copy():
        if event.update(delta_time_s):
            transformation_events.remove(event)

# @Note: Kept so any old call site still works; it just forwards to the method.
def processTransformationEvent(event: TransformationEvent, delta_time_s: float) -> bool:
    return event.update(delta_time_s)
