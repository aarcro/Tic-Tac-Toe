#!/usr/bin/env python

import curses
import random

LEFT_DIAGONAL = ((0, 0), (1, 1), (2, 2))
RIGHT_DIAGONAL = ((0, 2), (1, 1), (2, 0))

class SpaceOccupied(Exception):
    pass

def turn_alternator():
    while 1:
        yield 1
        yield 10

class Game(object):
    def __init__(self, window):
        self.window = window
        self.turns = turn_alternator()
        self.current_turn = self.turns.next()
        self.rows = (
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0])

    def __iter__(self):
        for values, spaces in self.lines:
            yield values, spaces

    def play(self, y, x):
        """Record a move for the current player.
            Returns True if the game is over, and does not change player
            Returns False if the game continues and changes to next player
        """

        if self.rows[y][x] == 0:
            self.rows[y][x] = self.current_turn
        else:
            raise SpaceOccupied()

        self.display_state()

        # Check Lines
        for values, spaces in self.lines:
            # Only the current player can win
            if sum(values) == (3 * self.current_turn):
                return True

        self.current_turn = self.turns.next()
        return False

    @property
    def lines(self):
        """Generate tuples of (values, spaces)
        values is a three item list, each item is:
             0 - Unoccupied
             1 - X player
            10 - O player

        spaces is a three item list, of (y,x) cordinates specifying the location
            of each value
        """

        for y, row in enumerate(self.rows):
            yield row, [(y, x) for x in xrange(3)]

        for x, col in enumerate(self.columns):
            yield col, [(y, x) for y in xrange(3)]

        yield self.left_diagonal, LEFT_DIAGONAL
        yield self.right_diagonal, RIGHT_DIAGONAL

    @property
    def columns(self):
        result = []
        for idx in xrange(3):
            result.append([r[idx] for r in self.rows])
        return result

    @property
    def left_diagonal(self):
        return [self.rows[y][x] for y,x in LEFT_DIAGONAL]

    @property
    def right_diagonal(self):
        return [self.rows[y][x] for y,x in RIGHT_DIAGONAL]

    def display_state(self):
        """Redraw everything good for staring a game
        """

        self.window.erase()
        self.draw_board()

        for y, row in enumerate(self.rows):
            self.window.addstr(15 + y, 0, str(row))
            for x, val in enumerate(row):
                if val == 1:
                    self.draw_x(y, x)
                if val == 10:
                    self.draw_o(y, x)

        self.window.refresh()

    def draw_board(self):
        for y in xrange(1, 12):
            if y and not y % 4:
                # Every 4th row, but not the first
                ch = curses.ACS_PLUS

                for x in xrange(11):
                    self.window.addch(y, x, curses.ACS_HLINE)
            else:
                ch = curses.ACS_VLINE

            for x in (3, 7):
                self.window.addch(y, x, ch)

    def draw_chr(self, y, x, char):
        y_loc = (y * 4) + 2
        x_loc = (x * 4) + 1
        self.window.addstr(y_loc, x_loc, char)

    def draw_o(self, y, x):
        self.draw_chr(y, x, 'O')

    def draw_x(self, y, x):
        self.draw_chr(y, x, 'X')

    def key_prompt(self, prompt):
        self.show_message(prompt)
        ch = self.window.getkey()
        self.show_message(' ' * len(prompt))
        return ch

    def show_message(self, msg):
        self.window.addstr(13, 0, msg)

    def get_interactive_move(self):
        #Show numbers
        self.window.erase()
        self.display_state()
        self.window.attron(curses.A_BOLD)
        valid = {}
        nums = (str(n) for n in xrange(1, 10))
        for y in xrange(3):
            for x in xrange(3):
                num = nums.next()
                if self.rows[y][x] == 0:
                    # No value, display as choice
                    self.draw_chr(y, x, num)
                    valid[num] = (y, x)
        self.window.attroff(curses.A_BOLD)
        self.window.refresh()

        choice = None
        while choice is None:
            choice = self.key_prompt('Your move? ')
            if choice not in valid:
                choice = None
        return self.play(*valid[choice])


class Player(object):
    def __init__(self, game):
        self.game = game


class PerfectPlayer(Player):
    def play(self):
        pass
        # Win
        # Block wins
        # Fork
        # Block fork
        # Center
        # opposite corner
        # any corner
        # side


class RandomPlayer(Player):
    def play(self):
        """Find random open location, and play there"""
        # Don't need output, just a press to continue
        self.game.display_state()
        self.game.key_prompt('Ready?')

        open_list = [(y, x) for y, row in enumerate(self.game.rows) for x, val in enumerate(row) if val == 0]
        if not open_list:
            self.display_state()
            self.game.show_message('The board is full')
            return
        return self.game.play(*random.choice(open_list))


def main(stdscr):
    game = Game(stdscr)
    game.display_state()

    user_first = None
    while user_first is None:
        user_first = game.key_prompt('Would you like to play first (y/n)? ')
        if user_first not in 'yn':
            user_first = None

    game.display_state()

    user_first = user_first == 'y'

    if user_first:
        # Can't win on the first move, so don't check
        game.get_interactive_move()
    else:
        game.show_message("Ok, I'll go first")
        stdscr.getch()

    cpu = RandomPlayer(game)

    for t in xrange(9):
        if cpu.play():
            game.show_message("I win !!!!")
            break

        if game.get_interactive_move():
            game.show_message("You win !!!!")
            break

    stdscr.getch()


if __name__ == '__main__':
    curses.wrapper(main)
