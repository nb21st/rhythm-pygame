# @Intro:
#     Small UI behaviours that sit on top of the entity tree.

import pygame
import entity

class ButtonFeedback:
    """Feedback for buttons: plays a click sound when one is clicked, grows its image while the
    mouse hovers it, and shrinks that image while it is held down.

    The image is found automatically: for every RectButton / CircleButton, the Images in the
    *same Container* that sit at the *same position* as the button are its images (so a pot
    behind a "Play" button reacts, but the paper behind the play button on the chart card does not).
    Use add() to attach more by hand.

    It only writes `Image.scale` (a render-time multiplier), so it never fights with lerp
    animating `transformation`, and it never changes the button's hit area, so hovering
    can't flicker at the edge.

        feedback = ButtonFeedback.fromEntities(entities)      # once, after building the tree
        ...
        detectButtonCollisions(button_clicks, button_hovers, entities, ...)
        feedback.update(button_clicks, button_hovers, delta_time_s)   # once per frame
    """

    def __init__(self, hover_scale: float = 1.12, press_scale: float = 0.92, speed: float = 20.0):
        self.click_sound = pygame.mixer.Sound("sounds/click.ogg")
        self.click_sound.set_volume(0.02)
        self.hover_scale = hover_scale
        self.press_scale = press_scale
        self.speed       = speed          # higher = snappier; ~20 settles in about 0.15s
        self._images:  dict[int, list[entity.Image]] = {}
        self._scale:   dict[int, float] = {}
        self._pressed: set[int] = set()   # buttons the current mouse press started on

    @classmethod
    def fromEntities(cls, entities, **kwargs) -> "ButtonFeedback":
        feedback = cls(**kwargs)
        feedback._collect(entities)
        return feedback

    def add(self, button_id: int, *images: entity.Image) -> None:
        self._images.setdefault(button_id, []).extend(images)
        self._scale.setdefault(button_id, 1.0)

    def _collect(self, entities) -> None:
        images = [e for e in entities if isinstance(e, entity.Image)]
        for b in entities:
            if isinstance(b, (entity.RectButton, entity.CircleButton)):
                self.add(b.id, *[i for i in images if tuple(i.pos) == tuple(b.pos)])
        for e in entities:
            if isinstance(e, entity.Container):
                self._collect(e.entities)

    def update(self, button_clicks, button_hovers, delta_time_s: float) -> None:
        mouse_down = pygame.mouse.get_pressed()[0]
        clicked = False
        for button_id, images in self._images.items():
            if button_clicks[button_id]:
                clicked = True
                self._pressed.add(button_id)
            if not mouse_down:
                self._pressed.discard(button_id)

            hovered = button_hovers[button_id]
            if hovered and button_id in self._pressed:
                target = self.press_scale
            elif hovered:
                target = self.hover_scale
            else:
                target = 1.0

            current = self._scale[button_id]
            current += (target - current) * min(1.0, delta_time_s * self.speed)
            if abs(target - current) < 0.002:
                current = target  # settle exactly, so draw.py's surface cache stops being rebuilt
            self._scale[button_id] = current

            for image in images:
                image.scale = current

        if clicked:
            self.click_sound.play()  # once per frame, however many buttons were hit
