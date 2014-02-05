#!/usr/bin/env python

import curses
import random


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
        for row in self.rows:
            yield row

    def play(self, y, x):
        """Record a move for the current player.
            Returns True if the game is over, and does not change player
            Returns False if the game continues and changes to next player
        """

        if self.rows[y][x] == 0:
            self.rows[y][x] = self.current_turn
        else:
            raise SpaceOccupied()

        # Check Lines
        for line in self.lines:
            # Only the current player can win
            if sum(line) == (3 * self.current_turn):
                return True

        self.current_turn = self.turns.next()
        self.display_state()
        return False

    @property
    def lines(self):
        for row in self.rows:
            yield row

        for col in self.columns:
            yield col

        yield self.left_diagonal
        yield self.right_diagonal

    @property
    def columns(self):
        result = []
        for idx in xrange(3):
            result.append([r[idx] for r in self.rows])
        return result

    @property
    def left_diagonal(self):
        return (self.rows[0][0],
            self.rows[1][1],
            self.rows[2][2])

    @property
    def right_diagonal(self):
        return (self.rows[0][2],
            self.rows[1][1],
            self.rows[2][0])

    def display_state(self):
        """Redraw everything good for staring a game
        """

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

    def draw_o(self, y, x):
        y_loc = (y * 4) + 2
        x_loc = (x * 4) + 1
        self.window.addstr(y_loc, x_loc, 'O')

    def draw_x(self, y, x):
        y_loc = (y * 4) + 2
        x_loc = (x * 4) + 1
        self.window.addstr(y_loc, x_loc, 'X')

    def key_prompt(self, prompt):
        self.show_message(prompt)
        ch = self.window.getkey()
        self.window.erase()
        self.display_state()

        return ch

    def show_message(self, msg):
        self.window.erase()
        self.display_state()
        self.window.addstr(13, 0, msg)


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
        open_list = [(y, x) for y, row in enumerate(self.game) for x, val in enumerate(row) if val == 0]
        if not open_list:
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

    user_first = user_first == 'y'

    if user_first:
        game.show_message('Ok, choose your square')
        # TODO get move
    else:
        game.show_message("Ok, I'll go first")

    stdscr.getch()

    cpu = RandomPlayer(game)

    for t in xrange(9):
        if cpu.play():
            if game.current_turn == 1:
                game.show_message("X wins")
            else:
                game.show_message("O wins")
            break

        game.show_message("Next?")
        stdscr.getch()

    stdscr.getch()


if __name__ == '__main__':
    curses.wrapper(main)
