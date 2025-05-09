# agent/utils/directions.py

from agent.utils.board_utils import is_within_bounds

class Direction:
    def __init__(self, dr: int, dc: int):
        self.dr = dr
        self.dc = dc

    def apply(self, position: tuple[int, int]) -> tuple[int, int] | None:
        """Apply the direction to a position if within bounds."""
        new_row = position[0] + self.dr
        new_col = position[1] + self.dc
        if is_within_bounds(new_row, new_col):
            return new_row, new_col
        return None

# Define all possible directions
DIRECTIONS = {
    'N': Direction(-1, 0),
    'NE': Direction(-1, 1),
    'E': Direction(0, 1),
    'SE': Direction(1, 1),
    'S': Direction(1, 0),
    'SW': Direction(1, -1),
    'W': Direction(0, -1),
    'NW': Direction(-1, -1),
}
