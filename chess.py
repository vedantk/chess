#!/usr/bin/pypy

'''
Todo:
>	Castling
'''

import random
from functools import reduce
from collections import namedtuple, deque

piece = namedtuple('Piece', ['type', 'color'])
empty = piece(type=' ', color='white-or-black')
opposite = lambda color: 'black' if color == 'white' else 'white'

class posn(namedtuple('Posn', ['row', 'col'])):
	def __add__(self, that):
		return posn(self.row + that[0], self.col + that[1])

	def __eq__(self, that):
		return isinstance(that, posn) and \
			self.row == that.row and self.col == that.col

class board:
	def __init__(self):
		front = ['p'] * 8
		back = ['r', 'k', 'b', 'Q', 'K', 'b', 'k', 'r']
		def make_row(template, is_black):
			color = 'black' if is_black else 'white'
			return [piece(elt, color) for elt in template]
		self.mat = [make_row(back if k in (0, 7) else front, k < 2)
			if k < 2 or k > 5 else [empty] * 8 for k in range(8)]
		self.kings = {'white': posn(7, 4), 'black': posn(0, 4)}
		self.draws = {'long': 0, 'three': deque(range(6), maxlen=6)}
		self.state = 'normal'
		self.history = [] # [(old/new: posn, orig/dest: piece)]

	def foreach(self):
		for j, row in enumerate(self.mat):
			for k, soldier in enumerate(row):
				yield j, k, soldier

	def __hash__(self):
		return reduce(lambda v, e: v ^ hash(e), self.foreach(), 1007)

	def __getitem__(self, pos):
		return self.mat[pos.row][pos.col]

	def __setitem__(self, pos, elt):
		self.mat[pos.row][pos.col] = elt

	def display(self):
		red = lambda s: '\033[91m' + s + '\033[0m'
		show = lambda p: p.type if p.color == 'white' else red(p.type)
		for row in self.mat:
			print(' '.join([show(elt) for elt in row]))
		print("-" * 40)

	def is_empty(self, pos):
		return self[pos] == empty

	def handle_draws(self, orig, dest):
		if dest != empty or orig.type == 'p':
			# Captures and pawn advances reset the long draw.
			self.draws['long'] = 0
			return
		else:
			self.draws['long'] += 1
			if self.draws['long'] >= 50:
				self.state = 'draw'
				return
		deq = self.draws['three']
		deq.append(hash(self))
		if deq[0] == deq[2] == deq[4] or deq[1] == deq[3] == deq[5]:
			# If three previous states were the same, call a draw.
			self.state = 'draw'

	def update_kings(self, orig, new):
		if orig.type == 'K':
			# Keep track of where kings are for quick check detection.
			self.kings[orig.color] = new

	def move_piece(self, old, new, fake=False):
		orig, dest = self[old], self[new]
		self[new], self[old] = orig, empty
		self.update_kings(orig, new)
		if orig.type == 'p':
			# Promote pawns to queens when they reach the final row.
			end = 0 if orig.color == 'white' else 7
			if new.row == end:
				self[new] = piece(type='Q', color=orig.color)
		if not fake:
			self.handle_draws(orig, dest)
		self.history.append((old, new, orig, dest))

	def undo_move(self):
		old, new, orig, dest = self.history.pop()
		self[old], self[new] = orig, dest
		self.update_kings(orig, old)

	def all_moves(self, color):
		# Find all possible moves available to <color>.
		pool = []
		for j, k, soldier in self.foreach():
			if soldier.color == color:
				pos = posn(j, k)
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

def delta_moves(game, pos, color, deltas, max_probe=False):
	probe = 1
	search = [True] * len(deltas)
	while any(search) and (not(max_probe) or probe <= max_probe):
		for k, (rp, cp) in enumerate(deltas):
			if not search[k]:
				continue
			loc = pos + (rp * probe, cp * probe)
			if in_bounds(loc):
				occupant = game[loc]
				if occupant == empty or occupant.color != color:
					yield loc
				if occupant != empty:
					search[k] = False
			else:
				search[k] = False
		probe += 1

def move_finder(deltas, max_probe=False):
	return lambda game, pos, color: \
		delta_moves(game, pos, color, deltas, max_probe)

def pawn_moves(game, pos, color):
	delta, dbl = (1, 1) if color == 'black' else (-1, 6)
	advance = pos + (delta, 0)
	if in_bounds(advance) and game.is_empty(advance):
		yield advance
	if pos.row == dbl:
		double = pos + (2 * delta, 0)
		if game.is_empty(double):
			yield double
	safe = color, empty.color
	attacks = pos + (delta, -1), pos + (delta, 1)
	for atk in attacks:
		if in_bounds(atk) and game[atk].color not in safe:
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

def potential_moves(game, color):
	def free_from_check(pair):
		old, new = pair
		game.move_piece(old, new, fake=True)
		test = not(game.in_check(color))
		game.undo_move()
		return test
	check = game.in_check(color)
	my = list(filter(free_from_check, game.all_moves(color)))
	if check:
		print("{0} is in check!".format(color))
	if not len(my):
		game.state = 'done' if check else 'draw'
		if check:
			print("{0} loses...".format(color))
		return check
	return my

def best_move(game, color):
	pool = potential_moves(game, color)
	if isinstance(pool, bool):
		return pool, None
	return random.choice(pool)

def new_game():
	color = 'white'
	game = board()
	while game.state == 'normal':
		lhs, rhs = best_move(game, color)
		if rhs == None:
			break
		else:
			game.move_piece(lhs, rhs)
			color = opposite(color)
	game.display()
	print(game.state)

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
