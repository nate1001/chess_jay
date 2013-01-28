

from PyQt4 import QtCore

'''
http://wbec-ridderkerk.nl/html/UCIProtocol.html
'''

class EngineError(Exception): pass

class UciInfo(dict):
    
    keys = [
        'depth', 'seldepth', 'time', 'nodes', 'pv',
        'multipv', 'score', 'currmove', 'currmovenumber',
        'hashfull', 'nps', 'tbhits', 'cpuload', 'string',
        'refutation', 'currline'
    ]

    def __repr__(self):
        if self.bestmove:
            return '<UciInfo bestmove: {}>'.format(self.bestmove)
        else:
            return '<UciInfo depth: {depth} score: {score} pv: {pv}>'.format(**self)
    
    def __init__(self, info):
        super(UciInfo, self).__init__()
        
        self.bestmove = None

        self._info = info
        self._pieces = info.split()
        self._parse()
        del self._pieces

        for key in self.keys:
            if key not in self:
                self[key] = None

    
    def _parse(self):

        token = self._pieces.pop(0)

        if token == 'bestmove':
            self._handle_bestmove()

        elif token == 'info':
            try:
                while self._handle_token(self._pieces.pop(0)):
                    pass
            except IndexError:
                pass
        else:
            raise ValueError(token)
    
    def _handle_bestmove(self):
        
        self.bestmove = self._pieces.pop(0)
    
    def _handle_token(self, token):
        if token not in self.keys:
            raise ValueError(token)

        if hasattr(self, '_handle_' + token):
            getattr(self, '_handle_' + token)()
        else:
            self[token] = self._pieces.pop(0)
        
        return True
    
    def _handle_score(self):
        
        #FIXME handle mate
        cp = self._pieces.pop(0)
        score = self._pieces.pop(0)
        self['score'] = score

    def _handle_pv(self):

        self['pv'] = ''
        while True:
            try:
                self['pv'] += ' ' + self._pieces.pop(0)
            except IndexError:
                break

class Process(QtCore.QProcess):
    
    output_read = QtCore.pyqtSignal(str)
    timeout = 5000
    
    def __init__(self, path):
        super(Process, self).__init__()

        self.start(path)
        self._buffer = ''
        self._async = False

        if not self.waitForStarted():
            raise EngineError('Could not start engine.')

        if not self.waitForReadyRead(self.timeout):
            raise EngineError('Engine startup headers not available.')

        self._header = self._read()


    def _read(self):
        
        buf = []
        while self.canReadLine():
            data = self.readLine()
            buf.append(str(data))

            if self._async:
                self.output_read.emit(str(data))

        return ''.join(buf)

    def asyncSend(self, cmd):
        self._async = True
        self.readyRead.connect(self._read)
        self.write(cmd + '\n')

    def stopAsync(self):
        self._async = False
        try:
            self.readyRead.disconnect(self._read)
        except TypeError:
            pass

    def blockingSend(self, cmd):
        self.write(cmd + '\n')
        if not self.waitForReadyRead(self.timeout):
            raise EngineError("Timeout before engine wating to read.")
        return self._read()

    def __del__(self):
        self.close()
        self.waitForFinished()



class UciEngine(QtCore.QThread):
    
    info_recieved = QtCore.pyqtSignal(UciInfo)
    bestmove_recieved = QtCore.pyqtSignal(UciInfo)
    
    def __init__(self, path):
        super(UciEngine, self).__init__()

        self._process = None
        self._fen = None
        self._depth = None

        self._path = path
        
    def isready(self):
        response = self._process.blockingSend('isready')
        if response != 'readyok':
            return False
        return True

    def _onInfo(self, text):

        text = str(text)
        info = UciInfo(text)

        if text.startswith('bestmove'):
            self._process.stopAsync()
            self.bestmove_recieved.emit(info)
        else:
            self.info_recieved.emit(info)

    def analyze(self, fen):
    
        isready = self._process.blockingSend('position {0}\n isready'.format(fen)).strip()
        if isready != 'readyok':
            raise EngineError("engine not ready - {0}".format(repr(isready)))
        self._process.asyncSend('go depth {0}'.format(self._depth))

    def exit(self):
        if self._process:
            self._process.stopAsync()
        super(UciEngine, self).exit()

    def run(self):

        if not self._process:
            self._process = Process(self._path)
            self._process.output_read.connect(self._onInfo)

        self.analyze(self._fen)
        super(UciEngine, self).run()

    def start(self, fen, depth):
        self._fen = fen
        self._depth = int(depth)
        super(UciEngine, self).start()



if __name__ == '__main__':

    STOCKFISH = '/usr/games/bin/stockfish'
    
    from PyQt4 import QtGui
    import sys

    app = QtGui.QApplication(sys.argv)

    class View(QtGui.QGraphicsView):
        
        def __init__(self, scene):
            
            super(View, self).__init__(scene)

            self.engine = UciEngine(STOCKFISH)
            self.info = QtGui.QGraphicsSimpleTextItem()
            self.bestmove = QtGui.QGraphicsSimpleTextItem()
            self.status = QtGui.QGraphicsSimpleTextItem()

            self.engine.info_recieved.connect(self._onInfo)
            self.engine.bestmove_recieved.connect(self._onBestMove)

            scene.addItem(self.info)
            scene.addItem(self.bestmove)
            self.bestmove.setPos(0, 50)
            self.status.setPos(0, 100)

        def _onInfo(self, info):
            self.info.setText(str(info))

        def _onBestMove(self, info):
            self.bestmove.setText(str(info))
            fen = 'QQQ5/1K6/1Q6/8/5r2/4rk2/8/8 w - - 0 0'
            self.engine.start(fen, 10)

        def analyze(self):

            fen = 'QQQ5/1K6/1Q6/8/5r2/4rk2/8/8 w - - 0 0'
            self.engine.start(fen, 10)
            self.info.setText('waiting ...')
            self.bestmove.setText('waiting ...')

        def stop(self):
            self.engine.exit()
            self.info.setText('stopped')
            self.bestmove.setText('stopped')

        def keyPressEvent(self, event):

            if event.key() == QtCore.Qt.Key_Escape:
                self.close()
            elif event.key() == QtCore.Qt.Key_Space:
                self.analyze()
            elif event.key() == QtCore.Qt.Key_Q:
                self.stop()

            super(View, self).keyPressEvent(event)


    view = View(QtGui.QGraphicsScene())
    view.setGeometry(0,0,800,200)
    view.show()
    sys.exit(app.exec_())

