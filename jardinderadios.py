#!/usr/bin/env python3
#
import os, sys, time
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5 import QtMultimedia, QtMultimediaWidgets
from PyQt5.QtSql import *
from PyQt5.QtMultimediaWidgets import QVideoWidget
import requests
import iconosResource_rc # pyrcc5 iconosResource.qrc -o iconosResource_rc.py
import subprocess
from qt_material import apply_stylesheet, list_themes
from youtubesearchpython import VideosSearch
# from lyricsgenius import Genius
from flask import Flask, render_template, request, redirect, url_for
import time

# Create the connection
con = QSqlDatabase.addDatabase("QSQLITE")
con.setDatabaseName("radios.db")

# Try to open the connection and handle possible errors
if not con.open():
    QMessageBox.critical(
        None,
        "App Name - Error!",
        "Database Error: %s" % con.lastError().databaseText(),
    )
    sys.exit(1)

class Worker(QObject):
    ytstring = pyqtSignal(str)
    subirvol = pyqtSignal()
    bajarvol = pyqtSignal()
    fav = pyqtSignal(str)
    ytp = pyqtSignal(str)
    subir30 = pyqtSignal()
    men30 = pyqtSignal()

    def __init__(self, favoritos):
        super().__init__()
        self.favoritos = favoritos
        self.ytresults = None
        self.app = Flask(__name__)
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/volup', 'volup', self.volup)
        self.app.add_url_rule('/voldown', 'voldown', self.voldown)
        self.app.add_url_rule('/ytsearch', 'ytsearch', self.ytsearch, methods=['POST'])
        self.app.add_url_rule('/ytresult/<number>', 'ytresult', self.ytresult)
        self.app.add_url_rule('/favorito/<number>', 'favorito', self.favorito)
        self.app.add_url_rule('/menos30', 'menostreinta', self.menos30)
        self.app.add_url_rule('/mas30', 'mastreinta', self.mas30)

    def run(self):
        self.app.run(host='0.0.0.0')

    def index(self):
        return render_template('index.html', favoritos=self.favoritos)

    def volup(self):
        self.subirvol.emit()
        return redirect(url_for('index'))

    def voldown(self):
        self.bajarvol.emit()
        return redirect(url_for('index'))

    def ytsearch(self):
        name = request.form['ytsearch']
        self.ytresults = None
        self.ytstring.emit(name)
        while not self.ytresults:
            time.sleep(1)
        return render_template('ytresults.html', results=self.ytresults)

    def ytresult(self, number):
        self.ytp.emit(number)
        return redirect(url_for('index'))

    def favorito(self, number):
        self.fav.emit(number)
        return redirect(url_for('index'))

    def menos30(self):
        self.men30.emit()
        return redirect(url_for('index'))


    def mas30(self):
        self.subir30.emit()
        return redirect(url_for('index'))



