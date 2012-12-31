
from PyQt4 import QtCore, QtGui


class RectItem(QtGui.QGraphicsRectItem):
	def __init__(self):
		super(RectItem, self).__init__()

		self.setRect(0, 0, 100, 100)
		self.setBrush(QtGui.QBrush(QtGui.QColor('blue')))


class View(QtGui.QGraphicsView):
	def __init__(self, scene):
		super(View, self).__init__(scene)

	def keyPressEvent(self, event):
		if event.key() == QtCore.Qt.Key_Escape:
			self.close()

if __name__ == '__main__':

	
	import sys
	app = QtGui.QApplication(sys.argv)

	item = RectItem()
	scene = QtGui.QGraphicsScene()
	scene.addItem(item)
	view = View(scene)
	view.show()

	sys.exit(app.exec_())

