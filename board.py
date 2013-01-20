'''
Copyright Nate Carson 2012

'''

from PyQt4 import QtCore, QtGui

from square import SquareWidget, ChessFontDict, PieceWidget, GuideLabelItem
from game_engine import Move, AlgSquare, PaletteSquare, BoardString, Piece
from util import tr, GraphicsWidget, Action
import settings


class MoveError(Exception): pass


class BoardItem(QtGui.QGraphicsRectItem):

    def __init__(self):
        super(BoardItem, self).__init__()

        self._squares = {}
        self._font = None
        self.setRect(0,0, settings.boardSize(), settings.boardSize())

    
    def __getitem__(self, key):
        return self._squares[key]
    
    def __iter__(self):
        for item in self._squares.itervalues():
            yield item
    
    def __str__(self):
        return "<BoardItem %s>" % self.toString()

    def size(self):
        rect = self.boundingRect()
        return QtCore.QSizeF(rect.width(), rect.height())
    
    def getSquare(self, x, y):  
        for square in self:
            if square.algsquare.x == x and square.algsquare.y == y:
                return square
        raise KeyError((x, y))
    
    def setBoard(self, boardstring):

        self._font = ChessFontDict(settings.chess_font)

        #clear the old squares
        for square in self._squares.itervalues():
            if self.scene():
                self.scene().removeItem(square)
            else:
                square.setParentItem(None)
                square.square.setParentItem(None)
        self._squares = {}

        self._createSquares(str(boardstring))

    def toString(self):
        algsquares = list(AlgSquare.generate())
        string = list(BoardString.EMPTY_SQUARE * len(algsquares))
        for square in algsquares:
            idx = self._toboardnum(square.x, square.y)
            piece = self._squares[square.label].getPiece()
            if piece:
                string[idx] = piece.name
        return ''.join(string)
    
    def _createSquares(self, boardstring):
        # AlgSquares
        for algsquare in AlgSquare.generate():
            idx = self._toboardnum(algsquare.x, algsquare.y)
            symbol = boardstring[idx]
            square = self._createSquare(algsquare, symbol)

    def _toboardnum(self, x, y):
        return ((8-y) * 8) + x - 1 
    
    def _itemSetPos(self, item, x, y):
        side = settings.square_size
        item.setPos((x-1) * side , (8 - y) * side)

    def _createPiece(self, square, symbol):
        piece = PieceWidget(self._font[symbol])
        square.addPiece(piece)
    
    def _createSquare(self, algsquare, symbol):

        square = SquareWidget(algsquare)
        self._itemSetPos(square, algsquare.x, algsquare.y)
        square.setParentItem(self)
        self._squares[square.algsquare.label] = square

        if symbol != BoardString.EMPTY_SQUARE:
            self._createPiece(square, symbol)

        return square


class PaletteWidget(GraphicsWidget):
    def __init__(self, palette):
        super(PaletteWidget, self).__init__()
        palette.setParentItem(self)
        self.item = palette
    
    def size(self):
        rect = self.item.boundingRect()
        return QtCore.QSizeF(rect.width(), rect.height())
    
    def preferredSize(self):
        return self.size()


class PaletteItem(BoardItem):
    def __init__(self):
        super(PaletteItem, self).__init__()
        side = settings.square_size
        self.setRect(0,0, side * 2, side * 8)

    def _createSquares(self, boardstring):
        # PaletteSquares
        for idx, algsquare in enumerate(PaletteSquare.generate()):
            symbol = Piece.pieces[idx]
            square = self._createSquare(algsquare, symbol)
            square.square.setCustomColor(settings.COLOR_NONE)
    
    def _createCursor(self):
        pass

    def _itemSetPos(self, item, x, y):
        super(PaletteItem, self)._itemSetPos(item, x - 8, y)
    


