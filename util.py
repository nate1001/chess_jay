'''
Copyright Nate Carson 2012
'''

from PyQt4 import QtCore, QtGui

import settings

# XXX stub
def tr(text):
	return text



class Icon(object):
	
	@classmethod
	def fromName(cls, name):
		
		icon = QtGui.QIcon.fromTheme(name)
		if icon.isNull():
			raise ValueError(name)
		return icon


class ToolBar(QtGui.QToolBar):
	def __init__(self):
		super(ToolBar, self).__init__()

		self.setIconSize(QtCore.QSize(32, 32))
		self.setFloatable(False)
		self.setMovable(False)


	#FIXME remove settings dependency
	def addAction(self, label, settings_key, tip, callback, icon_name=None):

		action = QtGui.QAction(label, self)
		action.setShortcut(settings.keys[settings_key])
		action.setToolTip(tip)
		action.triggered.connect(callback)
		if icon_name:
			icon = Icon.fromName(icon_name)
			action.setIcon(icon)
		super(ToolBar, self).addAction(action)
		return action


class GraphicsWidget(QtGui.QGraphicsWidget):
	'''Base class for widgets to handle animation.'''

	def __init__(self):
		super(GraphicsWidget, self).__init__()
	
		self._anim_fade = QtCore.QPropertyAnimation(self, 'opacity')
		self._anim_move = QtCore.QPropertyAnimation(self, 'pos')
	
	def move(self, new, duration, old=None):

		if not old:
			old = self.pos()

		self._anim_move.setDuration(duration)
		self._anim_move.setStartValue(old)
		self._anim_move.setEndValue(new)
		self._anim_move.start()
	
	def fadeOut(self, duration):
		self._anim_fade.setDuration(duration)
		self._anim_fade.setStartValue(1)
		self._anim_fade.setEndValue(0)
		self._anim_fade.start()

	def fadeIn(self, duration):
		self._anim_fade.setDuration(duration)
		self._anim_fade.setStartValue(0)
		self._anim_fade.setEndValue(1)
		self._anim_fade.start()


class ListWidget(QtGui.QGraphicsWidget):
	'''
	Removal of items is not supported. The list should be clear()ed and then rebuilt.
	Selection or the methods first, last, next, previous move the current item pointer to the requested item, while slices and inding will not move the current item pointer.

	'''
	def __init__(self):
		super(ListWidget, self).__init__()
		
		self._layout = QtGui.QGraphicsGridLayout()
		self.setLayout(self._layout)
		self._idx = None
		#XXX we need to hold a reference to our items or they disappear
		self._items = []

	def __iter__(self):
		for idx in range(self._layout.count()):
			yield self._layout.itemAt(idx)

	def __len__(self):
		return self._layout.count()
	
	def __nonzero__(self):
		return self._layout.count() > 0

	def __getitem__(self, key):
		l = []
		for item in self:
			l.append(item)
		return l[key]
	
	def clear(self):
		for idx in range(self._layout.count()):
			item = self[0]
			self._layout.removeAt(0)
			item.scene().removeItem(item)
		self._idx = None
		self._items = []
	
	def addItem(self, item, row, col):

		item.itemSelected.connect(self._onItemSelected)
		self._layout.addItem(item, row, col)
		self._items.append(item)
	
	def index(self, item):
		for idx, i in enumerate(self):
			if item is i:
				return idx
		raise IndexError(item)

	
	def _onItemSelected(self, item):

		if self._idx is not None:
			selected = self[self._idx]
			selected.setSelected(False)

		for idx, _item in enumerate(self):
			if item is _item:
				item.setSelected(True)
				self._idx = idx
				return
		raise ValueError(item)
	

	def first(self):
		if not self:
			return
		self._idx = 0
		return self[0]

	def last(self):
		if not self:
			return
		self._idx = len(self) -1
		return self[-1]
	
	def _get(self, offset):
		if not self or (offset < 0 and self._idx + offset < 0):
			return
		try:
			self[self._idx + offset]
			self._idx += offset
			return self[self._idx]
		except IndexError:
			return

	def next(self):
		return self._get(1)

	def previous(self):
		return self._get(-1)
	
	def current(self):
		return self._get(0)
	

class ListItem(QtGui.QGraphicsWidget):

	itemSelected = QtCore.pyqtSignal(QtGui.QGraphicsWidget)
	outline_width = .3

	def __init__(self, text):
		super(ListItem, self).__init__()

		self.box = QtGui.QGraphicsRectItem()
		self.box.setParentItem(self)
		self.box.setPen(QtGui.QPen(settings.square_outline_color, self.outline_width))

		self.text = QtGui.QGraphicsSimpleTextItem(text)
		self.text.setParentItem(self)

	def __repr__(self):
		return str(self.text.text())

	def mousePressEvent(self, event):
		if event.button() != QtCore.Qt.LeftButton:
			event.ignore()
			return
		self.itemSelected.emit(self)

	def setSelected(self, selected):

		if selected:
			self.box.setBrush(QtGui.QBrush(settings.square_selected_color))
		else:
			self.box.setBrush(QtGui.QBrush(settings.COLOR_NONE))
		self.text.update()


	
class ScalingView(QtGui.QGraphicsView):
	def __init__(self, scene, rect):
		super(ScalingView, self).__init__(scene)
		self._rect = rect
		self.setSceneRect(rect)

		self._size_hint = None

	def resizeEvent(self, event):
		# find the largest square for old and new and resize to the ratio
		old_side = min(event.oldSize().width(), event.oldSize().height())
		new_side = min(event.size().width(), event.size().height())
		if old_side <= 0 or new_side <= 0:
			return

		print old_side, new_side
		factor = float(new_side) / old_side 
		side = max(new_side, old_side)
		print side
		self._size_hint = QtCore.QSize(side, side)
		self.scale(factor, factor)
	
	def minimumSizeHint(self):
		print 11, self._size_hint
		return self._size_hint
	


class ScalingWidget(QtGui.QWidget):
	def __init__(self):
		super(ScalingWidget, self).__init__()
	def resizeEvent(self, event):
		pass
