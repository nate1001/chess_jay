'''
Copyright Nate Carson 2012

'''

from PyQt4 import QtCore, QtGui

from square import SquareWidget, ChessFontDict, PieceWidget, GraphicsWidget
from game_engine import Move, AlgSquare, PalleteSquare, BoardString
from util import tr
import settings


class MoveError(Exception): pass
	

class CursorWidget(GraphicsWidget):
	
	def __init__(self, squares, algsquare):
		super(CursorWidget, self).__init__()
		self.item = CursorItem(algsquare)
		self.item.setParentItem(self)
		self._squares = squares
	
	def _getSquares(self):
		return self.parentWidget().squares

	def onDirectionPressed(self, direction):
		
		squares = self._getSquares()
		old = squares[self.item._algsquare.label].algsquare
		x, y = old.x, old.y

		if direction == 'north':
			y += 1
		elif direction == 'south':
			y -= 1
		elif direction == 'west':
			x -= 1
		elif direction == 'east':
			x += 1
		elif direction == 'northeast':
			x += 1; y += 1
		elif direction == 'northwest':
			y += 1; x -= 1
		elif direction == 'southwest':
			y -= 1; x -= 1
		elif direction == 'southeast':
			y -= 1; x += 1
		elif direction == 'select':
			self.cursorSelect()
			return
		else:
			raise ValueError(direction)

		new = squares.getSquare(x, y)
		self.item._algsquare = new.algsquare
		self.move(new.pos(), settings.animation_duration)

	def cursorSelect(self):
		squares = self._getSquares()
		square = squares[self.item._algsquare.label]
		board = self.parentWidget()
		board.onSquareSelected(square)

class CursorItem(QtGui.QGraphicsRectItem):
	'''Rectangle Item to be used as a cursor for selecting squares with the keyboard.'''

	def __init__(self, algsquare):
		super(CursorItem, self).__init__()

		self._algsquare = algsquare
		#self.animation = MoveAnimation(self)

		length = settings.square_size
		self.setRect(0, 0, length, length)
		self.setPen(QtGui.QPen(settings.cursor_color, length / 15))
		self._selected_pen = QtGui.QPen(settings.cursor_selected_color, length / 15)
		self._none_pen = QtGui.QPen(settings.COLOR_NONE)




class BoardItem(QtGui.QGraphicsRectItem):
	
	def __init__(self):
		
		super(BoardItem, self).__init__()

		self._squares = {}
		self._squares_by_xy = {}
		self._font = None
		self.cursor = None

		self.setRect(0,0, settings.board_size, settings.board_size)
	
	def __getitem__(self, key):
		return self._squares[key]
	
	def __iter__(self):
		for item in self._squares.itervalues():
			yield item
	
	def __str__(self):
		return "<BoardItem %s>" % self.toString()
	
	def getSquare(self, x, y):	
		for square in self:
			if square.algsquare.x == x and square.algsquare.y == y:
				return square
		raise KeyError((x, y))

	def setBoard(self, boardstring):

		self._font = ChessFontDict(settings.chess_font)

		#clear out pieces if any
		for square in self._squares.itervalues():
			if square.getPiece():
				square.removePiece()

		# AlgSquares
		for algsquare in AlgSquare.generate():
			idx = self._toboardnum(algsquare.x, algsquare.y)
			symbol = boardstring[idx]
			square = self._createSquare(algsquare, symbol)

		if self.cursor is None:
			s = self['e4'].algsquare
			self.cursor = CursorWidget(self, s)
			self.cursor.setParentItem(self)
			self._itemSetPos(self.cursor, s.x, s.y)

	def toString(self):
		algsquares = list(AlgSquare.generate())
		string = list(BoardString.EMPTY_SQUARE * len(algsquares))
		for square in algsquares:
			idx = self._toboardnum(square.x, square.y)
			piece = self._squares[square.label].getPiece()
			if piece:
				string[idx] = piece.name
		return ''.join(string)

	def _toboardnum(self, x, y):
		return ((8-y) * 8) + x - 1 
	
	def _itemSetPos(self, item, x, y):
		side = settings.square_size
		item.setPos((x-1) * side , (8 - y) * side)

	def _createGuide(self, label, x, y):
		guide = GuideItem(x, y, label, centered_label=True)
		self._itemSetPos(guide, x, y)
		guide.setParentItem(self)
		return guide
	
	def _createPiece(self, square, symbol):
		piece = PieceWidget(self._font[symbol])
		square.addPiece(piece)
	
	def _createSquare(self, algsquare, symbol):

		square = SquareWidget(algsquare)
		self._itemSetPos(square, algsquare.x, algsquare.y)
		square.setParentItem(self)
		self._squares[square.algsquare.label] = square
		self._squares_by_xy[(algsquare.x, algsquare.y)] = square


		if symbol != BoardString.EMPTY_SQUARE:
			self._createPiece(square, symbol)

		return square



