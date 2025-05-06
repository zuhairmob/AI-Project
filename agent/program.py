# COMP30024 Artificial Intelligence, Semester 1 2025
# Project Part B: Game Playing Agent

from referee.game import PlayerColor, Coord, Direction, \
    Action, MoveAction, GrowAction

from agent.board import Board
from agent.eval import evaluate

import random

class Agent:
    """
    This class is the "entry point" for your agent, providing an interface to
    respond to various Freckers game events.
    """

    def __init__(self, color: PlayerColor, **referee: dict):
        """
        This constructor method runs when the referee instantiates the agent.
        Any setup and/or precomputation should be done here.
        """
        self._color = color
        self.board = Board(color)
        self.board.initialize()

        match color:
            case PlayerColor.RED:
                print("Testing: I am playing as RED")
            case PlayerColor.BLUE:
                print("Testing: I am playing as BLUE")

    def action(self, **referee: dict) -> Action:
        """
        This method is called by the referee each time it is the agent's turn
        to take an action. It must always return an action object. 
        """

        my_frogs = list(self.board.my_frogs)
        random.shuffle(my_frogs)

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

        for frog in my_frogs:
            directions = valid_dirs[self._color]
            random.shuffle(directions)
            for direction in directions:
                if self.is_legal_single_step(frog, direction):
                    vec = direction.value
                    new_coord = Coord(frog.r + vec.r, frog.c + vec.c)
                    print(f"Testing: {self._color.name} is playing MOVE from {frog} to {new_coord} via [{direction}]")
                    return MoveAction(frog, [direction])

        print(f"Testing: {self._color.name} is playing a GROW action")
        return GrowAction()

    def is_legal_single_step(self, start: Coord, direction: Direction) -> bool:
        vec = direction.value
        next_r = start.r + vec.r
        next_c = start.c + vec.c

        # Check board bounds BEFORE creating Coord
        if not (0 <= next_r < 8 and 0 <= next_c < 8):
            return False

        dest = Coord(next_r, next_c)

        # Make sure destination is an empty lilypad
        if dest not in self.board.lilypads:
            return False
        if dest in self.board.my_frogs or dest in self.board.enemy_frogs:
            return False

        return True

    def update(self, color: PlayerColor, action: Action, **referee: dict):
        """
        This method is called by the referee after a player has taken their
        turn. You should use it to update the agent's internal game state. 
        """

        # There are two possible action types: MOVE and GROW. Below we check
        # which type of action was played and print out the details of the
        # action for demonstration purposes. You should replace this with your
        # own logic to update your agent's internal game state representation.
        match action:
            case MoveAction(coord, dirs):
                dirs_text = ", ".join([str(dir) for dir in dirs])
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
