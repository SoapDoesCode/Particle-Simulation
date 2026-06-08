import random
from typing import Callable

class ParticleSim:
    def __init__(self, n_rows: int, n_cols: int):
        self.n_rows = n_rows # rows
        self.n_cols = n_cols # columns

        self.selected_particle = Sand

    # define what the particle matrix looks like when printed
    def __repr__(self):
        width = max(len(str(cell)) for row in self.matrix for cell in row)

        return "\n".join(
            " ".join(str(cell).ljust(width) for cell in row)
            for row in self.matrix
        )

        # return "\n".join(str(row) for row in self.matrix)
        # return "\n".join(f"{i}: {row}" for i, row in enumerate(self.matrix))
    
    def generate(self):
        """Generate grid as [row][col]"""
        self.matrix: list[list[Element]] = [
            [Void(self, (row, col)) for col in range(self.n_cols)]
            for row in range(self.n_rows)
        ]
        return self

    def simulate(self):
        """One simulaton tick"""

        # reset update flags
        for row in self.matrix:
            for p in row:
                p.has_been_updated = False

        # bottom-up update to prevent double-falling
        for row in reversed(self.matrix):
            for particle in row:
                particle.update()

    def get_pos(self, row: int, col: int) -> Element | None:
        """
        Returns the particle at the given position, or None if the position is out of bounds
        """
        if (row < 0) or (row >= self.n_rows):
            return
        if (col < 0) or (col >= self.n_cols):
            return
        
        return self.matrix[row][col]
    
    def can_move_density(self, source: Element, target: Element) -> bool:
        """
        Check whether movement from source to target particle is allowed based on density.

        vertical_direction:
            1  = moving down
            -1  = moving up
        """
        return (source.DENSITY - target.DENSITY) * source.VERTICAL_DIR > 0
    
    def can_move_into(self, source: Element, target: Element) -> bool:
        """
        Check whether movement from source to target particle is allowed
        """
        # out of bounds should already be handled

        # empty cell (Void) is ALWAYS valid
        if target.ID == Void.ID:
            return True
        
        # blocked my immovable particles
        if not target.MOVABLE:
            return False
        
        # states of matter
        if isinstance(source, Solid) and isinstance(target, Solid):
            return # don't allow solids to swap with each other

        # if source(solid), pass
        # if source(liquid) and target(not solid), pass
        # if source(gas), pass

        # solid can pass through all
        # liquid can pass through gas but not solid
        # gas can pass through liquid, gas, solid
        
        # density rule
        return (source.DENSITY - target.DENSITY) * source.VERTICAL_DIR > 0

    def swap(self, a: Element, b: Element):
        """
        Swap particles on the grid.

        Automatically sets `has_been_updated = True` on both particles
        """
        # print(f"Swapped: {a} and {b}")
        a_row, a_col = a.location
        b_row, b_col = b.location

        # swap the particles
        self.matrix[a_row][a_col], self.matrix[b_row][b_col] = self.matrix[b_row][b_col], self.matrix[a_row][a_col]

        # update the particles' self-tracked locations
        a.location, b.location = b.location, a.location

        # mark both particles as having been updated
        a.has_been_updated = True
        b.has_been_updated = True


    def replace(self, location: tuple[int, int], particle: Element):
        """Replaces the particle at the given location with one of the given type"""
        row, col = location
        
        self.matrix[row][col] = particle(self, (row, col))

class Element:
    """Particles must define:
    - `NAME: str`
    - `ID: int`
    - `COLOR: tuple[int, int, int]` (RGB)
    - `DENSITY: int | float` (kg/m^3)
    - `VERTICAL_DIR: int` (1 or -1)
      - 1 = moving down
      - -1 = moving up

    Optional:
    - `MOVABLE: bool`
    """
    ABSTRACT = False

    NAME = None
    ID = None
    COLOR = None

    DENSITY = None
    VERTICAL_DIR = None

    MOVABLE = True # particles are considered movable by default

    _warned = set()

    registry = []

    # automatically register each particle as it gets defined
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # ignore abstract classes
        if cls.__dict__.get("ABSTRACT", False):
            return
        # if getattr(cls, "ABSTRACT", False):
        #     return

        Element.registry.append(cls)

    def __init__(self, grid: ParticleSim, location: list[int, int]):
        if (self.NAME is None) or (self.ID is None) or (self.COLOR is None) or (self.DENSITY is None) or (self.VERTICAL_DIR is None):
            raise NotImplementedError("""Subclass must define: NAME, ID, COLOR, DENSITY, VERTICAL_DIR""")
        
        self.grid = grid
        self.location = location # (row, col)

        self.lifetime = 0
        self.velocity: list[int, int] = [0, 0]
        self.has_been_updated: bool = False

    def update(self):
        """This update function implementation is blank and should be overridden by the subclass"""
        cls = self.__class__.__name__

        # check if a warning has already been issued for this subclass
        if cls not in Element._warned:
            # print a warning if one has not yet been issued
            print(f"[WARNING] {cls} has not overridden update()")
            Element._warned.add(cls) # mark this subclass as warned

    def __repr__(self):
        return f"{self.NAME}:{self.location}"

