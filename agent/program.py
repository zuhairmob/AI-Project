# agent/program.py

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
    GROW_CUTOFF = 8  # after 8 turns, never Grow again

    def __init__(self, color: PlayerColor, **referee: dict):
        self._color = color
        self.board = Board(color)
        self.board.initialize()
        # --- inject both goal rows so evaluate() won't crash ---
        # our goal (where our frogs want to reach)
        self.board.goal_row = 7 if color == PlayerColor.RED else 0
        # opponent’s goal
        self.board.enemy_goal_row = 0 if color == PlayerColor.RED else 7

        self.turn = 0

        match color:
            case PlayerColor.RED:
                print("Testing: I am playing as RED")
            case PlayerColor.BLUE:
                print("Testing: I am playing as BLUE")

    def action(self, **referee: dict) -> Action:
        self.turn += 1
        current_board = self.board

        # 1) generate & prune actions
        actions = self.generate_actions(current_board, True)
        if self.turn > Agent.GROW_CUTOFF:
            actions = [a for a in actions if not isinstance(a, GrowAction)]
        actions.sort(
            key=lambda a: (
                isinstance(a, MoveAction),
                len(a.directions) if isinstance(a, MoveAction) else 0
            ),
            reverse=True
        )
        if not actions:
            return GrowAction()

        # 2) iterative deepening with α–β
        time_limit = min(referee.get("time_remaining", 1.0), 1.0)
        start_time = time.time()
        best_action = random.choice(actions)
        depth = 1

        while True:
            alpha, beta = -math.inf, math.inf
            new_best, new_best_score = None, -math.inf

            # keep jumps first
            actions.sort(
                key=lambda a: (
                    isinstance(a, MoveAction),
                    len(a.directions) if isinstance(a, MoveAction) else 0
                ),
                reverse=True
            )

            for act in actions:
                if time.time() - start_time > time_limit - 0.05:
                    break
                nb = self.simulate_action(act, current_board, True)
                score = self.minimax(nb, depth - 1, alpha, beta, False,
                                     start_time, time_limit)
                if score > new_best_score or (score == new_best_score and random.random() < 0.5):
                    new_best_score, new_best = score, act
                alpha = max(alpha, score)

            if time.time() - start_time > time_limit - 0.05:
                break
            if new_best:
                best_action = new_best

            depth += 1
            actions = self.generate_actions(current_board, True)
            if self.turn > Agent.GROW_CUTOFF:
                actions = [a for a in actions if not isinstance(a, GrowAction)]
            actions.sort(
                key=lambda a: (
                    isinstance(a, MoveAction),
                    len(a.directions) if isinstance(a, MoveAction) else 0
                ),
                reverse=True
            )

        print(f"[DEBUG] Time used: {time.time() - start_time:.2f}s, depth reached: {depth}, selected: {best_action}")
        return best_action

    def minimax(self, board, depth, alpha, beta, maximizing,
                start_time=None, time_limit=None):
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
                nb = self.simulate_action(act, board, True)
                sc = self.minimax(nb, depth - 1, alpha, beta, False, start_time, time_limit)
                max_eval = max(max_eval, sc)
                alpha = max(alpha, sc)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for act in actions:
                nb = self.simulate_action(act, board, False)
                sc = self.minimax(nb, depth - 1, alpha, beta, True, start_time, time_limit)
                min_eval = min(min_eval, sc)
                beta = min(beta, sc)
                if beta <= alpha:
                    break
            return min_eval

    def generate_actions(self, board, for_maximizer):
        frogs = board.my_frogs if for_maximizer else board.enemy_frogs
        color = board.color if for_maximizer else (
            PlayerColor.RED if board.color == PlayerColor.BLUE else PlayerColor.BLUE
        )

        valid_dirs = {
            PlayerColor.RED: [Direction.Right, Direction.Left, Direction.Down, Direction.DownLeft, Direction.DownRight],
            PlayerColor.BLUE: [Direction.Right, Direction.Left, Direction.Up, Direction.UpLeft, Direction.UpRight],
        }

        actions = []
        for f in frogs:
            for d in valid_dirs[color]:
                if self.is_legal_single_step(board, f, d):
                    actions.append(MoveAction(f, [d]))
            all_f = board.my_frogs | board.enemy_frogs
            for path in self.find_jump_paths(board, f, valid_dirs[color], all_f):
                actions.append(MoveAction(f, path))

        actions.append(GrowAction())
        return actions

    def find_jump_paths(self, board, start, directions, all_frogs):
        results = []
        def dfs(cur, path, seen):
            for d in directions:
                dr, dc = d.value
                or_, oc = cur.r + dr, cur.c + dc
                lr, lc = cur.r + 2*dr, cur.c + 2*dc
                if not (is_within_bounds(or_, oc) and is_within_bounds(lr, lc)):
                    continue
                over, land = Coord(or_, oc), Coord(lr, lc)
                if (over in all_frogs and land in board.lilypads
                        and land not in board.my_frogs
                        and land not in board.enemy_frogs
                        and land not in seen):
                    newp = path + [d]
                    results.append(newp)
                    seen.add(land)
                    dfs(land, newp, seen)
                    seen.remove(land)
        dfs(start, [], set())
        return results

    def simulate_action(self, action, board, for_maximizer):
        try:
            nb = copy.deepcopy(board)
            if isinstance(action, MoveAction):
                if for_maximizer:
                    nb.apply_move(action.coord, action.directions)
                else:
                    nb.update_opponent(action.coord, action.directions)
            else:
                nb.apply_grow()
            return nb
        except:
            return board

    def is_legal_single_step(self, board, start: Coord, direction: Direction) -> bool:
        dr, dc = direction.value
        rr, cc = start.r + dr, start.c + dc
        if not is_within_bounds(rr, cc):
            return False
        dest = Coord(rr, cc)
        return dest in board.lilypads and dest not in board.my_frogs and dest not in board.enemy_frogs

    def update(self, color: PlayerColor, action: Action, **referee: dict):
        match action:
            case MoveAction(c, ds):
                if color == self._color:
                    self.board.apply_move(c, ds)
                else:
                    self.board.update_opponent(c, ds)
            case GrowAction():
                if color == self._color:
                    self.board.apply_grow()
            case _:
                raise ValueError(f"Unknown action: {action}")
