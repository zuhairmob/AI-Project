# agent/program.py

# COMP30024 Artificial Intelligence, Semester 1 2025
# Project Part B: Game Playing Agent

from referee.game import PlayerColor, Coord, Direction, Action, MoveAction, GrowAction
from .board import Board
from .eval import evaluate
from .utils.board_utils import is_within_bounds

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
        
        # Dynamically decide whether to use GrowAction
        if not actions or (self.turn <= Agent.GROW_CUTOFF and isinstance(actions[0], GrowAction)):
            return GrowAction()

        # 2) iterative deepening with α–β
        time_limit = min(referee.get("time_remaining", 1.0), 1.0)
        start_time = time.time()
        best_action = actions[0]
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

            if len(actions) < 5:  # Few moves left, search deeper
                depth += 2
            else:
                depth += 1

            actions = self.generate_actions(current_board, True)
            if self.turn > Agent.GROW_CUTOFF:
                actions = [a for a in actions if not isinstance(a, GrowAction)]

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

        actions.sort(key=lambda a: evaluate(self.simulate_action(a, board, maximizing)), reverse=True)

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
        if (board.color == PlayerColor.RED and for_maximizer) or (board.color == PlayerColor.BLUE and not for_maximizer):
            frogs = sorted(frogs, key=lambda f: f.r)  # Prioritize frogs further up
        else:
            frogs = sorted(frogs, key=lambda f: f.r, reverse=True) # Prioritize frogs further down

        color = board.color if for_maximizer else (
            PlayerColor.RED if board.color == PlayerColor.BLUE else PlayerColor.BLUE
        )

        valid_dirs = {
            PlayerColor.RED: [Direction.Down, Direction.DownLeft, Direction.DownRight, Direction.Right, Direction.Left],
            PlayerColor.BLUE: [Direction.Up, Direction.UpLeft, Direction.UpRight, Direction.Right, Direction.Left],
        }

        actions = []
        for f in frogs:

            # Skip frogs already in the goal row
            if f.r == board.goal_row:
                continue

            # Check if the frog is on the second-to-last row
            if f.r == (board.goal_row - 1 if board.goal_row > 0 else board.goal_row + 1):
                # Evaluate grow-and-move strategy
                grow_and_move_option, grow_and_move_cost = evaluate_grow_and_move(self, f, board)
                if grow_and_move_option:
                    adjacent, blank = grow_and_move_option
                    
                    # Calculate the direction to move next to the blank space
                    direction_tuple = (adjacent.r - f.r, adjacent.c - f.c)
                    if direction_tuple in [d.value for d in Direction]:
                        direction = Direction(direction_tuple)
                        actions.append(MoveAction(f, [direction]))  # Move next to blank
                        actions.append(GrowAction())  # Grow
                        direction_to_blank = (blank.r - adjacent.r, blank.c - adjacent.c)
                        if direction_to_blank in [d.value for d in Direction]:
                            actions.append(MoveAction(adjacent, [Direction(direction_to_blank)]))  # Move into blank

            # Generate regular move actions
            for d in valid_dirs[color]:
                if self.is_legal_single_step(board, f, d):
                    actions.append(MoveAction(f, [d]))
            all_f = board.my_frogs | board.enemy_frogs
            for path in self.find_jump_paths(board, f, valid_dirs[color], all_f):
                actions.append(MoveAction(f, path))

        actions.sort(
            key=lambda a: (
                isinstance(a, MoveAction),
                evaluate_move_progress(self, a, board),  # Prioritize moves with better progress
                evaluate_move_efficiency(self, a)  # Penalize inefficient moves
            ),
            reverse=True
        )

        # Evaluate the GrowAction
        grow_benefit = evaluate_grow_action(self, board)

        # If GrowAction is more beneficial than the best MoveAction, prioritize it
        if grow_benefit > 0 and (not actions or grow_benefit > evaluate_move_progress(self, actions[0], board)):
            actions.insert(0, GrowAction())

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

def evaluate_move_progress(self, action, board):
    if isinstance(action, MoveAction):

        if (action.coord.r == board.goal_row):
            return -50

        # Simulate the move
        simulated_board = self.simulate_action(action, board, True)

        goal_row = simulated_board.goal_row

        current_progress = sum(abs(goal_row - frog.r) for frog in board.my_frogs)
        new_progress = sum(abs(goal_row - frog.r) for frog in simulated_board.my_frogs)
        total_progress = abs(current_progress - new_progress)

        current_farthest = max(abs(goal_row - frog.r) for frog in board.my_frogs)
        new_farthest = max(abs(goal_row - frog.r) for frog in simulated_board.my_frogs)
        if current_farthest > new_farthest:
            total_progress += 1
        
        return total_progress
    return 0  # GrowAction progress

