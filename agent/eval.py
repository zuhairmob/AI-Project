# agent/eval.py

from referee.game import Coord, PlayerColor

def evaluate(board) -> int:
    """
    Simple evaluation function.
    Positive = good for our agent.
    """
    score = 0
    goal_row = 7 if board.color == PlayerColor.RED else 0

    # Reward frogs close to goal row
    for frog in board.my_frogs:
        dist = abs(frog.r - goal_row)
        score -= dist

    # Penalize enemy frogs close to their goal
    for frog in board.enemy_frogs:
        dist = abs(frog.r - (0 if board.color == PlayerColor.RED else 7))
        score += dist

    return score
