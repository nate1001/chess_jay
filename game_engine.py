'''
Copyright Nate Carson 2012

'''

from util import tr

#FIXME
import sys
sys.path.append('../python-chess/')

from chess import Position, Move, MoveError, SanNotation


class BoardString(object):
    
    EMPTY_SQUARE = '.'
    FEN_SEP = '/'

    def __init__(self, board=tr('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')):

        cls = self.__class__
        self.string = (str(board).split()[0].replace('/','').
                replace('8', cls.EMPTY_SQUARE * 8).
                replace('7', cls.EMPTY_SQUARE * 7).
                replace('6', cls.EMPTY_SQUARE * 6).
                replace('5', cls.EMPTY_SQUARE * 5).
                replace('4', cls.EMPTY_SQUARE * 4).
                replace('3', cls.EMPTY_SQUARE * 3).
                replace('2', cls.EMPTY_SQUARE * 2).
                replace('1', cls.EMPTY_SQUARE * 1)
        )
    
    def __str__(self):
        return self.string  

    def __iter__(self):
        return self.string.__iter__()
    
    def _getIdx(self, algsquare):
        return ((8 - algsquare.y) * 8) + algsquare.x - 1
    
    def __getitem__(self, algsquare):
        
        idx = self._getIdx(algsquare)
        return self.string[idx]
    
    def __setitem__(self, algsquare, value):
        idx = self._getIdx(algsquare)
        l = list(self.string)
        l[idx] = value
        self.string = ''.join(l)

    def makeMove(self, ssquare, esquare, promotion=''):
        if not promotion:
            self[esquare] = self[ssquare]
        else:
            self[move.esquare] = promotion
        self[ssquare] = self.__class__.EMPTY_SQUARE
    
    def isEmpty(self, algsquare):
        return self[algsquare] == self.__class__.EMPTY_SQUARE 

    def toFen(self):
        
        fen = ''
        for y in xrange(8):
            empties = 0
            for x in xrange(8):
                char = self.string[y * 8 + x]
                if char == self.EMPTY_SQUARE:
                    empties += 1
                else:
                    if empties:
                        fen += str(empties)
                        empties = 0
                    fen += char
            if empties:
                fen += str(empties)
            if y != 7:
                fen += self.FEN_SEP
        return fen


class Piece(object):
    
    pieces = tr('PBNRQKpbnrqk')
    WHITE_PAWN, WHITE_BISHOP, WHITE_KNIGHT, WHITE_ROOK, WHITE_QUEEN, WHITE_KING, \
    BLACK_PAWN, BLACK_BISHOP, BLACK_KNIGHT, BLACK_ROOK, BLACK_QUEEN, BLACK_KING  = range(12)

    PAWN, BISHOP, KNIGHT, ROOK, QUEEN, KING = range(6)

    @staticmethod
    def toSVGFont(piece):
        #FIXME if pieces were translated this will break the svg file naming convention
        
        if Piece.isWhite(piece):
            color = 'w' 
        else:
            color = 'b'
        return color + piece.lower() 
            
    @staticmethod
    def isWhite(piece):
        return list(Piece.pieces).index(piece) < 6  

    @staticmethod
    def toPieceClass(piece):
        #see if it pops
        list(Piece.pieces).index(piece)
        return list(Piece.pieces[6:]).index(piece)


                

class AlgSquare(object):
    
    files = tr('abcdefgh')
    ranks = tr('12345678')

    def __init__(self, label):
        
        if len(label) != 2:
            raise ValueError(label)

        cls = self.__class__

        self.x = cls.files.index(label[0]) + 1
        self.y = cls.ranks.index(label[1]) + 1
        self.label = label
    
    def isPalette(self):
        return False
    
    def __str__(self):
        return self.label
    
    @classmethod
    def generate(cls):
        
        for x in range(8):
            for y in range(8):
                yield cls(cls.files[x] + cls.ranks[y])



class PaletteSquare(AlgSquare):
#XXX this really belongs with board.py but its nice
#    to have it next to the orignal definition.

    files = AlgSquare.files + 'ij'

    def isPalette(self):
        return True

    @classmethod
    def generate(cls):
        
        for x in range(8, 10):
            for y in range(6):
                yield cls(cls.files[x] + cls.ranks[y])



