# @Intro:
#     This is the entry point of the game. It starts with initializing the pygame library,
#     assigns main menu function as the current scene, and loop back to the next scene if the
#     current scene ended and returned the next scene. Otherwise, the game is ended.
#     Although, the game typically ended with sys.exit().
#
import ctypes
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass
#ทำให้จอฉันไม่ใหญ่ ToT

import pygame
import scenes.scenes as scenes
from utils import *

def main():
    pygame.init()
    screen     = pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN | pygame.SCALED)
    next_scene = scenes.mainMenu
    context    = None

    while next_scene is not None:
        current_scene = next_scene
        next_scene, context = current_scene(screen, context)


if __name__ == "__main__":
    main()
