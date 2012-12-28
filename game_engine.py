'''
Copyright Nate Carson 2012

'''

from util import tr


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
		self.string = (board.split()[0].replace('/','').
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

		self.x = AlgSquare.files.index(label[0]) + 1
		self.y = AlgSquare.ranks.index(label[1]) + 1
		self.label = label
	
	def __str__(self):
		return self.label
	
	@classmethod
	def generate(cls):
		
		for x in range(8):
			for y in range(8):
				yield cls(cls.files[x] + cls.ranks[y])


class Move(object):
	
	def __init__(self, move):
		
		self.ssquare = AlgSquare(move[:2])
		self.esquare = AlgSquare(move[2:4])
		self.promotion = move[4:5] or None
		self.move = move
	
	def __str__(self):
		return self.move
	

class GameMove(Move):
	
	def __init__(self, move):
		super(GameMove, self).__init__(move)
		self.movenum = None
		self.iswhite = None
		self.board_before = None
		self.board_after = None
		self.san = None
	
	@staticmethod
	def getGameMove(dbmove):
		game_move = GameMove(dbmove.move)
		game_move.movenum = dbmove.movenum
		game_move.iswhite = dbmove.iswhite
		game_move.board_before = BoardString(dbmove.board_before)
		game_move.board_after = BoardString(dbmove.board_after)
		game_move.san = dbmove.san
		return game_move
	
	def __str__(self):
		return '%s %s %s' %(self.move, self.movenum, self.iswhite)
	
	def __eq__(self, other):
		# XXX equality checks that is the same half move, not the same square
		if not other:
			return False
		return self.movenum == other.movenum and self.iswhite == other.iswhite

	def halfmove(self):
		return (self.movenum - 1 ) * 2 + int(not self.iswhite) + 1
	
	def reverse(self):
		'''Return a new move for taking back a move.'''
		
		move = GameMove(str(self.esquare) + str(self.ssquare) + (self.promotion or ''))
		move.movenum = self.movenum
		move.iswhite = self.iswhite 
		move.board_before = self.board_after
		move.board_after = self.board_before
		return move

	def getTarget(self):
		piece = self.board_before[self.esquare]
		if piece == BoardString.EMPTY_SQUARE:
			return None
		return piece

	def getSubject(self):
		piece = self.board_before[self.ssquare]
		if piece == BoardString.EMPTY_SQUARE:
			return None
		return piece
	



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
	
	def newGame(self, boardstring):
		self.boardstring = boardstring
		self.initial = boardstring
	
	def reset(self, boardstring):
		
		if boardstring is None:
			self.boardstring = BoardString(self.initial.string)
		else:
			self.boardstring = BoardString(boardstring.string)
	
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


	def castleRookMove(self, move):
		'''Returns the corresponding rook move if a given move is a castling one.'''

		subject, start, end = move.getSubject(), str(move.ssquare), str(move.esquare)

		for castle in [self.castles, self.castles_reversed]:
			if castle.has_key((subject, start, end)):
				return castle[(subject, start, end)]
		return None
	


class DumbGameEngine(AbstractGameEngine):
	# all moves are legal ... no checking

	def __init__(self):
		super(DumbGameEngine, self).__init__()
	
	def validateMove(self, move):
		# if our start square is empty
		if self.boardstring.isEmpty(move.ssquare):
			return False
		return True


class DBGameEngine(AbstractGameEngine):

	def __init__(self):
		super(DumbGameEngine, self).__init__()






if __name__ == '__main__':
	
	engine = DumbGameEngine()
	b = BoardString()
	engine.newGame(b)
	print engine
	m = Move('a3a4')
	engine.makeMove(m)
	print engine
	
