'''
Copyright Nate Carson 2012

'''

import os

from PyQt4 import QtGui, QtCore

dbname = 'chess'
lib = '/../build/lib'
media_piece = '/media/pieces/'
dbchesslib = os.getcwd() + lib

COLOR_NONE = QtGui.QColor(0,0,0,0)

square_size = 60
board_size = square_size * 8



keys = {
	'first_move': QtGui.QKeySequence.MoveToStartOfLine,
	'previous_move': QtGui.QKeySequence.MoveToPreviousChar,
	'next_move': QtGui.QKeySequence.MoveToNextChar,
	'last_move': QtGui.QKeySequence.MoveToEndOfLine,
	'reload_board': QtGui.QKeySequence('r'),

	'cursor_north': QtGui.QKeySequence('k'),
	'cursor_south': QtGui.QKeySequence('j'),
	'cursor_east': QtGui.QKeySequence('l'),
	'cursor_west': QtGui.QKeySequence('h'),
	'cursor_northwest': QtGui.QKeySequence('y'),
	'cursor_northeast': QtGui.QKeySequence('u'),
	'cursor_southwest': QtGui.QKeySequence('b'),
	'cursor_southeast': QtGui.QKeySequence('n'),
	'cursor_select': QtCore.Qt.Key_Return,

}

piece_directory = os.getcwd() + media_piece
chess_font = 'Internet'
square_light_color = QtGui.QColor('white')
square_dark_color= QtGui.QColor('green')
#square_dark_color= QtGui.QColor('white')
square_outline_color = QtGui.QColor('black')
square_hover_color = QtGui.QColor('orange')
square_selected_color = QtGui.QColor('orange')
cursor_color = QtGui.QColor('magenta')
cursor_selected_color = QtGui.QColor('red')
square_label_color = QtGui.QColor('red')
guide_color = QtGui.QColor('red')
show_labels = False
show_guides = False
animation_duration = 300


