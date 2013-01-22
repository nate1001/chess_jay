'''
Copyright Nate Carson 2013
'''

from PyQt4 import QtCore, QtGui

from board_widget import BoardWidget
from game_engine import ChessLibGameEngine
from moves_widget import MovesWidget
from fen_widget import FenWidget, FenTextItem
from util import tr, Action, GraphicsWidget
import settings

class ChessGameWidget(GraphicsWidget):

    def __init__(self):

        super(ChessGameWidget, self).__init__()


        #board
        self.board = BoardWidget()
        self.board.setParentItem(self)

        self.fen = self.board.fen.text
        self.fen.setParentItem(self)

        #moves
        game_engine = ChessLibGameEngine()
        self.moves = MovesWidget(self.board, game_engine)
        self.moves.setParentItem(self)
        self.moves.newGame()

        #actions
        self.addActions([
            Action(self, "Play", settings.keys['mode_play'], tr("play game"), self.onShowMoves, 'media-playback-start'),
            Action(self, "Edit", settings.keys['mode_edit'], tr("set board position"), self.onShowPallete, 'document-edit'),
            Action(self, "Analyze", settings.keys['mode_analyze'], tr("analyze position"), self.onShowMoves, 'games-solve'),

        ])

        self.moves.setPos(0, 0)
        size = self.moves.preferredSize()
        self.board.setPos(0, size.height())

        x = self.board.squares.size().width()
        self._pack_actions(self.actions(), x + 10, -40, True)

        x, y = self.board.squares.size().width() + self.board.spacing, size.height()
        self._pack_actions(self.moves.actions(), x, y + 10, False)

        self.onShowMoves()
    
    def _pack_actions(self, actions, x, y, is_horizontal):

        # set moves actions
        for idx, action in enumerate(actions):
            action.graphics_button.setParentItem(self)
            if is_horizontal:
                offset = (action.graphics_button.preferredSize().width() + 5)* idx
                action.graphics_button.setPos(x + offset, y)
            else:
                offset = (action.graphics_button.preferredSize().height() + 5)* idx
                action.graphics_button.setPos(x, y + offset)

    def onShowMoves(self):
        self.board.setEditable(False)
        self.moves.setEnabled(True)
        #self.fen.fadeOut(settings.animation_duration)
        self.fen.hide()

    def onShowPallete(self):
        self.board.setEditable(True)
        self.moves.setEnabled(False)
        #self.fen.fadeIn(settings.animation_duration)
        self.fen.show()



if __name__ == '__main__':

    class View(QtGui.QGraphicsView):
        def keyPressEvent(self, event):
            if event.key() == QtCore.Qt.Key_Escape:
                self.close()
    import sys

    app = QtGui.QApplication(sys.argv)
    scene = QtGui.QGraphicsScene()
    widget = ChessGameWidget()
    scene.addItem(widget)

    rect = QtCore.QRectF(0, -50, 650, 700)
    view = View(scene)
    view.setGeometry(100, 50, 700, 600)
    view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    view.show()

    sys.exit(app.exec_())
