
from PyQt4 import QtCore, QtGui

from util import GraphicsWidget, GraphicsButton, RectF, SizeF
import settings
from square_widget import ChessFontDict, PieceItem

import sys
sys.path.append('../python-chess/')
from chess import Piece, Square


class TurnItem(QtGui.QGraphicsRectItem):

    white = QtGui.QColor('white')
    black = QtGui.QColor('black')

    side = settings.square_size / 2


    def __init__(self):

        super(TurnItem, self).__init__()
        self._iswhite = None
        rect = QtCore.QRectF(0, 0, self.side, self.side)
        self.setRect(rect)

        self.iswhite = True

    def size(self):
        return QtCore.QSizeF(self.side, self.side)

    @property
    def iswhite(self):
        return self._iswhite

    @iswhite.setter
    def iswhite(self, iswhite):

        color = self.white if iswhite else self.black
        outline = self.black if iswhite else self.white

        self.setBrush(QtGui.QBrush(color))
        self.setPen(QtGui.QPen(outline))

        self._iswhite = iswhite


class TurnWidget(GraphicsWidget):

    updated = QtCore.pyqtSignal()

    def __init__(self):
        super(TurnWidget, self).__init__()
        self.turn = TurnItem()
        button = GraphicsButton(self.turn)
        button.setParentItem(self)
        button.clicked.connect(self.onClicked)

    def onClicked(self, button):
        self.turn.iswhite = not self.turn.iswhite
        self.updated.emit()

    @property
    def iswhite(self):
        return self.turn.iswhite

    def __str__(self):
        return 'w' if self.turn.iswhite else 'b'

    def sizeHint(self, which, constraint):
        return self.turn.size() * 1.25


class CastleRightsWidget(GraphicsWidget):

    updated = QtCore.pyqtSignal()

    def __init__(self, font):

        super(CastleRightsWidget, self).__init__()

        self._buttons = []
        side = settings.square_size / 2
        layout = QtGui.QGraphicsLinearLayout()

        for idx, symbol in enumerate(Piece.castleclass):
            piece = PieceItem(font[symbol])
            piece.scaleTo(side)
            button = GraphicsButton(piece, checkable=True, data=symbol)
            button.checked = True
            button.toggled.connect(self.onToggled)
            self._buttons.append(button)
            layout.addItem(button)

        self.setLayout(layout)

    def onToggled(self, castle, checked):
        self.updated.emit()

    def __str__(self):
        return ''.join([b.data for b in self._buttons if b.checked]) or '-'



class CharacterItem(QtGui.QGraphicsSimpleTextItem):
    
    def __init__(self, char):
        super(CharacterItem, self).__init__()
        self.setText(char)

    def size(self):
        side  = settings.square_size / 2
        return QtCore.QSizeF(side, side / 2)


class EnPassantWidget(GraphicsWidget):

    updated = QtCore.pyqtSignal()

    def __init__(self, font, turn):

        super(EnPassantWidget, self).__init__()

        self.turn = turn
        self._buttons = []


        layout = QtGui.QGraphicsLinearLayout()
        for idx, symbol in enumerate(Square.files):
            item = CharacterItem(symbol)
            button = GraphicsButton(item, checkable=True, data=symbol)
            button.toggled.connect(self.onToggled)
            self._buttons.append(button)
            layout.addItem(button)
        self.setLayout(layout)

    def onToggled(self, button, checked):
        for other in self._buttons:
            if other is not button and other.checked:
                other.checked = False
        self.updated.emit()

    def __str__(self):

        f = ''.join([b.data for b in self._buttons if b.checked])
        if f:
            rank = '5' if self.turn.iswhite else '3'
            return f + rank
        else:
            return '-'


class IntegerWidget(GraphicsWidget):

    updated = QtCore.pyqtSignal()
    
    def __init__(self, default, minimum, maximum):
        super(IntegerWidget, self).__init__()

        self.minimum = int(minimum)
        self.maximum = int(maximum)
        int(default)
        self.item = CharacterItem(str(default))
        button = GraphicsButton(self.item)
        button.setParentItem(self)

    def sizeHint(self, which, constraint):
        return self.item.size()

    def mousePressEvent(self, event):
        
        value = int(self.item.text())

        if event.button() == QtCore.Qt.LeftButton:
            value += 1
        elif event.button() == QtCore.Qt.RightButton:
            value -= 1
        else:
            event.ignore()
            return
        if value > self.maximum or value < self.minimum:
            return
        self.item.setText(str(value))
        self.updated.emit()

    def __str__(self):
        return str(self.item.text())


class FenTextItem(QtGui.QGraphicsTextItem):
    
    def __init__(self):
        super(FenTextItem, self).__init__()

        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)


class FenWidget(GraphicsWidget):

    updated = QtCore.pyqtSignal(str)
    
    def __init__(self, board):

        super(FenWidget, self).__init__()

        font = ChessFontDict(settings.chess_font)

        self.board = board
        self.board.board_changed.connect(self.onUpdated)

        self.turn = TurnWidget()
        self.castle = CastleRightsWidget(font)
        self.enpassant = EnPassantWidget(font, self.turn)
        self.fiftymove = IntegerWidget(0, 0, 100)
        self.fullmove = IntegerWidget(1, 1, 10**10)

        layout = QtGui.QGraphicsLinearLayout()
        for widget in [self.turn, self.castle, self.enpassant, self.fiftymove, self.fullmove]:
            widget.updated.connect(self.onUpdated)
            layout.addItem(widget)
        self.setLayout(layout)

        self.text = FenTextItem() 
        self.updated.connect(self.text.setPlainText)

        self.setOrientation(QtCore.Qt.Vertical)

    def setOrientation(self, orientation):

        self.layout().setOrientation(orientation)
        self.castle.layout().setOrientation(orientation)
        self.enpassant.layout().setOrientation(orientation)

    def onUpdated(self):
        self.updated.emit(str(self))

    def __str__(self):
        return ' '.join(
        [
            str(i) for i in
            [   self.board.squares.toString().toFen(), 
                self.turn, 
                self.castle, 
                self.enpassant, 
                self.fiftymove, 
                self.fullmove
            ]
        ])



if __name__ == '__main__':

    class View(QtGui.QGraphicsView):
        def __init__(self, scene):
            super(View, self).__init__(scene)

        def keyPressEvent(self, event):
            if event.key() == QtCore.Qt.Key_Escape:
                self.close()

       #def resizeEvent(self, event):
       #    old_side = min(event.oldSize().width(), event.oldSize().height())
       #    new_side = min(event.size().width(), event.size().height())
       #    if old_side == -1 or new_side == -1:
       #        return
       #    factor = float(new_side) / old_side 
       #    self.scale(factor, factor)

    
    import sys
    app = QtGui.QApplication(sys.argv)

    sys.path.append('../python-chess/')

    from chess import Fen
    from board_widget import BoardWidget, BoardString


    string = BoardString()
    board = BoardWidget()
    board.setBoard(string)

    widget = FenWidget(board)
    text = FenTextItem() 
    text.setPlainText(str(widget))
    widget.updated.connect(text.setPlainText)

    scene = QtGui.QGraphicsScene()
    scene.addItem(widget)
    scene.addItem(text)
    text.setPos(0, 50)
    view = View(scene)
    view.setGeometry(100, 100, 800, 200)
    view.show()

    sys.exit(app.exec_())

