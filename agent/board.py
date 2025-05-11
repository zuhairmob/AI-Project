from referee.game import Coord, PlayerColor, Direction
from agent.utils.board_utils import is_within_bounds
from typing import Set

class Board:
    def __init__(self, color: PlayerColor):
        self.color = color
        self.my_frogs: Set[Coord] = set()
        self.enemy_frogs: Set[Coord] = set()
        self.lilypads: Set[Coord] = set()

    def initialize(self):
        red_row, blue_row = 0, 7
        for col in range(1, 7):
            red = Coord(red_row, col)
            blue = Coord(blue_row, col)
            self.lilypads.update({red, blue})
            if self.color == PlayerColor.RED:
                self.my_frogs.add(red)
                self.enemy_frogs.add(blue)
            else:
                self.my_frogs.add(blue)
                self.enemy_frogs.add(red)

    def apply_move(self, coord: Coord, dirs: list[Direction]):
        # Remove frog and its lilypad
        self.my_frogs.remove(coord)
        self.lilypads.discard(coord)
        dest = self.follow_directions(coord, dirs)
        self.my_frogs.add(dest)

    def update_opponent(self, coord: Coord, dirs: list[Direction]):
        self.enemy_frogs.remove(coord)
        self.lilypads.discard(coord)
        dest = self.follow_directions(coord, dirs)
        self.enemy_frogs.add(dest)

    def apply_grow(self):
        for frog in list(self.my_frogs):
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    r, c = frog.r + dr, frog.c + dc
                    if is_within_bounds(r, c):
                        self.lilypads.add(Coord(r, c))

    def follow_directions(self, start: Coord, dirs: list[Direction]) -> Coord:
        current = start
        for d in dirs:
            dr, dc = d.value
            # Determine if this hop is a jump (over another frog) or a step
            mid = Coord(current.r + dr, current.c + dc)
            if mid in self.my_frogs or mid in self.enemy_frogs:
                step = 2
            else:
                step = 1
            next_r = current.r + step * dr
            next_c = current.c + step * dc

            if not is_within_bounds(next_r, next_c):
                raise ValueError(f"Out-of-bounds coordinate: {next_r}-{next_c}")

            current = Coord(next_r, next_c)

        return current
