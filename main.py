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

font = pygame.font.SysFont(None, 22)

# simulation settings
GRID_SIZE = tuple(map(int, config.get('Settings', 'grid_size').removeprefix("(").removesuffix(")").split(',')))
REFRESH_RATE = config.getint("Settings", "refresh_rate")

# HUD settings
SHOW_HUD = config.getboolean("Settings", "show_hud")
HUD_MARGIN = config.getint("Settings", "hud_margin")
HUD_PADDING = config.getint("Settings", "hud_padding")
HUD_LINE_SPACING = config.getint("Settings", "hud_line_spacing")

# window settings
WINDOW_WIDTH = config.getint("Settings", "window_width")
WINDOW_HEIGHT = config.getint("Settings", "window_height")
WINDOW_BORDER_PADDING = config.getint("Settings", "window_border_padding")
WINDOW_BORDER_COLOUR = tuple(map(int, config.get('Settings', 'window_border_colour').removeprefix("(").removesuffix(")").split(',')))

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Particle Simulator")

def get_click_pos(sim: ParticleSim, mouse_pos: tuple[int, int]) -> tuple[int, int]:
    mouse_x, mouse_y = mouse_pos

    cell_height = (WINDOW_HEIGHT - (WINDOW_BORDER_PADDING*2)) // sim.n_rows
    cell_width = (WINDOW_WIDTH - (WINDOW_BORDER_PADDING*2)) // sim.n_cols

    # ignore clicks outside the grid
    if (
        mouse_x < WINDOW_BORDER_PADDING
        or mouse_x >= WINDOW_WIDTH - WINDOW_BORDER_PADDING
        or mouse_y < WINDOW_BORDER_PADDING
        or mouse_y >= WINDOW_HEIGHT - WINDOW_BORDER_PADDING
    ):
        return
    
    col = (mouse_x - WINDOW_BORDER_PADDING) // cell_width
    row = (mouse_y - WINDOW_BORDER_PADDING) // cell_height

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
    cell_height = (WINDOW_HEIGHT - (WINDOW_BORDER_PADDING*2)) // sim.n_rows
    cell_width = (WINDOW_WIDTH - (WINDOW_BORDER_PADDING*2)) // sim.n_cols

    for row in sim.matrix:
        for particle in row:
            pygame.draw.rect(
                screen,
                particle.COLOR,
                pygame.Rect(
                    WINDOW_BORDER_PADDING + (particle.col * cell_width),
                    WINDOW_BORDER_PADDING + (particle.row * cell_height),
                    cell_width,
                    cell_height
                )
            )

def draw_hud(sim: ParticleSim):
    LINES = (
        f"FPS: {clock.get_fps():.1f}/{REFRESH_RATE}",
        f"Grid: {sim.n_rows}x{sim.n_cols}",
        f"Cells: {(sim.n_rows*sim.n_cols):,}"
    )

    surfaces = [font.render(line, True, (0, 255, 0)) for line in LINES]

    # calculate HUD WINDOW_WIDTH and WINDOW_HEIGHT
    hud_width = max(s.get_width() for s in surfaces) + (HUD_PADDING * 2)
    hud_height = sum(s.get_height() for s in surfaces) + (HUD_PADDING * 2) + (HUD_LINE_SPACING * (len(LINES) -1))

    # calculate HUD position
    hud_x_pos = WINDOW_WIDTH - hud_width - HUD_MARGIN
    hud_y_pos = HUD_MARGIN

    # draw HUD background
    pygame.draw.rect(
        screen,
        (0, 0, 0),
        (hud_x_pos, hud_y_pos, hud_width, hud_height)
    )

    current_y = hud_y_pos + HUD_PADDING # set where first line of text should start

    for surf in surfaces:
        screen.blit(surf, (hud_x_pos + HUD_PADDING, current_y))
        current_y += surf.get_height() + HUD_LINE_SPACING # increment current_y to the next line

async def main_game():
    screen.fill(WINDOW_BORDER_COLOUR) # fill in the border once (doesn't need to happen again)

    sim = ParticleSim(GRID_SIZE[0], GRID_SIZE[1]).generate()
    
    simulating = True

    while True:
        if simulating:
            # step the simulation to the next tick
            sim.step()

        mouse_buttons = pygame.mouse.get_pressed() # check which mouse buttons are pressed

        # if left mouse button is pressed (or held)
        if mouse_buttons[0]:
            pos = get_click_pos(sim, pygame.mouse.get_pos())

            # to prevent errors in the case the user clicks outside the grid
            if pos is not None:
                row, col = pos
                sim.replace((row, col), sim.selected_particle)

                for x in (1, 0, -1):
                    for y in (1, 0, -1):
                        try:
                            sim.replace((row+x, col+y), sim.selected_particle)
                        except:
                            pass
        
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

        # draw the simulation on the screen
        draw_simulation(sim)

        # draw the HUD in the top right
        if SHOW_HUD:
            draw_hud(sim)

        # sets the refresh rate (fps)
        clock.tick(REFRESH_RATE)

        # update the game state and draw the screen
        pygame.display.flip()

        await asyncio.sleep(0) # this is needed, DO NOT REMOVE


asyncio.run(main_game())