import os
import pygame
import asyncio

from configparser import ConfigParser

from particles import *

configFilePath = os.path.join(os.path.dirname(__file__), 'config.ini')
config = ConfigParser()
config.read(configFilePath)

pygame.init()
clock = pygame.time.Clock()

### SIMULATION SETTINGS ###
WIDTH = config.getint("Settings", "window_width")
HEIGHT = config.getint("Settings", "window_height")
REFRESH_RATE = config.getint("Settings", "refresh_rate")

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Particle Simulator")

grid_size = tuple(map(int, config.get('Settings', 'grid_size').removeprefix("(").removesuffix(")").split(',')))
BORDER_PADDING = config.getint("Settings", "border_padding")
BORDER_COLOUR = tuple(map(int, config.get('Settings', 'border_colour').removeprefix("(").removesuffix(")").split(',')))
### SIMULATION SETTINGS ###

def get_click_pos(sim: ParticleSim, mouse_pos: tuple[int, int]) -> tuple[int, int]:
    mouse_x, mouse_y = mouse_pos

    cell_height = (HEIGHT - (BORDER_PADDING*2)) // sim.n_rows
    cell_width = (WIDTH - (BORDER_PADDING*2)) // sim.n_cols

    # ignore clicks outside the grid
    if (
        mouse_x < BORDER_PADDING
        or mouse_x >= WIDTH - BORDER_PADDING
        or mouse_y < BORDER_PADDING
        or mouse_y >= HEIGHT - BORDER_PADDING
    ):
        return
    
    col = (mouse_x - BORDER_PADDING) // cell_width
    row = (mouse_y - BORDER_PADDING) // cell_height

    # check if row is out of range
    if (row >= sim.n_rows) or (row < 0):
        return
    # check if col is out of range
    if (col >= sim.n_cols) or (col < 0):
        return

    # print(f"Clicked row={row}, col={col}")
    return row, col

def select_particle(sim: ParticleSim, dir: int):
    i = (sim.selected_particle.ID + dir) % len(Element.registry)

    sim.selected_particle = Element.registry[i]

def draw_simulation(sim: ParticleSim) -> None:
    cell_height = (HEIGHT - (BORDER_PADDING*2)) // sim.n_rows
    cell_width = (WIDTH - (BORDER_PADDING*2)) // sim.n_cols

    for row in sim.matrix:
        for particle in row:
            row_i, col_i = particle.location

            pygame.draw.rect(
                screen,
                particle.COLOR,
                pygame.Rect(
                    BORDER_PADDING + (col_i * cell_width),
                    BORDER_PADDING + (row_i * cell_height),
                    cell_width,
                    cell_height
                )
            )

async def main_game():
    screen.fill(BORDER_COLOUR) # fill in the border once (doesn't need to happen again)

    sim = ParticleSim(grid_size[0], grid_size[1]).generate()
    
    simulating = True

    while True:
        if simulating:
            # step the simulation to the next tick
            sim.simulate()

        mouse_buttons = pygame.mouse.get_pressed() # check which mouse buttons are pressed

        # if left mouse button is pressed (or held)
        if mouse_buttons[0]:
            pos = get_click_pos(sim, pygame.mouse.get_pos())

            # to prevent errors in the case the user clicks outside the grid
            if pos is not None:
                row, col = pos
                sim.replace((row, col), sim.selected_particle)
        
        # draw the simulation on the screen
        draw_simulation(sim)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: # space bar
                    simulating = not simulating # toggle the simulation on/off
                    print("Resumed simulation" if simulating else "Paused simulation")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4: # scroll wheel up
                    select_particle(sim, 1) # cycle the selected particle
                    print(sim.selected_particle.NAME)
                elif event.button == 5: # scroll wheel down
                    select_particle(sim, -1) # cycle the selected particle
                    print(sim.selected_particle.NAME)

        # sets the refresh rate (fps)
        clock.tick(REFRESH_RATE)

        # update the game state and draw the screen
        pygame.display.flip()

        await asyncio.sleep(0) # this is needed, DO NOT REMOVE


asyncio.run(main_game())