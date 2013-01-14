'''
Copyright Nate Carson 2012

'''

from PyQt4 import QtCore, QtGui


from game_engine import GameMove, BoardString
from util import ToolBar, tr, ListItem, ListWidget, GraphicsWidget, Action
import settings





class MoveItem(ListItem):

	width, height, padding = 50, 20, 2

	def __init__(self, move):
		super(MoveItem, self).__init__(move.san)
		self.move = move

		size = QtCore.QSizeF(self.width, self.height)
		self.setMaximumSize(size)

		self.box.setRect(
			-self.padding,
			-self.padding,
			self.width + self.padding,
			self.height + self.padding)


class MovenumItem(ListItem):

	width, height, padding = 30, 20, 5

	def __init__(self, move):
		super(MovenumItem, self).__init__(str(move.movenum) + '.')
		self.movnum = move.movenum

		size = QtCore.QSizeF(self.width, self.height)
		self.setMaximumSize(size)


class MoveList(ListWidget):
	
	moveSelected = QtCore.pyqtSignal(GameMove, int)

	def __init__(self):
		super(MoveList, self).__init__()
		self._last_selected = None

		actions = [
			Action(self, "|<", settings.keys['move_first'], tr("first move"), self.first , 'go-first'),
			Action(self, "<", settings.keys['move_previous'], tr("previous move"), self.previous , 'go-previous'),
			Action(self, ">", settings.keys['move_next'], tr("next move"), self.next , 'go-next'),
			Action(self, ">|", settings.keys['move_last'], tr("last move"), self.last, 'go-last'),
		]
		self.addActions(actions)

	def clear(self):
		super(MoveList, self).clear()
		self._last_selected = None
	
	def toCurrentSlice(self):
		'''Return new move list up to but not including the current move.'''
		if not self._idx:
			return None
		return self[:self._idx - 1]

	def appendMove(self, move):

		row = len(self) / 3

		if len(self) % 3 == 0:
			item = MovenumItem(move)
			self.addItem(item, row, 0)

		col = 1 if move.iswhite else 2
		item = MoveItem(move)
		item.itemSelected.connect(self.onMoveItemSelected)
		self.addItem(item, row, col)
	
	def onMoveItemSelected(self, item):
		diff = self._last_selected and item.move.halfmove() - self._last_selected.halfmove()
		self.moveSelected.emit(item.move, diff)
	
	def first(self):
		if not self:
			return None
		move = self[1]
		move.itemSelected.emit(move)

	def last(self):
		moves = self[:]
		moves[-1].itemSelected.emit(moves[-1])
	
	def _get(self, offset):
		
		current = self.current()
		if current is None:
			return self.first()
		else:
			current = current.move

		for item in self:
			if not hasattr(item, 'move'):
				continue
			if item.move.halfmove() == current.halfmove() + offset:
				item.itemSelected.emit(item)
				return item
				
	def next(self):
		return self._get(1)

	def previous(self):
		return self._get(-1)
	
	
		
class MoveTable(GraphicsWidget):

	moveMade = QtCore.pyqtSignal(GameMove)
	gameLoaded = QtCore.pyqtSignal()

	def __init__(self, board, game_engine):
		
		super(MoveTable, self).__init__()

		self.game_engine = game_engine
		self.board = board
		self.move_list = MoveList()

		self.move_list.moveSelected.connect(self.onMoveSelected)
		self.board.newMove.connect(self.onNewMove)
		self.move_list.setParentItem(self)

		actions = [
			Action(self, "New Game", settings.keys['game_new'], tr("New Game"), self.newGame, 'document-new'),
		]
		self.addActions(actions + self.move_list.actions())

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
			self.move_list.appendMove(move)
		self.gameLoaded.emit()
		return b

	def setEngine(self, game_engine):
		self.game_engine = game_engine
	
	def resetEngine(self, boardstring):
		self.game_engine.reset(boardstring)
	
	def onMoveSelected(self, move, diff):

		# one move backward from current
		if diff == -1:
			next = self.move_list.next()
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

	def reload(self):
		#FIXME
		pass

	def firstMove(self):
		#FIXME
		self.move_list.first()

	def lastMove(self):
		self.move_list.last()
		
	def nextMove(self):
		self.move_list.next()

	def previousMove(self):
		self.move_list.previous()


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
	table = MoveTable(board, game_engine)
	table.move_list.moveSelected.connect(onMoveSelected)
	moves = db.Moves.select(1)[:]
	table.loadGame(moves)
	
	scene = Scene()
	scene.addItem(table)
	size = table.move_list.preferredSize()
	print 11, size

	
	rect = QtCore.QRectF(0, 0, size.width(), size.height())
	view = ScalingView(scene, rect)
	view.setGeometry(200, 0, size.width(), 600)

	print 33, view.sizeHint()
	print 44, view.minimumSize()
	print 44, view.maximumSize()

	view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
	view.show()

	sys.exit(app.exec_())
	



