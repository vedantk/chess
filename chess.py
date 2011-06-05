#!/usr/bin/pypy

import itertools
from collections import namedtuple

piece = namedtuple('Piece', ['type', 'player'])
empty = piece(type=' ', player='none')

posn_init = namedtuple('Posn', ['row', 'col'])
class posn(posn_init):
	def __add__(self, that):
		return posn(self.row + that[0], self.col + that[1])

def new_board():
	board = []
	front = ['p'] * 8
	back = ['r', 'k', 'b', 'Q', 'K', 'b', 'k', 'r']
	def make_row(template, k):
		color = 'black' if k < 2 else 'white'
		return [piece(type=elt, player=color) for elt in template]
	for k in range(8):
		if k in (0, 7):
			row = make_row(back, k)
		elif k in (1, 6):
			row = make_row(front, k)
		else:
			row = [empty] * 8
		board.append(row)
	return board

def print_board(board):
	for row in board:
		print(' '.join([elt.type for elt in row]))

def in_bounds(pos):
        return (0 <= pos.row < 8) and (0 <= pos.col < 8)

def get_piece(board, pos):
	if in_bounds(pos):
		return board[pos.row][pos.col]
	return empty

def set_piece(board, pos, elt):
	board[pos.row][pos.col] = elt

def move_piece(board, old, new):
	orig = get_piece(board, old)
	set_piece(board, new, orig)
	set_piece(board, old, empty)

def is_empty(board, pos):
	return in_bounds(pos) and get_piece(board, pos) == empty

def pawn_moves(board, pos, color):
	delta = 1 if color == 'black' else -1
	advance = pos + (delta, 0)
	if is_empty(board, advance):
		yield advance
	if pos.row in (1, 6):
		double = pos + (2 * delta, 0)
		if is_empty(board, double):
			yield double
	attack = lambda col: pos + (delta, col)
	is_atk = lambda atk: get_piece(atk).player not in (color, empty.player)
	for atk in filter(is_atk, (attack(col - 1), attack(col + 1))):
		yield atk

def rook_moves(board, pos, color):
	deltas = (0, -1), (-1, 0), (0, 1), (1, 0) # l, u, r, d
	return delta_moves(board, pos, color, deltas)

def bishop_moves(board, pos, color):
	deltas = (-1, -1), (-1, 1), (1, 1), (1, -1) # ul, ur, dr, dl
	return delta_moves(board, pos, color, deltas)

def queen_moves(board, pos, color):
	arg = (board, pos, color)
	gens = map(lambda fn: apply(fn, arg), (rook_moves, bishop_moves))
	return itertools.chain(gens)

def delta_moves(board, pos, color, deltas):
	probe = 1
	diffs = [True] * len(deltas)
	while any(diffs):
		for k, (rp, cp) in enumerate(deltas):
			if not diffs[k]:
				continue
			loc = pos + (rp * probe, cp * probe)
			if in_bounds(loc):
				occupant = get_piece(board, loc)
				if occupant != empty:
					diffs[k] = False
				elif occupant.player == color:
					continue
				yield loc
			else:
				diffs[k] = False
		probe += 1

def find_moves(board, player):
	moves = {
		'p': pawn_moves,
		'r': rook_moves,
		'k': knight_moves,
		'b': bishop_moves,
		'Q': queen_moves,
		'K': king_moves,
	}
	for row, k in enumerate(board):
		for elt, j in enumerate(row):
			if elt.player == player:
				pos = posn(k, j)
				finder = moves[elt.type]
				gen = finder(board, pos, elt.player)
				yield ((pos, next(gen)) for k in gen)

def main():
	board = new_board()
	print_board(board)
	move_piece(board, posn(0, 0), posn(5, 5))
	print('-' * 16)
	print_board(board)


main()


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
