# agent/board.py

from referee.game import Coord, PlayerColor, Direction
from typing import Set


class Board:
    def __init__(self, color: PlayerColor):
        self.color = color
        self.my_frogs: Set[Coord] = set()
        self.enemy_frogs: Set[Coord] = set()
        self.lilypads: Set[Coord] = set()

    def initialize(self):
        red_row, blue_row = 0, 7
        for col in [1, 2, 3, 4, 5, 6]:
            red_coord = Coord(red_row, col)
            blue_coord = Coord(blue_row, col)
            self.lilypads.add(red_coord)
            self.lilypads.add(blue_coord)
            if self.color == PlayerColor.RED:
                self.my_frogs.add(red_coord)
                self.enemy_frogs.add(blue_coord)
            else:
                self.my_frogs.add(blue_coord)
                self.enemy_frogs.add(red_coord)

    def apply_move(self, coord: Coord, dirs: list[Direction]):
        if coord in self.my_frogs:
            self.my_frogs.remove(coord)
        self.lilypads.discard(coord)

        try:
            new_coord = self.follow_directions(coord, dirs)
        except ValueError as e:
            print(f"[ERROR] Illegal move from {coord} via {dirs}: {e}")
            raise

        self.my_frogs.add(new_coord)

    def update_opponent(self, coord: Coord, dirs: list[Direction]):
        if coord in self.enemy_frogs:
            self.enemy_frogs.remove(coord)
        self.lilypads.discard(coord)

        try:
            new_coord = self.follow_directions(coord, dirs)  # defaults to step=2
        except ValueError as e:
            print(f"[ERROR] Illegal opponent move from {coord} via {dirs}: {e}")
            raise

        self.enemy_frogs.add(new_coord)

    def apply_grow(self):
        for frog in self.my_frogs:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    new_r, new_c = frog.r + dr, frog.c + dc
                    if 0 <= new_r < 8 and 0 <= new_c < 8:
                        self.lilypads.add(Coord(new_r, new_c))

    def follow_directions(self, start: Coord, dirs: list[Direction], step: int = 2) -> Coord:
        current = start
        for d in dirs:
            vec = d.value
            next_r = current.r + step * vec.r
            next_c = current.c + step * vec.c
            if not (0 <= next_r < 8 and 0 <= next_c < 8):
                raise ValueError(f"Out-of-bounds coordinate: {next_r}-{next_c}")
            current = Coord(next_r, next_c)
        return current

