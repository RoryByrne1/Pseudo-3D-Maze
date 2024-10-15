import pygame

from constants import *
from classes import Game

pygame.init()


screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_WIDTH))
clock = pygame.time.Clock()
font = pygame.font.Font(pygame.font.get_default_font(), 20)

game = Game("grid4")

render_3D = True
while True:
    event_list = pygame.event.get()
    for event in event_list:
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                render_3D = not render_3D

    screen.fill(BACKGROUND_COLOUR)

    game.update(screen)

    if render_3D:
        game.draw_3D(screen)
    else:
        game.draw_2D(screen)

    screen.blit(font.render(str(round(clock.get_fps(),2)), True, (255,255,255), ), (2,2))

    pygame.display.flip()
    clock.tick(FPS)