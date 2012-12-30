'''
Copyright Nate Carson 2012

'''

from PyQt4 import QtCore, QtGui, QtSvg


from move_list import MoveTable
from game_engine import Move, AlgSquare, PalleteSquare, BoardString, Piece
from util import tr, ToolBar
import settings

	

class CursorItem(QtGui.QGraphicsRectItem):
	'''Rectangle Item to be used as a cursor for selecting squares with the keyboard.'''

	def __init__(self, algsquare):
		super(CursorItem, self).__init__()

		self._algsquare = algsquare
		self.animation = MoveAnimation(self)

		length = settings.square_size
		self.setRect(0, 0, length, length)
		self.setPen(QtGui.QPen(settings.cursor_color, length / 15))
		self._selected_pen = QtGui.QPen(settings.cursor_selected_color, length / 15)
		self._none_pen = QtGui.QPen(settings.COLOR_NONE)


	def onDirectionPressed(self, direction):
		
		board = self.parentWidget()
		old = board._squares[self._algsquare.label]
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

		if not board._squares_by_xy.has_key((x, y)):
			return

		new = board._squares_by_xy[(x, y)]
		self._algsquare = new.algsquare
		self.animation.move(new.pos())

	def cursorSelect(self):
		board = self.parentWidget()
		square = board._squares[self._algsquare.label]
		board.onSquareSelected(square)


class MoveError(Exception): pass


class MoveAnimation(QtCore.QObject):
	'''
		QObject to handle animations for GraphicsItems.
		Pyqt does not handle multiple inheritance (and will silently let you pretend that it can.) 
		So for graphics items to use signals and animiations we must delegate to a QObject class
	'''
	
	def __init__(self, item):
		
		super(MoveAnimation, self).__init__()
		self.item = item
	
		# XXX animations must be made an instance attribute or it will not work
		# qt probably destroys the animation ( but it will not raise an error)

		self.anim_move = QtCore.QPropertyAnimation(self, 'pos')
		self.anim_fade = QtCore.QPropertyAnimation(self, 'opacity')

	def _set_pos(self, pos):
		self.item.setPos(pos)
	def _get_pos(self):
		return self.item.pos()
	pos = QtCore.pyqtProperty(QtCore.QPointF, fset=_set_pos, fget=_get_pos)

	def _set_opacity(self, opacity):
		self.item.setOpacity(opacity)
	def _get_opacity(self):
		return self.item.opacity()
	opacity = QtCore.pyqtProperty(float, fset=_set_opacity, fget=_get_opacity)


	def move(self, new, old=None):

		if not old:
			old = self.item.pos()

		self.anim_move.setDuration(settings.animation_duration)
		self.anim_move.setStartValue(old)
		self.anim_move.setEndValue(new)
		self.anim_move.start()
	
	def fadeOut(self):
		self.anim_fade.setDuration(settings.animation_duration)
		self.anim_fade.setStartValue(1)
		self.anim_fade.setEndValue(0)
		self.anim_fade.start()

	def fadeIn(self):
		self.anim_fade.setDuration(settings.animation_duration)
		self.anim_fade.setStartValue(0)
		self.anim_fade.setEndValue(1)
		self.anim_fade.start()


