
from PyQt4 import QtCore, QtGui, QtSvg

from game_engine import Piece

import settings


class GraphicsWidget(QtGui.QGraphicsWidget):

	def __init__(self):
		super(GraphicsWidget, self).__init__()
	
		self._anim_fade = QtCore.QPropertyAnimation(self, 'opacity')
		self._anim_move = QtCore.QPropertyAnimation(self, 'pos')
	
	def move(self, new, duration, old=None):

		if not old:
			old = self.pos()

		self._anim_move.setDuration(duration)
		self._anim_move.setStartValue(old)
		self._anim_move.setEndValue(new)
		self._anim_move.start()
	
	def fadeOut(self, duration):
		self._anim_fade.setDuration(duration)
		self._anim_fade.setStartValue(1)
		self._anim_fade.setEndValue(0)
		self._anim_fade.start()

	def fadeIn(self, duration):
		self._anim_fade.setDuration(duration)
		self._anim_fade.setStartValue(0)
		self._anim_fade.setEndValue(1)
		self._anim_fade.start()


class SquareWidget(GraphicsWidget):

	squareSelected = QtCore.pyqtSignal(GraphicsWidget)
	squareDoubleClicked = QtCore.pyqtSignal(GraphicsWidget)
	pieceDragStart = QtCore.pyqtSignal(GraphicsWidget)
	pieceDragEnd = QtCore.pyqtSignal(GraphicsWidget)
	pieceDragPause = QtCore.pyqtSignal(GraphicsWidget)
	pieceDragContinue = QtCore.pyqtSignal(GraphicsWidget)

	def __init__(self, algsquare):
		super(SquareWidget, self).__init__()

		islight = (algsquare.x + algsquare.y) % 2 == 1
		self.square = SquareItem(islight)
		self.label = SquareLabelItem(algsquare.label)
		self.algsquare = algsquare
		self._piece = None

		self.square.setParentItem(self)
		self.label.setParentItem(self)

		self.setGeometry(self.square.rect())
		self.setAcceptDrops(True)
		self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
	
	def __str__(self):
		return '<SquareWidget %s>' % self.algsquare
	
	def setSelected(self, selected):
		self.square.setSelected(selected)


	def addPiece(self, piece):
		piece.setParentItem(self)
		self._piece = piece

	def removePiece(self):

		if not self._piece:
			raise ValueError('square %s has no piece to remove' % self.algsquare)
		piece = self._piece
		self._piece.setParent(None)
		self._piece = None
		return piece
	
	def getPiece(self):
		return self._piece

	def mousePressEvent(self, event):
		if event.button() != QtCore.Qt.LeftButton:
			event.ignore()
			return
		self.squareSelected.emit(self)

	def dragEnterEvent(self, event):
		self.pieceDragContinue.emit(self)
		self.square.setHoverPiece(True)

	def dragLeaveEvent(self, event):
		self.pieceDragPause.emit(self)
		self.square.setHoverPiece(False)
	
	def dropEvent(self, event):
		self.square.setHoverPiece(False)
		self.squareSelected.emit(self)
		self.pieceDragEnd.emit(self)

	def mouseDoubleClickEvent(self, event):
		if event.button() != QtCore.Qt.LeftButton:
			event.ignore()
			return
		self.squareDoubleClicked.emit(self)

	def mouseMoveEvent(self, event):
		if not self._piece:
			event.ignore()
			return
		
		drag = QtGui.QDrag(event.widget())
		mime = QtCore.QMimeData()

		# if the parent is a square item
		#if hasattr(item, 'algsquare'):
		#	mime.setText(item.algsquare.label)
		# else its from the piece pallete
		#else:

		mime.setText(self.algsquare.label)
		drag.setMimeData(mime)
		self.pieceDragStart.emit(self)
		drag.exec_()



