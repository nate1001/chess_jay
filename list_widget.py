'''
Copyright Nate Carson 2012

'''

class DBList(QtGui.QListWidget):
	def __init__(self, parent, *args):

		super(DBList, self).__init__(parent, *args)
		self.activated.connect(self.onActivate)
		self.currentRowChanged.connect(self.onRowChanged)
		self.load()
	
	def _init(self, *args):
		select = self.select(*args)

		self.data = [row for row in select]

		# clear any previous items
		while self.takeItem(0):
			pass
		self.addItems([str(row) for row in self.data])
		self.update()

	def onActivate(self, index):
		datum = self.data[index.row()]
		self.doActivate(datum)

	def onRowChanged(self, index):
		datum = self.data[index]
		self.doActivate(datum)
	
	def select(self):
		return self.klass.select()

	def doActivate(self, index):
		raise NotImplementedError

	def load(self, *args):
		raise NotImplementedError
	
	
class GameList(DBList):
	klass = db.Games

	def __init__(self, parent, move_list):
		super(GameList, self).__init__(parent)
		self.move_list = move_list

	def load(self):
		self._init()
	
	def doActivate(self, game):
		self.move_list.load(game.id)


class MoveList(DBList):
	klass = db.Moves

	def __init__(self, parent, callback, attacked_callback, protected_callback, attacksum_callback):
		super(MoveList, self).__init__(parent)
		self.callback = callback
		self.attacked_callback = attacked_callback
		self.protected_callback = protected_callback
		self.attacksum_callback = attacksum_callback

	def select(self, *args):
		return self.klass.select(args[0])
	
	def load(self, *args):
		if args:
			self._init(args)

	def doActivate(self, move):
		
		self.callback(move)
		forces = db.Force.select(move.fen)
		self.attacksum_callback(forces)

		#attacked = db.Attacked.select(move.fen)
		#self.attacked_callback(attacked)

		#protected = db.Protected.select(move.fen)
		#self.protected_callback(protected)

