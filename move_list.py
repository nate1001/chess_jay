'''
Copyright Nate Carson 2012

'''

from PyQt4 import QtCore, QtGui


from game_engine import GameMove, BoardString
from util import ToolBar, tr, ListItem, ListWidget, GraphicsWidget
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

	
	def clear(self):
		self._last_selected = None
		super(MoveList, self).clear()
	
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

		self.addItem(item, row, col)
		item.itemSelected.connect(self._onMoveSelected)


	def _onMoveSelected(self, move):
		diff = self._last_selected and (move.move.halfmove() - self._last_selected.halfmove())
		self._last_selected = move.move
		self.moveSelected.emit(move.move, diff)
		


class MoveTable(GraphicsWidget):

	moveMade = QtCore.pyqtSignal(GameMove)

	def __init__(self, board, game_engine):
		
		super(MoveTable, self).__init__()

		self.game_engine = game_engine
		self.board = board
		self.move_list = MoveList()

		self.move_list.moveSelected.connect(self.onMoveSelected)
		self.board.newMove.connect(self.onNewMove)

		self.toolbar = ToolBar()

		self.toolbar.addAction("|<", 'first_move', tr("first move"), self.firstMove, 'go-first')
		self.toolbar.addAction("<", 'previous_move', tr("previous move"), self.previousMove, 'go-previous')
		self.toolbar.addAction(">", 'next_move', tr("next move"), self.nextMove, 'go-next')
		self.toolbar.addAction(">|", 'last_move', tr("last move"), self.lastMove, 'go-last')
		#self.toolbar.addAction("R", 'reload_board', tr("reload board"), self.reload, 'edit-redo')

		proxy = QtGui.QGraphicsProxyWidget()
		proxy.setWidget(self.toolbar)

		layout = QtGui.QGraphicsLinearLayout()
		layout.setOrientation(QtCore.Qt.Vertical)

		layout.addItem(proxy)
		layout.addItem(self.move_list)

		layout.setContentsMargins(0,0,0,0)
		layout.setSpacing(0)
		self.setLayout(layout)

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
		return b

	def setEngine(self, game_engine):
		self.game_engine = game_engine
	
	def resetEngine(self, boardstring):
		self.game_engine.reset(boardstring)
	
	def onMoveSelected(self, move, diff):

		# one move backward from current
		if diff == -1:
			next = self.move_list[self.move_list.index(move) + 1]
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
		
	import sys
	app = QtGui.QApplication(sys.argv)

	import db
	ml = MoveList()
	moves = db.Moves.select(1)[:]
	for move in moves:
		ml.appendMove(move)

	scene = Scene()
	scene.addItem(ml)

	view = View(scene)
	view.setGeometry(100, 0, 820, 600)
	view.show()

	sys.exit(app.exec_())
	