class BoardWidget(QtGui.QGraphicsWidget):
	'''
		BoardWidget keeps tracks of the squares and moves pieces around.
		The newMove signal will be emitted when two squares with pieces are clicked
		or a piece is dragged to another square. It does not move the piece but delegates
		to the game widget to check the validity of the move. The game widget will then call
		the board widget to move the piece.
	'''

	newMove = QtCore.pyqtSignal(Move)
	boardChanged = QtCore.pyqtSignal(str)
	pieceRemoved = QtCore.pyqtSignal(PieceWidget)

	def __init__(self):
		super(BoardWidget, self).__init__()

		self.squares = BoardItem()
		self.squares.setParentItem(self)

		self.cursor = None

		self._guides= {}
		self._selected_square = None
		self._editable = False

		#self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable, True)

		# guides
		#for f, r, idx in [(AlgSquare.files[i], AlgSquare.ranks[i], i) for i in range(len(AlgSquare.ranks))]:
		#	self._guides[f] = self._createGuide(f, idx+1, 0)
		#	self._guides[r] = self._createGuide(r, 0, idx+1)
		#XXX we need this to overide default behavier of using square label_settings
		#self.toggleGuides(), self.toggleGuides()


	
	def movePiece(self, move, uncapture=None):
		'''
			Makes the appropiate move or raises a value error.
			Does not call itself but waits for the parent widget to call it 
			after BoardWidget emits a newMove signal.

			uncapture will add back pieces for moving back in a game.
		'''
		
		fromsquare = self.squares[move.ssquare.label]
		tosquare = self.squares[move.esquare.label]

		# if its a capture
		if tosquare.getPiece():
			self._removePiece(tosquare)
		else:
			captured = None

		# remove the old piece
		try:
			piece = fromsquare.removePiece()
		except ValueError:
			raise MoveError(move)
			
		# put the piece on the new square
		tosquare.addPiece(piece)

		# we need to set zvalues lower for all squares except our piece's square
		# so we can see the animation move. Otherwise, depending on insertion order
		# the piece will be drawn under some squares.
		for square in self.squares:
			square.setZValue(-1)
		tosquare.setZValue(0)

		new = piece.pos()
		# we have to add the new position (which is a piece) to the square position difference
		# to account for the fact the pieces are not placed in the upper-left hand corner of the square
		old = fromsquare.pos() - tosquare.pos() + new

		duration = settings.animation_duration
		piece.move(new, duration, old=old)

		if uncapture:
			self._addPiece(fromsquare, uncapture)
	
	def _removePiece(self, square):
		piece = square.removePiece()
		piece.fadeOut(settings.animation_duration)
		self.pieceRemoved.emit(piece)
	
	def _addPiece(self, square, symbol):
		piece = PieceItem(square, self._font[symbol])
		piece.fadeIn(duration)
		square.addPiece(piece)

	def onSquareDoubleClicked(self, square):
		if self._editable and not square.algsquare.isPallete() and square.getPiece():
			self._removePiece(square)
		self._selected_square = None
		square.setSelected(False)
		self.boardChanged.emit(self.squares.toString())
	
	def onSquareSelected(self, square):
		'''Catches squareSelected signal from squares and keeps track of currently selected square.'''


		tosquare, fromsquare = square, self._selected_square

		# if its the same square then deselect
		if fromsquare == tosquare:
			square.setSelected(False)
			self._selected_square = None


		# else if we have a selected square already then this square is a drop ... a move
		elif fromsquare is not None:
			ssquare = self._selected_square.algsquare
			esquare = square.algsquare

			# we cannot drop onto the pallete
			if esquare.isPallete():
				tosquare.setSelected(False)
				return

			# else we have a new move
			else:
				# if we adding from the pallete
				if ssquare.isPallete():
					if self._editable:
						if tosquare.getPiece():
							self._removePiece(tosquare)
						self._addPiece(tosquare, fromsquare.getPiece().name)
						self.boardChanged.emit(self.squares.toString())
					else:
						# we cannot use the pallete if we are not editing
						pass

				# else it is a standard move
				else:
					move = Move(str(ssquare) + str(esquare))
					# if we are editing then just move the piece
					if self._editable:
						self.movePiece(move)
						self.boardChanged.emit(self.squares.toString())
					# else mother may I
					else:
						self.newMove.emit(move)

				fromsquare.setSelected(False)
				self._selected_square = None

		# else its the first selection
		else:
			if not tosquare.getPiece():
				return
			tosquare.setSelected(True)
			self._selected_square = tosquare
	
	def toggleLabels(self):
		'''Shows algabraic labels inside the squares.'''
		
		settings.show_labels = not settings.show_labels
		for square in self._squares.values():
			square.label.setVisible(settings.show_labels)

	def toggleGuides(self):
		'''Shows file and rank guides at the side of the board.'''
		
		settings.show_guides = not settings.show_guides
		for guide in self._guides.values():
			guide.label.setVisible(settings.show_guides)
	
	def setEditable(self, editable):
		self._editable = editable
	
	def setBoard(self, boardstring):
		self.squares.setBoard(boardstring)
		for square in self.squares:
			square.squareSelected.connect(self.onSquareSelected)
			square.squareDoubleClicked.connect(self.onSquareDoubleClicked)

	


