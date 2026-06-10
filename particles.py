import random
from typing import Literal

class Direction:
    UP = -1
    DOWN = 1
    LEFT = -1
    RIGHT = 1

    NONE = 0

def get_rand_pref() -> tuple[Direction, Direction]:
    return (1, -1) if random.random() > 0.5 else (-1, 1)

class ParticleSim:
    def __init__(self, n_rows: int, n_cols: int):
        self.n_rows = n_rows # rows
        self.n_cols = n_cols # columns

        self.selected_particle = Sand

        # internal flag used to alternate between the simulation scan happening Left -> Right and Right -> Left
        self._invert_eval = False

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

    def step(self):
        """One simulaton step"""

        # reset update flags
        for row in self.matrix:
            for p in row:
                p.has_been_updated = False

        # bottom-up update to prevent double-falling
        for row in reversed(self.matrix):
            if self._invert_eval: # if scanning Left -> Right
                for particle in row:
                    particle.update()
            else: # if scanning Right -> Left
                for particle in reversed(row):
                    particle.update()
        
        # invert the scan direction flag
        self._invert_eval = not self._invert_eval

    def get_pos(self, row: int, col: int) -> Element | None:
        """
        Returns the particle at the given position, or None if the position is out of bounds
        """
        if (row < 0) or (row >= self.n_rows):
            return
        if (col < 0) or (col >= self.n_cols):
            return
        
        return self.matrix[row][col]
    
    def can_move_into(self, source: Element, target: Element) -> bool:
        """
        Check whether movement from source to target particle is allowed
        """
        # out of bounds should already be handled

        # empty cell (Void) is ALWAYS valid
        if target.ID == Void.ID:
            return True
        
        # cannot swap with a cell that has already updated
        if target.has_been_updated:
            return False
        
        # states of matter
        if isinstance(source, Solid) and isinstance(target, Solid):
            return # don't allow solids to swap with each other

        if isinstance(source, Liquid) and isinstance(target, Gas):
            return # unsure if this will break anything else, but it fixes gases getting trapped inside liquids

        # if source(solid), pass
        # if source(liquid) and target(not solid), pass
        # if source(gas), pass

        # solid can pass through all
        # liquid can pass through gas but not solid
        # gas can pass through liquid, gas, solid

        # blocked my immovable particles
        if not target.MOVABLE:
            return False
        
        # density rule
        return (source.DENSITY - target.DENSITY) * source.VERTICAL_DIR > 0

    def swap(self, a: Element, b: Element):
        """
        Swap particles on the grid.

        Automatically sets `has_been_updated = True` on both particles
        """
        # print(f"Swapped: ({a.row}, {a.col}) and ({b.row}, {b.col})")

        # swap the particles
        self.matrix[a.row][a.col], self.matrix[b.row][b.col] = self.matrix[b.row][b.col], self.matrix[a.row][a.col]

        # update the particles' self-tracked locations
        a.row, b.row = b.row, a.row
        a.col, b.col = b.col, a.col
        # a.row, a.col = b.row, b.col
        # b.row, b.col = a.row, a.col

        # mark both particles as having been updated
        a.has_been_updated = True
        b.has_been_updated = True

    def replace(self, location: tuple[int, int], particle: Element):
        """Replaces the particle at the given location with one of the given type"""
        row, col = location
        
        self.matrix[row][col] = particle(self, (row, col))

