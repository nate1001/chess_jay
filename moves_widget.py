
from PyQt4 import QtCore, QtGui
from util import TextWidget, GraphicsWidget, Action, tr, ToolBar, GraphicsButton
from game_engine import GameMove, BoardString
import settings

class MoveItem(TextWidget):

	def __init__(self, move):
		super(MoveItem, self).__init__(move.san)

		self.gamemove = move

		#size = QtCore.QSizeF(self.width, self.height)
		#self.setMaximumSize(size)

		#self.box.setRect(
		#	-self.padding,
		#	-self.padding,
		#	self.width + self.padding,
		#	self.height + self.padding)


class MovenumItem(TextWidget):


	def __init__(self, movenum):
		super(MovenumItem, self).__init__(' ' + str(movenum) + '.')
		self.movenum = movenum

		#size = QtCore.QSizeF(self.width, self.height)
		#self.setMaximumSize(size)


class PagingList(GraphicsWidget):

	padding = 7
	height = 30
	
	def __init__(self, width):
		super(PagingList, self).__init__()

		self._items = []
		self._x = 0
		self._selected = None
		self._width = width

		#self.box = QtGui.QGraphicsRectItem()
		#self.box.setPen(QtGui.QPen(settings.square_outline_color, 1))
		#self.box.setParentItem(self)
		#self.box.setRect(0,0, width, 50)

	
	def __iter__(self):
		for item in self._items:
			yield item

	def append(self, item):

		self._items.append(item)
		item.setParentItem(self)
		item.setPos(self._x + self.padding, self.padding)
		item.itemSelected.connect(self.onItemSelected)
		self._x += item.preferredSize().width() + self.padding
	
	def pop(self):
		item = self._items.pop()
		item.itemSelected.disconnect(self.onItemSelected)
		self.scene().removeItem(item)
		self._x -= item.preferredSize().width()
		return item
	
	def clear(self):
		try:
			while True:
				self.pop()
		except IndexError:
			pass
		
	def onItemSelected(self, item):
		if self._selected:
			self._selected.setSelected(False)
		self._selected = item
		item.setSelected(True)
	
		# center of viewable area
		center = self._width / 2
		# center of the item to be centered
		center -= (item.preferredSize().width() + self.padding) / 2
		# offset of the item to the center
		xo = center - item.x()

		selected = item
		for item in self:
			pos = QtCore.QPointF(item.pos().x() + xo, self.padding)
			item.move(pos, settings.animation_duration)
			x, w = item.x(), item.text.boundingRect().width()
			# if we are outside the viewable area
			if x + xo < 0 or x + xo + w > self._width:
				item.fadeOut(settings.animation_duration)
			else:
				item.fadeIn(settings.animation_duration)

	def _get_offset(self, offset):
		
		current = self._selected
		if current is None:
			return self.first()


		# throw out items that are not enabled
		enabled = [i for i in self._items if i.isEnabled()]
		idx = enabled.index(current)

		if idx + offset >= len(enabled) or idx + offset < 0:
			return None
		enabled[idx + offset].itemSelected.emit(enabled[idx + offset])
		return enabled[idx + offset]

	def next(self):
		return self._get_offset(1)

	def previous(self):
		return self._get_offset(-1)
	
	def _get_idx(self, idx):
		enabled = [i for i in self._items if i.isEnabled()]
		if not enabled:
			return None
		enabled[idx].itemSelected.emit(enabled[idx])
		return enabled[idx]

	def first(self):
		return self._get_idx(0)

	def last(self):
		return self._get_idx(-1)
	
	def sizeHint(self, which, constraint=None):
		size = QtCore.QSizeF(self._width, self.height)
		if which == QtCore.Qt.PreferredSize:
			return size
		return size


class MovePagingList(PagingList):

	moveSelected = QtCore.pyqtSignal(GameMove, int)

	def __init__(self, width):
		super(MovePagingList, self).__init__(width)

		self._last_selected = None

		actions = [
			Action(self, "|<", settings.keys['move_first'], tr("first move"), self.first , 'go-first'),
			Action(self, "<", settings.keys['move_previous'], tr("previous move"), self.previous , 'go-previous'),
			Action(self, ">", settings.keys['move_next'], tr("next move"), self.next , 'go-next'),
			Action(self, ">|", settings.keys['move_last'], tr("last move"), self.last, 'go-last'),
		]
		self.addActions(actions)

	def toCurrentSlice(self):
		'''Return new move list up to but not including the current move.'''
		if not self._selected:
			return []
		l, selected  = [], self._selected
		for item in self:
			if item is selected:
				break
			l.append(item)
		return l

	def append(self, move):

		if move.iswhite:
			item = MovenumItem(move.movenum)
			super(MovePagingList, self).append(item)
			item.setEnabled(False)

		item = MoveItem(move)
		item.itemSelected.connect(self.onMoveItemSelected)
		super(MovePagingList, self).append(item)

	def clear(self):
		super(MovePagingList, self).clear()
		self._last_selected = None

	def onMoveItemSelected(self, item):
		last = self._last_selected
		diff = last and item.gamemove.halfmove() - last.gamemove.halfmove()
		self._last_selected = item

		self.moveSelected.emit(item.gamemove, diff)


