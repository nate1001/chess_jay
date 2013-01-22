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
        self.moves.newGame()

        self.fen = self.board.fen.text
        self.fen.setParentItem(self.board)
        self.fen.setPos(0, -40)


        #actions
        actions = [
            Action(self, "Play", settings.keys['mode_play'], tr("play game"), self.onShowMoves, 'media-playback-start'),
            Action(self, "Edit", settings.keys['mode_edit'], tr("set board position"), self.onShowPallete, 'document-edit'),
            Action(self, "Analyze", settings.keys['mode_analyze'], tr("analyze position"), self.onShowAnalyze, 'games-solve'),
        ]
        self._buttons = [b.graphics_button for b in actions]
        for button in self._buttons:
            button._checkable = True
            button._radio = True
        self.addActions(actions)

        size = self.moves.preferredSize()
        x, y = self.board.squares.size().width() + self.board.spacing, size.height()
        self._pack_actions(self.moves.actions(), x + 10, y + 10, False)

        self.onShowMoves()

        layout = QtGui.QGraphicsLinearLayout()
        buttons = self.getGraphicsButtonLayout()
        layout.addItem(buttons)
        layout.setAlignment(buttons, QtCore.Qt.AlignRight)
        layout.addItem(self.moves)
        layout.addItem(self.board)
        layout.setOrientation(QtCore.Qt.Vertical)
        self.setLayout(layout)
    
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
        self.board.editable = False
        self.moves.setEnabled(True)
        self.fen.fadeOut(settings.animation_duration)
        self._buttons[1].checked = False
        self._buttons[2].checked = False

    def onShowPallete(self):
        self.board.editable = True
        self.moves.setEnabled(False)
        self.fen.fadeIn(settings.animation_duration)
        self._buttons[0].checked = False
        self._buttons[2].checked = False

    def onShowAnalyze(self):
        self._buttons[0].checked = False
        self._buttons[1].checked = False



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


    widget.layout().preferredSize()
    view = View(scene)
    view.setGeometry(100, 50, 700, 600)
    view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    view.show()

    sys.exit(app.exec_())
