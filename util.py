'''
Copyright Nate Carson 2012
'''

from PyQt4 import QtCore, QtGui, QtSvg

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


class DropShadow(QtGui.QGraphicsDropShadowEffect):
	
	def __init__(self):
		super(DropShadow, self).__init__()
		self.setColor(QtGui.QColor(210,210,210))
		self.setBlurRadius(2)

class Colorize(QtGui.QGraphicsColorizeEffect):
	def __init__(self):
		super(Colorize, self).__init__()


class Action(QtGui.QAction):

	def __init__(self, parent, label, keycode, tip, callback, icon_name=None):
		super(Action, self).__init__(label, parent)

		self.setShortcut(keycode)
		self.setToolTip(tip)
		self.triggered.connect(callback)
		if icon_name:
			icon = Icon.fromName(icon_name)
			self.setIcon(icon)

		if icon_name:
			self.graphics_button = GraphicsButton(icon_name)
			self.graphics_button.pushed.connect(callback)
			self.triggered.connect(self.graphics_button.onTriggered)
		else:
			self.graphics_button = None
	
	
class RaiseAnimation(QtCore.QParallelAnimationGroup):

	def __init__(self, widget, scale, duration):
		super(RaiseAnimation, self).__init__()

		self._anim_scale = QtCore.QPropertyAnimation(widget, 'scale')
		self._anim_pos = QtCore.QPropertyAnimation(widget, 'pos')
	
		# move the origin in relation with scale
		delta = widget.scale() - scale
		size = widget.size() - widget.size() * delta
		w, h = widget.size().width() - size.width(), widget.size().height() - size.height()
		pos = widget.pos()
		new = QtCore.QPointF(pos.x() + w,  pos.y() + h)

		self._anim_pos.setDuration(duration)
		self._anim_pos.setStartValue(widget.pos())
		self._anim_pos.setEndValue(new)
		
		self._anim_scale.setDuration(duration)
		self._anim_scale.setStartValue(widget.scale())
		self._anim_scale.setEndValue(scale)

		self.addAnimation(self._anim_scale)
		self.addAnimation(self._anim_pos)

	def goForward(self):
		self.setDirection(QtCore.QAbstractAnimation.Forward)
		self.start()

	def goBackward(self):
		self.setDirection(QtCore.QAbstractAnimation.Backward)
		self.start()


class PressAnimation(QtCore.QSequentialAnimationGroup):

	def __init__(self, widget, scale, duration):
		super(PressAnimation, self).__init__()

		orig = widget.scale()
		self._anim_in = RaiseAnimation(widget, scale, duration)
		self._anim_out = RaiseAnimation(widget, orig, duration)

		self.addAnimation(self._anim_in)
		self.addAnimation(self._anim_out)


class GraphicsWidget(QtGui.QGraphicsWidget):
	'''Base class for widgets to handle animation.'''

	def __init__(self):
		super(GraphicsWidget, self).__init__()
	
		self._anim_fade = QtCore.QPropertyAnimation(self, 'opacity')
		self._anim_move = QtCore.QPropertyAnimation(self, 'pos')
		self._anim_scale = QtCore.QPropertyAnimation(self, 'scale')

	
	def move(self, new, duration, old=None):

		if not old:
			old = self.pos()

		self._anim_move.setDuration(duration)
		self._anim_move.setStartValue(old)
		self._anim_move.setEndValue(new)
		self._anim_move.start()
	
	def fadeOut(self, duration):

		self._anim_fade.setDuration(duration)
		self._anim_fade.setStartValue(self.opacity())
		self._anim_fade.setEndValue(0)
		self._anim_fade.start()

	def fadeIn(self, duration):
		self._anim_fade.setDuration(duration)
		self._anim_fade.setStartValue(self.opacity())
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
	

class TextWidget(GraphicsWidget):

	itemSelected = QtCore.pyqtSignal(QtGui.QGraphicsWidget)
	outline_width = .3
	padding = 2

	def __init__(self, text):
		super(TextWidget, self).__init__()

		self.setGraphicsEffect(DropShadow())
		self.setAcceptHoverEvents(True)
		self._selected = False

		self.box = QtGui.QGraphicsRectItem()
		self.box.setPen(QtGui.QPen(settings.square_outline_color, self.outline_width))
		self.box.setParentItem(self)

		self.text = QtGui.QGraphicsSimpleTextItem(text)
		self.text.setParentItem(self)

		size = self.preferredSize()
		p = self.padding
		self.box.setRect(-p, -p, size.width()+p, size.height()+p)

	def __repr__(self):
		return str(self.text.text())
	
	def preferredSize(self):
		rect = self.text.boundingRect()
		return QtCore.QSize(rect.width(), rect.height())

	def mousePressEvent(self, event):
		if event.button() != QtCore.Qt.LeftButton:
			event.ignore()
			return
		self.itemSelected.emit(self)
	
	def setSelected(self, selected):

		if selected:
			self._selected = True
			self.box.setBrush(QtGui.QBrush(settings.square_selected_color))
		else:
			self._selected = False
			self.box.setBrush(QtGui.QBrush(settings.COLOR_NONE))
		self.text.update()
	
	def setEnabled(self, enabled):
		super(TextWidget, self).setEnabled(enabled)		
		
		self.setSelected(enabled)
		if not enabled:
			self.box.setPen(QtGui.QPen(settings.COLOR_NONE, 0))
		else:
			self.box.setPen(QtGui.QPen(settings.square_outline_color, self.outline_width))
		self.update()

	def hoverEnterEvent(self, event):
		self.box.setBrush(QtGui.QBrush(settings.square_hover_color))
	
	def hoverLeaveEvent(self, event):
		self.setSelected(self._selected)




	
