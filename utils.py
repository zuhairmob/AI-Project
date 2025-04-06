# COMP30024 Artificial Intelligence, Semester 1 2025
# Project Part A: Single Player Freckers

from .core import Coord, CellState, BOARD_N


def apply_ansi(
    text: str, 
    bold: bool = False, 
    color: str | None = None
):
    """
    Wraps some text with ANSI control codes to apply terminal-based formatting.
    Note: Not all terminals will be compatible!
    """
    bold_code = "\033[1m" if bold else ""
    color_code = ""
    if color == "r":
        color_code = "\033[31m"
    if color == "b":
        color_code = "\033[34m"
    if color == "g":
        color_code = "\033[32m"
    return f"{bold_code}{color_code}{text}\033[0m"


def render_board(
    board: dict[Coord, CellState], 
    ansi: bool = False
) -> str:
    """
    Visualise the Tetress board via a multiline ASCII string, including
    optional ANSI styling for terminals that support this.

    If a target coordinate is provided, the token at that location will be
    capitalised/highlighted.
    """
    output = ""
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            cell_state = board.get(Coord(r, c), None)
            if cell_state:
                text = '.'
                color = None
                if cell_state == CellState.RED:
                    text = "R"
                    color = "r"
                elif cell_state == CellState.BLUE:
                    text = "B"
                    color = "b"
                elif cell_state == CellState.LILY_PAD:
                    text = "*"
                    color = "g"

                if ansi:
                    output += apply_ansi(text, color=color)
                else:
                    output += text
            else:
                output += "."
            output += " "
        output += "\n"
    return output