class SquareItem(QtGui.QGraphicsRectItem):
	'''
		GraphicsItem represents a square of a board and may contain a piece. 
		Sends square selected and hover drop signals for the board to handle.
	'''


	def __init__(self, x, y, algsquare, centered_label=False):
		super(SquareItem, self).__init__()

		self.x = x
		self.y = y
		self.algsquare = algsquare
		self.label = SquareLabelItem(str(algsquare), self, centered_label)
		self.signals = SquareSignals()

		self._piece = None
		self._hover_pen = None
		self._nohover_pen = None
		self._custom_color = None

		self.setAcceptDrops(True)

		self._init(x, y)
	
	def __str__(self):
		return '<SquareItem %s>' % (self.algsquare)
		self._piece = None 

	def _init(self, x, y):

		length = settings.square_size
		self.setRect(0, 0, length, length)
		self._setColor()

		self._selected_brush = QtGui.QBrush(settings.square_selected_color)
		width = settings.square_size / 15
		self._hover_pen = QtGui.QPen(settings.square_hover_color, width)
		self._none_pen = QtGui.QPen(settings.COLOR_NONE)
	
	def setCustomColor(self, color):
		self._custom_color = color
		self._setColor()
	
	def _setColor(self):

		self.setPen(QtGui.QPen(settings.square_outline_color))

		if self._custom_color:
			self.setBrush(QtGui.QBrush(self._custom_color))
		else:
			if (self.x + self.y) % 2 == 0:
				self.setBrush(QtGui.QBrush(settings.square_dark_color))
			else:
				self.setBrush(QtGui.QBrush(settings.square_light_color))
	
	def addPiece(self, piece):
		piece.setParentItem(self)
		self._piece = piece

	def removePiece(self):

		piece = self._piece
		if not piece:
			raise ValueError('square %s has no piece to remove' % self)
		self._piece = None
		piece.setParent(None)
		return piece
	
	def getPiece(self):
		return self._piece
		
	def mousePressEvent(self, event):
		if event.button() != QtCore.Qt.LeftButton:
			event.ignore()
			return
		self.signals.squareSelected.emit(self)

	def setSelected(self, active):
		if active:
			self.setBrush(self._selected_brush)
		else:
			self._setColor()
		self.update()
	
	def setHoverPiece(self, active):
		if active:
			self.setPen(self._hover_pen)
		else:
			self.setPen(self._none_pen)
		self.update()
	
	def dragEnterEvent(self, event):
		self.setHoverPiece(True)

	def dragLeaveEvent(self, event):
		self.setHoverPiece(False)
	
	def dropEvent(self, event):

		fromsquare = event.mimeData().text()
		tosquare = self.algsquare.label
		self.signals.squareSelected.emit(self)

		self.setHoverPiece(False)


class SquareSignals(QtCore.QObject):
		squareSelected = QtCore.pyqtSignal(SquareItem)
		squareDoubleClicked = QtCore.pyqtSignal(SquareItem)


class BoardWidget(QtGui.QGraphicsWidget):

	newMove = QtCore.pyqtSignal(Move)
	boardChanged = QtCore.pyqtSignal(BoardString)

	def test(self):
		pass


	def __init__(self):
		super(BoardWidget, self).__init__()

		self.geometryChanged.connect(self.test)

		self.squares = BoardSquaresWidget()
		self.squares.setParentItem(self)

	
	def newGame(self):
		pass
		#FIXME
	
	def setBoard(self, boardstring):
		self.squares.setBoard(boardstring)
	


