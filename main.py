# @Intro:
#     Yeah, this is main.

import pygame
import scenes.scenes as scenes
from utils import *

def main():
    pygame.init()
    screen     = pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN)
    next_scene = scenes.mainMenu
    context    = None
    while next_scene is not None:
        current_scene = next_scene
        next_scene, context = current_scene(screen, context)

if __name__ == "__main__":
    main()
