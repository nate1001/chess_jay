
from PyQt4 import QtCore, QtGui
from util import TextWidget, GraphicsWidget, Action, tr, ToolBar, GraphicsButton
from game_engine import GameMove, BoardString
import settings

class MoveItem(TextWidget):

    def __init__(self, move):
        super(MoveItem, self).__init__(str(move))

        self.gamemove = move

        #size = QtCore.QSizeF(self.width, self.height)
        #self.setMaximumSize(size)

        #self.box.setRect(
        #   -self.padding,
        #   -self.padding,
        #   self.width + self.padding,
        #   self.height + self.padding)

    def __repr__(self):
        return "MoveItem(%s)" % repr(str(self))

    def setWhite(self):
        self.box.setBrush(QtGui.QColor('white'))
        self.box.setPen(QtGui.QPen(QtGui.QColor('black'), 1))

    def setBlack(self):
        self.box.setBrush(QtGui.QColor('black'))
        self.box.setPen(QtGui.QPen(QtGui.QColor('white'), 1))


class MovenumItem(TextWidget):


    def __init__(self, movenum):
        super(MovenumItem, self).__init__(' ' + str(movenum) + '.')
        self.movenum = movenum

        #size = QtCore.QSizeF(self.width, self.height)
        #self.setMaximumSize(size)

    def __repr__(self):
        return "MoveNumItem(%s)" % repr(str(self))


class PagingList(GraphicsWidget):

    padding = 7
    height = 30
    
    def __init__(self, width):
        super(PagingList, self).__init__()

        self._items = []
        self._selected = None
        self._width = width

        #self.box = QtGui.QGraphicsRectItem()
        #self.box.setPen(QtGui.QPen(settings.square_outline_color, 1))
        #self.box.setParentItem(self)
        #self.box.setRect(0,0, width, 50)

    
    def __iter__(self):
        for item in self._items:
            yield item

    def append(self, item):

        item.setParentItem(self)
        item.itemSelected.connect(self.onItemSelected)

        last = self._items[-1] if self._items else None
        if last:
            x = last.pos().x() + last.preferredSize().width() + self.padding
        else:
            x = 0
        item.setPos(x, self.padding)
        self._items.append(item)
    
    def pop(self):
        item = self._items.pop()
        item.itemSelected.disconnect(self.onItemSelected)
        item.setParentItem(None)
        if self.scene():
            self.scene().removeItem(item)
        return item
    
    def clear(self):
        try:
            while True:
                self.pop()
        except IndexError:
            pass
        
    def onItemSelected(self, item):
        if self._selected:
            self._selected.setSelected(False)
        self._selected = item
        item.setSelected(True)
    
        # center of viewable area
        center = self._width / 2
        # center of the item to be centered
        center -= (item.preferredSize().width() + self.padding) / 2
        # offset of the item to the center
        xo = center - item.x()

        selected = item
        for item in self:
            pos = QtCore.QPointF(item.pos().x() + xo, self.padding)
            item.move(pos, settings.animation_duration)
            x, w = item.x(), item.text.boundingRect().width()
            # if we are outside the viewable area
            if x + xo < 0 or x + xo + w > self._width:
                item.fadeOut(settings.animation_duration)
            else:
                item.fadeIn(settings.animation_duration)

    def _get_offset(self, offset, emit):
        
        current = self._selected
        if current is None:
            return self.first()

        # throw out items that are not enabled
        enabled = [i for i in self._items if i.isEnabled()]
        idx = enabled.index(current)

        if idx + offset >= len(enabled) or idx + offset < 0:
            return None
        if emit:
            enabled[idx + offset].itemSelected.emit(enabled[idx + offset])
        return enabled[idx + offset]

    def current(self, emit=True):
        return self._get_offset(0, emit)

    def next(self, emit=True):
        return self._get_offset(1, emit)

    def previous(self, emit=True):
        return self._get_offset(-1, emit)
   
    def _get_idx(self, idx):
        enabled = [i for i in self._items if i.isEnabled()]
        if not enabled:
            return None
        enabled[idx].itemSelected.emit(enabled[idx])
        return enabled[idx]

    def first(self):
        return self._get_idx(0)

    def last(self):
        return self._get_idx(-1)
    
    def sizeHint(self, which, constraint=None):
        size = QtCore.QSizeF(self._width, self.height)
        if which == QtCore.Qt.PreferredSize:
            return size
        return size