class Liquid(Element):
    ABSTRACT = True
    VERTICAL_DIR = 1 # down

    def update(self):
        if self.has_been_updated:
            return
        
        row, col = self.location

        checks = (
            (row+1, col),   # down
            (row+1, col-1), # down-left
            (row+1, col+1), # down-right
            (row, col-1),   # left
            (row, col+1),   # right
        )
        
        for dest_row, dest_col in checks:
            if (target := self.grid.get_pos(dest_row, dest_col)):
                if self.grid.can_move_into(self, target):
                    self.grid.swap(self, target)
                    return

class Solid(Element):
    ABSTRACT = True
    VERTICAL_DIR = 1 # down

    def update(self):
        if self.has_been_updated:
            return
        
        row, col = self.location

        checks = (
            (row+1, col),   # down
            (row+1, col-1), # down-left
            (row+1, col+1), # down-right
        )
        
        for dest_row, dest_col in checks:
            if (target := self.grid.get_pos(dest_row, dest_col)):
                if self.grid.can_move_into(self, target):
                    self.grid.swap(self, target)
                    return

class MovableSolid(Solid):
    ABSTRACT = True

class ImmovableSolid(Solid):
    ABSTRACT = True

    MOVABLE = False

    def update(self):
        """
        Immovable solids have no behaviour by default
        """
        return

class Gas(Element):
    ABSTRACT = True
    VERTICAL_DIR = -1 # up

    def update(self):
        if self.has_been_updated:
            return
        
        row, col = self.location

        checks = (
            (row-1, col),   # up
            (row-1, col-1), # up-left
            (row-1, col+1), # up-right
            (row, col-1),   # left
            (row, col+1),   # right
        )
        
        for dest_row, dest_col in checks:
            if (target := self.grid.get_pos(dest_row, dest_col)):
                if self.grid.can_move_into(self, target):
                    self.grid.swap(self, target)
                    return

class Void(Element):
    NAME = "Void"
    ID = 0
    COLOR = (0, 0, 0)
    DENSITY = 0

    VERTICAL_DIR = 0

    def update(self):
        return # void has no functionality




class Sand(MovableSolid):
    NAME = "Sand"
    ID = 1
    COLOR = (230, 197, 92)
    DENSITY = 1430

class Water(Liquid):
    NAME = "Water"
    ID = 2
    COLOR = (35, 137, 218)
    DENSITY = 1000

    # randomise the water colour
    def __init__(self, grid, location):
        super().__init__(grid, location)
        self.COLOR = random.choice(((35, 137, 218), (28, 163, 236), (90, 188, 216), (116, 204, 244)))

class Smoke(Gas):
    NAME = "Smoke"
    ID = 3
    COLOR = (115, 130, 118)
    DENSITY = 1.2
    # density of smoke can range:
    # Fresh, hot smoke can be 0.6-1.1kg/m^3
    # Cooled, room temperature smoke can be around 1.0-1.3kg/m^3

class Hydrogen(Gas):
    NAME = "Hydrogen"
    ID = 4
    COLOR = (255, 255, 255)
    DENSITY = 1

class Clay(ImmovableSolid):
    NAME = "Clay"
    ID = 5
    COLOR = (182, 106, 80)
    DENSITY = 1330

class Silt(MovableSolid):
    NAME = "Silt"
    ID = 6
    COLOR = (138, 125, 114)
    DENSITY = 1380

# print(Element.registry)