def evaluate_move_efficiency(self, action):
    if isinstance(action, MoveAction):
         # Additional penalty for stagnation (no progress toward the goal row)
        start_row = action.coord.r
        end_row = action.coord.r + sum(d.value.r for d in action.directions)
        if start_row == end_row:  # No progress
            return -30  # Penalize stagnation
        
        # Penalize moves that are not diagonal when diagonal is possible
        if len(action.directions) == 1:
            direction = action.directions[0]
            if direction in [Direction.DownLeft, Direction.DownRight, Direction.UpLeft, Direction.UpRight]:
                return 10  # No penalty for diagonal moves
            elif direction in [Direction.Left, Direction.Right]:
                return -50  # Strong penalty for horizontal moves
            else:
                return 10 # No penalty for vertical moves
    return 0

def evaluate_grow_action(self, board):
    # Simulate the grow action
    simulated_board = copy.deepcopy(board)
    simulated_board.apply_grow()

    # Determine the valid directions based on the player's goal row
    if board.goal_row == 7:  # RED player
        valid_directions = [Direction.Down, Direction.DownLeft, Direction.DownRight]
    else:  # BLUE player
        valid_directions = [Direction.Up, Direction.UpLeft, Direction.UpRight]

    # Calculate the potential benefits of the grow action
    benefit = 0
    for frog in simulated_board.my_frogs:
        if (frog.r == board.goal_row):
            continue
        for direction in valid_directions:
            dr, dc = direction.value
            rr, cc = frog.r + dr, frog.c + dc
            if is_within_bounds(rr, cc):
                dest = Coord(rr, cc)
                if dest in simulated_board.lilypads and dest not in board.lilypads:
                    benefit += 1  # Reward for enabling new forward moves
    return benefit

def frogs_on_second_last_row(self, board):
    second_last_row = board.goal_row - 1 if board.goal_row > 0 else board.goal_row + 1
    return [frog for frog in board.my_frogs if frog.r == second_last_row]

def closest_lilypad_in_goal_row(self, frog, board):
    goal_row = board.goal_row
    lilypads_in_goal_row = [l for l in board.lilypads if l.r == goal_row]
    if not lilypads_in_goal_row:
        return None
    # Find the closest lily pad by Manhattan distance
    return min(lilypads_in_goal_row, key=lambda l: abs(l.r - frog.r) + abs(l.c - frog.c))

def evaluate_grow_and_move(self, frog, board):
    goal_row = board.goal_row
    second_last_row = goal_row - 1 if goal_row > 0 else goal_row + 1

    # Determine the valid directions based on the player's goal row
    if goal_row == 7:  # RED player
        valid_directions = [Direction.DownLeft, Direction.DownRight, Direction.Left, Direction.Right]
    else:  # BLUE player
        valid_directions = [Direction.UpLeft, Direction.UpRight, Direction.Left, Direction.Right]

    # Find blank spaces in the goal row
    blank_spaces = [Coord(goal_row, c) for c in range(8) if (Coord(goal_row, c) not in board.lilypads and Coord(goal_row, c) not in board.my_frogs and Coord(goal_row, c) not in board.enemy_frogs)]

    best_option = None
    best_cost = float('inf')

    for blank in blank_spaces:
        # Check if the frog can move next to the blank space
        for direction in valid_directions:
            dr, dc = direction.value

            adjacent_r = blank.r - dr
            adjacent_c = blank.c - dc

            # Ensure the adjacent coordinate is within bounds
            if not is_within_bounds(adjacent_r, adjacent_c):
                continue

            adjacent = Coord(adjacent_r, adjacent_c)
            if adjacent in board.lilypads and adjacent not in board.my_frogs and adjacent not in board.enemy_frogs:
                # Simulate moving next to the blank space, growing, and moving into the blank space
                move_cost = abs(frog.r - adjacent.r) + abs(frog.c - adjacent.c)  # Cost to move next to the blank space
                grow_cost = 1  # Growing takes 1 turn
                move_into_blank_cost = 1  # Moving into the blank space takes 1 turn
                total_cost = move_cost + grow_cost + move_into_blank_cost

                if total_cost < best_cost:
                    best_cost = total_cost
                    best_option = (adjacent, blank)  # Store the adjacent position and the blank space

    return best_option, best_cost