class BoardWidget(GraphicsWidget):
    '''
        BoardWidget keeps tracks of the squares and moves pieces around.
        The newMove signal will be emitted when two squares with pieces are clicked
        or a piece is dragged to another square. It does not move the piece but delegates
        to the game widget to check the validity of the move. The game widget will then call
        the board widget to move the piece.
    '''

    newMove = QtCore.pyqtSignal(Move)
    boardChanged = QtCore.pyqtSignal(str)

    spacing = 10

    def __init__(self):
        super(BoardWidget, self).__init__()


        self.cursor = None
        self.squares = BoardItem()
        self.palette = PaletteWidget(PaletteItem())
        self.fen = FenTextWidget()

        self._selected_square = None
        self._editable = False

        self.boardChanged.connect(self.fen.setFen)
        self.squares.setParentItem(self)
        self.palette.setParentItem(self)
        self.palette.setPos(settings.boardSize()+ self.spacing, 0)

        actions = [
            Action(self, "New", settings.keys['board_new'], tr("reset to starting"), self.onNewBoard, 'document-new'),
            Action(self, "Clear", settings.keys['board_clear'], tr("remove pieces"), self.onClearPieces, 'edit-clear'),
        ]
        self.addActions(actions)
        new, clear = [a.graphics_button for a in self.actions()]
        new.setParentItem(self.palette)
        clear.setParentItem(self.palette)
        clear.setPos(new.size().width(), 0)
    
    def onClearPieces(self):
        empty = BoardString.EMPTY_SQUARE * 64
        self.squares.setBoard(empty)
    
    def onNewBoard(self):
        new = BoardString()
        self.squares.setBoard(new)

    def size(self):
        a = self.squares.boundingRect()
        b = self.palette.item.boundingRect()
        return QtCore.QSizeF(a.width() + b.width() + self.spacing, max(a.height(), b.height()))
    
    def sizeHint(self, which, constraint):
        if which == QtCore.Qt.PreferredSize:
            return self.size()
        return QtCore.QSizeF()

    def movePiece(self, move, uncapture=None):
        '''
            Makes the appropiate move or raises a value error.
            Does not call itself but waits for the parent widget to call it 
            after BoardWidget emits a newMove signal.

            uncapture will add back pieces for moving back in a game.
        '''
        
        fromsquare = self.squares[move.source.name]
        tosquare = self.squares[move.target.name]

        # if its a capture
        if tosquare.getPiece():
            captured = self._removePiece(tosquare)
        else:
            captured = None

        # remove the old piece
        try:
            piece = self._removePiece(fromsquare, nofade=True)
        except ValueError:
            raise MoveError(move)
            
        # put the piece on the new square
        tosquare.addPiece(piece)

        # we need to set zvalues lower for all squares except our piece's square
        # so we can see the animation move. Otherwise, depending on insertion order
        # the piece will be drawn under some squares.
        for square in self.squares:
            square.setZValue(-1)
        tosquare.setZValue(0)

        new = piece.pos()
        # we have to add the new position (which is a piece) to the square position difference
        # to account for the fact the pieces are not placed in the upper-left hand corner of the square
        old = fromsquare.pos() - tosquare.pos() + new

        duration = settings.animation_duration
        piece.move(new, duration, old=old)

        if uncapture:
            self._addPiece(fromsquare, uncapture)
    
    def _removePiece(self, square, nofade=False):
        piece = square.removePiece()
        if not nofade:
            piece.fadeOut(settings.animation_duration)
        return piece
    
    def _addPiece(self, square, symbol):
        piece = PieceWidget(self.squares._font[symbol])
        piece.fadeIn(settings.animation_duration)
        square.addPiece(piece)

    def onSquareDoubleClicked(self, square):
        if self._editable and not square.algsquare.isPalette() and square.getPiece():
            self._removePiece(square)
            self.boardChanged.emit(self.squares.toString())
        self._selected_square = None
        square.setSelected(False)
    
    def onSquareSelected(self, square):
        '''Catches squareSelected signal from squares and keeps track of currently selected square.'''

        tosquare, fromsquare = square, self._selected_square

        # if its the same square then deselect
        if fromsquare == tosquare:
            square.setSelected(False)
            self._selected_square = None


        # else if we have a selected square already then this square is a drop ... a move
        elif fromsquare is not None:
            ssquare = self._selected_square.algsquare
            esquare = square.algsquare

            # we cannot drop onto the palette
            if esquare.isPalette():
                tosquare.setSelected(False)
                return

            # else we have a new move
            else:
                # if we adding from the palette
                if ssquare.isPalette():
                    if self._editable:
                        if tosquare.getPiece():
                            self._removePiece(tosquare)
                        self._addPiece(tosquare, fromsquare.getPiece().name)
                        self.boardChanged.emit(self.squares.toString())
                    else:
                        # we cannot use the palette if we are not editing
                        pass

                # else it is a standard move
                else:
                    move = Move.from_uci(str(ssquare) + str(esquare))
                    # if we are editing then just move the piece
                    if self._editable:
                        self.movePiece(move)
                        self.boardChanged.emit(self.squares.toString())
                    # else mother may I
                    else:
                        self.newMove.emit(move)

                fromsquare.setSelected(False)
                self._selected_square = None

        # else its the first selection
        else:
            if not tosquare.getPiece():
                return
            tosquare.setSelected(True)
            self._selected_square = tosquare
    
    def toggleLabels(self):
        '''Shows algabraic labels inside the squares.'''
        
        settings.show_labels = not settings.show_labels
        for square in self.squares:
            square.label.setVisible(settings.show_labels)

    def toggleGuides(self):
        '''Shows file and rank guides at the side of the board.'''
        
        settings.show_guides = not settings.show_guides
        for square in self.squares:
            square.guide and square.guide.setVisible(settings.show_guides)
    
    def setEditable(self, editable):
        if editable:
            self.palette.fadeIn(settings.animation_duration)
            self.fen.fadeIn(settings.animation_duration)
        else:
            self.fen.fadeOut(settings.animation_duration)
            self.palette.fadeOut(settings.animation_duration)

        self._editable = editable
        for action in self.actions():
            action.setVisible(editable)

        self.cursor.usePalette(editable)
    
    def _getSquareAll(self, x, y):

        try:
            return self.squares.getSquare(x, y)
        except KeyError:
            return self.palette.item.getSquare(x, y)
    
    def _onMoveCursor(self, square):

        if square.algsquare.isPalette():
            pos = self.palette.mapToItem(self, square.pos())
        else:
            pos = square.pos()
        self.cursor.move(pos, settings.animation_duration)
    
    def setBoard(self, boardstring):
        self.squares.setBoard(str(boardstring))
        for square in self.squares:
            square.squareSelected.connect(self.onSquareSelected)
            square.squareDoubleClicked.connect(self.onSquareDoubleClicked)
            file, rank = square.algsquare.label
            if rank == '1':
                square.addGuide(GuideLabelItem(file))
            if file == 'a':
                square.addGuide(GuideLabelItem('  ' + rank))

        self.palette.item.setBoard(None)
        for square in self.palette.item:
            square.squareSelected.connect(self.onSquareSelected)

        if self.cursor is None:
            square = self.squares['e4']
            self.cursor = CursorWidget(self._getSquareAll, square.algsquare)
            self.cursor.setParentItem(self)
            self.cursor.setPos(square.pos())
            self.cursor.setZValue(2)
            self.cursor.moveCursor.connect(self._onMoveCursor)
    
    def cursorSetEnabled(self, enable):
        if enable:
            self.cursor.show()
        else:
            self.cursor.hide()
        self.cursor._enabled = enable
    

