
# adapted from: https://github.com/nyergler/teaching-python-with-pygame/blob/master/ttt-tutorial/tictactoe.py

import pygame
from pygame.locals import *
import itertools
import argparse

class Wait(object):
    pass


class MarkSquare(object):
    __slots__ = ['row', 'col']

    def __init__(self, row, col):
        self.row = row
        self.col = col


class HumanAgent(object):
    def __init__(self, player):
        super(HumanAgent, self).__init__()
        self.player = player

    def handle_event(self, event, board):
        if event.type is MOUSEBUTTONDOWN:
            (mouseX, mouseY) = pygame.mouse.get_pos()
            row = min(mouseY // 100, 2)
            col = min(mouseX // 100, 2)
            return MarkSquare(row, col)
        return Wait()

    def handle_error(self, move, board):
        return Wait()

    def notify_outcome(self, won):
        if won:
            print(f'player {self.player} is happy')
        else:
            print(f'player {self.player} is sad')


class RationalAgent(object):

    """
    Here is some pseudo code for alpha beta pruning search!

    function alphabeta(node, depth, α, β, maximizingPlayer) is
    if depth = 0 or node is a terminal node then
        return the heuristic value of node
    if maximizingPlayer then
        value := −∞
        for each child of node do
            value := max(value, alphabeta(child, depth − 1, α, β, FALSE))
            α := max(α, value)
            if α ≥ β then
                break (* β cut-off *)
        return value
    else
        value := +∞
        for each child of node do
            value := min(value, alphabeta(child, depth − 1, α, β, TRUE))
            β := min(β, value)
            if α ≥ β then
                break (* α cut-off *)
        return value
    """

    def __init__(self, player):
        super(RationalAgent, self).__init__()
        self.player = player

    """
    I used this debug method to help my development.
    """
    def print_best_move(self, board, player, move, utility):
        print()
        print(board)
        print("Best move for", player, "is", move, "with utility", utility)

    """
    Gets the successor states given a board; that is, returns all empty squares.
    """
    def get_successors(self, board):
        return [(x, y) for (x, y) in itertools.product(range(len(board)), range(len(board))) if board[x][y] is None]

    """
    Returns the winner of the board, or None if there is no winner.
    """
    def get_winner(self, board):
        for row in range(0, 3):
            if (board[row][0] == board[row][1] == board[row][2]) and (board[row][0] is not None):
                return board[row][0]
        for col in range(0, 3):
            if (board[0][col] == board[1][col] == board[2][col]) and (board[0][col] is not None):
                return board[0][col]
        if (board[0][0] == board[1][1] == board[2][2]) and (board[0][0] is not None):
            return board[0][0]
        if (board[0][2] == board[1][1] == board[2][0]) and (board[0][2] is not None):
            return board[0][2]
        return None

    """
    Utility method that returns the other player given a player.
    """
    def other_player(self, player):
        return 'O' if player is 'X' else 'O'
   
    """
    Minimax algorithm implementation with alpha-beta pruning.
    """
    def minimax(self, board, alpha, beta, is_max_agent):
        # handle terminal states
        winner = self.get_winner(board)
        if winner:
            return float('inf') if winner is self.player else float('-inf')
        successors = self.get_successors(board)
        if not len(successors): # if draw
            return 0
        # handle non-terminal states
        if is_max_agent:
            best_value = float('-inf')
            for move_x, move_y in successors: # iterate through descendants
                board[move_x][move_y] = self.player
                move_value = self.minimax(board, alpha, beta, False) # recursive structure - traverses game tree via DFS
                if move_value > best_value: # better move? update alpha and best move
                    best_value = move_value
                    alpha = move_value
                board[move_x][move_y] = None
                if alpha >= beta: # means this move can be prevented
                    break
            return best_value
        else:
            best_value = float('inf')
            for move_x, move_y in successors:
                board[move_x][move_y] = self.other_player(self.player)
                move_value = self.minimax(board, alpha, beta, True)
                if move_value < best_value:
                    best_value = move_value
                    beta = move_value
                board[move_x][move_y] = None
                if beta <= alpha: # means we won't ever get in this bad of a position
                    break
            return best_value
            

    """
    The next function is the only function you need to care about! 
    Don't worry about the other ones. 

    Your job is just to decide in which
    row and column you want to play, based on the current state of the 
    board (represented as a 3x3 array and stored in variable "board").

    Sanity check: row and col should both get set: can be 0, 1, or 2.

    """
    def handle_event(self, event, board):
        if event.type is USEREVENT:
            best_move = None
            best_value = float('-inf')   
            for move_x, move_y in self.get_successors(board):
                board[move_x][move_y] = self.player # make move
                move_value = self.minimax(board, float('-inf'), float('inf'), False) # we tried a move, now it's our opponent's turn
                if move_value > best_value: # update if this move was better
                    best_value = move_value
                    best_move = (move_x, move_y)
                board[move_x][move_y] = None # undo move
            row, col = best_move
            return MarkSquare(row, col)
        return Wait()

    def handle_error(self, move, board):
        return Wait()

    def notify_outcome(self, won):
        pass


class Game(object):
    def __init__(self, player_x, player_o):
        self.players = {'X': player_x('X'),
                        'O': player_o('O')}
        self.grid = [[None, None, None],
                     [None, None, None],
                     [None, None, None]]

    def clone_grid(self):
        return [[x for x in row] for row in self.grid]

    def poll_agent(self, agent, event):
        action = agent.handle_event(event, self.clone_grid())

        while True:
            if isinstance(action, Wait):
                return action
            elif isinstance(action, MarkSquare):
                row, col = action.row, action.col
                if self.grid[row][col] is None:
                    return action
                action = agent.handle_error(action, self.clone_grid())
            else:
                raise ValueError(f'unknown action type {type(action)}')

    def run(self):
        pygame.init()
        ttt = pygame.display.set_mode((300, 325))
        pygame.display.set_caption('Tic-Tac-Toe')
        pygame.time.set_timer(USEREVENT, 100)

        board = pygame.Surface(ttt.get_size())
        board = board.convert()

        self.init_board(board)

        player = 'X'
        winner = None
        while True:
            for event in pygame.event.get():
                if event.type is QUIT:
                    return

                if winner is None:
                    action = self.poll_agent(self.players[player], event)

                    if isinstance(action, MarkSquare):
                        row, col = action.row, action.col
                        self.make_move(board, row, col, player)
                        player = self.other_player(player)

                    winner, position = self.get_winner()

                    if winner:
                        self.draw_win_line(board, position)
                        self.players[winner].notify_outcome(True)
                        self.players[self.other_player(winner)].notify_outcome(False)
                        message = f'{winner} won the game!'
                    else:
                        message = f'it is {player}\'s turn'

                    self.draw_status(board, message)
                    ttt.blit(board, (0, 0))
                    pygame.display.flip()

                elif event.type is MOUSEBUTTONDOWN:
                    # reset
                    self.init_board(board)
                    player = 'X'
                    winner = None
                    continue

    def other_player(self, player):
        return 'O' if player == 'X' else 'X'

    def init_board(self, board):
        self.grid = [[None, None, None],
                     [None, None, None],
                     [None, None, None]]

        board.fill((250, 250, 250))

        pygame.draw.line(board, (0, 0, 0), (100, 0), (100, 300), 2)
        pygame.draw.line(board, (0, 0, 0), (200, 0), (200, 300), 2)

        pygame.draw.line(board, (0, 0, 0), (0, 100), (300, 100), 2)
        pygame.draw.line(board, (0, 0, 0), (0, 200), (300, 200), 2)

    def draw_status(self, board, message):
        font = pygame.font.Font(None, 24)
        text = font.render(message, 1, (10, 10, 10))

        board.fill((250, 250, 250), (0, 300, 300, 25))
        board.blit(text, (10, 300))

    def make_move(self, board, row, col, player):
        centerX = (col * 100) + 50
        centerY = (row * 100) + 50

        if player == 'O':
            pygame.draw.circle(board, (0, 0, 0), (centerX, centerY), 44, 2)
        else:
            pygame.draw.line(board, (0, 0, 0), (centerX - 22, centerY - 22), (centerX + 22, centerY + 22), 2)
            pygame.draw.line(board, (0, 0, 0), (centerX + 22, centerY - 22), (centerX - 22, centerY + 22), 2)

        self.grid[row][col] = player

    def get_winner(self):
        for row in range(0, 3):
            if (self.grid[row][0] == self.grid[row][1] == self.grid[row][2]) and (self.grid[row][0] is not None):
                return self.grid[row][0], ('row', row)

        for col in range(0, 3):
            if (self.grid[0][col] == self.grid[1][col] == self.grid[2][col]) and (self.grid[0][col] is not None):
                return self.grid[0][col], ('col', col)

        if (self.grid[0][0] == self.grid[1][1] == self.grid[2][2]) and (self.grid[0][0] is not None):
            return self.grid[0][0], ('diag', 0)

        if (self.grid[0][2] == self.grid[1][1] == self.grid[2][0]) and (self.grid[0][2] is not None):
            return self.grid[0][2], ('diag', 1)

        return None, None

    def draw_win_line(self, board, line):
        lines = {
            'row': lambda row: ((0, (row + 1) * 100 - 50), (300, (row + 1) * 100 - 50)),
            'col': lambda col: (((col + 1) * 100 - 50, 0), ((col + 1) * 100 - 50, 300)),
            'diag': lambda x: ((50 + 200 * x, 50), (250 - 200 * x, 250))}
        key, idx = line
        a, b = lines[key](idx)
        pygame.draw.line(board, (250, 0, 0), a, b, 2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A TicTacToe with a minimax AI agent. Select a play mode.")
    command_group = parser.add_mutually_exclusive_group(required=True)
    command_group.add_argument('--one-player-o', action='store_true', help='Human vs. computer. The human is \'O\'.')
    command_group.add_argument('--one-player-x', action='store_true', help='Human vs. computer. the human is \'X\'.')
    command_group.add_argument('--two-player', action='store_true', help='Human vs. human')
    command_group.add_argument('--ai-only', action='store_true', help='Computer vs. computer')
    args = parser.parse_args()
    player1 = None
    player2 = None
    if args.one_player_o:
        player1 = RationalAgent
        player2 = HumanAgent
    elif args.one_player_x:
        player1 = HumanAgent
        player2 = RationalAgent
    elif args.two_player:
        player1 = HumanAgent
        player2 = HumanAgent
    elif args.ai_only:
        player1 = RationalAgent
        player2 = RationalAgent
    else: 
        raise Exception("Play mode argument not recognized.")
    game = Game(player1, player2)
    # Switch out one or both human players for a RationalAgent (AI player)
    # to test out your AI!
    game.run()