class Element:
    """All Elements must define:
    - `NAME: str`
    - `ID: int`
    - `COLOR: tuple[int, int, int]` (RGB)
    - `DENSITY: int | float` (kg/m^3)
    - `VERTICAL_DIR: Direction` (default: DOWN)
      - Direction.DOWN = moves downward
      - Direction.UP = moves upward

    Optional:
    - `MOVABLE: bool` (default: True)
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

        Element.registry.append(cls)

    def __init__(self, grid: ParticleSim, location: tuple[int, int]):
        if (self.NAME is None) or (self.ID is None) or (self.COLOR is None) or (self.DENSITY is None) or (self.VERTICAL_DIR is None):
            raise NotImplementedError("""Subclass must define: NAME, ID, COLOR, DENSITY, VERTICAL_DIR""")
        
        self.grid = grid
        # self.location = location # (row, col)
        self.row = location[0] # vertical position (up/down)
        self.col = location[1] # horizontal position (left/right)

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
        return f"{self.NAME}:({self.row}, {self.col})"

class Liquid(Element):
    """All Liquids must define:
    - `NAME: str`
    - `ID: int`
    - `COLOR: tuple[int, int, int]` (RGB)
    - `DENSITY: int | float` (kg/m^3)

    Optional:
    - `MOVABLE: bool` (default: True)
    - `VERTICAL_DIR: Direction` (default: DOWN)
      - Direction.DOWN = moves downward
      - Direction.UP = moves upward
    - `MAX_DISPERSION: int` (default: 5)
    """
    ABSTRACT = True
    VERTICAL_DIR = Direction.DOWN

    MAX_DISPERSION = 5

    def update(self):
        if self.has_been_updated:
            return

        # randomise whether the particle prefers to move left or right
        dir_pref = get_rand_pref()

        # Liquids check:
        # -> down
        # -> diagonal down
        # -> sideways
        
        # down
        if (target := self.grid.get_pos(self.row+self.VERTICAL_DIR, self.col)): # check down
            if self.grid.can_move_into(self, target):
                self.grid.swap(self, target)
                return
        
        # diagonal down
        for side in dir_pref:
            if (target := self.grid.get_pos(self.row, self.col+side)): # check side first (prevent clipping)
                if self.grid.can_move_into(self, target): # if we can move to the side
                    if (target := self.grid.get_pos(self.row+self.VERTICAL_DIR, self.col+side)): # then check down and sideways
                        if self.grid.can_move_into(self, target):
                            self.grid.swap(self, target)
                            return

        # if we got this far without moving, start trying to disperse sideways
        last_valid = [] # the last valid swap position found

        # disperse sideways
        for side in dir_pref:
            for i in range(1, self.MAX_DISPERSION+1):
                if (target := self.grid.get_pos(self.row, self.col+(i*side))): # check sideways by i
                    if self.grid.can_move_into(self, target): # if we can move into that cell
                        # set the last valid position to that cell
                        last_valid.append(target)
                    else:
                        break
                else:
                    break
            if last_valid: # if there are any, swap into a random valid position
                self.grid.swap(self, random.choice(last_valid))
                return

class Solid(Element):
    """All Solids must define:
    - `NAME: str`
    - `ID: int`
    - `COLOR: tuple[int, int, int]` (RGB)
    - `DENSITY: int | float` (kg/m^3)

    Optional:
    - `MOVABLE: bool` (default: False)
    - `VERTICAL_DIR: Direction` (default: DOWN)
      - Direction.DOWN = moves downward
      - Direction.UP = moves upward
    """
    ABSTRACT = True
    VERTICAL_DIR = Direction.DOWN

    def update(self):
        if self.has_been_updated:
            return

        # Solids check:
        # (row+1, col)   # down
        # (row+1, col-1) # down-left
        # (row+1, col+1) # down-right
        
        # down
        if (target := self.grid.get_pos(self.row+1, self.col)): # check down
            if self.grid.can_move_into(self, target):
                self.grid.swap(self, target)
                return
        
        # down-left
        if (target_l := self.grid.get_pos(self.row, self.col-1)): # check left first (prevent clipping)
            if self.grid.can_move_into(self, target_l): # if we can move left
                if (target := self.grid.get_pos(self.row+self.VERTICAL_DIR, self.col-1)): # then check down-left
                    if self.grid.can_move_into(self, target):
                        self.grid.swap(self, target)
                        return
            
        # down-right
        if (target_r := self.grid.get_pos(self.row, self.col+1)): # check right first (prevent clipping)
            if self.grid.can_move_into(self, target_r): # if we can move right
                if (target := self.grid.get_pos(self.row+self.VERTICAL_DIR, self.col+1)): # then check down-right
                    if self.grid.can_move_into(self, target):
                        self.grid.swap(self, target)
                        return

class MovableSolid(Solid):
    """All Movable Solids must define:
    - `NAME: str`
    - `ID: int`
    - `COLOR: tuple[int, int, int]` (RGB)
    - `DENSITY: int | float` (kg/m^3)

    Optional:
    - `MOVABLE: bool` (default: False)
    - `VERTICAL_DIR: Direction` (default: DOWN)
      - Direction.DOWN = moves downward
      - Direction.UP = moves upward
    """
    ABSTRACT = True

class ImmovableSolid(Solid):
    """All Immovable Solids must define:
    - `NAME: str`
    - `ID: int`
    - `COLOR: tuple[int, int, int]` (RGB)
    - `DENSITY: int | float` (kg/m^3)

    Optional:
    - `MOVABLE: bool` (default: False)
    - `VERTICAL_DIR: Direction` (default: NONE)
      - Direction.DOWN = moves downward
      - Direction.UP = moves upward
    """
    ABSTRACT = True

    VERTICAL_DIR = Direction.NONE
    MOVABLE = False

    def update(self):
        """
        Immovable solids have no behaviour by default
        """
        return

class Gas(Element):
    """All Gases must define:
    - `NAME: str`
    - `ID: int`
    - `COLOR: tuple[int, int, int]` (RGB)
    - `DENSITY: int | float` (kg/m^3)

    Optional:
    - `MOVABLE: bool` (default: False)
    - `VERTICAL_DIR: Direction` (default: UP)
      - Direction.DOWN = moves downward
      - Direction.UP = moves upward
    - `MAX_DISPERSION: int` (default: 5)
    """
    ABSTRACT = True
    VERTICAL_DIR = Direction.UP

    MAX_DISPERSION = 5

    def update(self):
        if self.has_been_updated:
            return

        # randomise whether the particle prefers to move left or right
        dir_pref = get_rand_pref()

        # Gases check:
        # -> up
        # -> diagonal up
        # -> sideways
        
        # up
        if (target := self.grid.get_pos(self.row+self.VERTICAL_DIR, self.col)): # check up
            if self.grid.can_move_into(self, target):
                self.grid.swap(self, target)
                return
        
        # diagonal up
        for side in dir_pref:
            if (target := self.grid.get_pos(self.row, self.col+side)): # check side first (prevent clipping)
                if self.grid.can_move_into(self, target): # if we can move to the side
                    if (target := self.grid.get_pos(self.row+self.VERTICAL_DIR, self.col+side)): # then check diagonal up
                        if self.grid.can_move_into(self, target):
                            self.grid.swap(self, target)
                            return

        # if we got this far without moving, start trying to disperse sideways
        last_valid = [] # the last valid swap position found

        # disperse sideways
        for side in dir_pref:
            for i in range(1, self.MAX_DISPERSION+1):
                if (target := self.grid.get_pos(self.row, self.col+(i*side))): # check sideways by i
                    if self.grid.can_move_into(self, target): # if we can move into that cell
                        # set the last valid position to that cell
                        last_valid.append(target)
                    else:
                        break
                else:
                    break
            if last_valid: # if there are any, swap into a random valid position
                self.grid.swap(self, random.choice(last_valid))
                return

class Void(Element):
    NAME = "Void"
    ID = 0
    COLOR = (0, 0, 0)
    DENSITY = 0

    VERTICAL_DIR = Direction.NONE

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