'''
Copyright Nate Carson 2012

'''
from PyQt4 import QtCore, QtGui

from db import Moves, Opening
from util import tr
from game_engine import BoardString, Move
import settings


class TableWidget(QtGui.QTableWidget):
	COLUMN_WIDTH = 60

	def __init__(self):
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

		self.itemActivated.connect(self.onItemSelected)
		self.itemClicked.connect(self.onItemSelected)

		# layout
		self.container = QtGui.QWidget()
		self.toolbar = QtGui.QToolBar(self)
		layout = QtGui.QVBoxLayout(self.container)
		layout.addWidget(self.toolbar)
		layout.addWidget(self)
		layout.setContentsMargins(0,0,0,0)
	
	def _addAction(self, label, settings_key, tip, callback):

		self.toolbar.addAction(
			QtGui.QAction(
				label, 
				self, 
				shortcut=settings.keys[settings_key], 
				statusTip=tr(tip), 
				triggered=callback
		))
	



	def __getitem__(self, rowname):
		row, name = rowname
		column = self.labels.index(name)
		return self.item(row, column).text()



class OpeningTable(TableWidget):

	labels = [tr('Eco'), tr('Opening'), tr('Variation'), tr('Move')]

	moveSelected = QtCore.pyqtSignal(str)

	def onMoveMade(self, boardstring, move, halfmove):

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

		self.current = None
	
	
	def byKey(self, movenum, iswhite):
		for move in self:
			if move.movenum == movenum and move.iswhite == iswhite:
				return move
		raise KeyError(movenum, iswhite)
	
	def toCurrentSlice(self):
		'''Return new move list up to but not including the current move.'''
		ml = MoveList()
		if self.current == None or not self:
			raise ValueError("Moves list is emtpy")

		for move in self:
			ml.append(move)
			if move == self.current:
				return ml
		raise ValueError("current move was not found")
	
	def first(self):
		if not self:
			return None
		return self[0]

	def last(self):
		if not self:
			return None
		return self[-1]
	
	def next(self):
		if not self.current and not self:
			return None
		elif not self.current:
			return self[0]

		idx = self.index(self.current)
		try:
			return self[idx + 1]
		except IndexError:
			return None
	
	def previous(self):
		if not self:
			return None
		idx = self.index(self.current)
		# if we are not on the first move
		if idx > 0:
			return self[idx - 1]
		return None
	
	

class MoveTable(TableWidget):

	labels = ['White', 'Black']

	moveMade = QtCore.pyqtSignal(str, str, int)

	def __init__(self, board, game_engine):
		super(MoveTable, self).__init__()

		self.board = board
		self.game_engine = game_engine
		self.move_list = None

		self.board.newMove.connect(self.onNewMove)

		self._addAction("|<", 'first_move', tr("first move"), self.firstMove)
		self._addAction("<", 'previous_move', tr("previous move"), self.previousMove)
		self._addAction(">", 'next_move', tr("next move"), self.nextMove)
		self._addAction(">|", 'last_move', tr("last move"), self.lastMove)
		self._addAction("R", 'reload_board', tr("reload board"), self.reload)

		self.castles  = {
			('K', 'e1', 'g1'): Move('h1f1'),
			('K', 'e1', 'c1'): Move('a1d1'),
			('k', 'e8', 'g8'): Move('h8f8'),
			('k', 'e8', 'c8'): Move('a8d8'),
		}

		self.castles_reversed  = {
			('K', 'g1', 'e1'): Move('f1h1'),
			('K', 'c1', 'e1'): Move('d1a1'),
			('k', 'g8', 'e8'): Move('f8h8'),
			('k', 'c8', 'e8'): Move('d8a8'),
		}
	
	def newGame(self):
		b = BoardString()
		self.game_engine.newGame(b)
		self.move_list = MoveList()
		return b
	
	def loadGame(self, moves):
		b = self.newGame()
		self.setMoves(moves, setmove=False)
		return b
	
	def setEngine(self, game_engine):
		self.game_engine = game_engine

	def reload(self):

		self._set_move(self.move_list.current)

	def firstMove(self):
		self._set_move(self.move_list.first(), first=True)

	def lastMove(self):
		self._set_move(self.move_list.last())

	def nextMove(self):
		self._set_move(self.move_list.next())

	def previousMove(self):
		self._set_move(self.move_list.current)

	def onItemSelected(self, item):
		movenum = item.row() + 1
		iswhite = item.column() == 0
		game_move = self.move_list.byKey(movenum, iswhite)
		self._set_move(game_move)
	
	def onNewMove(self, move):
		if not self.game_engine.validateMove(move):
			print 'did not validate'
			#TODO we could beep here
			return

		# let the engine make the move
		game_move = self.game_engine.makeMove(move)

		# add the move into the list:
		# if this is the first move of the game
		if not self.move_list.current:
			self.appendMove(game_move)

		# else if this a new move to be appended to the game
 		elif self.move_list.last().halfmove() + 1 == game_move.halfmove():
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
		item = QtGui.QTableWidgetItem(game_move.san)

		# XXX this will not take into account games that do not start from move 1
		# But, does it make sense to allow a game fragment, with a starting move other than 1?
		# FIXME will not be able to show move if this did happen.
		self.setRowCount(len(self.move_list)/2 + 1)

		self.setItem( game_move.movenum - 1, int(not game_move.iswhite), item)

		if setmove:
			self._set_move(game_move)
	
	def _move_piece(self, move, uncapture=''):
		#We need this to check for castling moves so we can move the rook.
		
		subject, start, end = move.getSubject(), str(move.ssquare), str(move.esquare)

		self.board.movePiece(move, uncapture)

		for castle in [self.castles, self.castles_reversed]:
			if castle.has_key((subject, start, end)):
				rook = castle[(subject, start, end)]
				self.board.movePiece(rook, uncapture)
	
	def _set_move(self, game_move, first=False):

		if not game_move:
			return
		#make sure the move is in the move list
		self.move_list.byKey(game_move.movenum, game_move.iswhite)

		self.setCurrentCell(game_move.movenum - 1, int(not game_move.iswhite))

		current = self.move_list.current

		#update the board

		# if the move is going backwards by one halfmove
		if current and current.halfmove() - game_move.halfmove() == 0:
			self._move_piece(game_move.reverse(), game_move.getTarget())
			self.game_engine.reset(game_move, game_move.board_before)
			current = self.move_list.previous()
			self.move_list.current = current

		# if we want the very first move
		elif first:
			self.board.setBoard(game_move.board_before)
			self.game_engine.reset(game_move, game_move.board_before)
			self.move_list.current = None

		else:
			# if we are on the first move of the game
			if not current and game_move.halfmove() == 1:
				self.game_engine.reset(game_move, game_move.board_after)
				self._move_piece(game_move)

			# if it is the same move
			elif game_move == current:
				# reset anyways as it might be a reload
				self.board.setBoard(game_move.board_after)
				self.game_engine.reset(game_move, game_move.board_after)

			# else if this is one move forward
			elif current and current.halfmove() == game_move.halfmove() - 1: 
				self._move_piece(game_move)
				self.game_engine.reset(game_move, game_move.board_after)

			# else reset the board since there are multiple moves in between
			else:
				self.board.setBoard(game_move.board_after)
				self.game_engine.reset(game_move, game_move.board_after)

			self.move_list.current = game_move

		self.moveMade.emit(game_move.board_before.board, game_move.move, game_move.halfmove())

	


