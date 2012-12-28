'''
Copyright Nate Carson 2012

'''
from PyQt4 import QtCore, QtGui

from db import Moves, Opening
from util import tr
from game_engine import BoardString, GameMove
import settings


class TableWidget(QtGui.QTableWidget):
	COLUMN_WIDTH = 60

	def __init__(self, toolbar):
		super(TableWidget, self).__init__()

		self.setColumnCount(len(self.labels))
		labels = []
		for idx, label in enumerate(self.labels):
			#if label.startswith('_'):
			#	self.setColumnHidden(idx, True)
			labels.append(tr(label))
			#self.setColumnWidth(idx, self.COLUMN_WIDTH)
		self.setHorizontalHeaderLabels(labels)

		self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)

		#self.itemActivated.connect(self.onItemSelected)
		#self.itemClicked.connect(self.onItemSelected)
		self.currentCellChanged.connect(self.onCellChanged)

		self.toolbar = toolbar
	

	def __getitem__(self, rowname):
		row, name = rowname
		column = self.labels.index(name)
		return self.item(row, column).text()



class OpeningTable(TableWidget):

	labels = [tr('Eco'), tr('Opening'), tr('Variation'), tr('Move')]

	moveSelected = QtCore.pyqtSignal(str)

	#FIXME
	def onMoveMade(self, move):

		rows = Opening.select(str(boardstring), str(move))
		self.setRowCount(len(rows))

		for idx, row in enumerate(rows):
			try:
				m = row.moves[halfmove]
			except IndexError:
				m = ''

			item = QtGui.QTableWidgetItem(row.eco)
			self.setItem(idx, 0, item)
			item = QtGui.QTableWidgetItem(row.opening)
			self.setItem(idx, 1, item)
			item = QtGui.QTableWidgetItem(row.variation)
			self.setItem(idx, 2, item)
			item = QtGui.QTableWidgetItem(m)
			self.setItem(idx, 3, item)
	

	def onItemSelected(self, item):
		row = item.row()
		move = str(self[row, 'move'])
		self.moveSelected.emit(move)


class VariationsTable(TableWidget):

	labels = [
		'San', 'Total', 'White', 'Draw', 'Black', 
		'_ssquare', '_esquare', '_subject', '_target'
	]

	moveSelected = QtCore.pyqtSignal(str, str, str, str)

	def __init__(self):
		super(VariationsTable, self).__init__()

		self._addAction('0', 'first_move', 'first move', self.onItemSelected)
	

	
	def onItemSelected(self, item):
		row = item.row()
		ssquare = self[row, '_ssquare']
		esquare = self[row, '_esquare']
		subject = self[row, '_subject']
		target = self[row, '_target']
		self.moveSelected.emit(ssquare, esquare, subject, target)

	
	def set(self, move):

		variations =  db.VariationStats.select(move.board_before)
		self.setRowCount(len(variations))

		for idx, variation in enumerate(variations):

			item = QtGui.QTableWidgetItem(variation.san)
			self.setItem(idx, 0, item)

			item = QtGui.QTableWidgetItem(str(variation.total))
			self.setItem(idx, 1, item)

			item = QtGui.QTableWidgetItem(str(variation.white_winr))
			self.setItem(idx, 2, item)

			item = QtGui.QTableWidgetItem(str(variation.drawr))
			self.setItem(idx, 3, item)

			item = QtGui.QTableWidgetItem(str(variation.white_loser))
			self.setItem(idx, 4, item)

			item = QtGui.QTableWidgetItem(str(variation.ssquare))
			self.setItem(idx, 5, item)

			item = QtGui.QTableWidgetItem(str(variation.esquare))
			self.setItem(idx, 6, item)

			item = QtGui.QTableWidgetItem(str(variation.subject))
			self.setItem(idx, 7, item)

			item = QtGui.QTableWidgetItem(str(variation.target))
			self.setItem(idx, 8, item)



class MoveList(list):
	
	def __init__(self):
		super(MoveList, self).__init__()

		self._current = None
	
	def toCurrentSlice(self):
		'''Return new move list up to but not including the current move.'''

		ml = MoveList()

		if not self._current:
			return ml
		if not self:
			raise ValueError("Moves list is emtpy")

		for move in self:
			ml.append(move)
			if move == self._current:
				return ml
		raise ValueError("current move was not found")
	
	def getNewMoveNum(self):

		# if not current we are on the first move
		if self._current is None:
			# if the first move starts with blacks go
			if self and self[0].iswhite == False:
				return 1, False
			else:
				return 1, True

		idx = self.index(self._current) + 1
		return (idx / 2 + 1, not(idx % 2))
	
	def diff(self, move):
		return self._current and self.index(move) - self.index(self._current)
	
	def setCurrent(self, move):
		
		if move is not None:
			# make sure its in there
			self.index(move)
		self._current = move
	

