'''
Copyright Nate Carson 2012

'''

import psycopg2

import settings
from game_engine import Move


class Conn(object):

	def __init__(self):
		self.conn = psycopg2.connect('dbname=' + settings.dbname)

		print ('''
			set DYNAMIC_LIBRARY_PATH to '$libdir:%s' 
			; load 'libpgchess';
		''' % settings.dbchesslib)

		cursor = self.conn.cursor()
		cursor.execute('''
			set DYNAMIC_LIBRARY_PATH to '$libdir:%s' 
			; load 'libpgchess';
		''' % settings.dbchesslib)

	def execute(self, sql, *args):

		cursor = self.conn.cursor()
		if not args:
			sql = cursor.mogrify(sql)
		else:
			sql = cursor.mogrify(sql, *args)
		cursor.execute(sql)
		for row in cursor.fetchall():
			yield row



class Table(object):
	
	conn = None

	@classmethod
	def select(cls, *args):

		if Table.conn is None:
			Table.conn = Conn()
		
		select = getattr(cls, '_select' + str(len(args)))

		rows = []
		for row in Table.conn.execute(select, args):
			rows.append(cls(row))
		return rows

	
	def __init__(self, row):
		
		for i, field in enumerate(self._rows):
			setattr(self, field, row[i])
				
		self._data = row


class Games(Table):
	
	_rows = ['id', 'event', 'site', 'date_', 'round', 'white', 'black']
	_select0 = 'select games.* from games()'
	_select1 = 'select games.* from games(%s)'

	def __str__(self):
		return '%s vs. %s' %(self.white, self.black)


class Moves(Table):
	
	_rows = [
			'id', 'game_id', 'movenum', 'iswhite', 'move', 'san', 'board_before', 'board_after']

	_select1 = 'select * from moves(%s)'

	def __init__(self, row):
		super(Moves, self).__init__(row)

	def __repr__(self):
		return '%s%s %s' % (
			'... ' if not self.iswhite else '    ',
			self.movenum,
			self.san
		)
	

class Opening(Table):
	
	_rows = [
			'id', 'eco', 'opening', 'variation', 'subvar', 'moves']

	_select2 = 'select * from classify_opening(%s, %s)'

	def __init__(self, row):
		super(Opening, self).__init__(row)

	def __repr__(self):
		return '%s %s %s %s' % (self.eco, self.opening, self.variation, self.moves)


class VariationStats(Table):
	
	_rows = [ 'white_winr', 'white_loser', 'drawr', 'total', 'wins', 'losses', 'draws', 
				'undetermined', 'position_id', 'ssquare', 'esquare' ,'subject', 'target' ,'san']
	_select1 = 'select * from variationstats(%s)'


class ValidMoves(Table):
	
	_rows = ['piece', 'fid', 'tid', 'direc', 'length', 'target']
	_select1 = 'select * from validmoves(%s)'

	def __str__(self):
		return '%s %s %s' %(self.piece, self.fid, self.tid)

class Protected(Table):
	
	_rows = ['piece', 'fid', 'tid', 'direc', 'length', 'target']
	_select1 = 'select * from protected(%s)'

	def __str__(self):
		return '%s %s %s' %(self.piece, self.fid, self.tid)

class Attacked(Table):
	
	_rows = ['piece', 'fid', 'tid', 'direc', 'length', 'target']
	_select1 = 'select * from attacked(%s)'

	def __str__(self):
		return '%s %s %s :%s' %(self.piece, self.fid, self.tid, self.target)


class AttackSum(Table):
	
	_rows = ['attacking', 'tid', 'target', 'sum']
	_select1 = 'select * from attack_sum(%s)'

class Force(Table):
	
	_rows = ['tid', 'c_white', 'c_black']
	_select1 = 'select * from force(%s)'

