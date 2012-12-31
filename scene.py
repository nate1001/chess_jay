
class ChessScene(QtGui.QGraphicsScene):

	def __init__(self, game_engine):

		super(ChessScene, self).__init__()

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
		layout.setContentsMargins(0,0,0,0)
		layout.setSpacing(0)
	
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
		layout.setContentsMargins(0,0,0,0)
		layout.setSpacing(0)
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

		w = settings.board_size
		h = settings.board_size 

		board = BoardView(self.scene, w, h)
		sidebar = SideBarView(self.scene, w, h)
		
		layout = QtGui.QHBoxLayout()
		layout.addWidget(board)
		layout.addWidget(sidebar)
		self.setLayout(layout)
		#fixed
		layout.setSizeConstraint(3)
		layout.setContentsMargins(0,0,0,0)

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
