#!/usr/bin/env python

from collections import Iterator, defaultdict
import argparse
import curses
import random


LEFT_DIAGONAL = ((0, 0), (1, 1), (2, 2))
RIGHT_DIAGONAL = ((0, 2), (1, 1), (2, 0))
CORNERS = ((0,0), (0, 2), (2, 0), (2, 2))
SIDES = ((0,1), (1, 0), (1, 2), (2, 1))
CENTER = (1,1)

class SpaceOccupied(Exception):
    pass


def flip_loc(val):
    """Switches 0 to 2 and vice versa"""
    return (val + 2) % 4

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
    def corners(self):
        """Generate corner (value, location) tuples"""

        for y, x in CORNERS:
            yield self.rows[y][x], (y,x)

    @property
    def sides(self):
        """Generate side (value, location) tuples"""

        for y, x in SIDES:
            yield self.rows[y][x], (y,x)

    @property
    def left_diagonal(self):
        return [self.rows[y][x] for y,x in LEFT_DIAGONAL]

    @property
    def right_diagonal(self):
        return [self.rows[y][x] for y,x in RIGHT_DIAGONAL]

    def display_state(self):
        """Clear and Redraw everything"""

        self.window.erase()
        self.draw_board()

        for y, row in enumerate(self.rows):
            if self.DEBUG:
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
                    self.window.addch(y, x, curses.ACS_HLINE, curses.color_pair(6))
            else:
                ch = curses.ACS_VLINE

            for x in (3, 7):
                self.window.addch(y, x, ch, curses.color_pair(6))

    def draw_chr(self, y, x, char, *args):
        y_loc = (y * 4) + 2
        x_loc = (x * 4) + 1
        self.window.addstr(y_loc, x_loc, char, *args)

    def draw_o(self, y, x):
        self.draw_chr(y, x, 'O', curses.color_pair(3))

    def draw_x(self, y, x):
        self.draw_chr(y, x, 'X', curses.color_pair(2))

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
    """Logic based on http://en.wikipedia.org/wiki/Tic_tac_toe#Strategy
    and http://www.wikihow.com/Win-at-Tic-Tac-Toe"""

    def __init__(self, *args, **kwargs):
        super(PerfectPlayer, self).__init__(*args, **kwargs)
        self.first_turn = True

    def _first_play(self):
        game = self.game
        self.first_turn = False

        if game.current_turn == 1:
            # I'm X - play a corner
            game.debug('First play corner')
            return game.play(*random.choice(CORNERS))
        else:
            # I'm O
            # Corner if Center
            if game.rows[1][1]:
                game.debug('Corner to Counter Center')
                return game.play(*random.choice(CORNERS))
            # Center if Corner
            if 1 in [val for val, loc in game.corners]:
                game.debug('Center to Counter Corner')
                return game.play(*CENTER)

            # Must be side - find it
            for val, loc in game.sides:
                if val:
                    break
            y, x = loc
            locations = [(1,1)]

            if y == 1:
                #Center row
                locations.append((0, x))
                locations.append((2, x))
                locations.append((1, flip_loc(x)))
            else:
                #Center Column
                locations.append((y, 0))
                locations.append((y, 2))
                locations.append((flip_loc(y), 1))

            game.debug('Center, Touching corner, or Opposite side')
            return game.play(*random.choice(locations))

    def _play(self):
        if self.first_turn:
            return self._first_play()

        game = self.game

        # Dictionary, of (y, x) to occurances
        x_spaces = defaultdict(int)
        o_spaces = defaultdict(int)

        # If I have Center, play a side
        if game.rows[1][1] == game.current_turn:
            moves = [loc for val, loc in game.sides if val == 0]
            if moves:
                move = random.choice(moves)
                game.debug('My center, play side {}'.format(move))
                return game.play(*move)

        # Find lines with two open spaces
        for values, spaces in game:
            s = sum(values)
            if s not in (1, 10):
                continue
            # Make sure spaces is mutable (Diagonals aren't)
            spaces = list(spaces)
            # Remove occupied
            del spaces[values.index(s)]
            if s == 1:
                use = x_spaces
            if s == 10:
                use = o_spaces

            for space in spaces:
                use[space] += 1

        # Try to fork, then to block
        if game.current_turn == 1:
            trial = x_spaces, o_spaces
        else:
            trial = o_spaces, x_spaces

        for spaces in trial:
            # good val is usually 2
            # 3 is possible if the center is open after 5 turns
            moves = [loc for loc, val in spaces.items() if val > 1]
            if moves:
                move = random.choice(moves)
                game.debug('Fork or block Fork at {}'.format(move))
                return game.play(*move)


        # Center
        if game.rows[1][1] == 0:
            game.debug('Take Center')
            return game.play(1, 1)

        # opposite corner
        for val, loc in game.corners:
            y, x = loc
            if val == game.next_turn:
                try:
                    move = (flip_loc(y), flip_loc(x))
                    game.debug('try opposite corner at {}'.format(move))
                    return game.play(*move)
                except SpaceOccupied:
                    game.debug('Missed it')

        # any corner
        moves = [loc for val, loc in game.corners if val == 0]
        if moves:
            move = random.choice(moves)
            game.debug('Any corner at {}'.format(move))
            return game.play(*move)

        # side -- If we got this far, there must be one open
        moves = [loc for val, loc in game.sides if val == 0]
        move = random.choice(moves)
        game.debug('Any side at {}'.format(move))
        return game.play(*move)


    def play(self):
        # Let smart handle Win/Block
        result = super(PerfectPlayer, self)._play()

        if result is not None:
            #Move made, return it
            return result

        return self._play()


def main(stdscr, **kwargs):
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)

    PLAYERS = [RandomPlayer, SmartPlayer, PerfectPlayer]
    solo = kwargs['solo']

    while 1:
        game = Game(stdscr, debug=kwargs['debug'])
        game.display_state()

        level = None
        while level is None:
            level = game.key_prompt('What difficulty would you like (1: Easy, 2: Smart, 3: Imposible) ')
            if level not in '123':
                level = None

        level = int(level) - 1

        # Clear message
        game.display_state()

        if not solo:
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
        if solo:
            cpu2 = PLAYERS[level](game)

        def cpu_end_game(game):
            if game.won:
                if solo:
                    if game.current_turn == 1:
                        game.key_prompt("X wins !!!!")
                    else:
                        game.key_prompt("O wins !!!!")
                else:
                    game.key_prompt("I win !!!!")
            else:
                game.key_prompt("Draw")

        for t in xrange(9):
            if cpu.play():
                cpu_end_game(game)
                break


            if solo and cpu2.play():
                cpu_end_game(game)
                break

            if not solo and game.get_interactive_move():
                if game.won:
                    game.key_prompt("You win !!!!")
                else:
                    game.key_prompt("Draw")
                break

        again = None
        while again is None:
            again = game.key_prompt('Would you like to play again (y/n)? ')
            if again not in 'yn':
                again = None

        if again == 'n':
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Interactivly play tictactoe.')
    parser.add_argument(
        '-d', '--debug',
        dest='debug',
        action='store_true',
        default=False,
        help='Display game internal state and CPU descisions'
    )

    parser.add_argument(
        '-s', '--solo',
        dest='solo',
        action='store_true',
        default=False,
        help='Run with two CPU players'
    )

    args = parser.parse_args()
    curses.wrapper(main, **vars(args))
