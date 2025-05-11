# agent/eval.py

from referee.game import Coord, PlayerColor

def evaluate(board) -> int:
    score = 0
    goal_row = 7 if board.color == PlayerColor.RED else 0
    enemy_goal = 0 if board.color == PlayerColor.RED else 7

    for frog in board.my_frogs:
        # Reward progress
        progress = abs(frog.r - goal_row)
        score -= 2 * progress

        # Bonus for goal row
        if frog.r == goal_row:
            score += 50

        # Bonus for being in enemy half
        if (board.color == PlayerColor.RED and frog.r > 3) or \
           (board.color == PlayerColor.BLUE and frog.r < 4):
            score += 5

        # Check local mobility (adjacent lilypads)
        mobility = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = frog.r + dr, frog.c + dc
                if 0 <= r < 8 and 0 <= c < 8:
                    if Coord(r, c) in board.lilypads:
                        mobility += 1
        score += mobility

    for frog in board.enemy_frogs:
        # Penalize enemy frogs in our goal
        if frog.r == enemy_goal:
            score -= 50
        else:
            score += abs(frog.r - enemy_goal)

    return score
