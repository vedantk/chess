#!/usr/bin/pypy

'''
Todo:
>	Castling
>	Pawn => opponent's back row conversion
>	refactor board and friends into a class
		if you do this, you can get rid of the hacky fake=True stuff
		this is really needed when doing pawn upgrades
		if you're scouting possible moves and a pawn is pushed to the
		opponent's baseline (with fake=True), then you ought to take
		the attack benefits of the pawn's transformation into account
		BUT if you convert the pawn, there is no clean way to convert
		it back when you go into fake=False mode
		you have to deepcopy each time

class board:
	def __init__(self):


	def get_piece(self, pos):

	def set_piece(self, pos):

	def move_piece(self, old, new):

class game:
	def __init__(self):

	def opposite_color(self, color):
'''

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

def new_board():
	front = ['p'] * 8
	back = ['r', 'k', 'b', 'Q', 'K', 'b', 'k', 'r']
	def make_row(template, is_black):
		color = 'black' if is_black else 'white'
		return [piece(type=elt, color=color) for elt in template]
	return [make_row(back if k in (0, 7) else front, k < 2)
			if k < 2 or k > 5 else [empty] * 8 for k in range(8)]

def print_board(board):
	red = lambda s: '\033[91m' + s + '\033[0m'
	show = lambda p: p.type if p.color == 'white' else red(p.type)
	for row in board:
		print(' '.join([show(elt) for elt in row]))
	print("-" * 40)

def in_bounds(pos):
	return (0 <= pos.row < 8) and (0 <= pos.col < 8)

def get_piece(board, pos):
	return board[pos.row][pos.col]

def set_piece(board, pos, elt):
	board[pos.row][pos.col] = elt

def hash_board(board):
	h = 104729
	for j, row in enumerate(board):
		for k, elt in enumerate(row):
			h ^= hash((elt.type, elt.color, j, k))
	return h

kings = {'white': posn(7, 4), 'black': posn(0, 4)}
draws = {'long-draw': 0, 'three-draw': deque([0, 0, 0], maxlen=3)}

def move_piece(board, old, new, fake=False):
	orig = get_piece(board, old)
	dest = get_piece(board, new)
	set_piece(board, new, orig)
	set_piece(board, old, empty)
	if orig.type == 'K':
		kings[orig.color] = new
	if not fake:
		if dest != empty or orig.type == 'p':
			draws['long-draw'] = 0
		if dest == empty:
			draws['long-draw'] += 1
			if draws['long-draw'] >= 50:
				raise Exception("Long Draw")
		deq = draws['three-draw']
		deq.append(hash_board(board))
		if deq[0] == deq[1] == deq[2]:
			raise Exception("Three-Move Draw")

def is_empty(board, pos):
	return get_piece(board, pos) == empty

def delta_moves(board, pos, color, deltas, max_probe):
	probe = 1
	may_probe = [True] * len(deltas)
	while any(may_probe) and (not(max_probe) or probe <= max_probe):
		for k, (rp, cp) in enumerate(deltas):
			if not may_probe[k]:
				continue
			loc = pos + (rp * probe, cp * probe)
			if in_bounds(loc):
				occupant = get_piece(board, loc)
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
	delta, dbl_row = (1, 1) if color == 'black' else (-1, 6)
	advance = pos + (delta, 0)
	if in_bounds(advance) and is_empty(board, advance):
		yield advance
	if pos.row == dbl_row:
		double = pos + (2 * delta, 0)
		if is_empty(board, double):
			yield double
	safe = color, empty.color
	attacks = pos + (delta, -1), pos + (delta, 1)
	for atk in attacks:
		if in_bounds(atk) and get_piece(board, atk).color not in safe:
			yield atk

rook_deltas = (0, -1), (-1, 0), (0, 1), (1, 0)
bishop_deltas = (-1, -1), (-1, 1), (1, 1), (1, -1)
queen_deltas = rook_deltas + bishop_deltas
knight_deltas = (2, -1), (2, 1), (-2, -1), (-2, 1), \
				(1, 2), (-1, 2), (1, -2), (-1, -2)

moves = {
	'p': pawn_moves,
	'r': move_finder(rook_deltas),
	'b': move_finder(bishop_deltas),
	'Q': move_finder(queen_deltas),
	'k': move_finder(knight_deltas, max_probe=1),
	'K': move_finder(queen_deltas, max_probe=1),
}

def all_moves(board, color):
	pool = []
	for k, row in enumerate(board):
		for j, elt in enumerate(row):
			if elt.color == color:
				pos = posn(k, j)
				gen = moves[elt.type](board, pos, elt.color)
				pool.extend([(pos, new) for new in gen if new])
	return pool

def in_check(board, color):
	my_king = kings[color]
	your = all_moves(board, opposite(color))
	for _, new in your:
		if new == my_king:
			return True
	return False

def potential_moves(board, color):
	my = all_moves(board, color)
	check = in_check(board, color)
	def free_from_check(pair):
		old, new = pair
		orig = get_piece(board, new)
		move_piece(board, old, new, fake=True)
		test = in_check(board, color)
		move_piece(board, new, old, fake=True)
		set_piece(board, new, orig)
		return not(test)
	my = list(filter(free_from_check, my))
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
	board = new_board()
	while True:
		print(">> {0}'s turn".format(color))
		print_board(board)
		try:
			old, new = best_move(board, color)
			move_piece(board, old, new)
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
