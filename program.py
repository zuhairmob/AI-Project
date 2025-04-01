# COMP30024 Artificial Intelligence, Semester 1 2025
# Project Part A: Single Player Freckers

from heapq import heappush, heappop
from itertools import count
from typing import Optional, List, Tuple, Dict, Set
from .core import CellState, Coord, Direction, MoveAction
from .utils import render_board

DIRECTION_STEPS = [
    Direction.Left,
    Direction.Right,
    Direction.Down,
    Direction.DownLeft,
    Direction.DownRight
]

def in_bounds(coord: Coord) -> bool:
    return 0 <= coord.r < 8 and 0 <= coord.c < 8

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
        over = start + direction
        land = over + direction
        if not in_bounds(land):
            continue
        if over in board and board[over] in (CellState.BLUE, CellState.RED):
            if land not in board or board[land] != CellState.LILY_PAD:
                continue
            if land in visited:
                continue
            new_path = path + [direction, direction]
            visited.add(land)
            sequences.append(new_path)
            sequences.extend(jump_sequences(board, land, visited, new_path))
            visited.remove(land)
    return sequences

def get_moves(board: Dict[Coord, CellState], pos: Coord) -> List[MoveAction]:
    moves = []
    for d in DIRECTION_STEPS:
        dest = pos + d
        if in_bounds(dest) and dest in board and board[dest] == CellState.LILY_PAD:
            moves.append(MoveAction(pos, d))

    for seq in jump_sequences(board, pos):
        moves.append(MoveAction(pos, seq))
    return moves

def apply_move(
    board: Dict[Coord, CellState], 
    move: MoveAction
) -> Tuple[Dict[Coord, CellState], Coord]:
    new_board = board.copy()
    del new_board[move.coord]
    pos = move.coord
    for d in move.directions:
        pos = pos + d
    new_board[pos] = CellState.RED
    return new_board, pos

def heuristic(coord: Coord) -> int:
    return 7 - coord.r

def search(
    board: dict[Coord, CellState]
) -> list[MoveAction] | None:
    print(render_board(board, ansi=True))

    start = next(c for c, s in board.items() if s == CellState.RED)
    frontier = []
    counter = count()
    heappush(frontier, (heuristic(start), 0, next(counter), start, board, []))
    visited = set()

    while frontier:
        _, cost, _, pos, state, path = heappop(frontier)

        if pos.r == 7:
            return path

        board_key = (pos, frozenset(state.items()))
        if board_key in visited:
            continue
        visited.add(board_key)

        for move in get_moves(state, pos):
            new_board, new_pos = apply_move(state, move)
            new_path = path + [move]
            heappush(frontier, (
                cost + 1 + heuristic(new_pos), 
                cost + 1, 
                next(counter), 
                new_pos, 
                new_board, 
                new_path
            ))

    return None