class BoardSquaresWidget(QtGui.QGraphicsWidget):
	'''
		BoardWidget keeps tracks of the squares and moves pieces around.
		The newMove signal will be emitted when two squares with pieces are clicked
		or a piece is dragged to another square. It does not move the piece but delegates
		to the game widget to check the validity of the move. The game widget will then call
		the board widget to move the piece.
	'''

	EMPTY_SQUARE = tr('.')



	def __init__(self, parent=None):
		super(BoardSquaresWidget, self).__init__(parent)

		self.cursor = None


		self._squares = {}
		self._squares_by_xy = {}
		self._guides= {}
		self._selected_square = None
		self._current_move = None
		self._font = None
		self._editable = False

		self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable, True)

		'''
		# guides
		for f, r, idx in [(AlgSquare.files[i], AlgSquare.ranks[i], i) for i in range(len(AlgSquare.ranks))]:
			self._guides[f] = self._createGuide(f, idx+1, 0)
			self._guides[r] = self._createGuide(r, 0, idx+1)
		#XXX we need this to overide default behavier of using square label_settings
		self.toggleGuides(), self.toggleGuides()
		'''


		#self.setSceneRect(QtCore.QRectF(0, 0, settings.board_size , settings.board_size))
	
	def setBoard(self, boardstring):

		#clear out board if any
		for square in self._squares.itervalues():
			square.setParentItem(None)
			if square.getPiece():
				square.removePiece()

		self._font = ChessFontDict(settings.chess_font)

		# AlgSquares
		for algsquare in AlgSquare.generate():
			idx = self._toboardnum(algsquare.x, algsquare.y)
			symbol = boardstring.string[idx]
			square = self._createSquare(algsquare, symbol)

		# PalleteSquares
		for idx, algsquare in enumerate(PalleteSquare.generate()):
			symbol = Piece.pieces[idx]
			square = self._createSquare(algsquare, symbol)
			square.setCustomColor(settings.COLOR_NONE)

		#cursor - init once
		if self.cursor is None:
			s = self._squares['e4']
			self.cursor = CursorItem(s.algsquare)
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
		length = settings.square_size
		item.setPos((x-1) * length , (8 - y) * length )

	def _createGuide(self, label, x, y):
		guide = GuideItem(x, y, label, centered_label=True)
		self._itemSetPos(guide, x, y)
		guide.setParentItem(self)
		return guide
	
	def _createPiece(self, square, symbol):
		piece = PieceItem(square, self._font[symbol])
		piece.signals.pieceDoubleClicked.connect(self.onPieceDoubleClicked)
		square.addPiece(piece)
	
	def _createSquare(self, algsquare, symbol):

		square = SquareItem(algsquare.x, algsquare.y, algsquare)
		self._itemSetPos(square, algsquare.x, algsquare.y)
		square.setParentItem(self)
		self._squares[square.algsquare.label] = square
		self._squares_by_xy[(square.x, square.y)] = square

		square.signals.squareSelected.connect(self.onSquareSelected)

		if symbol != BoardString.EMPTY_SQUARE:
			self._createPiece(square, symbol)

		return square

	
	def movePiece(self, move, uncapture=None):
		'''
			Makes the appropiate move or raises a value error.
			Does not call itself but waits for the parent widget to call it 
			after BoardWidget emits a newMove signal.

			uncapture will add back pieces for moving back in a game.
		'''
		
		fromsquare = self._squares[move.ssquare.label]
		tosquare = self._squares[move.esquare.label]

		# if its a capture
		if tosquare.getPiece():
			captured = tosquare.removePiece()
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
		for square in self._squares.values():
			square.setZValue(-1)
		tosquare.setZValue(0)

		new = piece.pos()
		# we have to add the new position (which is a piece) to the square position difference
		# to account for the fact the pieces are not placed in the upper-left hand corner of the square
		old = fromsquare.pos() - tosquare.pos() + new

		piece.animation.move(new, old)
		captured and captured.animation.fadeOut()

		if uncapture:
			piece = PieceItem(square, self._font[uncapture])
			piece.animation.fadeIn()
			fromsquare.addPiece(piece)

	def onPieceDoubleClicked(self, piece):
		square = piece.parentItem()
		if self._editable and not square.algsquare.isPallete():
			piece = square.removePiece()
			piece.animation.fadeOut()

		self._selected_square = None
		square.setSelected(False)
	
	def onSquareSelected(self, square):
		'''Catches squareSelected signal from squares and keeps track of currently selected square.'''

		# if its the same square then deselect
		if self._selected_square == square:
			square.setSelected(False)
			self._selected_square = None

		# else if we have a selected square already then this square is a drop ... a move
		elif self._selected_square is not None:
			ssquare = self._selected_square.algsquare
			esquare = square.algsquare

			# we cannot drop onto the pallete
			if esquare.isPallete():
				square.setSelected(False)
				return

			# else we have a new move
			else:
				# if we adding from the pallete
				if ssquare.isPallete():
					if self._editable:
						try:
							old = square.removePiece()
							old.animation.fadeOut()
						except ValueError:
							pass
						symbol = self._selected_square.getPiece().name
						new = PieceItem(square, self._font[symbol])
						square.addPiece(new)
						new.animation.fadeIn()
						self.boardChanged.emit(BoardString(self.toString()))
				# else it is a standard move
				else:
					move = Move(str(ssquare) + str(esquare))
					if self._editable:
						self.movePiece(move)
					else:
						self.newMove.emit(move)

				self._selected_square.setSelected(False)
				self._selected_square = None

		# else its the first selection
		else:
			if not square.getPiece():
				return
			square.setSelected(True)
			self._selected_square = square
	
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
	

class SquareLabelItem(QtGui.QGraphicsSimpleTextItem):
	'''Item that shows the algbraic label for a square.'''

	def __init__(self, algsquare, square, centered_label):

		super(SquareLabelItem, self).__init__(algsquare, square)

		if centered_label:
			divisor = 3
		else:
			divisor = 15
		padding = settings.square_size / divisor
		self.setPos(padding, padding)
		self.setVisible(settings.show_labels)

		font = QtGui.QFont()
		font.setBold(True)
		self.setFont(font)
	
	def setVisible(self, active):
		if active:
			self.setBrush(QtGui.QBrush(settings.square_label_color))
		else:
			self.setBrush(QtGui.QBrush(settings.COLOR_NONE))

class GuideItem(SquareItem):
	'''Item that shows the rank or file for a board.'''
	def __init__(self, x, y, algsquare, centered_label):
		super(GuideItem, self).__init__(x, y, algsquare, centered_label)

	def _setColor(self):
		self.setPen(QtGui.QPen(settings.COLOR_NONE))
		self.setBrush(QtGui.QBrush(settings.guide_color))


