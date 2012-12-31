
from PyQt4 import QtCore, QtGui


class RectItem(QtGui.QGraphicsRectItem):
	def __init__(self):
		super(RectItem, self).__init__()

		self.setRect(0, 0, 100, 100)
		self.setBrush(QtGui.QBrush(QtGui.QColor('blue')))



if __name__ == '__main__':

	class View(QtGui.QGraphicsView):
		def __init__(self, scene):
			super(View, self).__init__(scene)

		def keyPressEvent(self, event):
			if event.key() == QtCore.Qt.Key_Escape:
				self.close()

		def resizeEvent(self, event):

			old_side = min(event.oldSize().width(), event.oldSize().height())
			new_side = min(event.size().width(), event.size().height())
			if old_side == -1 or new_side == -1:
				return

			factor = float(new_side) / old_side 
			self.scale(factor, factor)

	
	import sys
	app = QtGui.QApplication(sys.argv)

	item = RectItem()
	scene = QtGui.QGraphicsScene()
	scene.addItem(item)
	view = View(scene)
	view.setGeometry(100, 100, 300, 300)
	view.show()

	sys.exit(app.exec_())

