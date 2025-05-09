# COMP30024 Artificial Intelligence, Semester 1 2025
# Project Part B: Game Playing Agent

from referee.game import PlayerColor, Coord, Direction, Action, MoveAction, GrowAction
from agent.board import Board
from agent.eval import evaluate
from agent.utils.board_utils import is_within_bounds  # ✅ added import

import random
import math
import copy

class Agent:
    def __init__(self, color: PlayerColor, **referee: dict):
        self._color = color
        self.board = Board(color)
        self.board.initialize()

        match color:
            case PlayerColor.RED:
                print("Testing: I am playing as RED")
            case PlayerColor.BLUE:
                print("Testing: I am playing as BLUE")

    def action(self, **referee: dict) -> Action:
        best_score = -math.inf
        best_action = None
        alpha = -math.inf
        beta = math.inf
        depth = 3

        actions = self.generate_actions(self.board, True)

        print("==== VALID ACTIONS GENERATED ====")
        for action in actions:
            print("Trying:", action)

        for action in actions:
            new_board = self.simulate_action(action, self.board, True)
            score = self.minimax(new_board, depth - 1, alpha, beta, False)

            if score > best_score:
                best_score = score
                best_action = action
            alpha = max(alpha, score)

        return best_action if best_action else GrowAction()

    def minimax(self, board, depth, alpha, beta, maximizing):
        if depth == 0:
            return evaluate(board)

        actions = self.generate_actions(board, maximizing)
        if not actions:
            return evaluate(board)

        if maximizing:
            max_eval = -math.inf
            for action in actions:
                next_board = self.simulate_action(action, board, True)
                score = self.minimax(next_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for action in actions:
                next_board = self.simulate_action(action, board, False)
                score = self.minimax(next_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return min_eval

    def generate_actions(self, board, for_maximizer):
        frogs = board.my_frogs if for_maximizer else board.enemy_frogs
        color = board.color if for_maximizer else (
            PlayerColor.RED if board.color == PlayerColor.BLUE else PlayerColor.BLUE
        )

        valid_dirs = {
            PlayerColor.RED: [
                Direction.Right, Direction.Left, Direction.Down,
                Direction.DownLeft, Direction.DownRight
            ],
            PlayerColor.BLUE: [
                Direction.Right, Direction.Left, Direction.Up,
                Direction.UpLeft, Direction.UpRight
            ],
        }

        actions = []

        for frog in frogs:
            for d in valid_dirs[color]:
                if self.is_legal_single_step(frog, d):
                    actions.append(MoveAction(frog, [d]))

            all_frogs = board.my_frogs | board.enemy_frogs
            jump_paths = self.find_jump_paths(board, frog, valid_dirs[color], all_frogs)
            for path in jump_paths:
                actions.append(MoveAction(frog, path))

        actions.append(GrowAction())
        return actions

    def find_jump_paths(self, board, start, directions, all_frogs):
        results = []

        def dfs(current, path, visited):
            for d in directions:
                dr, dc = d.value
                over_r = current.r + dr
                over_c = current.c + dc
                land_r = current.r + 2 * dr
                land_c = current.c + 2 * dc

                if not is_within_bounds(land_r, land_c):  # ✅ updated check
                    continue

                over = Coord(over_r, over_c)
                land = Coord(land_r, land_c)

                if (
                    over in all_frogs and
                    land in board.lilypads and
                    land not in board.my_frogs and
                    land not in board.enemy_frogs and
                    land not in visited
                ):
                    new_path = path + [d]
                    results.append(new_path)
                    visited.add(land)
                    dfs(land, new_path, visited)
                    visited.remove(land)

        dfs(start, [], set())
        return results

    def simulate_action(self, action, board, for_maximizer):
        try:
            new_board = copy.deepcopy(board)
            if isinstance(action, MoveAction):
                try:
                    if for_maximizer:
                        if not self.validate_move(new_board, action.coord, action.directions):
                            raise ValueError("Invalid simulated move")
                        new_board.apply_move(action.coord, action.directions)
                    else:
                        if not self.validate_move(new_board, action.coord, action.directions):
                            raise ValueError("Invalid simulated opponent move")
                        new_board.update_opponent(action.coord, action.directions)

                except Exception as e:
                    print(f"[SIM ERROR]: Invalid move skipped during simulate: {action}, error: {e}")
                    return board

            elif isinstance(action, GrowAction):
                new_board.apply_grow()
            return new_board
        except ValueError as e:
            print(f"[SIMULATION ERROR]: Skipping invalid move {action}: {e}")
            return board

    def is_legal_single_step(self, start: Coord, direction: Direction) -> bool:
        dr, dc = direction.value
        next_r = start.r + dr
        next_c = start.c + dc

        if not is_within_bounds(next_r, next_c):  # ✅ updated check
            return False

        dest = Coord(next_r, next_c)

        if dest not in self.board.lilypads:
            return False
        if dest in self.board.my_frogs or dest in self.board.enemy_frogs:
            return False

        return True

    def validate_move(self, board, start: Coord, directions: list[Direction]) -> bool:
        pos = start
        for d in directions:
            dr, dc = d.value
            next_r, next_c = pos.r + dr, pos.c + dc

            if not is_within_bounds(next_r, next_c):
                return False

            next_pos = Coord(next_r, next_c)

            if next_pos not in board.lilypads:
                return False
            if next_pos in board.my_frogs or next_pos in board.enemy_frogs:
                return False

            pos = next_pos

        return True

    def update(self, color: PlayerColor, action: Action, **referee: dict):
        match action:
            case MoveAction(coord, dirs):
                dirs_text = ", ".join([dir.name for dir in dirs])
                print(f"Testing: {color} played MOVE action:")
                print(f"  Coord: {coord}")
                print(f"  Directions: {dirs_text}")
                if color == self._color:
                    self.board.apply_move(coord, dirs)
                else:
                    try:
                        self.board.update_opponent(coord, dirs)
                    except ValueError as e:
                        print(f"[ERROR] Illegal opponent move from {coord} via {dirs}: {e}")

            case GrowAction():
                print(f"Testing: {color} played GROW action")
                if color == self._color:
                    self.board.apply_grow()
            case _:
                raise ValueError(f"Unknown action type: {action}")