class PieceItem(QtSvg.QGraphicsSvgItem):
	'''Item that represents the piece on a square.'''

	name_map = {
		'wp': 'P',
		'wn': 'N',
		'wb': 'B',
		'wr': 'R',
		'wq': 'Q',
		'wk': 'K',
		'bp': 'p',
		'bn': 'n',
		'bb': 'b',
		'br': 'r',
		'bq': 'q',
		'bk': 'k',
	}

	def __init__(self, square, renderer):
		super(PieceItem, self).__init__(square)

		self.name = self.name_map[renderer.name]
		self.animation = MoveAnimation(self)
		self.setSharedRenderer(renderer)
		self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
		self._init(renderer)
		self.signals = PieceSignals()
	
	def __str__(self):
		return '<PieceItem %s>' % self.name
	
	def _init(self, renderer):

		x = renderer.defaultSize().width()
		y = renderer.defaultSize().height()

		# scale the piece from its arbitrary svg size
		size = settings.square_size
		scalex, scaley = x / float(size), y / float(size)
		if scalex > .75 or scaley > .75:
			self.setScale(1 / (max([scalex, scaley]) + .25))

		self.setPos(size / 12, size / 12)

	def mousePressEvent(self, event):
		if event.button() != QtCore.Qt.LeftButton:
			event.ignore()
			return

		# self.square.board
		item = self.parentItem().parentItem()
		# it the parent is a square item
		if item is not None:
			item.onSquareSelected(self.parentItem())

	def mouseDoubleClickEvent(self, event):
		if event.button() != QtCore.Qt.LeftButton:
			event.ignore()
			return
		self.signals.pieceDoubleClicked.emit(self)
	

	def mouseMoveEvent(self, event):
		
		drag = QtGui.QDrag(event.widget())
		mime = QtCore.QMimeData()
		item = self.parentItem()

		# if the parent is a square item
		if hasattr(item, 'algsquare'):
			mime.setText(item.algsquare.label)
		# else its from the piece pallete
		else:
			mime.setText(self.name)

		drag.setMimeData(mime)
		drag.exec_()

class PieceSignals(QtCore.QObject):
	pieceDoubleClicked = QtCore.pyqtSignal(PieceItem)
	

class ChessFontRenderer(QtSvg.QSvgRenderer):
	'''Holds the svg font for a chess font.'''


	def __init__(self, fontname, piece):
		self.name = Piece.toSVGFont(piece)
		fname = settings.piece_directory + '/' + fontname + '/' + self.name + '.svg'
		super(ChessFontRenderer, self).__init__(fname)

		if not self.isValid():
			raise ValueError('could not parse svg file ' + fname)


class ChessFontDict(dict):
	'''Holds all svg chess fonts.'''
	
	def __init__(self, fontname):

		for piece in Piece.pieces:
			self[piece] = ChessFontRenderer(fontname, piece)


class ChessScene(QtGui.QGraphicsScene):

	def __init__(self, game_engine):

		super(ChessScene, self).__init__()

		font = ChessFontDict(settings.chess_font)

		#board
		self.board = BoardWidget()
		self.addItem(self.board)

		#move_table 
		self.move_table = MoveTable(self.board, game_engine)
		self.board.boardChanged.connect(self.move_table.resetEngine)

		x, y = settings.board_size + 5, 0
		self.addItem(self.move_table)
		self.move_table.setPos(x, y)

		#opening_table
		#self.opening_table = OpeningTable()
		#self.move_table.moveMade.connect(self.opening_table.onMoveMade)

		#game engine
		self.setEngine(game_engine)
		self.newGame()

	def onShowPallete(self):
		self.move_table.hide()
		self.board.setEditable(True)

	def onShowMoves(self):
		self.move_table.show()
		self.board.setEditable(False)

	def moveCursor(self, direction):
		self.board.moveCursor(direction)

	def cursorSelect(self):
		self.board.cursorSelect()

	def toggleLabels(self):
		self.board.toggleLabels()

	def toggleGuides(self):
		self.board.toggleGuides()

	def loadGame(self, moves):
		board = self.move_table.loadGame(moves)

	def newGame(self):
		self.move_table.newGame()

	def setEngine(self, game_engine):
		self.move_table.setEngine(game_engine)
	

	def onVariationSelected(self, from_square, to_square, subject, target):
		
		# go back on move
		last_move = self.moves_table.previousMove()
		self.setMove(last_move)
		self.moves_table.onMoveMade(last_move)

		# set the new move
		self.onNewMove(from_square, to_square, subject, target)


