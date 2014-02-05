#!/usr/bin/env python

import curses

from gettext import gettext


class Game(object):
    def __init__(self, window):
        self.window = window
        self.state = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]]

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

    def display_state(self):
        """Redraw everything good for staring a game
        """

        self.draw_board()

        for y, row in enumerate(self.state):
            for x, col in enumerate(row):
                if col == 1:
                    self.draw_x(y, x) 
                if col == 10:
                    self.draw_o(y, x)
                
    def draw_x(self, y, x):
        y_loc = (y * 4) + 2
        x_loc = (y * 4) + 1
        self.window.addstr(y_loc, x_loc, 'X')

    def draw_o(self, y, x):
        y_loc = (y * 4) + 2
        x_loc = (y * 4) + 1
        self.window.addstr(y_loc, x_loc, 'O')


class PerfectPlayer(object):
    def __init__(self, play_first=True):
        self.play_first = play_first

    def play(self, game):
        pass
        # Win
        # Block wins
        # Fork
        # Block fork
        # Center
        # opposite corner
        # any corner
        # side


def main(stdscr):
    game = Game(stdscr)
    game.display_state()

    c = stdscr.getch()
    #user_first = None
    #while user_first is None:
    #    user_first = raw_input('Would you like to user_first first (y/n)? ').lower()[0]
    #    if user_first not in 'yn':
    #        print 'Excuse me?'
    #        user_first = None

    #user_first = user_first == 'y'

    #cpu = PerfectPlayer(play_first=not user_first)


if __name__ == '__main__':
    curses.wrapper(main)
