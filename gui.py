'''
Copyright Nate Carson 2012

'''

from PyQt4 import QtCore, QtGui, QtSvg

import db
import data



	def setAttackSum(self, forces):
		for force in forces:
			self._squares[force.tid].setAttackSum(force.c_white, force.c_black)

	def setAttackSum(self, c_white, c_black):
		
		c_white, c_black = c_white or 0, c_black or 0

		factor = 30
		color = QtGui.QColor(
			min(128 + c_black * factor, 255),
			max(128 - (c_white + c_black) * (factor/2), 0),  
			min(128 + c_white * factor, 255)
		)
		'''

		val = (c_white - c_black) * 32
		o = abs(c_white) + abs(c_black) * 64
		color = QtGui.QColor(
			min(max(128 - val, 0), 255)
			,128
			,max(min(128 + val, 255), 0)
			,min(o, 255)
		)

		#self._piece and self._piece.setOpacity(255)
		#self._piece and self._piece.setZValue(100)
		self.setBrush(QtGui.QBrush(color))
		'''

	
	def setByMove(self, move):

		if self._current_move is None:
			self.setByString(move.boardstring())

		# if we are going forward one move
		elif self._current_move.halfmove() + 1 == move.halfmove():
			self.movePiece(move.start, move.end)

		# else re-init board
		else:
			self.setByString(move.boardstring())

		self._current_move = move



class MainWindow(QtGui.QMainWindow):

	def __init__(self):
		super(MainWindow, self).__init__()

		self.scene = BoardScene(settings.initial_pos)
		layout = QtGui.QHBoxLayout()
		#layout.addWidget(self.toolBox)
		self.view = ChessView(self.scene)
		layout.addWidget(self.view)

		self.widget = QtGui.QWidget()
		self.widget.setLayout(layout)

		self.setCentralWidget(self.widget)
		self.setWindowTitle("Chess Analyzer")

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
		
		self.move_dock = Dock(MoveList, 'Moves', self, 
			self.scene.setBoard, 
			self.scene.setAttacked, 
			self.scene.setProtected,
			self.scene.setAttackSum,
		)
		self.game_dock = Dock(GameList, 'Games', self, self.move_dock.items)


class Dock(QtGui.QDockWidget):
	
	def __init__(self, list_class, name, parent, *args):
		super(Dock, self).__init__(name, parent)
		self.items = list_class(self, *args)
		self.setWidget(self.items)
		parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, self)
		parent.view_menu.addAction(self.toggleViewAction())
	

class DBList(QtGui.QListWidget):
	def __init__(self, parent, *args):

		super(DBList, self).__init__(parent, *args)
		self.activated.connect(self.onActivate)
		self.currentRowChanged.connect(self.onRowChanged)
		self.load()
	
	def _init(self, *args):
		select = self.select(*args)

		self.data = [row for row in select]

		# clear any previous items
		while self.takeItem(0):
			pass
		self.addItems([str(row) for row in self.data])
		self.update()

	def onActivate(self, index):
		datum = self.data[index.row()]
		self.doActivate(datum)

	def onRowChanged(self, index):
		datum = self.data[index]
		self.doActivate(datum)
	
	def select(self):
		return self.klass.select()

	def doActivate(self, index):
		raise NotImplementedError

	def load(self, *args):
		raise NotImplementedError
	
	
class GameList(DBList):
	klass = db.Games

	def __init__(self, parent, move_list):
		super(GameList, self).__init__(parent)
		self.move_list = move_list

	def load(self):
		self._init()
	
	def doActivate(self, game):
		self.move_list.load(game.id)


class MoveList(DBList):
	klass = db.Moves

	def __init__(self, parent, callback, attacked_callback, protected_callback, attacksum_callback):
		super(MoveList, self).__init__(parent)
		self.callback = callback
		self.attacked_callback = attacked_callback
		self.protected_callback = protected_callback
		self.attacksum_callback = attacksum_callback

	def select(self, *args):
		return self.klass.select(args[0])
	
	def load(self, *args):
		if args:
			self._init(args)

	def doActivate(self, move):
		
		self.callback(move)

		forces = db.Force.select(move.fen)
		self.attacksum_callback(forces)

		#attacked = db.Attacked.select(move.fen)
		#self.attacked_callback(attacked)

		#protected = db.Protected.select(move.fen)
		#self.protected_callback(protected)




	
if __name__ == '__main__':

	import sys

	app = QtGui.QApplication(sys.argv)

	mainWindow = MainWindow()
	s = settings.board_size
	l = settings.square_size
	mainWindow.setGeometry(100, 50, l + s*1.1 +100, l + s*1.2 + 100)
	mainWindow.show()

	sys.exit(app.exec_())
