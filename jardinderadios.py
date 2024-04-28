#!/usr/bin/env python3
#
import os, sys
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
from qt_material import apply_stylesheet
from youtubesearchpython import VideosSearch


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
        print("close video")
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
        self.fileMenu = QMenu("&File")
        # self.videoWidget = QVideoWidget()
        self.videoWidget = Video()
        # self.videoWidget.resize(QSize(400, 300))
        self.videoPushButton.clicked.connect(self.showVideo)
        self.buscarPushButton.clicked.connect(self.buscar)
        # self.errorLabel.setStyleSheet("color: red")
        self.cb = QApplication.clipboard()
        self.st = QSystemTrayIcon(QIcon(":/iconos/play.png"))
        self.st.activated.connect(self.iconoClick)
        self.st.show()
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
        # self.buscarTableWidget.setColumnWidth(2,160)
        self.buscarTableWidget.itemDoubleClicked.connect(self.playCurrent)

        self.historialTableWidget.setColumnCount(2)
        self.historialTableWidget.setSelectionBehavior(QTableView.SelectRows)
        self.historialTableWidget.setHorizontalHeaderLabels(["Title", "Url"])
        self.historialTableWidget.setColumnWidth(0,200)
        self.historialTableWidget.setColumnWidth(1,350)
        # self.historialTableWidget.setColumnWidth(2,160)
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

        self.volumeDial.setMinimum(0)
        self.volumeDial.setMaximum(100)
        self.volumeDial.valueChanged.connect(self.cambioVolumen)
        query = QSqlQuery("SELECT valor FROM init WHERE desc='volume'")
        query.last()
        self.volumeDial.setValue(query.value(0))

        # self.subtitleLineEdit.editingFinished.connect(self.cambioMetadata)
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
        self.show()

        self.playingNow = "radio"


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
            # print(item['_source']['subtitle'])
            # print(item['_source']['title'])
            # print(item['_source']['url'])
            self.buscarTableWidget.setRowCount(rows + 1)
            # if 'subtitle' in item['_source']:
            #     self.buscarTableWidget.setItem(rows, 0, QTableWidgetItem(item['_source']['subtitle']))
            # else:
            #     self.buscarTableWidget.setItem(rows, 0, QTableWidgetItem('sin nombre'))
            self.buscarTableWidget.setItem(rows, 0, QTableWidgetItem(item['_source']['title']))
            self.buscarTableWidget.setItem(rows, 1, QTableWidgetItem(item['_source']['url']))
            rows+=1

    def playCurrent(self):
        self.player.stop()
        if self.tabWidget.currentIndex() == 1:
            if self.buscarTableWidget.currentRow() == -1: return
            ID = self.buscarTableWidget.item(self.buscarTableWidget.currentRow(), 1).text()[-8:]
            url = "http://radio.garden/api/ara/content/listen/%s/channel.mp3" % ID
            # subtitle = self.buscarTableWidget.item(self.buscarTableWidget.currentRow(), 0).text()
            title = self.buscarTableWidget.item(self.buscarTableWidget.currentRow(), 0).text()
            # self.agregarHistorial(url, subtitle, title)
            self.play(url, title, "")

        elif self.tabWidget.currentIndex() == 0:
            if self.favoritosTableWidget.currentRow() == -1: return
            url = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(),1).text()
            # subtitle = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(), 0).text()
            title = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(), 0).text()
            tag = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(), 2).text()
            # self.agregarHistorial(url, title)
            self.play(url, title, tag)

        elif self.tabWidget.currentIndex() == 2:
            if self.historialTableWidget.currentRow() == -1: return
            url = self.historialTableWidget.item(self.historialTableWidget.currentRow(),1).text()
            # subtitle = self.historialTableWidget.item(self.historialTableWidget.currentRow(), 0).text()
            title = self.historialTableWidget.item(self.historialTableWidget.currentRow(), 0).text()
            # self.agregarHistorial(url, subtitle, title)
            self.play(url, title, "")

        elif self.tabWidget.currentIndex() == 3:
            if self.youtubeTableWidget.currentRow() == -1: return
            idurl = self.youtubeTableWidget.item(self.youtubeTableWidget.currentRow(),0).text()
            url = "https://www.youtube.com/watch?v=%s" % idurl
            # subtitle = self.youtubeTableWidget.item(self.youtubeTableWidget.currentRow(), 1).text()
            title = self.youtubeTableWidget.item(self.youtubeTableWidget.currentRow(),1).text()
            tag = "youtube music"
            # self.agregarHistorial(url, subtitle, title)
            self.play(url, title, tag)


    def agregarHistorial(self, url, title):
        query = QSqlQuery("SELECT url FROM historial WHERE url='%s'" % url)
        query.last()
        if query.isValid(): return
        query = QSqlQuery('INSERT INTO historial (title, url) VALUES ("%s", "%s")' % (title, url))
        self.loadHistorial()


    def agregarFav(self):
        # url = self.player.currentMedia().request().url().toString()
        # url = self.ultimoUrl
        # if url == "": return
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
            # self.favoritosTableWidget.setItem(rows, 2, QTableWidgetItem(query.value(3)))
            self.favoritosTableWidget.setItem(rows, 2, QTableWidgetItem(query.value(4)))
            self.favoritosTableWidget.item(rows, 2).setTextAlignment(Qt.AlignCenter)
            rows+=1

        # context menu
        testItems = []
        for i in range(0, self.favoritosTableWidget.rowCount()):
            testItems.append(self.favoritosTableWidget.item(i, 0).text())

        self.fileMenu.clear()
        for item in testItems:
            print(item)
            action = self.fileMenu.addAction(item)
            action.triggered.connect(
                lambda chk, item=item: self.printItem(item))
        self.st.setContextMenu(self.fileMenu)


    def loadHistorial(self):
        query = QSqlQuery("SELECT * FROM historial ORDER BY id DESC")
        self.historialTableWidget.setRowCount(0)
        while query.next():
            rows = self.historialTableWidget.rowCount()
            self.historialTableWidget.setRowCount(rows + 1)
            self.historialTableWidget.setItem(rows, 0, QTableWidgetItem(query.value(1)))
            self.historialTableWidget.setItem(rows, 1, QTableWidgetItem(query.value(2)))
            # self.historialTableWidget.setItem(rows, 2, QTableWidgetItem(query.value(3)))
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
        # query = QSqlQuery("SELECT id FROM favoritos WHERE url='%s'" % self.player.currentMedia().request().url().toString())
        query.last()
        if query.isValid():
            query = QSqlQuery("UPDATE favoritos SET title='%s', tag='%s' WHERE id='%s'" %
                              (self.titleLineEdit.text(), self.tagLineEdit.text(), query.value(0)))
            self.loadFavoritos()

    def playClipboard(self):
        self.play(self.cb.text(), "Clipboard", "")

    def prueboYoutube(self, youtubeUrl):
        # youtubeUrl = self.player.currentMedia().request().url().toString()
        result = subprocess.run(['./get-stream.sh', youtubeUrl], stdout=subprocess.PIPE)
        url = result.stdout.decode('utf-8')
        # self.player.setMedia(QtMultimedia.QMediaContent(QUrl(url)))
        # self.player.play()
        # self.ultimoUrl =  youtubeUrl
        return url


    def showVideo(self):
        self.player.setVideoOutput(self.videoWidget)
        self.videoWidget.show()
        self.playCurrent()

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
            if self.player.state() == 2:
                self.player.play()
            else:
                self.player.pause()

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


    def printItem(self, item):
        print("holis action")
        print(item)

def main():
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml')
    ex = Jardin()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
