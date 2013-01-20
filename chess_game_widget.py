'''
Copyright Nate Carson 2013
'''

from PyQt4 import QtCore, QtGui

from board_widget import BoardWidget
from game_engine import ChessLibGameEngine
from moves_widget import MovesWidget
from util import tr, Action, GraphicsWidget
import settings

class ChessGameWidget(GraphicsWidget):

    def __init__(self):

        super(ChessGameWidget, self).__init__()


        #board
        self.board = BoardWidget()
        self.board.setParentItem(self)

        #moves
        game_engine = ChessLibGameEngine()
        self.moves = MovesWidget(self.board, game_engine)
        self.board.boardChanged.connect(self.moves.resetEngine)
        self.moves.setParentItem(self)
        self.moves.newGame()

        #fen
        self.board.fen.setParentItem(self)

        #actions
        actions = [
            Action(self, "Play", settings.keys['mode_play'], tr("play game"), self.onShowMoves, 'media-playback-start'),
            Action(self, "Edit", settings.keys['mode_edit'], tr("set board position"), self.onShowPallete, 'document-open')

        ]
        self.addActions(actions)

        self.moves.setPos(0, 0)
        size = self.moves.preferredSize()
        self.board.setPos(0, size.height())

        # set mode buttons
        play, edit = [a.graphics_button for a in actions]
        play.setParentItem(self)
        edit.setParentItem(self)
        rect = self.board.squares.boundingRect()
        play.setPos(rect.width(), 0)
        edit.setPos(rect.width() + play.size().width(), 0)

        # set moves actions
        for idx, action in enumerate(self.moves.actions()):
            action.graphics_button.setParentItem(self)
            x, y = self.board.squares.size().width() + self.board.spacing, size.height()
            offset = (action.graphics_button.preferredSize().height() + 5)* idx
            action.graphics_button.setPos(x, y + offset)

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

    rect = QtCore.QRectF(0, 0, 650, 550)
    view = View(scene)
    view.setGeometry(100, 50, 650, 550)
    view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    view.show()

    # FIXME have to call after view is shown to center 
    widget.moves.move_list.first()

    sys.exit(app.exec_())
