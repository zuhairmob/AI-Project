# COMP30024 Artificial Intelligence, Semester 1 2025
# Project Part A: Single Player Freckers

from heapq import heappush, heappop  # Priority queue for A* search
from itertools import count          # Unique counter for tiebreaking
from typing import Optional, List, Tuple, Dict, Set
from .core import CellState, Coord, Direction, MoveAction
from .utils import render_board

# Valid directions for simple movement or jumps
# (Diagonal up is not included — only downward motion is goal-directed)
DIRECTION_STEPS = [
    Direction.Left,
    Direction.Right,
    Direction.Down,
    Direction.DownLeft,
    Direction.DownRight
]

# Recursively finds all valid jump chains from a starting point
# Only adds sequences where Red can legally jump over another frog
# and land on a lily pad that hasn’t been visited yet
def jump_sequences(
    board: Dict[Coord, CellState], 
    start: Coord, 
    visited: Set[Coord] = None,
    path: List[Direction] = None
) -> List[List[Direction]]:
    if visited is None:
        visited = set()
    if path is None:
        path = []

    sequences = []
    for direction in DIRECTION_STEPS:
        try:
            over = start + direction 
            land = over + direction
        except ValueError:
            continue
        
        if over in board and board[over] in (CellState.BLUE, CellState.RED):
            if land not in board or board[land] != CellState.LILY_PAD:
                continue
            if land in visited:
                continue
            new_path = path + [direction]
            visited.add(land)
            sequences.append(new_path)
            sequences.extend(jump_sequences(board, land, visited, new_path))
            visited.remove(land)
    return sequences

# Combines all simple 1-step moves and multi-jump chains for the Red frog
def get_moves(board: Dict[Coord, CellState], pos: Coord) -> List[MoveAction]:
    
    moves = []

    # Check 1-step moves to adjacent lily pads
    for d in DIRECTION_STEPS:
        try: dest = pos + d
        except ValueError:
            continue

        if dest in board and board[dest] in (CellState.BLUE, CellState.RED):
            try: dest = dest + d  # Jump over the frog
            except (ValueError, KeyError):
                continue

        if dest in board and board[dest] == CellState.LILY_PAD:
            moves.append(MoveAction(pos, d)) 

    # Add legal multi-jump sequences
    for seq in jump_sequences(board, pos):
        moves.append(MoveAction(pos, seq))
    return moves

# Simulate applying a move to the board: 
# - Removes frog from its old position
# - Moves it to the final location after the move or jump chain
def apply_move(
    board: Dict[Coord, CellState], 
    move: MoveAction
) -> Tuple[Dict[Coord, CellState], Coord]:
    new_board = board.copy()
    del new_board[move.coord]
    pos = move.coord
    for d in move.directions:
        if pos + d in new_board and new_board[pos + d] in (CellState.BLUE, CellState.RED):
            pos = pos + d + d  # Jump over the frog
        else:
            pos = pos + d
    new_board[pos] = CellState.RED
    return new_board, pos

# Simple heuristic: how many rows until we reach row 7 (goal)
def heuristic(coord: Coord) -> int:
    return 7 - coord.r

# Main A* search function:
# Finds the shortest path (in number of moves) to get Red frog to row 7
def search(
    board: dict[Coord, CellState]
) -> list[MoveAction] | None:
    
    """
    A* search algorithm to find the shortest path for the Red frog to reach row 7.
    Parameters:
        `board`: a dictionary representing the initial board state, mapping
            coordinates to "player colours". The keys are `Coord` instances,
            and the values are `CellState` instances which can be one of
            `CellState.RED`, `CellState.BLUE`, or `CellState.LILY_PAD`.
    
    Returns:
        A list of "move actions" as MoveAction instances, or `None` if no
        solution is possible.
    """

    # The render_board() function is handy for debugging. It will print out a
    # board state in a human-readable format. If your terminal supports ANSI
    # codes, set the `ansi` flag to True to print a colour-coded version!
    print(render_board(board, ansi=True))

    start = next(c for c, s in board.items() if s == CellState.RED)

    # Each item in the frontier is a tuple of:
    # (total estimated cost, path cost so far, unique counter, position, board state, path taken)
    frontier = []
    counter = count()
    heappush(frontier, (heuristic(start), 0, next(counter), start, board, []))
    visited = set()

    while frontier:
        _, cost, _, pos, state, path = heappop(frontier)

        # Goal reached if Red frog is on last row
        if pos.r == 7:
            return path

        # Avoid revisiting same board states from same position
        board_key = (pos, frozenset(state.items()))
        if board_key in visited:
            continue
        visited.add(board_key)

        # Generate and enqueue all valid next moves
        for move in get_moves(state, pos):
            new_board, new_pos = apply_move(state, move)
            new_path = path + [move]
            heappush(frontier, (
                cost + 1 + heuristic(new_pos),  # f(n) = g(n) + h(n)
                cost + 1,
                next(counter),
                new_pos,
                new_board,
                new_path
            ))

    # If we exhaust the search space without reaching row 7, no solution
    return None