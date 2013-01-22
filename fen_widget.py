
from PyQt4 import QtCore, QtGui

from util import GraphicsWidget, GraphicsButton, RectF, SizeF
import settings
from square_widget import ChessFontDict, PieceItem
from game_engine import BoardString

import sys
sys.path.append('../python-chess/')
from chess import Piece, Square

class FenPartWidget(GraphicsWidget):

    updated = QtCore.pyqtSignal()

    def __init__(self):

        super(FenPartWidget, self).__init__()
        self.item = self.item_class()

        button = GraphicsButton(self.item)
        button.setParentItem(self)
        button.clicked.connect(self.onClicked)


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

class TurnWidget(FenPartWidget):

    item_class = TurnItem

    def onClicked(self, button):
        self.item.iswhite = not self.item.iswhite
        self.updated.emit()

    def setValue(self, value):
        if value == 'w':
            self.item.iswhite = True
        elif value == 'b':
            self.item.iswhite = False
        else:
            raise ValueError(value)

    @property
    def iswhite(self):
        return self.item.iswhite

    def __str__(self):
        return 'w' if self.item.iswhite else 'b'

    def sizeHint(self, which, constraint):
        return self.item.size() * 1.25


class CastleRightsWidget(GraphicsWidget):

    updated = QtCore.pyqtSignal()

    default = Piece.castleclass
    side = settings.square_size / 2

    def __init__(self, font):

        super(CastleRightsWidget, self).__init__()

        self._buttons = []
        layout = QtGui.QGraphicsLinearLayout()

        for idx, symbol in enumerate(self.default):
            piece = PieceItem(font[symbol])
            piece.scaleTo(self.side)
            button = GraphicsButton(piece, checkable=True, data=symbol)
            button.checked = True
            button.toggled.connect(self.onToggled)
            self._buttons.append(button)
            layout.addItem(button)

        self.setLayout(layout)

    def setValue(self, value):

        if value == '-':
            for button in self._buttons:
                button.checked = False
            return

        for castle in value:
            if castle not in Piece.castleclass:
                raise ValueError(value)

        for button in self._buttons:
            if button.data in value:
                button.checked = True
            else:
                button.checked = False

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

    def setValue(self, value):
        
        if value == '-':
            for button in self._buttons:
                button.checked = False
            return

        if len(str(value)) == 2:
            value = str(value)[0]

        if value not in Square.files:
            raise ValueError(value)
            
        for button in self._buttons:
            if value == button.data:
                button.checked = True
            else:
                button.checked = False

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
        self.setValue(value)
        self.updated.emit()

    def setValue(self, value):
        if not (value <= self.maximum or value >= self.minimum):
            raise ValueError(value)
        self.item.setText(str(value))

    def __str__(self):
        return str(self.item.text())


class FenTextWidget(GraphicsWidget):
    
    def __init__(self):
        super(FenTextWidget, self).__init__()
            
        text = QtGui.QGraphicsTextItem()
        text.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        text.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        text.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        text.setParentItem(self)
        self.text = text

    def size(self):
        return RectF(self.text.boundingRect()).toSizeF()

    def setPlainText(self, text):
        self.text.setPlainText(text)


class FenWidget(GraphicsWidget):

    changed = QtCore.pyqtSignal(str)
    
    def __init__(self, squares):

        super(FenWidget, self).__init__()

        font = ChessFontDict(settings.chess_font)

        self.squares = squares
        self.turn = TurnWidget()
        self.castle = CastleRightsWidget(font)
        self.enpassant = EnPassantWidget(font, self.turn)
        self.fiftymove = IntegerWidget(0, 0, 10**10)
        self.fullmove = IntegerWidget(1, 1, 10**10)

        layout = QtGui.QGraphicsLinearLayout()
        for widget in [self.turn, self.castle, self.enpassant, self.fiftymove, self.fullmove]:
            widget.updated.connect(self._onChanged)
            layout.addItem(widget)
        self.setLayout(layout)

        self.text = FenTextWidget() 
        self.changed.connect(self.text.setPlainText)

    def _onChanged(self):
        self.changed.emit(str(self))

    def setValue(self, fen):

        board, turn, castle, enpassant, fiftymove, fullmove = fen.split(' ')

        ### XXX do not set the squares
        #self.squares.setBoard(BoardString(board))

        self.turn.setValue(turn)
        self.castle.setValue(castle)
        self.enpassant.setValue(enpassant)
        self.fiftymove.setValue(fiftymove)
        self.fullmove.setValue(fullmove)

        fen = str(self)
        self.text.setPlainText(fen)
        self.changed.emit(fen)

    def setOrientation(self, orientation):

        self.layout().setOrientation(orientation)
        self.castle.layout().setOrientation(orientation)
        self.enpassant.layout().setOrientation(orientation)


    def __str__(self):
        return ' '.join(
        [
            str(i) for i in
            [   self.squares.toString().toFen(), 
                self.turn, 
                self.castle, 
                self.enpassant, 
                self.fiftymove, 
                self.fullmove
            ]
        ])


if __name__ == '__main__':

    import sys

    class View(QtGui.QGraphicsView):
        def __init__(self, scene):
            super(View, self).__init__(scene)

        def keyPressEvent(self, event):
            if event.key() == QtCore.Qt.Key_Escape:
                self.close()

    def onChanged(new_fen):
        sys.stdout.write('fen changed: ' + new_fen + '\n')

    app = QtGui.QApplication(sys.argv)

    sys.path.append('../python-chess/')
    from chess import Fen
    from board_widget import BoardItem

    f = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq c3 0 1'

    widget = FenWidget(BoardItem())
    widget.setValue(str(Fen()))
    widget.changed.connect(onChanged)

    scene = QtGui.QGraphicsScene()
    scene.addItem(widget)
    scene.addItem(widget.text)
    widget.text.setPos(0, 50)

    view = View(scene)
    view.setGeometry(100, 100, 800, 200)
    view.show()

    sys.exit(app.exec_())