class FenTextWidget(GraphicsWidget):
    def __init__(self):
        super(FenTextWidget, self).__init__()
        self.item = FenTextItem()
        self.item.setParentItem(self)

    def setFen(self, fen):
        self.item.setPlainText(fen)

class FenTextItem(QtGui.QGraphicsTextItem):
    
    def __init__(self):
        super(FenTextItem, self).__init__()
        self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction | QtCore.Qt.TextSelectableByKeyboard )
        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable | QtGui.QGraphicsItem.ItemIsFocusable | QtGui.QGraphicsItem.ItemIsMovable);
    


class CursorWidget(GraphicsWidget):
    
    moveCursor = QtCore.pyqtSignal(SquareWidget)

    def __init__(self, getsquare_callback, algsquare):
        super(CursorWidget, self).__init__()
        self.item = CursorItem(algsquare)
        self.item.setParentItem(self)
        self.getsquare_callback = getsquare_callback

        self._use_palette = False

        direcs = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest']
        for direc in direcs:
            action = Action(
                self, direc, 
                settings.keys['cursor_%s' % direc], 
                tr("cursor %s"), 
                getattr(self, 'on%s' % direc.capitalize()),
                ''
            )
            self.addAction(action)
        action = Action(self, 'Cursor Select', settings.keys['cursor_select'], tr("select cursor square"), self.onCursorSelect, '')
        self.addAction(action)
    
    def usePalette(self, use):

        # get out the palette area if we are turning it off
        if not use and self.item._algsquare.isPalette():
            self.onWest()
            self.onWest()

        self._use_palette = use
    
    def _onDirec(self, xo, yo):

        old = self.item._algsquare
        x, y = old.x + xo, old.y + yo

        try:
            square = self.getsquare_callback(x, y)
            if square.algsquare.isPalette() and not self._use_palette:
                return
            self.moveCursor.emit(square)
        except KeyError:
            return
        self.item._algsquare = square.algsquare
    
    def onNorth(self):      self._onDirec(0, 1) 
    def onNortheast(self):  self._onDirec(1, 1) 
    def onEast(self):       self._onDirec(1, 0) 
    def onSoutheast(self):  self._onDirec(1, -1)    
    def onSouth(self):      self._onDirec(0, -1)    
    def onSouthwest(self):  self._onDirec(-1, -1)   
    def onWest(self):       self._onDirec(-1, 0)    
    def onNorthwest(self):  self._onDirec(-1, 1)    
    
    def onCursorSelect(self):

        algsquare = self.item._algsquare
        x, y = algsquare.x, algsquare.y
        square = self.getsquare_callback(x, y)
        board = self.parentWidget()
        board.onSquareSelected(square)
    