#class GuideItem(SquareItem):
#	'''Item that shows the rank or file for a board.'''
#	def __init__(self, x, y, algsquare, centered_label):
#		super(GuideItem, self).__init__(x, y, algsquare, centered_label)
#
#	def _setColor(self):
#		self.setPen(QtGui.QPen(settings.COLOR_NONE))
#		self.setBrush(QtGui.QBrush(settings.guide_color))



if __name__ == '__main__':

	class View(QtGui.QGraphicsView):

		directionPressed = QtCore.pyqtSignal(str)

		def __init__(self, scene):
			super(View, self).__init__(scene)

		def keyPressEvent(self, event):

			if event.key() == QtCore.Qt.Key_Escape:
				self.close()

			if event.key() == settings.keys['cursor_south']:
				self.directionPressed.emit('south')
			elif event.key() == settings.keys['cursor_north']:
				self.directionPressed.emit('north')
			elif event.key() == settings.keys['cursor_west']:
				self.directionPressed.emit('west')
			elif event.key() == settings.keys['cursor_east']:
				self.directionPressed.emit('east')

			elif event.key()  == settings.keys['cursor_northwest']:
				self.directionPressed.emit('northwest')
			elif event.key() == settings.keys['cursor_northeast']:
				self.directionPressed.emit('northeast')
			elif event.key() == settings.keys['cursor_southwest']:
				self.directionPressed.emit('southwest')
			elif event.key() == settings.keys['cursor_southeast']:
				self.directionPressed.emit('southeast')

			elif event.key() == settings.keys['cursor_select']:
				self.directionPressed.emit('select')

			super(View, self).keyPressEvent(event)


		def resizeEvent(self, event):

			# find the largest square for old and new and resize to the ratio

			old_side = min(event.oldSize().width(), event.oldSize().height())
			new_side = min(event.size().width(), event.size().height())
			if old_side == -1 or new_side == -1:
				return
			factor = float(new_side) / old_side 
			self.scale(factor, factor)
	
	def onMove(move):
		print 11, move
	def onBoardChanged(board):
		print 22, board

	import sys

	app = QtGui.QApplication(sys.argv)
	scene = QtGui.QGraphicsScene()
	# XXX must construct view before adding stuff to scene or
	# 	  recursive ghost resize events occur.
	view = View(scene)

	string = str(BoardString())

	board = BoardWidget()
	board.setBoard(string)
	board.newMove.connect(onMove)
	board.boardChanged.connect(onBoardChanged)
	board.setEditable(True)
	view.directionPressed.connect(board.squares.cursor.onDirectionPressed)

	scene.addItem(board)

	side = settings.board_size + 9
	view.setGeometry(100, 100, side, side)
	view.show()

	#print board.minimumSize()
	#print board.maximumSize()
	#print board.preferredSize()

	sys.exit(app.exec_())
