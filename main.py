'''
Copyright Nate Carson 2012

'''

from PyQt4 import QtCore, QtGui

import db
import settings
from util import tr

from table_widget import VariationsTable

class MainWindow(QtGui.QMainWindow):
	
	def __init__(self, engine, scene, view):
		super(MainWindow, self).__init__()

		layout = QtGui.QHBoxLayout()

		self.view = view
		self.scene = scene

		layout.addWidget(self.view)

		self.widget = QtGui.QWidget()
		self.widget.setLayout(layout)

		self.setCentralWidget(self.widget)
		self.setWindowTitle(tr("ChessJay"))

		self.createActions()
		self.createMenus()
		self.createDocks()
	

	def createActions(self):

		self.action_exit = QtGui.QAction("Quit", self, 
				shortcut="Ctrl+Q", statusTip="Quit", 
				triggered=self.close)

		self.action_show_square_labels = QtGui.QAction("Square Labels", self, 
				checkable=True, checked=settings.show_labels, statusTip="", 
				triggered=self.view.toggleLabels)

		self.action_show_guides = QtGui.QAction("Guides", self, 
				checkable=True, checked=settings.show_guides, statusTip="", 
				triggered=self.view.toggleGuides)

	def createMenus(self):
		self.file_menu = self.menuBar().addMenu("&File")
		self.file_menu.addAction(self.action_exit)

		self.view_menu = self.menuBar().addMenu("&View")
		self.view_menu.addAction(self.action_show_square_labels)
		self.view_menu.addAction(self.action_show_guides)
	
	def createDocks(self):

		pass
		#Dock(self.scene.opening_table, self.tr('Openings'), self)


		#variations_table
		#variations_table = VariationsTable()
		#self.variations_table.moveSelected.connect(self.onVariationSelected)
		#Dock(variations_table, self.tr('Variations'), self)


class Dock(QtGui.QDockWidget):
	
	def __init__(self, widget, name, parent):
		super(Dock, self).__init__(name, parent)
		self.setWidget(widget)
		parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, self)
		parent.view_menu.addAction(self.toggleViewAction())
	

if __name__ == '__main__':

	import sys

	from game_engine import DumbGameEngine, GameMove
	from board import ChessScene, ChessView

	app = QtGui.QApplication(sys.argv)

	game_engine = DumbGameEngine()
	scene = ChessScene(game_engine)
	view = ChessView(scene)
	mainWindow = MainWindow(game_engine, scene, view)

    #widget = ChessWidget()
    #icon = QtGui.QIcon('media/chess.ico')
    #widget.setWindowIcon(icon)
    #widget.setWindowTitle('ChessJay')

	s = settings.board_size
	l = settings.square_size
	#mainWindow.setGeometry(100, 0, 1200, 600)

	icon = QtGui.QIcon('media/chess.ico')
	mainWindow.setWindowIcon(icon)
	mainWindow.setWindowTitle('ChessJay')
	mainWindow.show()

	import db
	moves = []
	for row in db.Moves.select(1):
		moves.append(GameMove.getGameMove(row))
	scene.loadGame(moves)

	sys.exit(app.exec_())

