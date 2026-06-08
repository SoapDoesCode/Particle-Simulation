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
            [Air(self, [row, col]) for col in range(self.n_cols)]
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
    
    def is_empty(self, row: int, col: int) -> bool:
        """
        Check occpancy and whether a cell is out of bounds
        """
        if (row < 0) or (row >= self.n_rows):
            return False
        if (col < 0) or (col >= self.n_cols):
            return False
        
        # a location is considered empty if occupied by air
        return self.matrix[row][col].ID == Air.ID
    
    def get_pos(self, row: int, col: int) -> Element | None:
        """
        Returns the particle at the given position, or None if the position is out of bounds
        """
        if (row < 0) or (row >= self.n_rows):
            return
        if (col < 0) or (col >= self.n_cols):
            return
        
        return self.matrix[row][col]

    def swap(self, a: tuple[int, int], b: tuple[int, int]):
        """Swap particles on the grid"""
        # print(f"Swapped: {a} and {b}")
        a_row, a_col = a
        b_row, b_col = b

        # swap the particles
        self.matrix[a_row][a_col], self.matrix[b_row][b_col] = self.matrix[b_row][b_col], self.matrix[a_row][a_col]

        # update the particles' self-tracked locations
        self.matrix[a_row][a_col].location = (a_row, a_col)
        self.matrix[b_row][b_col].location = (b_row, b_col)

    def swap_new(self, a: Element, b: Element):
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
    """
    ABSTRACT = False

    NAME = None
    ID = None
    COLOR = None

    DENSITY = None
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
        if (self.NAME is None) or (self.ID is None) or (self.COLOR is None) or (self.DENSITY is None):
            raise NotImplementedError("""Subclass must define: NAME, ID, COLOR, DENSITY""")
        
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

class Solid(Element):
    ABSTRACT = True

class MovableSolid(Solid):
    ABSTRACT = True

class ImmovableSolid(Solid):
    ABSTRACT = True

    MOVABLE = False

class Gas(Element):
    ABSTRACT = True



class Air(Gas):
    NAME = "Air"
    ID = 0
    COLOR = (0, 0, 0)
    DENSITY = 1.225

    def update(self):
        """Air currently has no logic, skip"""
        return

class Sand(MovableSolid):
    NAME = "Sand"
    ID = 1
    COLOR = (230, 197, 92)
    DENSITY = 1430
    
    def update(self):
        if self.has_been_updated:
            return # don't update if we have already done so this step

        row, col = self.location
        
        # check below
        if (target := self.grid.get_pos(row+1, col)):
            # if the target isn't None
            if target.DENSITY < self.DENSITY:
                self.grid.swap_new(self, target)
                return
        # else:
        #     pass # target out of bounds, ignore

        # check down-left
        if (target := self.grid.get_pos(row+1, col-1)):
            if target.DENSITY < self.DENSITY:
                self.grid.swap_new(self, target)
                return
        
        # check down-right
        if (target := self.grid.get_pos(row+1, col+1)):
            if target.DENSITY < self.DENSITY:
                self.grid.swap_new(self, target)
                return

class Water(Liquid):
    NAME = "Water"
    ID = 2
    COLOR = (35, 137, 218)
    DENSITY = 1000

    # if we want to randomise the water colour
    def __init__(self, grid, location):
        super().__init__(grid, location)
        self.COLOR = random.choice(((35, 137, 218), (28, 163, 236), (90, 188, 216), (116, 204, 244)))

    def update(self):
        if self.has_been_updated:
            return
        
        row, col = self.location

        # check below
        if (target := self.grid.get_pos(row+1, col)):
            if target.DENSITY < self.DENSITY:
                self.grid.swap_new(self, target)
                return

        # check down-left
        if (target := self.grid.get_pos(row+1, col-1)):
            if target.DENSITY < self.DENSITY:
                self.grid.swap_new(self, target)
                return
        
        # check down-right
        if (target := self.grid.get_pos(row+1, col+1)):
            if target.DENSITY < self.DENSITY:
                self.grid.swap_new(self, target)
                return
        
        # check left
        if (target := self.grid.get_pos(row, col-1)):
            if target.DENSITY < self.DENSITY:
                self.grid.swap_new(self, target)
                return

        # check right
        if (target := self.grid.get_pos(row, col+1)):
            if target.DENSITY < self.DENSITY:
                self.grid.swap_new(self, target)
                return

        # return super().update()

class Smoke(Gas):
    NAME = "Smoke"
    ID = 3
    COLOR = (115, 130, 118)
    DENSITY = 1.2
    # density of smoke can range:
    # Fresh, hot smoke can be 0.6-1.1kg/m^3
    # Cooled, room temperature smoke can be around 1.0-1.3kg/m^3

    def update(self):
        if self.has_been_updated:
            return

        row, col = self.location

        # WE CAN PROBABLY JUST GET AWAY WITH SWITCHING TO CHECKING BELOW AND REVERSE THE DENSITY FROM > TO <

        # check above
        if (target := self.grid.get_pos(row-1, col)):
            if target.DENSITY > self.DENSITY:
                self.grid.swap_new(self, target)
                return

        # check up-left
        if (target := self.grid.get_pos(row-1, col-1)):
            if target.DENSITY > self.DENSITY:
                self.grid.swap_new(self, target)
                return
        
        # check up-right
        if (target := self.grid.get_pos(row-1, col+1)):
            if target.DENSITY > self.DENSITY:
                self.grid.swap_new(self, target)
                return
        
        # check left
        if (target := self.grid.get_pos(row, col-1)):
            if target.DENSITY > self.DENSITY:
                self.grid.swap_new(self, target)
                return

        # check right
        if (target := self.grid.get_pos(row, col+1)):
            if target.DENSITY > self.DENSITY:
                self.grid.swap_new(self, target)
                return

# print(Element.registry)