#   class DumbGameEngine(AbstractGameEngine):
#       # all moves are legal ... no checking

#       def __init__(self):
#           super(DumbGameEngine, self).__init__()
#       
#       def validateMove(self, move):
#           return True
#           # if our start square is empty
#           if self.boardstring.isEmpty(move.ssquare):
#               return False
#           return True

#           return game_move



class GameMove(object):
    
    
    def __init__(self, san, movenum, iswhite, before, after, source, target, captured, piece):
        
        self.san = san
        self.movenum = movenum
        self.iswhite = iswhite
        self.fen_before = before
        self.fen_after = after
        self.source = source
        self.target = target
        self.captured = captured
        self.piece = piece

        self.is_start_pos = False

    @property
    def halfmove(self):
        return (self.movenum - 1 ) * 2 + int(not self.iswhite) + 1

    def reverse(self):
        '''Return a new move for taking back a move.'''

        return GameMove(
            self.san,
            self.movenum,
            self.iswhite,
            self.fen_after,
            self.fen_before,
            self.target,
            self.source,
            self.captured,
            self.piece
        )

    def __str__(self):
        return self.san
    
    def __eq__(self, other):
        # XXX equality checks that is the same half move, not the same square
        if not other:
            return False
        return self.movenum == other.movenum and self.iswhite == other.iswhite


class ChessLibGameEngine(object):
    
    def __init__(self):

        self.castles = {
            ('K', 'e1', 'g1'): Move.from_uci('h1f1'),
            ('K', 'e1', 'c1'): Move.from_uci('a1d1'),
            ('k', 'e8', 'g8'): Move.from_uci('h8f8'),
            ('k', 'e8', 'c8'): Move.from_uci('a8d8'),
        }

        self.castles_reversed  = {
            ('K', 'g1', 'e1'): Move.from_uci('f1h1'),
            ('K', 'c1', 'e1'): Move.from_uci('d1a1'),
            ('k', 'g8', 'e8'): Move.from_uci('f8h8'),
            ('k', 'c8', 'e8'): Move.from_uci('d8a8'),
        }
        self.position = None
        self._start_name = None

    @property
    def fen(self):
        return self.position and str(self.position.fen)
        

    def newGame(self, fen=None):

        #if we have a boardstring
        if fen:
            turn = self.position.fen.turn 
            self.position = Position(fen)
            self._start_name = "Custom"
        # else let it set to the default position
        else:
            self.position = Position()
            self._start_name = "Start"

    def makeMove(self, move):
        san = SanNotation(self.position, move)
        piece = self.position[move.source]
        captured = self.position[move.target]
        movenum = self.position.fen.full_move
        iswhite = self.position.fen.turn == 'w'
        before = self.fen
        self.position.make_move(move)
        after = self.fen

        game_move = GameMove(
            str(san),
            movenum,
            iswhite, 
            before, 
            after,
            move.source,
            move.target,
            captured,
            piece
        )
        return game_move

    def makeMoveFromSan(self, san):
        move = SanNotation.to_move(self.position, san)
        return self.makeMove(move)

    def sanToMove(self, san):
        return SanNotation.to_move(self.position, san)

    def validateMove(self, move):
        for m in self.position.get_legal_moves():
            if m == move:
                return True
        return False

    def castleRookMove(self, move):
        '''Returns the corresponding rook move if a given move is a castling one.'''

        piece, start, end = [str(move.piece), str(move.source), str(move.target)]

        for castle in [self.castles, self.castles_reversed]:
            if castle.has_key((piece, start, end)):
                return castle[(piece, start, end)]
        return None

    def toBoardstring(self):
        return BoardString(str(self.position.fen))

    def initialMove(self):
        '''Special game move to hold starting position.'''

        # FIXME: use iswhite
        start = GameMove(
            self._start_name,
            self.position.fen.full_move,
            self.position.fen.turn == 'w',
            None,
            self.fen,
            None,
            None,
            None,
            None
        )
        return start


if __name__ == '__main__':

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    engine = ChessLibGameEngine()
    engine.newGame(fen)
    move = Move.from_uci('e2e4')
    engine.makeMove(move)

    b = BoardString()
    print b.toFen()
