#!/usr/bin/env python3

from PyQt5 import QtCore, QtWidgets, QtNetwork, QtMultimedia

url = 'http://s48.myradiostream.com:8000/listen.mp3'

Errors = {}
for k, v in QtMultimedia.QMediaPlayer.__dict__.items():
    if isinstance(v, QtMultimedia.QMediaPlayer.Error):
        Errors[v] = k

class Buffer(QtCore.QIODevice):
    buffering = QtCore.pyqtSignal(object, object)
    fullBufferEmitted = False
    def __init__(self, reply, minBufferSize=250000):
        super().__init__()
        self.minBufferSize = max(200000, minBufferSize)
        self.reply = reply
        self.data = bytes()

        # the network reply is on another thread, use a mutex to ensure that
        # no simultaneous access is done in the meantime
        self.mutex = QtCore.QMutex()
        # this is important!
        self.setOpenMode(self.ReadOnly|self.Unbuffered)

        self.reply.readyRead.connect(self.dataReceived)

    def dataReceived(self):
        self.mutex.lock()
        self.data += self.reply.readAll().data()
        dataLen = len(self.data)
        self.mutex.unlock()
        self.buffering.emit(dataLen, self.minBufferSize)
        if not self.fullBufferEmitted:
            if dataLen < self.minBufferSize:
                return
            self.fullBufferEmitted = True
        self.readyRead.emit()

    def isSequential(self):
        return True

    def readData(self, size):
        self.mutex.lock()
        data = self.data[:size]
        self.data = self.data[size:]
        self.mutex.unlock()
        return data

    def bytesAvailable(self):
        return len(self.data) + super().bytesAvailable()


class Player(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        self.playButton = QtWidgets.QPushButton('Play', enabled=False)
        layout.addWidget(self.playButton)
        self.volumeSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        layout.addWidget(self.volumeSlider)
        self.statusLabel = QtWidgets.QLabel('Waiting')
        self.statusLabel.setFrameShape(
            self.statusLabel.StyledPanel|self.statusLabel.Sunken)
        layout.addWidget(self.statusLabel)

        self.player = QtMultimedia.QMediaPlayer(volume=16)
        self.volumeSlider.setValue(self.player.volume())

        self.networkManager = QtNetwork.QNetworkAccessManager()
        self.url = QtCore.QUrl(url)
        self.media = QtMultimedia.QMediaContent(self.url)
        reply = self.networkManager.get(QtNetwork.QNetworkRequest(self.url))
        self.buffer = Buffer(reply)

        self.playButton.clicked.connect(self.play)
        self.volumeSlider.valueChanged.connect(self.player.setVolume)
        self.player.error.connect(self.error)
        self.buffer.buffering.connect(self.buffering)

    def error(self, error):
        errorStr = 'Error: {} ({})'.format(
            Errors.get(error, 'Unknown error'), int(error))
        self.statusLabel.setText(errorStr)
        print(errorStr)

    def buffering(self, loaded, minBufferSize):
        self.statusLabel.setText('Buffer: {}%'.format(int(loaded / minBufferSize * 100)))
        if self.player.media().isNull() and loaded >= minBufferSize:
            self.player.setMedia(self.media, self.buffer)
            self.playButton.setEnabled(True)
            self.playButton.setFocus()
            self.statusLabel.setText('Ready to play')

    def play(self):
        if self.player.state() == self.player.PlayingState:
            self.player.pause()
            self.playButton.setText('Play')
        else:
            self.player.play()
            self.playButton.setText('Pause')


app = QtWidgets.QApplication([])
w = Player()
w.show()
app.exec_()
