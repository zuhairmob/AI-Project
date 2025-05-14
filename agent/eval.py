# a richer evaluation: goal‐completion, distance, jump‐potential, clustering.

from .utils.board_utils import is_within_bounds
from referee.game import Direction, Coord
from referee.game import PlayerColor

def evaluate(board) -> float:
    """
    Simple heuristic:
      +100 for each of your frogs on your goal row
      -100 for each enemy frog on their goal row
      -sum of vertical distances of your frogs to your goal row
    """

    me = board.my_frogs
    you = board.enemy_frogs

    # 1) figure out the min/max row on the board
    rows = [coord.r for coord in board.lilypads]
    min_row, max_row = min(rows), max(rows)

    # 2) your goal row = bottom if RED, top if BLUE
    if board.color == PlayerColor.RED:
        my_goal_row = max_row
        enemy_goal_row = min_row
    else:
        my_goal_row = min_row
        enemy_goal_row = max_row

    # 3) score frogs that have already reached goal
    reach_score = 100 * (sum(1 for f in me if f.r == my_goal_row)
                       - sum(1 for f in you if f.r == enemy_goal_row))

    # 4) penalize by vertical distance to your goal
    dist_penalty = sum(abs(f.r - my_goal_row) for f in me)

    return float(reach_score - dist_penalty)