class MovePagingList(PagingList):

    moveSelected = QtCore.pyqtSignal(GameMove, int)

    def __init__(self, board, width):
        super(MovePagingList, self).__init__(width)

        self._last_selected = None
        self.newGame(board, True)

        #TODO: investigate / add bug report for this behavior.
        #XXX
        # Move these out of MovePaginList because they add unwanted arguments in a nasty black magic way.
        # I thnk triggered action calls the callback something like:
        #
        # def onTriggered(self, calling_widget)
        #   try:
        #       self.callback(calling_widget)
        #   except:
        #       self.callback()
        # 
        # so if you have default keyword args they are happily overwritten with the calling widget.
        actions = [
            Action(self, "|<", settings.keys['move_first'], tr("first move"), self._onFirst , 'go-first'),
            Action(self, "<", settings.keys['move_previous'], tr("previous move"), self._onPrevious , 'go-previous'),
            Action(self, ">", settings.keys['move_next'], tr("next move"), self._onNext , 'go-next'),
            Action(self, ">|", settings.keys['move_last'], tr("last move"), self._onLast, 'go-last'),
        ]
        self.addActions(actions)

    def _onFirst(self): self.first()
    def _onPrevious(self): self.previous()
    def _onNext(self): self.next()
    def _onLast(self): self.last()


    def toCurrentSlice(self):
        '''Return new move list up to but not including the current move.'''
        if not self._selected:
            return []
        l, selected  = [], self._selected
        for item in self:
            if item is selected:
                break
            l.append(item)
        return l

    def append(self, move):

        dummy = super(MovePagingList, self).pop()
        item = MoveItem(move)
        item.itemSelected.connect(self.onMoveItemSelected)
        super(MovePagingList, self).append(item)

        self._setDummyMove(move.movenum, move.iswhite)

    def _setDummyMove(self, movenum, iswhite):

        if not iswhite:
            item = MovenumItem(movenum + 1)
            super(MovePagingList, self).append(item)
            item.setEnabled(False)

        item = MoveItem('   ')
        item.setEnabled(False)
        if iswhite:
            item.setBlack()
        else:
            item.setWhite()
        super(MovePagingList, self).append(item)

    def newGame(self, boardstring, iswhite):

        start = GameMove(
            'Start',
            0,
            False,
            None,
            boardstring,
            None,
            None,
            None,
            None
        )
        self.clear()
        self._setDummyMove(0, False)
        self.append(start)
        self._last_selected = None

    def onMoveItemSelected(self, item):
        last = self._last_selected
        diff = last and item.gamemove.halfmove - last.gamemove.halfmove
        self._last_selected = item

        self.moveSelected.emit(item.gamemove, diff)


