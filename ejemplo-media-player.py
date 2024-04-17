#!/usr/bin/env python3

from PyQt5 import QtCore, QtWidgets
from PyQt5 import QtMultimedia, QtMultimediaWidgets

url = "http://s48.myradiostream.com:8000/listen.mp3"

class Window(QtWidgets.QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.player = QtMultimedia.QMediaPlayer(self)
        self.viewer = QtMultimediaWidgets.QVideoWidget(self)
        self.player.setVideoOutput(self.viewer)
        self.player.stateChanged.connect(self.handleStateChanged)
        self.button1 = QtWidgets.QPushButton('Play', self)
        self.button2 = QtWidgets.QPushButton('Stop', self)
        self.button3 = QtWidgets.QPushButton('Stream', self)
        self.button1.clicked.connect(self.handleButton)
        self.button2.clicked.connect(self.player.stop)
        self.button3.clicked.connect(self.streamUrl)
        self.button2.setEnabled(False)
        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.viewer, 0, 0, 1, 2)
        layout.addWidget(self.button1, 1, 0)
        layout.addWidget(self.button2, 1, 1)
        layout.addWidget(self.button3, 1, 2)
        self._buffer = QtCore.QBuffer(self)
        self._data = None

    def handleButton(self):
        path = QtWidgets.QFileDialog.getOpenFileName(self)[0]
        if path:
            self.button1.setEnabled(False)
            self.button2.setEnabled(True)
            with open(path, 'rb') as stream:
                self._data = stream.read()
                self._buffer.setData(self._data)
                self._buffer.open(QtCore.QIODevice.ReadOnly)
                self.player.setMedia(QtMultimedia.QMediaContent(), self._buffer)
                self.player.play()

    def streamUrl(self):
        print('stream')
        self.player.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl(url)))
        self.player.play()


    def handleStateChanged(self, state):
        if state == QtMultimedia.QMediaPlayer.StoppedState:
            self._buffer.close()
            self._data = None
            self.button1.setEnabled(True)
            self.button2.setEnabled(False)

if __name__ == '__main__':

    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.setGeometry(500, 50, 640, 480)
    window.show()
    sys.exit(app.exec_())
