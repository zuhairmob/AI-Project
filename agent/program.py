# COMP30024 Artificial Intelligence, Semester 1 2025
# Project Part B: Game Playing Agent

from referee.game import PlayerColor, Coord, Direction, Action, MoveAction, GrowAction
from agent.board import Board
from agent.eval import evaluate
from agent.utils.board_utils import is_within_bounds

import random
import math
import copy
import time

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
        current_board = self.board
        actions = self.generate_actions(current_board, True)
        if not actions:
            return GrowAction()

        # Time management for iterative deepening
        time_remaining = referee.get("time_remaining", 1.0)
        # Cap per-move computation to at most 1 second
        time_limit = min(time_remaining, 1.0)
        start_time = time.time()

        # Initial fallback random action
        best_action = random.choice(actions)
        depth = 1

        # Iterative deepening loop
        while True:
            alpha = -math.inf
            beta = math.inf
            new_best = None
            new_best_score = -math.inf

            for act in actions:
                # Check against time budget (with 50ms safety buffer)
                if time.time() - start_time > time_limit - 0.05:
                    break

                new_board = self.simulate_action(act, current_board, True)
                score = self.minimax(new_board, depth - 1, alpha, beta, False, start_time, time_limit)

                # Tie-break randomly on equal scores
                if score > new_best_score or (score == new_best_score and random.random() < 0.5):
                    new_best_score = score
                    new_best = act
                alpha = max(alpha, score)

            # Stop deepening if out of time
            if time.time() - start_time > time_limit - 0.05:
                break

            # Update best action from this depth
            if new_best is not None:
                best_action = new_best

            # Prepare for next iteration
            depth += 1
            actions = self.generate_actions(current_board, True)

        # Debug info for final selection
        print(f"[DEBUG] Time used: {time.time() - start_time:.2f}s, depth reached: {depth}, selected: {best_action}")
        return best_action

    def minimax(self, board, depth, alpha, beta, maximizing, start_time=None, time_limit=None):
        # Early return on time cutoff
        if start_time and time_limit and time.time() - start_time > time_limit - 0.05:
            return evaluate(board)
        if depth == 0:
            return evaluate(board)

        actions = self.generate_actions(board, maximizing)
        if not actions:
            return evaluate(board)

        if maximizing:
            max_eval = -math.inf
            for act in actions:
                next_board = self.simulate_action(act, board, True)
                score = self.minimax(next_board, depth - 1, alpha, beta, False, start_time, time_limit)
                max_eval = max(max_eval, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for act in actions:
                next_board = self.simulate_action(act, board, False)
                score = self.minimax(next_board, depth - 1, alpha, beta, True, start_time, time_limit)
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
            # Single-step moves
            for d in valid_dirs[color]:
                if self.is_legal_single_step(board, frog, d):
                    actions.append(MoveAction(frog, [d]))
            # Jump moves
            all_frogs = board.my_frogs | board.enemy_frogs
            for path in self.find_jump_paths(board, frog, valid_dirs[color], all_frogs):
                actions.append(MoveAction(frog, path))

        actions.append(GrowAction())
        return actions

    def find_jump_paths(self, board, start, directions, all_frogs):
        results = []
        def dfs(current, path, visited):
            for d in directions:
                dr, dc = d.value
                # Calculate raw coordinates
                over_r = current.r + dr
                over_c = current.c + dc
                land_r = current.r + 2 * dr
                land_c = current.c + 2 * dc

                # Bounds check before creating Coord
                if not (is_within_bounds(over_r, over_c) and is_within_bounds(land_r, land_c)):
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
                if not self.validate_move(new_board, action.coord, action.directions):
                    raise ValueError("Invalid simulated move")
                if for_maximizer:
                    new_board.apply_move(action.coord, action.directions)
                else:
                    new_board.update_opponent(action.coord, action.directions)
            elif isinstance(action, GrowAction):
                new_board.apply_grow()
            return new_board
        except Exception:
            # Skip invalid simulations by returning original board
            return board

    def is_legal_single_step(self, board, start: Coord, direction: Direction) -> bool:
        dr, dc = direction.value
        dest_r, dest_c = start.r + dr, start.c + dc
        if not is_within_bounds(dest_r, dest_c):
            return False
        dest = Coord(dest_r, dest_c)
        return dest in board.lilypads and dest not in board.my_frogs and dest not in board.enemy_frogs

    def validate_move(self, board, start: Coord, directions: list[Direction]) -> bool:
        pos = start
        step = 2 if len(directions) > 1 else 1
        for d in directions:
            pos = Coord(pos.r + d.value[0] * step, pos.c + d.value[1] * step)
            if not (is_within_bounds(pos.r, pos.c) and pos in board.lilypads):
                return False
            if pos in board.my_frogs or pos in board.enemy_frogs:
                return False
        return True

    def update(self, color: PlayerColor, action: Action, **referee: dict):
        match action:
            case MoveAction(coord, dirs):
                dirs_text = ", ".join([d.name for d in dirs])
                print(f"Testing: {color} played MOVE action:")
                print(f"  Coord: {coord}\n  Directions: {dirs_text}")
                if color == self._color:
                    self.board.apply_move(coord, dirs)
                else:
                    try:
                        self.board.update_opponent(coord, dirs)
                    except ValueError as e:
                        print(f"[ERROR] Illegal opponent move: {e}")
            case GrowAction():
                print(f"Testing: {color} played GROW action")
                if color == self._color:
                    self.board.apply_grow()
            case _:
                raise ValueError(f"Unknown action: {action}")
            