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
	