class BoardView(QtGui.QWidget):

	def __init__(self, scene, w, h):

		super(BoardView, self).__init__()
		self.view = QtGui.QGraphicsView(scene)
		self.view.setSceneRect(0, 0, w, h)

		self.toolbar = ToolBar()

		self.toolbar.addAction("New", 'first_move', tr("new game"), self.newGame, 'document-new')

		layout = QtGui.QVBoxLayout()
		layout.addWidget(self.toolbar)
		layout.addWidget(self.view)
		self.setLayout(layout)
	
	def newGame(self):
		pass


class SideBarView(QtGui.QWidget):
	def __init__(self, scene, w, h):
		super(SideBarView, self).__init__()

		self.view = QtGui.QGraphicsView(scene)
		self.view.setSceneRect(w, 0, 200, h)
		self.setGeometry(0, 0, 200, h)

		self.toolbar = ToolBar()

		group = QtGui.QActionGroup(self.toolbar)
		group.setExclusive(True)

		a = self.toolbar.addAction("Play", 'first_move', tr("play game"), self.onShowMoves, 'media-playback-start') 
		a.setCheckable(True)
		a.setChecked(True)
		group.addAction(a)

		a = self.toolbar.addAction("Set", 'first_move', tr("set board"), self.onShowPallete, 'document-edit')
		a.setCheckable(True)
		group.addAction(a)

		layout = QtGui.QVBoxLayout()
		layout.addWidget(self.toolbar)
		layout.addWidget(self.view)
		self.setLayout(layout)

	
	def onShowMoves(self):
		pass
	def onShowPallete(self):
		pass


class ChessWidget(QtGui.QWidget):

	direction_pressed = QtCore.pyqtSignal(str)
	
	def __init__(self):
		super(ChessWidget, self).__init__()

		#self.direction_pressed.connect(
		#	scene.board.cursor.onDirectionPressed)

		game_engine = DumbGameEngine()
		self.scene = ChessScene(game_engine)

		w = settings.board_size + 6
		h = settings.board_size + 32 + 16

		board = BoardView(self.scene, w, h)
		sidebar = SideBarView(self.scene, w, h)
		
		layout = QtGui.QHBoxLayout()
		layout.addWidget(board)
		layout.addWidget(sidebar)
		self.setLayout(layout)
		#fixed
		layout.setSizeConstraint(3)

		self.setGeometry(0, 0, w*2, h)

	def loadGame(self, moves):
		self.scene.loadGame(moves)

	def keyPressEvent(self, event):

		if event.key() == QtCore.Qt.Key_Escape:
			self.close()

		if event.key() == settings.keys['cursor_south']:
			self.direction_pressed.emit('south')
		elif event.key() == settings.keys['cursor_north']:
			self.direction_pressed.emit('north')
		elif event.key() == settings.keys['cursor_west']:
			self.direction_pressed.emit('west')
		elif event.key() == settings.keys['cursor_east']:
			self.direction_pressed.emit('east')

		if event.key()  == settings.keys['cursor_northwest']:
			self.direction_pressed.emit('northwest')
		elif event.key() == settings.keys['cursor_northeast']:
			self.direction_pressed.emit('northeast')
		elif event.key() == settings.keys['cursor_southwest']:
			self.direction_pressed.emit('southwest')
		elif event.key() == settings.keys['cursor_southeast']:
			self.direction_pressed.emit('southeast')

		elif event.key() == settings.keys['cursor_select']:
			self.direction_pressed.emit('select')

		super(ChessWidget, self).keyPressEvent(event)

	def toggleLabels(self):
		self.scene().toggleLabels()

	def toggleGuides(self):
		self.scene().toggleGuides()



if __name__ == '__main__':

	import sys

	from game_engine import DumbGameEngine

	app = QtGui.QApplication(sys.argv)


	widget = ChessWidget()
	icon = QtGui.QIcon('media/chess.ico')
	widget.setWindowIcon(icon)
	widget.setWindowTitle('ChessJay')
	widget.show()


	import db
	moves = []
	for row in db.Moves.select(1):
		moves.append(row)
	widget.loadGame(moves)

	sys.exit(app.exec_())