class SquareLabelItem(QtGui.QGraphicsSimpleTextItem):
	'''Item that shows the algbraic label for a square.'''


	def __init__(self, label):

		super(SquareLabelItem, self).__init__(label)

		offset = settings.square_size / 10
		self.setPos(offset, offset)
		
		if not settings.show_labels:
			self.hide()

		font = QtGui.QFont()
		font.setBold(True)
		self.setFont(font)

		self.setBrush(QtGui.QBrush(settings.square_label_color))
	



class SquareItem(QtGui.QGraphicsRectItem):
	'''
		GraphicsItem represents a square of a board and may contain a piece. 
		Sends square selected and hover drop signals for the board to handle.
	'''

	def __init__(self, islight):
		super(SquareItem, self).__init__()


		self._islight = islight
		self._hover_pen = None
		self._nohover_pen = None
		self._custom_color = None

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
			if self._islight:
				self.setBrush(QtGui.QBrush(settings.square_light_color))
			else:
				self.setBrush(QtGui.QBrush(settings.square_dark_color))
	

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
	

class PieceWidget(QtSvg.QGraphicsSvgItem, GraphicsWidget):
	'''Item that represents the piece on a square.'''

	name_map = {
		'wp': 'P', 'wn': 'N', 'wb': 'B', 'wr': 'R', 'wq': 'Q', 'wk': 'K',
		'bp': 'p', 'bn': 'n', 'bb': 'b', 'br': 'r', 'bq': 'q', 'bk': 'k',
	}

	def __init__(self, renderer):
		super(PieceWidget, self).__init__()

		self.name = self.name_map[renderer.name]
		#self.animation = MoveAnimation(self)

		self.setSharedRenderer(renderer)
	
		# scale the piece from its arbitrary svg size
		x = renderer.defaultSize().width()
		y = renderer.defaultSize().height()
		size = settings.square_size

		scalex, scaley = x / float(size), y / float(size)
		if scalex > .75 or scaley > .75:
			self.setScale(1 / (max([scalex, scaley]) + .25))

		self.setPos(size / 12, size / 12)
	
	def __str__(self):
		return '<PieceItem %s>' % self.name
	
	


	

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

	



if __name__ == '__main__':

	class View(QtGui.QGraphicsView):
		def __init__(self, scene):
			super(View, self).__init__(scene)

		def keyPressEvent(self, event):
			if event.key() == QtCore.Qt.Key_Escape:
				self.close()
	
	def onSelected(square):
		print 99, square

	def onDoubleClicked(square):
		print 88, square

	def onPieceDragStart(square):
		print 77, square

	def onPieceDragEnd(square):
		print 66, square

	def onPieceDragPause(square):
		print 55, square

	def onPieceDragContinue(square):
		print 44, square

	font = ChessFontDict(settings.chess_font)

	def makeSquare(label, piece):
		widget = SquareWidget(AlgSquare(label))
		widget.squareSelected.connect(onSelected)
		widget.squareDoubleClicked.connect(onDoubleClicked)
		widget.pieceDragStart.connect(onPieceDragStart)
		widget.pieceDragEnd.connect(onPieceDragEnd)
		widget.pieceDragPause.connect(onPieceDragPause)
		widget.pieceDragContinue.connect(onPieceDragContinue)

		if piece:	
			piece = PieceItem(font[piece])
			widget.addPiece(piece)

		return widget

	
	import sys
	from game_engine import AlgSquare


	app = QtGui.QApplication(sys.argv)

	a = makeSquare('e1', 'p')
	b = makeSquare('e2', 'K')
	c = makeSquare('e3', '')

	scene = QtGui.QGraphicsScene()
	scene.addItem(a)
	scene.addItem(b)
	scene.addItem(c)
	b.setPos(100, 100)
	c.setPos(0, 100)


	view = View(scene)
	view.setGeometry(100, 100, 300, 300)
	view.show()

	pos = QtCore.QPointF(300, 300)
	a._piece.fadeOut(1000)
	#a._piece.move(pos, 1000)

	sys.exit(app.exec_())

