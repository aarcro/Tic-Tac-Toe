#!/usr/bin/env python

import curses
import random
import time

from gettext import gettext
from pprint import pprint as pp


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
        self.state = (
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0])

    def __iter__(self):
        for row in self.state:
            yield row

    def play(self, y, x):
        if self.state[y][x] == 0:
            self.state[y][x] = self.current_turn
        else:
            raise SpaceOccupied()

        # TODO Check for winner

        self.current_turn = self.turns.next()
        self.display_state()

    def display_state(self):
        """Redraw everything good for staring a game
        """

        self.draw_board()

        for y, row in enumerate(self.state):
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
        self.game.play(*random.choice(open_list))


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

    for t in xrange(10):
        cpu.play()
        game.show_message("Next?")
        stdscr.getch()


if __name__ == '__main__':
    curses.wrapper(main)