class ScalingView(QtGui.QGraphicsView):
	def __init__(self, scene, rect):
		super(ScalingView, self).__init__(scene)
		self._rect = rect
		self.setSceneRect(rect)
		self._last_new = None


	def resizeEvent(self, event):
		old, new = event.oldSize(), event.size()
		# if we are recursing
		if self._last_new == old:
			return

		# find the largest square for old and new and resize to the ratio
		old_side = min(old.width(), old.height())
		new_side = min(new.width(), new.height())

		# if we are a invalid size
		if old_side <= 0 or new_side <= 0:
			return

		factor = float(new_side) / old_side 
		side = max(new_side, old_side)
		self.scale(factor, factor)
		self._last_new = new
	

class FocusingView(QtGui.QGraphicsView):

	def __init__(self, scene, item, rect):
		super(FocusingView, self).__init__(scene)

		self._item = item
		self._rect = rect

		self.setSceneRect(rect)
		self.toolbar = ToolBar()
		self.fitInView(self._item, QtCore.Qt.KeepAspectRatio)


	def resizeEvent(self, event):
		self.fitInView(self._rect, QtCore.Qt.KeepAspectRatio)



class AspectLayout(QtGui.QLayout):

	def __init__(self):
		super(AspectLayout, self).__init__()

		self._item = None
		self._count = 0
		# keeps reseting margins
		#self.setContentsMargins(0,0,0,0)

		self._width_by_height = None

	
	def addItem(self, item):
		if self._item is not None:
			raise ValueError
		self._item = item
		self._count = 1


		size = item.widget().sizeHint()
		w, h = size.width(), size.height()

		if w <= 0 or h <= 0:
			raise ValueError
		self._width_by_height = w / float(h)

	def count(self):
		return self._count

	def itemAt(self, index):
		if index == 0 and self._count == 1:
			return self._item
		else:
			return None

	def takeAt(self, index):
		if self.itemAt(index):
			self._item = None
			return self._item
		return None

	def sizeHint(self):
		return self._item and self._item.widget().sizeHint()

	#def expandingDirections(self):
	#def minimumSize(self):

	
	def setGeometry(self, rect):

		margins = self._item.widget().contentsMargins()
		l, r, t, b = margins.left(), margins.right(), margins.top(), margins.bottom()

		x, y = rect.x() + l, rect.y() + t
		w, h = rect.width(), rect.height()
		ratio = self._width_by_height

		nw1, nh1 = h * ratio, h
		nw2, nh2 = w, w / ratio 


		if not (nw1 > w or nh1 > h):
			rect = QtCore.QRect(l, t, nw1 + l + r, nh1 + t + b + 1)
		else:
			rect = QtCore.QRect(l, t, nw2 + l + r, nh2 + t + b + 1)

		self._item.setGeometry(rect)



class SvgIcon(QtSvg.QGraphicsSvgItem):
	
	scalefactor = .8

	#FIXME
	direc = './media/icons/scalable/'
	def __init__(self, name):
		path = SvgIcon.direc + name + '.svg'
		super(SvgIcon, self).__init__(path)
		self.setScale(self.scalefactor)

	
	def size(self):
		rect = self.boundingRect()
		w, h  = rect.width(), rect.height()
		scale = self.scale()
		return QtCore.QSizeF(w * scale, h * scale)


class GraphicsButton(GraphicsWidget):

	pushed = QtCore.pyqtSignal(GraphicsWidget)
	outline_width = .5
	hover_scale = 1.10
	press_scale = .95

	def __init__(self, name):
		super(GraphicsButton, self).__init__()

		# set these up when we are sure we know thier position
		self._anim_hover = None
		self._anim_press = None

		self.box = QtGui.QGraphicsRectItem()
		self.box.setPen(QtGui.QPen(settings.COLOR_NONE, self.outline_width))
		self.box.setParentItem(self)

		self.icon = SvgIcon(name)
		self.icon.setParentItem(self)

		self.setGraphicsEffect(DropShadow())

		size = self.icon.size()
		rect = QtCore.QRectF(0,0,size.width(),size.height())
		self.box.setRect(rect)

		self.setAcceptHoverEvents(True)
	

	def onTriggered(self):
		self.mousePressEvent(None)

	def mousePressEvent(self, event):

		# if this is not a dummy event
		if event is not None:
			if event.button() != QtCore.Qt.LeftButton:
				event.ignore()
				return
			self.pushed.emit(self)

		# set up animation now that we know our position
		if self._anim_press is None:
			self._anim_press = PressAnimation(self, self.press_scale, settings.animation_duration/2)

		self._anim_press.start()
		

	def hoverEnterEvent(self, event):
		# set up animation now that we know our position
		if self._anim_hover is None:
			self._anim_hover = RaiseAnimation(self, self.hover_scale, settings.animation_duration/2)

		self._anim_hover.goForward()
	
	def hoverLeaveEvent(self, event):
		self._anim_hover.goBackward()
	
	def size(self):
		rect = self.icon.boundingRect()
		w, h  = rect.width(), rect.height()
		scale = self.scale()
		size = QtCore.QSizeF(w * scale - w * .25, h * scale - h *.25)
		return size
	
	def sizeHint(self, which, constraint=None):
		return self.size()
			

