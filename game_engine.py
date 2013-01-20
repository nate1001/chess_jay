'''
Copyright Nate Carson 2012

'''

from util import tr

#FIXME
import sys
sys.path.append('../python-chess/')

from chess import Position, Move, MoveError, SanNotation


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


class BoardString(object):
    
    EMPTY_SQUARE = '.'

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
        self.board = board
    
    def __str__(self):
        return self.string  
    
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



class IllegalMove(Exception): pass

class AbstractGameEngine(object):
    
    def __init__(self):
        self.boardstring = None

        self.castles  = {
            ('K', 'e1', 'g1'): Move('h1f1'),
            ('K', 'e1', 'c1'): Move('a1d1'),
            ('k', 'e8', 'g8'): Move('h8f8'),
            ('k', 'e8', 'c8'): Move('a8d8'),
        }

        self.castles_reversed  = {
            ('K', 'g1', 'e1'): Move('f1h1'),
            ('K', 'c1', 'e1'): Move('d1a1'),
            ('k', 'g8', 'e8'): Move('f8h8'),
            ('k', 'c8', 'e8'): Move('d8a8'),
        }
    
    def __str__(self):

        return str(self.boardstring)
    
    def validateMove(self, move):
        raise NotImplementedError

    def _makeMove(self, move):
        raise NotImplementedError
    
    def newGame(self, fen):
        print 99, fen
        #FIXME
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.boardstring = BoardString(fen)
        self.initial = self.boardstring
        self._fen = fen
    
    def reset(self, fen):
        print 88, fen
        
        self.boardstring = BoardString(str(fen))
        self._fen = fen
    
    def makeMove(self, move, movenum, iswhite):

        if not self.validateMove(move):
            raise IllegalMove(move)

        game_move = GameMove(move.move)
        game_move.board_before = BoardString(self.boardstring.string)

        self.boardstring.makeMove(move.ssquare, move.esquare, move.promotion)
        
        game_move.movenum = movenum
        game_move.iswhite = iswhite
        game_move.san = str(move)
        game_move.board_after = BoardString(self.boardstring.string)

        return game_move


    


class DumbGameEngine(AbstractGameEngine):
    # all moves are legal ... no checking

    def __init__(self):
        super(DumbGameEngine, self).__init__()
    
    def validateMove(self, move):
        return True
        print 11, type(move)
        # if our start square is empty
        if self.boardstring.isEmpty(move.ssquare):
            return False
        return True

        return game_move

class DBGameEngine(AbstractGameEngine):

    def __init__(self):
        super(DumbGameEngine, self).__init__()


class GameMove(object):
    
    
    def __init__(self, san, movenum, iswhite, before, after, source, target, captured, piece):
        
        self.san = san
        self.movenum = movenum
        self.iswhite = iswhite
        self.board_before = before
        self.board_after = after
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
            self.board_after,
            self.board_before,
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
        
        self.position = Position()

    def newGame(self, fen):
        self.position = Position()

    def reset(self, fen):
        self.position = Position()

    def makeMove(self, move):
        san = SanNotation(self.position, move)
        piece = self.position[move.source]
        captured = self.position[move.target]
        movenum = self.position.fen.full_move
        iswhite = self.position.fen.turn == 'w'
        before = self.position.fen.to_boardstring()
        self.position.make_move(move)
        after = self.position.fen.to_boardstring()

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
        

if __name__ == '__main__':

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    engine = ChessLibGameEngine()
    engine.newGame(fen)
    move = Move.from_uci('e2e4')
    engine.makeMove(move)