class MoveItem(QtGui.QTableWidgetItem):
	
	def __init__(self, move):
		super(MoveItem, self).__init__(move.san)
		self.move = move
	

class MoveTable(TableWidget):
	#FIXME empty cells f-up logic. Figure out how to disable them so they cannot be clicked or moved into.

	labels = ['White', 'Black']

	moveMade = QtCore.pyqtSignal(GameMove)

	def __init__(self, toolbar, board, game_engine):
		super(MoveTable, self).__init__(toolbar)

		self.board = board
		self.game_engine = game_engine
		self.move_list = None

		self.board.newMove.connect(self.onNewMove)

		self.toolbar.addAction("|<", 'first_move', tr("first move"), self.firstMove)
		self.toolbar.addAction("<", 'previous_move', tr("previous move"), self.previousMove)
		self.toolbar.addAction(">", 'next_move', tr("next move"), self.nextMove)
		self.toolbar.addAction(">|", 'last_move', tr("last move"), self.lastMove)
		self.toolbar.addAction("R", 'reload_board', tr("reload board"), self.reload)

	
	def newGame(self):
		b = BoardString()
		self.game_engine.newGame(b)
		self.setMoves([])
		self.setRowCount(0)
		self.board.setBoard(b)
		return b
	
	def loadGame(self, moves):
		b = self.newGame()
		self.setMoves(moves, setmove=False)
		return b
	
	def setEngine(self, game_engine):
		self.game_engine = game_engine
	
	def _setCurrent(self, cmp, diff):

		row, col = self.currentRow(), self.currentColumn()
		if row == -1 and col == -1:
			return False

		if col == cmp:
			row += diff
		col = int (not col)

		item = self.item(row, col)
		if not item:
			return None

		self.setCurrentCell(row, col)
		return True

	def reload(self):
		row, col = self.currentRow(), self.currentColumn()
		self.onCellChanged(row, col, row, col)

	def firstMove(self):
		self.setCurrentCell(-1, -1)

	def lastMove(self):
		l = len(self.move_list)
		if l == 0:
			return
		self.setCurrentCell(l / 2, (l+1) % 2)
		
	def nextMove(self):
		success = self._setCurrent(1, 1)
		# if we are trying to to cell with no move in it
		if success is None:
			return

		# if there is not a current cell and we have moves
		elif not success and self.move_list:
			# then goto the first move
			self.setCurrentCell(0,0)

		# else it already worked
		else:
			pass

	def previousMove(self):
		self._setCurrent(0, -1)

	def onNewMove(self, move):

		if not self.game_engine.validateMove(move):
			print 'did not validate'
			#TODO we could beep here
			return
		else:
			pass

		# let the engine make the move
		movenum, iswhite = self.move_list.getNewMoveNum()
		game_move = self.game_engine.makeMove(move, movenum, iswhite)

		# add the move into the list:
		# if this is the first move of the game
		if not self.move_list:
			self.appendMove(game_move)

		# else if this a new move to be appended to the game
 		elif self.move_list[-1].halfmove() + 1 == game_move.halfmove():
			self.appendMove(game_move)

		# else we have a new variation
		else:
			self.setMoves(self.move_list.toCurrentSlice(), setmove=False)
			self.move_list.current = game_move
			self.appendMove(game_move)

	def setMoves(self, moves, setmove=True):

		#clear out old items
		for i in range(self.rowCount()):
			white, black, = self.takeItem(i, 0), self.takeItem(i,1)

		self.move_list = MoveList()

		for game_move in moves:
			self.appendMove(game_move, setmove)
	
	def appendMove(self, game_move, setmove=True):

		self.move_list.append(game_move)

		item = MoveItem(game_move)
		l = len(self.move_list)
		self.setRowCount(l / 2 + 1)
		row, col = (l-1) / 2, int(not game_move.iswhite)

		self.setItem(row, col, item)
		if setmove:
			self.setCurrentCell(row, col)


	def _move_piece(self, move, uncapture=''):
		#We need this to check for castling moves so we can move the rook.
		self.board.movePiece(move, uncapture)
		rook = self.game_engine.castleRookMove(move)
		if rook:
			self.board.movePiece(rook, uncapture)

	def onCellChanged(self, cur_row, cur_col, prev_row, prev_col):

		# if no cell is selected go to initial board
		if cur_row == -1 and cur_col == -1:
			self.game_engine.reset(None)
			self.move_list.setCurrent(None)
			#self.moveMade.emit(None, None, None)
			self.board.setBoard(self.game_engine.initial)
			return

		item = self.item(cur_row, cur_col)
		if not item:
			return
		move = item.move
		diff = self.move_list.diff(move)

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
		self.move_list.setCurrent(move)
		self.moveMade.emit(move)
		
	


	