class MovesWidget(GraphicsWidget):

    moveMade = QtCore.pyqtSignal(GameMove)
    gameLoaded = QtCore.pyqtSignal()

    def __init__(self, board, game_engine):
        
        super(MovesWidget, self).__init__()
        
        self.game_engine = game_engine
        self.board = board

        bstring = game_engine.position.fen.to_boardstring()
        self.move_list = MovePagingList(bstring, 312)

        self.move_list.moveSelected.connect(self.onMoveSelected)
        self.board.newMove.connect(self.onNewMove)

        actions = [
            Action(self, "New Game", settings.keys['game_new'], tr("New Game"), self.newGame, 'document-new'),
            Action(self, "Draw", settings.keys['game_draw'], tr("Offer Draw"), self.offerDraw, 'face-plain'),
            Action(self, "Resign", settings.keys['game_resign'], tr("Resign Game"), self.resignGame, 'face-sad'),
        ]
        self.addActions(actions)

        first, previous, next, last = [a.graphics_button for a in self.move_list.actions()]
        layout = QtGui.QGraphicsLinearLayout()
        layout.addItem(first)
        layout.addItem(previous)
        layout.addItem(self.move_list)
        layout.addItem(next)
        layout.addItem(last)

        self.setLayout(layout)

        size = self.layout().preferredSize()
        self.box = QtGui.QGraphicsRectItem()
        self.box.setPen(QtGui.QPen(settings.square_outline_color, .5))
        self.box.setParentItem(self)
        self.box.setRect(0,0, size.width(), size.height())

        # FIXME make list expand to space left over from buttons
        size = first.sizeHint(QtCore.Qt.PreferredSize)
        w = size.width() + 4 * 33

    def setEnabled(self, enabled):
        if enabled:
            self.fadeIn(settings.animation_duration)
        else:
            self.fadeOut(settings.animation_duration)

        for action in self.actions():
            action.setVisible(enabled)

    def newGame(self):
        b = BoardString()
        self.game_engine.newGame(b)
        self.move_list.newGame(b, True)
        self.board.setBoard(b)
        return b
    
    def loadGame(self, moves):

        b = self.newGame()
        self.move_list.newGame()
        for move in moves:
            self.move_list.append(move)
        self.gameLoaded.emit()
        return b

    def setEngine(self, game_engine):
        self.game_engine = game_engine
    
    def resetEngine(self, boardstring):
        self.game_engine.reset(boardstring)
    
    def onMoveSelected(self, move, diff):

        # one move backward from current
        if diff == -1:
            current = self.move_list.current(emit=False)
            self._move_piece(current.gamemove.reverse(), current.gamemove.captured)

        # one move forward from current or first move from inital
        elif diff == 1:
            self._move_piece(move)

        # everything else
        else:
            self.board.setBoard(move.board_after)

        self.moveMade.emit(move)

    def _move_piece(self, move, uncapture=''):
        #We need this to check for castling moves so we can move the rook.

        self.board.movePiece(move, uncapture)
        rook = self.game_engine.castleRookMove(move)
        if rook:
            self.board.movePiece(rook, uncapture)

    def onNewMove(self, move):

        if not self.game_engine.validateMove(move):
            print 'did not validate'
            #TODO we could beep here
            return
        else:
            pass
        # let the engine make the move
        game_move = self.game_engine.makeMove(move)
        self.move_list.append(game_move)
        self.next()

    def current(self):
        return self.move_list.current()
    
    def first(self):
        return self.move_list.first()

    def next(self):
        return self.move_list.next()

    def previous(self):
        return self.move_list.previous()

    def last(self):
        return self.move_list.last()

    def offerDraw(self):
        pass

    def resignGame(self):
        pass



if __name__ == '__main__':

    class View(QtGui.QGraphicsView):
        
        def __init__(self, scene):
            super(View, self).__init__(scene)

        def keyPressEvent(self, event):

            if event.key() == QtCore.Qt.Key_Escape:
                self.close()

            if event.key() == QtCore.Qt.Key_Return:
                engine = self.scene().moves.game_engine
                move = engine.position.get_legal_moves().next()
                self.scene().moves.onNewMove(move)


    class Scene(QtGui.QGraphicsScene):
        pass
        
    import sys
    app = QtGui.QApplication(sys.argv)

    from util import ScalingView
    from board_widget import BoardWidget
    from game_engine import ChessLibGameEngine, Move
    import db

    board = BoardWidget()
    game_engine = ChessLibGameEngine()
    game_engine.newGame('kaka')
    table = MovesWidget(board, game_engine)
    table.setPos(50, 50)

    moves = 'e4 e5 Nf3 Bd6 Nc3 Nf6 d3 O-O Bg5 Bb4 Be2 Bxc3+ bxc3 d6 O-O Bg4 d4 Bxf3 Bxf3 exd4 ' \
     'cxd4 Nc6 c3 Qd7 Bxf6 gxf6 Bg4 f5 Bxf5 Qe7 Qh5 Rfe8 Qxh7+ Kf8 Qh8#'
    #for san in moves.split()[:4]:
        #move = game_engine.sanToMove(san)
        #table.onNewMove(move)
    
    scene = Scene()
    scene.addItem(table)
    scene.moves = table
    size = table.move_list.preferredSize()
    
    rect = QtCore.QRectF(0, 0, 300, 100)
    #view = ScalingView(scene, rect)
    view = View(scene)
    view.setGeometry(200, 0, 700, 120)

    view.show()
    table.move_list.first()
    view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    view.centerOn(0, 150)

    sys.exit(app.exec_())
    

        
    