class Video(QVideoWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.settings = QSettings( 'waltermas', 'jardinderadios-video')
        self.resize(self.settings.value("size", QSize(400, 300)))
        self.move(self.settings.value("pos", QPoint(50, 50)))
        # self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

    def closeEvent(self, event):
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        event.accept()


class Jardin(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("jardin.ui", self)
        self.initUI()

    def initUI(self):
        self.player = QtMultimedia.QMediaPlayer(self)
        self.player.mediaStatusChanged.connect(self.handleStateChanged)
        self.player.error.connect(self.handleError)
        self.timeSlider.valueChanged.connect(self.player.setPosition)
        self.player.durationChanged.connect(self.update_duration)
        self.player.positionChanged.connect(self.update_position)
        self.pausePushButton.clicked.connect(self.pause)
        self.player.stateChanged.connect(self.stateChanged)
        # self.player.mediaChanged.connect(self.mediaCambio)
        # self.player.videoAvailableChanged.connect(self.conVideo)

        self.videoWidget = Video()
        # self.videoWidget.resize(QSize(400, 300))
        self.videoPushButton.clicked.connect(self.showVideo)
        self.buscarPushButton.clicked.connect(self.buscar)
        # self.errorLabel.setStyleSheet("color: red")
        self.cb = QApplication.clipboard()
        self.st = QSystemTrayIcon(QIcon(":/iconos/play.png"))
        self.st.activated.connect(self.iconoClick)
        self.st.show()
        # menu
        self.fileMenu = QMenu("File")
        self.radiosMenu = QMenu("Radios")
        action = self.fileMenu.addAction("Play")
        action.triggered.connect(self.playCurrent)
        action = self.fileMenu.addAction("Pause")
        action.triggered.connect(self.pause)
        action = self.fileMenu.addAction("Stop")
        action.triggered.connect(self.stop)
        action = self.fileMenu.addAction("Exit")
        action.triggered.connect(self.close)

        self.fileMenu.addMenu(self.radiosMenu)
        self.st.setContextMenu(self.fileMenu)

        self.salirPushButton.clicked.connect(self.close)
        self.playPushButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playPushButton.clicked.connect(self.playCurrent)
        self.stopPushButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stopPushButton.clicked.connect(self.stop)
        self.favPushButton.clicked.connect(self.agregarFav)
        self.quitarFavPushButton.clicked.connect(self.quitarFav)
        self.upPushButton.clicked.connect(self.upOrden)
        self.downPushButton.clicked.connect(self.downOrden)
        self.clipboardPushButton.clicked.connect(self.playClipboard)

        self.favoritosTableWidget.setColumnCount(3)
        self.favoritosTableWidget.setSelectionBehavior(QTableView.SelectRows)
        self.favoritosTableWidget.setHorizontalHeaderLabels(["Title", "Url", "Tag"])
        self.favoritosTableWidget.setColumnWidth(0,200)
        self.favoritosTableWidget.setColumnWidth(1,220)
        self.favoritosTableWidget.setColumnWidth(2,160)
        self.favoritosTableWidget.setColumnWidth(3,160)
        self.favoritosTableWidget.itemDoubleClicked.connect(self.playCurrent)

        self.buscarTableWidget.setColumnCount(2)
        self.buscarTableWidget.setSelectionBehavior(QTableView.SelectRows)
        self.buscarTableWidget.setHorizontalHeaderLabels(["Title", "Url"])
        self.buscarTableWidget.setColumnWidth(0,200)
        self.buscarTableWidget.setColumnWidth(1,350)
        self.buscarTableWidget.itemDoubleClicked.connect(self.playCurrent)

        self.historialTableWidget.setColumnCount(2)
        self.historialTableWidget.setSelectionBehavior(QTableView.SelectRows)
        self.historialTableWidget.setHorizontalHeaderLabels(["Title", "Url"])
        self.historialTableWidget.setColumnWidth(0,200)
        self.historialTableWidget.setColumnWidth(1,350)
        self.historialTableWidget.itemDoubleClicked.connect(self.playCurrent)

        self.youtubeTableWidget.setColumnCount(4)
        self.youtubeTableWidget.setSelectionBehavior(QTableView.SelectRows)
        self.youtubeTableWidget.setHorizontalHeaderLabels(["Id", "Title", "Dur", "Views"])
        self.youtubeTableWidget.setColumnWidth(0,100)
        self.youtubeTableWidget.setColumnWidth(1,250)
        self.youtubeTableWidget.setColumnWidth(2,90)
        self.youtubeTableWidget.setColumnWidth(3,90)
        self.youtubeTableWidget.itemDoubleClicked.connect(self.playCurrent)
        self.ytBuscarPushButton.clicked.connect(self.buscarYoutube)
        # self.lyricsPushButton.clicked.connect(self.buscarLyrics)

        self.volumeDial.setMinimum(0)
        self.volumeDial.setMaximum(100)
        self.volumeDial.valueChanged.connect(self.cambioVolumen)
        query = QSqlQuery("SELECT valor FROM init WHERE desc='volume'")
        query.last()
        self.volumeDial.setValue(query.value(0))
        self.titleLineEdit.editingFinished.connect(self.cambioMetadata)
        self.tagLineEdit.editingFinished.connect(self.cambioMetadata)

        self.loadFavoritos()
        self.loadHistorial()
        self.loadBusquedas()
        self.loadBusquedasYoutube()
        self.tabWidget.setCurrentIndex(0)

        self.settings = QSettings( 'waltermas', 'jardinderadios')
        self.resize(self.settings.value("size", QSize(270, 225)))
        self.move(self.settings.value("pos", QPoint(50, 50)))
        # geniusToken = self.settings.value("geniusToken")
        # self.genius = Genius(geniusToken)
        # self.settings.setValue("geniusToken","genius token here")
        self.themeComboBox.addItems(list_themes())
        query = QSqlQuery("SELECT valor FROM init WHERE desc = 'ultimoTheme'")
        query.last()
        indice = self.themeComboBox.findText(query.value(0))
        self.themeComboBox.setCurrentIndex(indice)
        if query.value(0)[0:1] == 'd':
            self.titleLineEdit.setStyleSheet("color: white")
            self.tagLineEdit.setStyleSheet("color: white")
        else:
            self.titleLineEdit.setStyleSheet("color: black")
            self.tagLineEdit.setStyleSheet("color: black")

        self.show()
        self.playingNow = "radio"

        # Cargar ultimo estado
        query = QSqlQuery('SELECT valor FROM init WHERE desc="startState"')
        query.last()
        ultimoState = query.value(0)
        if ultimoState == 1:
            query = QSqlQuery('SELECT valor FROM init WHERE desc="startUrl"')
            query.last()
            ultimaRadio = query.value(0)
            self.playContextMenu(ultimaRadio)

        # Server
        favoritos = []
        for i in range(0, self.favoritosTableWidget.rowCount()):
            favoritos.append([i, self.favoritosTableWidget.item(i,0).text()])

        self.thread = QThread()
        self.worker = Worker(favoritos)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.ytstring.connect(self.flaskYtSearch)
        self.worker.subirvol.connect(self.flaskVolUp)
        self.worker.bajarvol.connect(self.flaskVolDown)
        self.worker.fav.connect(self.flaskFavorito)
        self.worker.ytp.connect(self.flaskYtPlay)
        self.worker.subir30.connect(self.flaskMas30)
        self.worker.men30.connect(self.flaskMen30)

        self.thread.start()

    def flaskYtSearch(self, name):
        self.tabWidget.setCurrentIndex(3)
        self.youtubeComboBox.setCurrentText(name)
        self.buscarYoutube()
        resp = []
        for i in range(9):
            resp.append([i, self.youtubeTableWidget.item(i,1).text()])
        self.worker.ytresults = resp

    def flaskYtPlay(self, number):
        self.youtubeTableWidget.setCurrentCell(int(number), 1)
        self.playCurrent()

    def flaskVolUp(self):
        nuevoValor = int(self.volumeDial.value() * 1.2)
        if nuevoValor > 100: nuevoValor = 100
        self.volumeDial.setValue(nuevoValor)

    def flaskVolDown(self):
        nuevoValor = int(self.volumeDial.value() * 0.8)
        if nuevoValor < 0: nuevoValor = 0
        self.volumeDial.setValue(nuevoValor)

    def flaskFavorito(self, number):
        self.tabWidget.setCurrentIndex(0)
        self.favoritosTableWidget.setCurrentCell(int(number),1)
        self.playCurrent()

    def flaskMen30(self):
        pos = self.player.position()
        nuevoPos = pos - 30000
        if nuevoPos < 0: nuevoPos = 0
        self.player.setPosition(nuevoPos)

    def flaskMas30(self):
        pos = self.player.position()
        nuevoPos = pos + 30000
        self.player.setPosition(nuevoPos)



    def play(self, urlPrev, title, tag):
        self.playingNow = urlPrev
        if urlPrev[:24] == "https://www.youtube.com/":
            url = self.prueboYoutube(urlPrev)
            self.agregarHistorial(urlPrev, title)
        else:
            url =  urlPrev
            self.agregarHistorial(url, title)

        self.player.setMedia(QtMultimedia.QMediaContent(QUrl(url)))
        self.titleLineEdit.setText(title)
        self.tagLineEdit.setText(tag)
        self.player.play()

    def stop(self):
        self.player.stop()

    def pause(self):
        if self.player.state() == 2:
            self.player.play()
        else:
            self.player.pause()

    def cambioVolumen(self):
        self.player.setVolume(self.volumeDial.value())
        self.volumeLevelLabel.setText(str(self.volumeDial.value()))

    def handleStateChanged(self, state):
        if state == 0: estado = "Unknowed"
        if state == 1: estado = "No media"
        if state == 2: estado = "Loading"
        if state == 3: estado = "Loaded"
        if state == 4: estado = "Stalled"
        if state == 5: estado = "Buffering"
        if state == 6: estado = "Buffered"
        if state == 7: estado = "End"
        if state == 8: estado = "Invalid media"
        self.infoLabel.setText(estado)
        self.errorLabel.setText("")

    def handleError(self, error):
        self.errorLabel.setText(self.player.errorString())

    def stateChanged(self, state):
        if state == 2: self.st.setIcon(QIcon(":/iconos/pause"))
        if state == 1: self.st.setIcon(QIcon(":/iconos/play"))
        if state == 0: self.st.setIcon(QIcon(":/iconos/stop"))

    def keyPressEvent(self, event):
        if self.focusWidget().objectName() == "buscarComboBox":
            if type(event) == QKeyEvent:
                if event.key() == Qt.Key_Return:
                    # self.emit(QtCore.SIGNAL('MYSIGNAL'))
                    self.buscar()
        if self.focusWidget().objectName() == "youtubeComboBox":
            if type(event) == QKeyEvent:
                if event.key() == Qt.Key_Return:
                    # self.emit(QtCore.SIGNAL('MYSIGNAL'))
                    self.buscarYoutube()

    def buscar(self):
        buscado = self.buscarComboBox.currentText()
        query = QSqlQuery('SELECT busqueda FROM busquedas WHERE busqueda="%s"' % buscado)
        query.last()
        if query.isValid() == False:
            query = QSqlQuery('INSERT INTO busquedas (busqueda) VALUES ("%s")' % buscado)
        r = requests.get("http://radio.garden/api/search?q=%s" % buscado)
        self.buscarTableWidget.setRowCount(0)
        rows = self.buscarTableWidget.rowCount()
        resp = r.json()
        for item in resp['hits']['hits']:
            self.buscarTableWidget.setRowCount(rows + 1)
            self.buscarTableWidget.setItem(rows, 0, QTableWidgetItem(item['_source']['title']))
            self.buscarTableWidget.setItem(rows, 1, QTableWidgetItem(item['_source']['url']))
            rows+=1

    def playCurrent(self):
        self.player.stop()
        if self.tabWidget.currentIndex() == 1:
            if self.buscarTableWidget.currentRow() == -1: return
            ID = self.buscarTableWidget.item(self.buscarTableWidget.currentRow(), 1).text()[-8:]
            url = "http://radio.garden/api/ara/content/listen/%s/channel.mp3" % ID
            title = self.buscarTableWidget.item(self.buscarTableWidget.currentRow(), 0).text()
            self.play(url, title, "")

        elif self.tabWidget.currentIndex() == 0:
            if self.favoritosTableWidget.currentRow() == -1: return
            url = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(),1).text()
            title = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(), 0).text()
            tag = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(), 2).text()
            self.play(url, title, tag)

        elif self.tabWidget.currentIndex() == 2:
            if self.historialTableWidget.currentRow() == -1: return
            url = self.historialTableWidget.item(self.historialTableWidget.currentRow(),1).text()
            title = self.historialTableWidget.item(self.historialTableWidget.currentRow(), 0).text()
            self.play(url, title, "")

        elif self.tabWidget.currentIndex() == 3:
            if self.youtubeTableWidget.currentRow() == -1: return
            idurl = self.youtubeTableWidget.item(self.youtubeTableWidget.currentRow(),0).text()
            url = "https://www.youtube.com/watch?v=%s" % idurl
            title = self.youtubeTableWidget.item(self.youtubeTableWidget.currentRow(),1).text()
            tag = "youtube music"
            self.play(url, title, tag)


    def agregarHistorial(self, url, title):
        query = QSqlQuery("SELECT url FROM historial WHERE url='%s'" % url)
        query.last()
        if query.isValid(): return
        query = QSqlQuery('INSERT INTO historial (title, url) VALUES ("%s", "%s")' % (title, url))
        self.loadHistorial()


    def agregarFav(self):
        query = QSqlQuery("SELECT url FROM favoritos WHERE url='%s'" % self.playingNow)
        query.last()
        if query.isValid(): return
        query = QSqlQuery("SELECT orden FROM favoritos ORDER BY orden")
        query.last()
        ultimoOrden = query.value(0)
        query = QSqlQuery('INSERT INTO favoritos (title, url, orden, tag) VALUES ("%s", "%s", "%s","%s")' % (
                        self.titleLineEdit.text(),
                        self.playingNow, ultimoOrden + 1,
                        self.tagLineEdit.text()))
        self.loadFavoritos()

    def quitarFav(self):
        if self.favoritosTableWidget.currentRow() < 0: return
        url = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(),1).text()
        query = QSqlQuery("DELETE FROM favoritos WHERE url='%s'" % url)
        self.loadFavoritos()

    def upOrden(self):
        row = self.favoritosTableWidget.currentRow()
        if row < 0: return
        url = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(),1).text()
        query = QSqlQuery("SELECT id, orden FROM favoritos WHERE url='%s'" % url)
        query.last()
        idActual = query.value(0)
        ordenActual = query.value(1)
        queryp = QSqlQuery("SELECT id, orden FROM favoritos WHERE orden<'%i'ORDER BY orden" % ordenActual)
        queryp.last()
        if queryp.isValid() == False: return
        idPrevio = queryp.value(0)
        ordenPrevio = queryp.value(1)
        query = QSqlQuery("UPDATE favoritos SET orden='%s' WHERE id='%s'" % (ordenActual, idPrevio))
        query = QSqlQuery("UPDATE favoritos SET orden='%s' WHERE id='%s'" % (ordenPrevio, idActual))
        self.loadFavoritos()
        self.favoritosTableWidget.setCurrentCell(row - 1,0)

    def downOrden(self):
        row = self.favoritosTableWidget.currentRow()
        if row > self.favoritosTableWidget.rowCount(): return
        url = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(),1).text()
        query = QSqlQuery("SELECT id, orden FROM favoritos WHERE url='%s'" % url)
        query.last()
        idActual = query.value(0)
        ordenActual = query.value(1)
        queryp = QSqlQuery("SELECT id, orden FROM favoritos WHERE orden>'%i' ORDER BY orden" % ordenActual)
        queryp.first()
        if queryp.isValid() == False: return
        idPrevio = queryp.value(0)
        ordenPrevio = queryp.value(1)
        query = QSqlQuery("UPDATE favoritos SET orden='%s' WHERE id='%s'" % (ordenActual, idPrevio))
        query = QSqlQuery("UPDATE favoritos SET orden='%s' WHERE id='%s'" % (ordenPrevio, idActual))
        self.loadFavoritos()
        self.favoritosTableWidget.setCurrentCell(row + 1,0)

    def closeEvent(self, event):
        query = QSqlQuery("UPDATE init SET valor='%s' WHERE desc='volume'" % self.player.volume())
        query = QSqlQuery("UPDATE init SET valor='%s' WHERE desc='startUrl'" % self.titleLineEdit.text())
        query = QSqlQuery("UPDATE init SET valor='%s' WHERE desc='startState'" % self.player.state())
        query = QSqlQuery("UPDATE init SET valor='%s' WHERE desc='ultimoTheme'" % self.themeComboBox.currentText())
        con.close()
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        event.accept()

    def loadFavoritos(self):
        query = QSqlQuery("SELECT * FROM favoritos ORDER BY orden")
        self.favoritosTableWidget.setRowCount(0)
        while query.next():
            rows = self.favoritosTableWidget.rowCount()
            self.favoritosTableWidget.setRowCount(rows + 1)
            self.favoritosTableWidget.setItem(rows, 0, QTableWidgetItem(query.value(1)))
            self.favoritosTableWidget.setItem(rows, 1, QTableWidgetItem(query.value(2)))
            self.favoritosTableWidget.setItem(rows, 2, QTableWidgetItem(query.value(4)))
            self.favoritosTableWidget.item(rows, 2).setTextAlignment(Qt.AlignCenter)
            rows+=1

        # context menu
        testItems = []
        for i in range(0, self.favoritosTableWidget.rowCount()):
            testItems.append(self.favoritosTableWidget.item(i, 0).text())

        self.radiosMenu.clear()
        for item in testItems:
            action = self.radiosMenu.addAction(item)
            action.triggered.connect(
                lambda chk, item=item: self.playContextMenu(item))
        # self.st.setContextMenu(self.fileMenu)


    def loadHistorial(self):
        query = QSqlQuery("SELECT * FROM historial ORDER BY id DESC")
        self.historialTableWidget.setRowCount(0)
        while query.next():
            rows = self.historialTableWidget.rowCount()
            self.historialTableWidget.setRowCount(rows + 1)
            self.historialTableWidget.setItem(rows, 0, QTableWidgetItem(query.value(1)))
            self.historialTableWidget.setItem(rows, 1, QTableWidgetItem(query.value(2)))
            rows+=1

    def loadBusquedas(self):
        self.buscarComboBox.clear()
        query = QSqlQuery("SELECT * FROM busquedas ORDER BY id DESC")
        while query.next():
            self.buscarComboBox.addItem(query.value(1))

    def loadBusquedasYoutube(self):
        self.youtubeComboBox.clear()
        query = QSqlQuery("SELECT * FROM busquedasyoutube ORDER BY id DESC")
        while query.next():
            self.youtubeComboBox.addItem(query.value(1))

    def cambioMetadata(self):
        query = QSqlQuery("SELECT id FROM favoritos WHERE url='%s'" % self.playingNow)
        query.last()
        if query.isValid():
            query = QSqlQuery("UPDATE favoritos SET title='%s', tag='%s' WHERE id='%s'" %
                              (self.titleLineEdit.text(), self.tagLineEdit.text(), query.value(0)))
            self.loadFavoritos()

    def playClipboard(self):
        self.play(self.cb.text(), "Clipboard", "")

    def prueboYoutube(self, youtubeUrl):
        result = subprocess.run(['./get-stream.sh', youtubeUrl], stdout=subprocess.PIPE)
        url = result.stdout.decode('utf-8')
        return url


    def showVideo(self):
        youtubeUrl = self.playingNow 
        self.vw = Video()
        self.vw.show()
        self.playerv = QtMultimedia.QMediaPlayer(self)
        result = subprocess.run(['./get-stream-video.sh', youtubeUrl], stdout=subprocess.PIPE)
        url = result.stdout.decode('utf-8')
        self.playerv.setMedia(QtMultimedia.QMediaContent(QUrl(url)))
        self.playerv.setVideoOutput(self.vw)
        self.playerv.play()


    def buscarYoutube(self):
        buscado = self.youtubeComboBox.currentText()
        query = QSqlQuery('SELECT busqueda FROM busquedasyoutube WHERE busqueda="%s"' % buscado)
        query.last()
        if query.isValid() == False:
            query = QSqlQuery('INSERT INTO busquedasyoutube (busqueda) VALUES ("%s")' % buscado)
        videosSearch = VideosSearch(buscado)
        res = videosSearch.result()
        self.youtubeTableWidget.setRowCount(0)
        rows = self.youtubeTableWidget.rowCount()
        for item in res['result']:
            self.youtubeTableWidget.setRowCount(rows + 1)
            self.youtubeTableWidget.setItem(rows, 0, QTableWidgetItem(item['id']))
            self.youtubeTableWidget.setItem(rows, 1, QTableWidgetItem(item['title']))
            self.youtubeTableWidget.setItem(rows, 2, QTableWidgetItem(item['duration']))
            self.youtubeTableWidget.setItem(rows, 3, QTableWidgetItem(item['viewCount']['short'][:-6]))
            rows+=1

    def iconoClick(self, reason):
        if reason == 3:
            if self.player.state() == 1:
                self.stop()
            else:
                self.stop()
                self.player.play()

    def update_duration(self, duration):
        self.timeSlider.setMaximum(duration)

        # if duration >= 0:
            # self.totalTimeLabel.setText(hhmmss(duration))

    def update_position(self, position):
        # if position >= 0:
            # self.currentTimeLabel.setText(hhmmss(position))

        # Disable the events to prevent updating triggering a setPosition event (can cause stuttering).
        self.timeSlider.blockSignals(True)
        self.timeSlider.setValue(position)
        self.timeSlider.blockSignals(False)
        self.posLabel.setText(time.strftime('%H:%M:%S', time.gmtime(position/1000)))


    def playContextMenu(self, item):
        it = self.favoritosTableWidget.findItems(item, Qt.MatchExactly)
        if len(it) == 1:
            self.favoritosTableWidget.setCurrentItem(self.favoritosTableWidget.item(it[0].row(),0))
            self.play(self.favoritosTableWidget.item(it[0].row(),1).text(), self.favoritosTableWidget.item(it[0].row(),0).text(), self.favoritosTableWidget.item(it[0].row(),2).text())

    # def buscarLyrics(self):
    #     song = self.genius.search_song(self.artistLineEdit.text(), self.songLineEdit.text())
    #     self.lyricsTextEdit.setPlainText(song.lyrics)


def main():
    app = QApplication(sys.argv)
    query = QSqlQuery("SELECT valor FROM init WHERE desc = 'ultimoTheme'")
    query.last()
    apply_stylesheet(app, theme=query.value(0))
    # global ex
    ex = Jardin()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
