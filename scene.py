'''
Copyright Nate Carson 2012
'''

from PyQt4 import QtCore, QtGui

from board import BoardWidget
from move_list import MoveTable
from util import tr, ToolBar, ScalingView, AspectLayout, SceneView, Action
import settings


class ChessScene(QtGui.QGraphicsScene):

	def __init__(self, game_engine):

		super(ChessScene, self).__init__()

		#board
		self.board = BoardWidget()
		self.addItem(self.board)

		#move_table 
		self.move_table = MoveTable(self.board, game_engine)
		self.board.boardChanged.connect(self.move_table.resetEngine)

		x, y = settings.boardSize() + 5, 0
		self.addItem(self.move_table)
		self.move_table.setPos(x, y)

		#opening_table
		#self.opening_table = OpeningTable()
		#self.move_table.moveMade.connect(self.opening_table.onMoveMade)

		#game engine
		self.setEngine(game_engine)
		self.newGame()

	def moveCursor(self, direction):
		self.board.moveCursor(direction)

	def cursorSelect(self):
		self.board.cursorSelect()

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
		rect = QtCore.QRectF(x, -80, w +70, h)

		sidebar = SceneView(self.scene, rect)
		sidebar.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

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
		board = SceneView(self.scene, rect)

		board.toolbar.addActions(self.scene.move_table.actions())
		board.toolbar.addActions(self.scene.board.actions())

		b = self.scene.board
		actions = [
			Action(self, "Guides", settings.keys['board_guides'], tr("toggle guides"), b.toggleGuides, ''),
			Action(self, "Labels", settings.keys['board_labels'], tr("toggle square labels"), b.toggleLabels, ''),
		]
		#board.toolbar.addActions(actions)
		
		#layout
		layout = QtGui.QHBoxLayout()
		layout.addWidget(board)
		layout.addWidget(sidebar)
		layout.setContentsMargins(0,0,0,0)
		layout.setAlignment(sidebar, QtCore.Qt.AlignRight)
		self.setLayout(layout)

	def onShowMoves(self):
		self.scene.board.setEditable(False)
		self.scene.move_table.setEnabled(True)

	def onShowPallete(self):
		self.scene.board.setEditable(True)
		self.scene.move_table.setEnabled(False)

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

	import sys

	from game_engine import DumbGameEngine

	app = QtGui.QApplication(sys.argv)

	widget = ChessWidget()
	icon = QtGui.QIcon('media/chess.ico')
	widget.setWindowIcon(icon)
	widget.setWindowTitle('ChessJay')

	size = widget.sizeHint()
	widget.setGeometry(100, 50, size.width(), size.height() + 16)
	widget.show()


	import db
	moves = []
	for row in db.Moves.select(1):
		moves.append(row)
	widget.loadGame(moves)

	sys.exit(app.exec_())
