# agent/utils/board_utils.py

from referee.game import Coord, Direction

def is_within_bounds(row: int, col: int, size: int = 8) -> bool:
    """Returns True if (row, col) is inside the board bounds."""
    return 0 <= row < size and 0 <= col < size

def safe_generate_moves(board, coord, directions, size=8):
    """Filter directions that result in in-bounds coordinates."""
    r0, c0 = coord.r, coord.c
    valid_directions = []
    for dir in directions:
        r, c = r0 + dir.r, c0 + dir.c
        if is_within_bounds(r, c, size):
            valid_directions.append(dir)
    return valid_directions

def apply_direction(coord: Coord, direction: Direction, step: int = 1) -> Coord:
    """Applies a direction to a coordinate and returns the new coordinate."""
    dr, dc = direction.value
    new_r, new_c = coord.r + dr * step, coord.c + dc * step
    if not is_within_bounds(new_r, new_c):
        raise ValueError(f"Out of bounds: {new_r}, {new_c}")
    return Coord(new_r, new_c)