class MovesWidget(GraphicsWidget):

	moveMade = QtCore.pyqtSignal(GameMove)
	gameLoaded = QtCore.pyqtSignal()

	def __init__(self, board, game_engine):
		
		super(MovesWidget, self).__init__()
		

		self.game_engine = game_engine
		self.board = board
		self.move_list = MovePagingList(312)

		self.move_list.moveSelected.connect(self.onMoveSelected)
		self.board.newMove.connect(self.onNewMove)

		actions = [
			Action(self, "New Game", settings.keys['game_new'], tr("New Game"), self.newGame, 'document-new'),
		]

		first = GraphicsButton('go-first')
		first.pushed.connect(self.move_list.first)
		next = GraphicsButton('go-next')
		next.pushed.connect(self.move_list.next)
		previous = GraphicsButton('go-previous')
		previous.pushed.connect(self.move_list.previous)
		last = GraphicsButton('go-last')
		last.pushed.connect(self.move_list.last)

		first, prev = [a.graphics_button for a in self.move_list.actions()[:2]]
		next, last = [a.graphics_button for a in self.move_list.actions()[2:]]

		layout = QtGui.QGraphicsLinearLayout()
		layout.addItem(first)
		layout.addItem(previous)
		layout.addItem(self.move_list)
		layout.addItem(next)
		layout.addItem(last)

		self.setLayout(layout)

		size = self.layout().preferredSize()
		self.box = QtGui.QGraphicsRectItem()
		self.box.setPen(QtGui.QPen(settings.square_outline_color, .5))
		self.box.setParentItem(self)
		self.box.setRect(0,0, size.width(), size.height())

		# FIXME make list expand to space left over from buttons
		size = first.sizeHint(QtCore.Qt.PreferredSize)
		w = size.width() + 4 * 33


	
	def setEnabled(self, enabled):
		if enabled:
			self.fadeIn(settings.animation_duration)
		else:
			self.fadeOut(settings.animation_duration)

		for action in self.actions():
			action.setVisible(enabled)

	def newGame(self):
		b = BoardString()
		self.game_engine.newGame(b)
		self.move_list.clear()
		self.board.setBoard(b)
		return b
	
	def loadGame(self, moves):

		b = self.newGame()
		self.move_list.clear()
		for move in moves:
			self.move_list.append(move)
		self.gameLoaded.emit()
		return b

	def setEngine(self, game_engine):
		self.game_engine = game_engine
	
	def resetEngine(self, boardstring):
		self.game_engine.reset(boardstring)
	
	def onMoveSelected(self, move, diff):

		# one move backward from current
		if diff == -1:
			next = self.move_list.next().gamemove
			self._move_piece(next.reverse(), next.getTarget())

		# one move forward from current or first move from inital
		elif diff == 1:
			self._move_piece(move)

		# everything else
		else:
			self.board.setBoard(move.board_after)

		self.game_engine.reset(move.board_after)
		self.moveMade.emit(move)

	def _move_piece(self, move, uncapture=''):
		#We need this to check for castling moves so we can move the rook.
		self.board.movePiece(move, uncapture)
		rook = self.game_engine.castleRookMove(move)
		if rook:
			self.board.movePiece(rook, uncapture)


	def onNewMove(self, move):

		if not self.game_engine.validateMove(move):
			print 'did not validate'
			#TODO we could beep here
			return
		else:
			pass

		# let the engine make the move
		#FIXME
		movenum, iswhite = self.move_list.getNewMoveNum()
		game_move = self.game_engine.makeMove(move, movenum, iswhite)

		# add the move into the list:
		# if this is the first move of the game
		if not self.move_list:
			self.move_list.appendMove(game_move)
	
	def first(self):
		return self.move_list.first()

	def next(self):
		return self.move_list.next()

	def previous(self):
		return self.move_list.previous()

	def last(self):
		return self.move_list.last()




if __name__ == '__main__':

	class View(QtGui.QGraphicsView):
		def keyPressEvent(self, event):
			if event.key() == QtCore.Qt.Key_Escape:
				self.close()

	class Scene(QtGui.QGraphicsScene):
		pass
	
	def onMoveSelected(move, diff):
		pass
		#print 11, move, diff
		
	import sys
	app = QtGui.QApplication(sys.argv)

	from util import ScalingView
	from board import BoardWidget
	from game_engine import DumbGameEngine
	import db

	board = BoardWidget()
	game_engine = DumbGameEngine()
	table = MovesWidget(board, game_engine)
	table.move_list.moveSelected.connect(onMoveSelected)
	moves = db.Moves.select(1)[:]
	table.loadGame(moves)
	table.setPos(50, 50)
	
	scene = Scene()
	scene.addItem(table)
	size = table.move_list.preferredSize()

	
	rect = QtCore.QRectF(0, 0, 300, 100)
	#view = ScalingView(scene, rect)
	view = View(scene)
	view.setGeometry(200, 0, 700, 120)

	view.show()
	table.move_list.first()
	view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
	view.centerOn(0, 150)

	sys.exit(app.exec_())
	

		
	
