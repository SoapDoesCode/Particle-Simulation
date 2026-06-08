import os
import subprocess
import time

from archive.particles import *

# how many times per second should the powder be simulated
SIMULATION_SPEED = 1

def clear():
    subprocess.call('cls' if os.name == 'nt' else 'clear')

simulation = ParticleSim(3, 5).generate()
# print(simulation)
# print(simulation.matrix)
# exit()

TICK_DELAY = 1 / SIMULATION_SPEED

simulation.replace((0, 0), Sand)

while True:
    clear()
    print(simulation)

    time.sleep(TICK_DELAY)
    simulation.simulate()