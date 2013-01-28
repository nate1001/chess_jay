
from util import GraphicsWidget
from uci_engine import UciEngine

class UciEngineWidget(GraphicsWidget):
    
    def __init__(self):
        
        super(UciEngineWidget, self).__init__()

        self.engine = UciEngine(UciEngine.STOCKFISH)
        self.info = QtGui.QGraphicsSimpleTextItem()
        self.bestmove = QtGui.QGraphicsSimpleTextItem()
        self.status = QtGui.QGraphicsSimpleTextItem()

        self.engine.info_recieved.connect(self._onInfo)
        self.engine.bestmove_recieved.connect(self._onBestMove)

        self.info.setParentItem(self)
        self.bestmove.setParentItem(self)
        self.status.setParentItem(self)

        self.bestmove.setPos(0, 50)
        self.status.setPos(0, 100)

    def _onInfo(self, info):
        self.info.setText(str(info))

    def _onBestMove(self, info):
        self.bestmove.setText(str(info))
        fen = 'QQQ5/1K6/1Q6/8/5r2/4rk2/8/8 w - - 0 0'
        self.engine.start(fen, 10)

    def analyze(self):

        fen = 'QQQ5/1K6/1Q6/8/5r2/4rk2/8/8 w - - 0 0'
        self.engine.start(fen, 10)
        self.info.setText('waiting ...')
        self.bestmove.setText('waiting ...')

    def stop(self):
        self.engine.exit()
        self.info.setText('stopped')
        self.bestmove.setText('stopped')



if __name__ == '__main__':

    from PyQt4 import QtGui, QtCore
    import sys

    class View(QtGui.QGraphicsView):
        
        def __init__(self, scene, uci):
            super(View, self).__init__(scene)
            self.uci = uci

        def keyPressEvent(self, event):

            if event.key() == QtCore.Qt.Key_Escape:
                self.close()
            elif event.key() == QtCore.Qt.Key_Space:
                self.uci.analyze()
            elif event.key() == QtCore.Qt.Key_Q:
                self.uci.stop()
            super(View, self).keyPressEvent(event)

    app = QtGui.QApplication(sys.argv)

    widget = UciEngineWidget()
    scene = QtGui.QGraphicsScene()
    view = View(scene, widget)
    scene.addItem(widget)

    view.setGeometry(0,0,800,200)
    view.show()

    sys.exit(app.exec_())