class CursorItem(QtGui.QGraphicsRectItem):
    '''Rectangle Item to be used as a cursor for selecting squares with the keyboard.'''

    def __init__(self, algsquare):
        super(CursorItem, self).__init__()

        self._algsquare = algsquare

        length = settings.square_size
        self.setRect(0, 0, length, length)
        self.setPen(QtGui.QPen(settings.cursor_color, length / 15))
        self._selected_pen = QtGui.QPen(settings.cursor_selected_color, length / 15)
        self._none_pen = QtGui.QPen(settings.COLOR_NONE)


if __name__ == '__main__':

    class View(QtGui.QGraphicsView):

        def __init__(self, scene):
            super(View, self).__init__(scene)

        def keyPressEvent(self, event):
            if event.key() == QtCore.Qt.Key_Escape:
                self.close()
            super(View, self).keyPressEvent(event)


    def onMove(move):
        print 11, move
    def onBoardChanged(board):
        print 22, board

    import sys

    app = QtGui.QApplication(sys.argv)
    scene = QtGui.QGraphicsScene()
    # XXX must construct view before adding stuff to scene or
    #     recursive ghost resize events occur.
    view = View(scene)

    string = str(BoardString())

    board = BoardWidget()
    board.setBoard(string)
    board.newMove.connect(onMove)
    board.boardChanged.connect(onBoardChanged)
    board.setEditable(True)
    board.toggleGuides()
    #board.toggleLabels()
    #board.cursorSetEnabled(False)
    scene.addItem(board)
    
    m = view.contentsMargins()
    size = board.sizeHint(QtCore.Qt.PreferredSize, None)
    width = size.width() + m.left() + m.right() + 1
    height = size.height() + m.top() + m.bottom() + 1
    view.setGeometry(0, 0, width, height)
    view.show()

    sys.exit(app.exec_())

