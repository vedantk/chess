#!/usr/bin/pypy

'''
Todo:
>	Castling
'''

import copy
import random
from collections import namedtuple, deque

piece = namedtuple('Piece', ['type', 'color'])
empty = piece(type=' ', color='white-or-black')
opposite = lambda color: 'black' if color == 'white' else 'white'

class posn(namedtuple('Posn', ['row', 'col'])):
	def __add__(self, that):
		row, col = that
		return posn(self.row + row, self.col + col)

	def __eq__(self, that):
		return self.row == that.row and self.col == that.col

class board:
	def __init__(self):
		front = ['p'] * 8
		back = ['r', 'k', 'b', 'Q', 'K', 'b', 'k', 'r']
		def make_row(template, is_black):
			color = 'black' if is_black else 'white'
			return [piece(type=elt, color=color) for elt in template]
		self.mat = [make_row(back if k in (0, 7) else front, k < 2) \
			if k < 2 or k > 5 else [empty] * 8 for k in range(8)]
		self.kings = {'white': posn(7, 4), 'black': posn(0, 4)}
		self.draws = {'long': 0, 'three': deque(range(6), maxlen=6)}

	def __hash__(self):
		h = 104729
		for j, row in enumerate(self.mat):
			for k, soldier in enumerate(row):
				h ^= hash((soldier.type, soldier.color, j, k))
		return h

	def __str__(self):
		red = lambda s: '\033[91m' + s + '\033[0m'
		show = lambda p: p.type if p.color == 'white' else red(p.type)
		for row in board:
			print(' '.join([show(elt) for elt in row]))
		print("-" * 40)

	def __getitem__(self, pos):
		return self.mat[pos.row][pos.col]

	def __setitem__(self, pos, elt):
		self.mat[pos.row][pos.col] = elt

	def is_empty(self, pos):
		return self[pos] == empty

	def move_piece(self, old, new):
		orig = self[old]
		dest = self[new]
		self[new] = orig
		self[old] = empty
		if orig.type == 'K':
			# Keep track of where kings are for quick check detection.
			self.kings[orig.color] = new
		if orig.type == 'p':
			# Promote pawns to queens when they reach the final row.
			end = 0 if orig.color == 'white' else 7
			if new.row == end:
				orig.type = 'Q'
		if dest != empty or orig.type == 'p':
			# If a capture or pawn advance occurs, delay a long draw.
			self.draws['long'] = 0
		else:
			self.draws['long'] += 1
			if draws['long'] >= 50:
				return 'long'
		deq = draws['three']
		deq.append(hash(self))
		if deq[0] == deq[2] == deq[4] or deq[1] == deq[3] == deq[5]:
			# If three previous states were the same, call a draw.
			return 'three'

	def all_moves(self, color):
		# Find all possible moves available to <color>.
		pool = []
		for k, row in enumerate(self.mat):
			for j, soldier in enumerate(row):
				if soldier.color == color:
					pos = posn(k, j)
					gen = moves[soldier.type](self, pos, soldier.color)
					pool.extend([(pos, new) for new in gen if new])
		return pool

	def in_check(self, color):
		# Determine if <color> is in check.
		my_king = self.kings[color]
		your = self.all_moves(opposite(color))
		for _, new in your:
			if new == my_king:
				return True
		return False

def in_bounds(pos):
	return (0 <= pos.row < 8) and (0 <= pos.col < 8)

def delta_moves(board, pos, color, deltas, max_probe):
	probe = 1
	may_probe = [True] * len(deltas)
	while any(may_probe) and (not(max_probe) or probe <= max_probe):
		for k, (rp, cp) in enumerate(deltas):
			if not may_probe[k]:
				continue
			loc = pos + (rp * probe, cp * probe)
			if in_bounds(loc):
				occupant = board[loc]
				if occupant == empty or occupant.color != color:
					yield loc
				if occupant != empty:
					may_probe[k] = False
			else:
				may_probe[k] = False
		probe += 1

def move_finder(deltas, max_probe=False):
	return lambda board, pos, color: \
		delta_moves(board, pos, color, deltas, max_probe)

def pawn_moves(board, pos, color):
	delta, dbl = (1, 1) if color == 'black' else (-1, 6)
	advance = pos + (delta, 0)
	if in_bounds(advance) and board.is_empty(advance):
		yield advance
	if pos.row == dbl:
		double = pos + (2 * delta, 0)
		if board.is_empty(double):
			yield double
	safe = color, empty.color
	attacks = pos + (delta, -1), pos + (delta, 1)
	for atk in attacks:
		if in_bounds(atk) and board[atk].color not in safe:
			yield atk

rook_deltas = (0, -1), (-1, 0), (0, 1), (1, 0)
bishop_deltas = (-1, -1), (-1, 1), (1, 1), (1, -1)
knight_deltas = (2, -1), (2, 1), (-2, -1), (-2, 1), \
				(1, 2), (-1, 2), (1, -2), (-1, -2)
queen_deltas = rook_deltas + bishop_deltas

moves = {
	'p': pawn_moves,
	'r': move_finder(rook_deltas),
	'b': move_finder(bishop_deltas),
	'Q': move_finder(queen_deltas),
	'k': move_finder(knight_deltas, max_probe=1),
	'K': move_finder(queen_deltas, max_probe=1),
}

def potential_moves(board, color):
	def available_move(pair):
		old, new = pair
		hypo = copy.deepcopy(board)
		hypo.move_piece(old, new)
		return not(hypo.in_check(color))
	check = board.in_check(color)
	my = list(filter(available_move, board.all_moves(color)))
	if check:
		print("{0} is in check!".format(color))
	if not len(my):
		print("{0} loses...".format(color) if check else "Draw.")
		return check
	return my

def best_move(board, color):
	pool = potential_moves(board, color)
	if isinstance(pool, bool):
		raise Exception("Game over.")
	return random.choice(pool)

def new_game():
	color = 'white'
	game = board()
	while True:
		print(board)
		print("^^^ {0}'s turn".format(color))
		try:
			old, new = best_move(board, color)
			board.move_piece(old, new)
			color = opposite(color)
		except Exception, msg:
			print(msg)
			return

new_game()

'''
function alphabeta(node, depth, α, β, Player)
    if  depth = 0 or node is a terminal node
        return the heuristic value of node
    if  Player = MaxPlayer
        for each child of node
            α := max(α, alphabeta(child, depth-1, α, β, not(Player) ))
            if β ≤ α
                break                             (* Beta cut-off *)
        return α
    else
        for each child of node
            β := min(β, alphabeta(child, depth-1, α, β, not(Player) ))
            if β ≤ α
                break                             (* Alpha cut-off *)
        return β
(* Initial call *)
alphabeta(origin, depth, -infinity, +infinity, MaxPlayer)
'''
