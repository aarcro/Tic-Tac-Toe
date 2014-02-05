#!/usr/bin/env python

import curses
import random
from collections import Iterator


LEFT_DIAGONAL = ((0, 0), (1, 1), (2, 2))
RIGHT_DIAGONAL = ((0, 2), (1, 1), (2, 0))

class SpaceOccupied(Exception):
    pass


class TurnAlternator(Iterator):
    """Generate values from a list, repeating forever.
    With a one item lookahead
    """
    def __init__(self, values):
        self.cache = values[0]
        self.gen = self._generate(values)
        # eat the first value
        next(self.gen)

    def _generate(self, values):
        while 1:
            for v in values:
                yield v

    def next(self):
        v = self.cache
        self.cache = next(self.gen)
        return v

    def peek(self):
        return self.cache


class Game(object):
    def __init__(self, window, debug=False):
        self.window = window
        self.DEBUG = debug
        self.turns = TurnAlternator([1, 10])
        self.current_turn = self.turns.next()
        self.won = False
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

        # Check Lines for win
        for values, spaces in self.lines:
            # Only the current player can win
            if sum(values) == (3 * self.current_turn):
                self.won = True
                return True

        # Check for Draw
        for row in self.rows:
            if 0 in row:
                # Available move exists
                self.current_turn = self.turns.next()
                return False

        #Draw
        return True

    @property
    def next_turn(self):
        return self.turns.peek()

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

    def debug(self, msg):
        if self.DEBUG:
            self.key_prompt(msg)

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

    def play(self):
        raise NotImplemented


class RandomPlayer(Player):
    def play(self):
        """Find random open location, and play there"""
        # faster, less typing
        game = self.game

        # Don't need output, just a press to continue
        game.display_state()

        open_list = [(y, x) for y, row in enumerate(game.rows) for x, val in enumerate(row) if val == 0]
        if not open_list:
            self.display_state()
            game.show_message('The board is full')
            return
        move = random.choice(open_list)
        game.debug('Random Playing to: {}'.format(move))
        return game.play(*move)


class SmartPlayer(RandomPlayer):
    def _play(self):
        """Returns game over as True or False if a move was made or None
        if no move could be found
        """

        # faster, less typing
        game = self.game

        # Win
        for values, spaces in game:
            if sum(values) == (2 * game.current_turn):
                # Find the zero and play there
                move = spaces[values.index(0)]
                game.debug('Win Playing to: {}'.format(move))
                return game.play(*move)

        # Block wins
        for values, spaces in game:
            if sum(values) == (2 * game.next_turn):
                # Find the zero and play there
                move = spaces[values.index(0)]
                game.debug('Block Playing to: {}'.format(move))
                return game.play(*move)
        # No Move made
        return None

    def play(self):
        # faster, less typing
        game = self.game

        result = self._play()

        if result is None:
            game.debug('Fall back to random')
            # Random
            result = super(SmartPlayer, self).play()

        return result


class PerfectPlayer(SmartPlayer):
    def _play(self):
        pass
        # Fork
        # Block fork
        # Center
        # opposite corner
        # any corner
        # side

    def play(self):
        result = super(PerfectPlayer, self)._play()

        if result is not None:
            #Move made, return it
            return result

        result = self._play()


def main(stdscr):
    PLAYERS = [RandomPlayer, SmartPlayer, PerfectPlayer]
    game = Game(stdscr, debug=True)
    game.display_state()

    level = None
    while level is None:
        level = game.key_prompt('What difficulty would you like (1: Easy, 2: Smart, 3: Imposible) ')
        if level not in '123':
            level = None

    level = int(level) - 1

    # Clear message
    game.display_state()

    user_first = None
    while user_first is None:
        user_first = game.key_prompt('Would you like to play first (y/n)? ')
        if user_first not in 'yn':
            user_first = None

    # Clear message
    game.display_state()

    user_first = user_first == 'y'

    if user_first:
        # Can't win on the first move, so don't check
        game.get_interactive_move()
    else:
        game.show_message("Ok, I'll go first")
        stdscr.getch()


    cpu = PLAYERS[level](game)

    for t in xrange(9):
        if cpu.play():
            if game.won:
                game.show_message("I win !!!!")
            else:
                game.show_message("Draw")
            break

        if game.get_interactive_move():
            if game.won:
                game.show_message("You win !!!!")
            else:
                game.show_message("Draw")
            break

    stdscr.getch()


if __name__ == '__main__':
    curses.wrapper(main)
