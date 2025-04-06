# COMP30024 Artificial Intelligence, Semester 1 2025
# Project Part A: Single Player Freckers

from enum import Enum
from dataclasses import dataclass
from typing import Generator, Iterator

# WARNING: Please *do not* modify any of the code in this file, as this could
#          break things in the submission environment. Failed test cases due to
#          modification of this file will not receive any marks. 
#
#          To implement your solution you should modify the `search` function
#          in `program.py` instead, as discussed in the specification.

BOARD_N = 8


@dataclass(frozen=True, slots=True)
class Vector2:
    """
    A simple 2D vector "helper" class with basic arithmetic operations
    overloaded for convenience.
    """
    r: int
    c: int

    def __lt__(self, other: 'Vector2') -> bool:
        return (self.r, self.c) < (other.r, other.c)
    
    def __hash__(self) -> int:
        return hash((self.r, self.c))
    
    def __str__(self) -> str:
        return f"Vector2({self.r}, {self.c})"

    def __add__(self, other: 'Vector2|Direction') -> 'Vector2':
        return self.__class__(self.r + other.r, self.c + other.c)

    def __sub__(self, other: 'Vector2|Direction') -> 'Vector2':
        return self.__class__(self.r - other.r, self.c - other.c)

    def __neg__(self) -> 'Vector2':
        return self.__class__(self.r * -1, self.c * -1)

    def __mul__(self, n: int) -> 'Vector2':
        return self.__class__(self.r * n, self.c * n)

    def __iter__(self) -> Generator[int, None, None]:
        yield self.r
        yield self.c

    def down(self, n: int = 1) -> 'Vector2':
        return self + Direction.Down * n
    
    def up(self, n: int = 1) -> 'Vector2':
        return self + Direction.Up * n
    
    def left(self, n: int = 1) -> 'Vector2':
        return self + Direction.Left * n
    
    def right(self, n: int = 1) -> 'Vector2':
        return self + Direction.Right * n


class Direction(Enum):
    """
    An `enum` capturing the eight directions on the square grid-based board.
    """
    Down      = Vector2(1, 0)
    DownLeft  = Vector2(1, -1)
    DownRight = Vector2(1, 1)
    Up        = Vector2(-1, 0)
    UpLeft    = Vector2(-1, -1)
    UpRight   = Vector2(-1, 1)
    Left      = Vector2(0, -1)
    Right     = Vector2(0, 1)

    @classmethod
    def _missing_(cls, value: tuple[int, int]):
        for item in cls:
            if item.value == Vector2(*value):
                return item
        raise ValueError(f"Invalid direction: {value}")

    def __neg__(self) -> 'Direction':
        return Direction(-self.value)

    def __mul__(self, n: int) -> 'Vector2':
        return self.value * n

    def __str__(self) -> str:
        return {
            Direction.Down:      "[↓]",
            Direction.DownLeft:  "[↙]",
            Direction.DownRight: "[↘]",
            Direction.Up:        "[↑]",
            Direction.UpLeft:    "[↖]",
            Direction.UpRight:   "[↗]",
            Direction.Left:      "[←]",
            Direction.Right:     "[→]",
        }[self]
    
    def __iter__(self) -> Iterator[int]:
        return iter(self.value)

    def __getattribute__(self, __name: str) -> int:
        match __name:
            case "r":
                return self.value.r
            case "c":
                return self.value.c
            case _:
                return super().__getattribute__(__name)


@dataclass(order=True, frozen=True)
class Coord(Vector2):
    """
    A specialisation of the `Vector2` class, representing a coordinate on the
    game board. This class also enforces that the coordinates are within the
    bounds of the game board, or in the case of addition/subtraction, using
    modulo arithmetic to "wrap" the coordinates at the edges of the board.
    """

    def __post_init__(self):
        if not (0 <= self.r < BOARD_N) or not (0 <= self.c < BOARD_N):
            raise ValueError(f"Out-of-bounds coordinate: {self}")

    def __str__(self):
        return f"{self.r}-{self.c}"

    def __add__(self, other: 'Direction|Vector2') -> 'Coord':
        return self.__class__(
            (self.r + other.r) % BOARD_N, 
            (self.c + other.c) % BOARD_N,
        )

    def __sub__(self, other: 'Direction|Vector2') -> 'Coord':
        return self.__class__(
            (self.r - other.r) % BOARD_N, 
            (self.c - other.c) % BOARD_N
        )
    

class CellState(Enum):
    """
    An `enum` capturing the possible states of a cell on the game board.
    """
    RED = 1
    BLUE = 2
    LILY_PAD = 3

    def __str__(self) -> str:
        return {
            CellState.RED: "R",
            CellState.BLUE: "B",
            CellState.LILY_PAD: "*",
        }[self]


@dataclass(frozen=True, slots=True)
class MoveAction():
    """
    A dataclass representing a "move action", which consists of a coordinate 
    and one or more directions (multiple directions used for multiple hops).
    """
    coord: Coord
    _directions: Direction | list[Direction]

    @property
    def directions(self) -> list[Direction]:
        if isinstance(self._directions, Direction):
            return [self._directions]
        return self._directions
    
    def __str__(self) -> str:
        try:
            dirs_text = ", ".join(str(d) for d in self.directions)
            return f"MOVE({self.coord}, [{dirs_text}])"
        except:
            return f"MOVE(<invalid coord/directions>)"
