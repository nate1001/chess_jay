
import pyglet


class Sound(object):
	
	@staticmethod
	def play(path):
		pyglet.media.load(path, streaming=False).play()
