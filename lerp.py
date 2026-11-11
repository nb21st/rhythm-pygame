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

def lerp(a, b, t):
    if isinstance(a, tuple):
        return tuple(lerp(x, y, t) for x, y in zip(a, b))
    return a + (b - a) * t

def processTransformationEvents(transformation_events: list[TransformationEvent], delta_time_s: float) -> None:
    for event in transformation_events.copy():
        if processTransformationEvent(event, delta_time_s):
            transformation_events.remove(event)

all_types = set()

def processTransformationEvent(event: TransformationEvent, delta_time_s: float) -> bool:
    finished = False

    event.elapsed += delta_time_s
    if event.elapsed >= event.duration:
        finished = True
        event.elapsed = event.duration
    t = event.elapsed / event.duration

    for f in fields(event.target_entity):
        if f.type not in (
                "int", "float",
                "Point2f", "Point3f",
                "Color",
        ):
            continue

        value = lerp(
            getattr(event.entity_a, f.name),
            getattr(event.entity_b, f.name),
            event.tween(t),
        )

        # @Note: Type specific adjustment.
        match f.type:
            case "Color":
                value = tupleCramp(value, 0, 255)

        setattr(
            event.target_entity,
            f.name,
            value,
        )
            
    return finished
