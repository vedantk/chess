#!/usr/bin/pypy

from collections import namedtuple

piece = namedtuple('Piece', ['type', 'color'])
empty = piece(type=' ', color='white-or-black')

class posn(namedtuple('Posn', ['row', 'col'])):
	def __add__(self, that):
		row, col = that
		return posn(self.row + row, self.col + col)

def new_board():
	front = ['p'] * 8
	back = ['r', 'k', 'b', 'Q', 'K', 'b', 'k', 'r']
	def make_row(template, is_black):
		color = 'black' if is_black else 'white'
		return [piece(type=elt, color=color) for elt in template]
	return [make_row(back if k in (0, 7) else front, k < 2)
			if k < 2 or k > 5 else [empty] * 8 for k in range(8)]

def print_board(board):
	for row in board:
		print(' '.join([elt.type for elt in row]))
	print("-" * 40)

def in_bounds(pos):
	return (0 <= pos.row < 8) and (0 <= pos.col < 8)

def get_piece(board, pos):
	return board[pos.row][pos.col]

def set_piece(board, pos, elt):
	board[pos.row][pos.col] = elt

def move_piece(board, old, new):
	orig = get_piece(board, old)
	set_piece(board, new, orig)
	set_piece(board, old, empty)

def is_empty(board, pos):
	return get_piece(board, pos) == empty

def pawn_moves(board, pos, color):
	delta = 1 if color == 'black' else -1
	advance = pos + (delta, 0)
	if in_bounds(advance) and is_empty(board, advance):
		yield advance
	if pos.row in (1, 6):
		double = pos + (2 * delta, 0)
		if is_empty(board, double):
			yield double
	safe = color, empty.color
	attacks = pos + (delta, -1), pos + (delta, 1)
	for atk in attacks:
		if in_bounds(atk) and get_piece(board, atk).color not in safe:
			yield atk

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

rook_deltas = (0, -1), (-1, 0), (0, 1), (1, 0) # l, u, r, d
bishop_deltas = (-1, -1), (-1, 1), (1, 1), (1, -1) # ul, ur, dr, dl
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

def find_moves(board, color):
	for k, row in enumerate(board):
		for j, elt in enumerate(row):
			if elt.color == color:
				pos = posn(k, j)
				gen = moves[elt.type](board, pos, elt.color)
				yield ((pos, potential) for potential in gen)

def new_game():
	board = new_board()
	print_board(board)
	mvgen = find_moves(board, 'white')
	for gen in mvgen:
		for old, new in gen:
			b = new_board()
			move_piece(b, old, new)
			print_board(b)
			raw_input(">> ")

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
