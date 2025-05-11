from referee.game import Coord, Direction

def is_within_bounds(row: int, col: int, size: int = 8) -> bool:
    return 0 <= row < size and 0 <= col < size

def apply_direction(coord: Coord, direction: Direction, step: int = 1) -> Coord:
    dr, dc = direction.value
    new_r, new_c = coord.r + dr * step, coord.c + dc * step
    if not is_within_bounds(new_r, new_c):
        raise ValueError(f"Out of bounds: {new_r}, {new_c}")
    return Coord(new_r, new_c)
