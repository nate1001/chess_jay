'''
Copyright Nate Carson 2012
'''

from PyQt4 import QtCore, QtGui

from board import BoardWidget
from moves_widget import MovesWidget
from util import tr, ToolBar, ScalingView, FocusingView, Action
import settings


class ChessScene(QtGui.QGraphicsScene):

	def __init__(self, game_engine):

		super(ChessScene, self).__init__()

		#board
		self.board = BoardWidget()
		self.addItem(self.board)

		#moves
		self.moves = MovesWidget(self.board, game_engine)
		self.board.boardChanged.connect(self.moves.resetEngine)
		self.addItem(self.moves)

		#fen
		self.addItem(self.board.fen)

		self.moves.setPos(0, 0)
		size = self.moves.preferredSize()
		self.board.setPos(0, size.height())

		#opening_table
		#self.opening_table = OpeningTable()
		#self.move_table.moveMade.connect(self.opening_table.onMoveMade)

		#game engine
		self.setEngine(game_engine)
		self.newGame()

		#actions
		actions = [
			Action(self, "Play", settings.keys['mode_play'], tr("play game"), self.onShowMoves, 'media-playback-start'),
			Action(self, "Edit", settings.keys['mode_edit'], tr("set board position"), self.onShowPallete, 'document-open')
		]
		#FIXME
		#self.addActions(actions)

		play, edit = [a.graphics_button for a in actions]
		self.addItem(play)
		self.addItem(edit)
		rect = self.board.squares.boundingRect()
		play.setPos(rect.width(), 0)
		edit.setPos(rect.width() + play.size().width(), 0)
		self.onShowMoves()

	def onShowMoves(self):
		self.board.setEditable(False)
		self.moves.setEnabled(True)

	def onShowPallete(self):
		self.board.setEditable(True)
		self.moves.setEnabled(False)

	def moveCursor(self, direction):
		self.board.moveCursor(direction)

	def cursorSelect(self):
		self.board.cursorSelect()

	def loadGame(self, moves):
		position = self.moves.loadGame(moves)
		self.moves.first()

	def newGame(self):
		self.moves.newGame()

	def setEngine(self, game_engine):
		self.moves.setEngine(game_engine)
	

	def onVariationSelected(self, from_square, to_square, subject, target):
		
		# go back on move
		last_move = self.moves_table.previousMove()
		self.setMove(last_move)
		self.moves_table.onMoveMade(last_move)

		# set the new move
		self.onNewMove(from_square, to_square, subject, target)



class ChessWidget(QtGui.QWidget):

	direction_pressed = QtCore.pyqtSignal(str)
	
	def __init__(self):
		super(ChessWidget, self).__init__()

		#scene
		game_engine = DumbGameEngine()
		self.scene = ChessScene(game_engine)

		#side_bar
		#FIXME bad rect / geometry
		side = settings.boardSize()
		side = self.scene.board.squares.rect().width()
		x = side + self.scene.board.spacing - 2
		w = self.scene.board.palette.item.rect().width()
		h = self.scene.board.palette.item.rect().height()
		rect = QtCore.QRectF(x, 0, w, h)

		sidebar = FocusingView(self.scene, self.scene.board.palette, rect)
		#sidebar.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

		#actions
		actions = [
			Action(self, "Play", settings.keys['mode_play'], tr("play game"), self.onShowMoves, 'media-playback-start'),
			Action(self, "Edit", settings.keys['mode_edit'], tr("set board position"), self.onShowPallete, 'document-edit')
		]

		self.addActions(actions)
		group = QtGui.QActionGroup(sidebar.toolbar)
		group.setExclusive(True)
		for action in actions:
			action.setCheckable(True)
			group.addAction(action)
		actions[0].activate(QtGui.QAction.Trigger)
		sidebar.toolbar.addActions(self.actions())

		#board
		side = settings.boardSize()
		rect = QtCore.QRectF(0, 0, side, side)
		board = FocusingView(self.scene, self.scene.board.squares, rect)

		board.toolbar.addActions(self.scene.moves.actions())
		board.toolbar.addActions(self.scene.board.actions())

		b = self.scene.board
		actions = [
			Action(self, "Guides", settings.keys['board_guides'], tr("toggle guides"), b.toggleGuides, ''),
			Action(self, "Labels", settings.keys['board_labels'], tr("toggle square labels"), b.toggleLabels, ''),
		]
		board.toolbar.addActions(actions)
		
		#layout
		layout = QtGui.QHBoxLayout()
		layout.addWidget(board)
		layout.addWidget(sidebar)
		layout.setContentsMargins(0,0,0,0)
		layout.setAlignment(sidebar, QtCore.Qt.AlignRight)
		self.setLayout(layout)


	def toggleLabels(self):
		self.scene.board.toggleLabels()

	def toggleGuides(self):
		self.scene.board.toggleGuides()

	def loadGame(self, moves):
		self.scene.loadGame(moves)

	def keyPressEvent(self, event):
		
		if event.key() == QtCore.Qt.Key_Escape:
			self.close()
		super(ChessWidget, self).keyPressEvent(event)



if __name__ == '__main__':

	class View(QtGui.QGraphicsView):
		def keyPressEvent(self, event):
			if event.key() == QtCore.Qt.Key_Escape:
				self.close()

	import sys
	from game_engine import DumbGameEngine

	app = QtGui.QApplication(sys.argv)

	#widget = ChessWidget()
	#icon = QtGui.QIcon('media/chess.ico')
	#widget.setWindowIcon(icon)
	#widget.setWindowTitle('ChessJay')

	game_engine = DumbGameEngine()
	scene = ChessScene(game_engine)

	rect = QtCore.QRectF(0, 0, 600, 550)

	view = ScalingView(scene, rect)
	view.setGeometry(100, 50, 600, 550)
	view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
	view.show()

	import db
	moves = []
	for row in db.Moves.select(1):
		moves.append(row)
	scene.loadGame(moves)

	sys.exit(app.exec_())
