#!/usr/bin/env python3
        # url = "https://manifest.googlevideo.com/api/manifest/hls_playlist/expire/1713403978/ei/6iMgZsKtGt2J4dUPubOD2Ag/ip/2001:13e8:e:13fe:a452:e14d:82b8:a4ca/id/shBvzTevAkw.1/itag/93/source/yt_live_broadcast/requiressl/yes/ratebypass/yes/live/1/sgoap/gir%3Dyes%3Bitag%3D140/sgovp/gir%3Dyes%3Bitag%3D134/rqh/1/hdlc/1/hls_chunk_host/rr2---sn-uxa8bb-gvne.googlevideo.com/xpc/EgVo2aDSNQ%3D%3D/spc/UWF9f9rokIYWF3p24RLEGD0myWJaQpIrk_Gd/vprv/1/playlist_type/LIVE/initcwndbps/412500/mh/Z8/mm/44/mn/sn-uxa8bb-gvne/ms/lva/mv/m/mvi/2/pl/51/dover/11/pacing/0/keepalive/yes/mt/1713381867/sparams/expire,ei,ip,id,itag,source,requiressl,ratebypass,live,sgoap,sgovp,rqh,hdlc,xpc,spc,vprv,playlist_type/sig/AJfQdSswRAIgSGmcfDltKM5RjTFPTZsh11eIQZImhqkiXis69JUK694CICT1RExUmKoKRLQ13Z0pHXm167WmF9G6M16XjbePjJmj/lsparams/hls_chunk_host,initcwndbps,mh,mm,mn,ms,mv,mvi,pl/lsig/ALClDIEwRgIhAPJVltPPcT-1o-ynJPyLVFw6952A7au5CNfmzkIzoBRXAiEAqFbm8YciqyQDCko_KzWY0GHYFrukTv_YJEBmpLvGzl4%3D/playlist/index.m3u8"
        # yt-dlp --list-formats url
        # yt-dlp -f <number> -g <url>
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


class Jardin(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("jardin.ui", self)
        self.initUI()

    def initUI(self):
        self.player = QtMultimedia.QMediaPlayer(self)
        self.player.stateChanged.connect(self.handleStateChanged)
        self.player.mediaChanged.connect(self.mediaCambio)
        self.player.error.connect(self.mediaError)
        # self.player.videoAvailableChanged.connect(self.conVideo)
        self.videoWidget = QVideoWidget()
        self.videoWidget.resize(QSize(400, 300))
        self.videoPushButton.clicked.connect(self.showVideo)

        self.errorLabel.setStyleSheet("color: red")
        self.cb = QApplication.clipboard()
        self.st = QSystemTrayIcon(QIcon(":/iconos/antena.png"))
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

        self.favoritosTableWidget.setColumnCount(4)
        self.favoritosTableWidget.setSelectionBehavior(QTableView.SelectRows)
        self.favoritosTableWidget.setHorizontalHeaderLabels(["Subtitle", "Title", "Url", "Tag"])
        self.favoritosTableWidget.setColumnWidth(0,160)
        self.favoritosTableWidget.setColumnWidth(1,160)
        self.favoritosTableWidget.setColumnWidth(2,160)
        self.favoritosTableWidget.setColumnWidth(3,160)
        self.favoritosTableWidget.itemDoubleClicked.connect(self.playCurrent)

        self.buscarTableWidget.setColumnCount(3)
        self.buscarTableWidget.setSelectionBehavior(QTableView.SelectRows)
        self.buscarTableWidget.setHorizontalHeaderLabels(["Subtitle", "Title", "Url"])
        self.buscarTableWidget.setColumnWidth(0,160)
        self.buscarTableWidget.setColumnWidth(1,160)
        self.buscarTableWidget.setColumnWidth(2,160)
        self.buscarTableWidget.itemDoubleClicked.connect(self.playCurrent)

        self.historialTableWidget.setColumnCount(3)
        self.historialTableWidget.setSelectionBehavior(QTableView.SelectRows)
        self.historialTableWidget.setHorizontalHeaderLabels(["Subtitle", "Title", "Url"])
        self.historialTableWidget.setColumnWidth(0,160)
        self.historialTableWidget.setColumnWidth(1,160)
        self.historialTableWidget.setColumnWidth(2,160)
        self.historialTableWidget.itemDoubleClicked.connect(self.playCurrent)

        self.volumeDial.setMinimum(0)
        self.volumeDial.setMaximum(100)
        self.volumeDial.valueChanged.connect(self.cambioVolumen)
        query = QSqlQuery("SELECT valor FROM init WHERE desc='volume'")
        query.last()
        self.volumeDial.setValue(query.value(0))

        self.subtitleLineEdit.editingFinished.connect(self.cambioMetadata)
        self.titleLineEdit.editingFinished.connect(self.cambioMetadata)
        self.tagLineEdit.editingFinished.connect(self.cambioMetadata)

        self.loadFavoritos()
        self.loadHistorial()
        self.loadBusquedas()
        self.tabWidget.setCurrentIndex(0)

        self.settings = QSettings( 'waltermas', 'jardinderadios')
        self.resize(self.settings.value("size", QSize(270, 225)))
        self.move(self.settings.value("pos", QPoint(50, 50)))
        self.show()

        self.ultimoUrl = "radio"


    def play(self, url, subtitle, title, tag):
        self.player.setMedia(QtMultimedia.QMediaContent(QUrl(url)))
        self.subtitleLineEdit.setText(subtitle)
        self.titleLineEdit.setText(title)
        self.tagLineEdit.setText(tag)
        self.player.play()

    def stop(self):
        self.player.stop()

    def cambioVolumen(self):
        self.player.setVolume(self.volumeDial.value())

    def handleStateChanged(self, state):
        print(state)
        # if state == QtMultimedia.QMediaPlayer.StoppedState:

    def keyPressEvent(self, event):
        if self.focusWidget().objectName() != "buscarComboBox": return
        if type(event) == QKeyEvent:
            if event.key() == Qt.Key_Return:
                # self.emit(QtCore.SIGNAL('MYSIGNAL'))
                self.buscar()

    def buscar(self):
        buscado = self.buscarComboBox.currentText()
        query = QSqlQuery("SELECT busqueda FROM busquedas WHERE busqueda='%s'" % buscado)
        query.last()
        if query.isValid() == False:
            query = QSqlQuery("INSERT INTO busquedas (busqueda) VALUES ('%s')" % buscado)
        r = requests.get("http://radio.garden/api/search?q=%s" % buscado)
        self.buscarTableWidget.setRowCount(0)
        rows = self.buscarTableWidget.rowCount()
        resp = r.json()
        for item in resp['hits']['hits']:
            # print(item['_source']['subtitle'])
            # print(item['_source']['title'])
            # print(item['_source']['url'])
            self.buscarTableWidget.setRowCount(rows + 1)
            if 'subtitle' in item['_source']:
                self.buscarTableWidget.setItem(rows, 0, QTableWidgetItem(item['_source']['subtitle']))
            else:
                self.buscarTableWidget.setItem(rows, 0, QTableWidgetItem('sin nombre'))
            self.buscarTableWidget.setItem(rows, 1, QTableWidgetItem(item['_source']['title']))
            self.buscarTableWidget.setItem(rows, 2, QTableWidgetItem(item['_source']['url']))
            rows+=1

    def playCurrent(self):
        if self.tabWidget.currentIndex() == 1:
            ID = self.buscarTableWidget.item(self.buscarTableWidget.currentRow(), 2).text()[-8:]
            url = "http://radio.garden/api/ara/content/listen/%s/channel.mp3" % ID
            subtitle = self.buscarTableWidget.item(self.buscarTableWidget.currentRow(), 0).text()
            title = self.buscarTableWidget.item(self.buscarTableWidget.currentRow(), 1).text()
            self.agregarHistorial(url, subtitle, title)
            self.play(url, subtitle, title, "")

        elif self.tabWidget.currentIndex() == 0:
            url = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(),2).text()
            subtitle = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(), 0).text()
            title = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(), 1).text()
            tag = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(), 3).text()
            self.agregarHistorial(url, subtitle, title)
            self.play(url, subtitle, title, tag)

        elif self.tabWidget.currentIndex() == 2:
            url = self.historialTableWidget.item(self.historialTableWidget.currentRow(),2).text()
            subtitle = self.historialTableWidget.item(self.historialTableWidget.currentRow(), 0).text()
            title = self.historialTableWidget.item(self.historialTableWidget.currentRow(), 1).text()
            self.agregarHistorial(url, subtitle, title)
            self.play(url, subtitle, title, "")

        self.ultimoUrl = url

    def agregarHistorial(self, url, subtitle, title):
        query = QSqlQuery("SELECT url FROM historial WHERE url='%s'" % url)
        query.last()
        if query.isValid(): return
        query = QSqlQuery("INSERT INTO historial (subtitle, title, url) VALUES ('%s', '%s', '%s')" % (subtitle, title, url))
        self.loadHistorial()


    def agregarFav(self):
        # url = self.player.currentMedia().request().url().toString()
        url = self.ultimoUrl
        if url == "": return
        query = QSqlQuery("SELECT url FROM favoritos WHERE url='%s'" % url)
        query.last()
        if query.isValid(): return
        query = QSqlQuery("SELECT orden FROM favoritos ORDER BY orden")
        query.last()
        ultimoOrden = query.value(0)
        query = QSqlQuery("INSERT INTO favoritos (subtitle, title, url, orden, tag) VALUES ('%s', '%s', '%s', '%s','%s')" % (self.subtitleLineEdit.text(),
                        self.titleLineEdit.text(),
                        url, ultimoOrden + 1,
                        self.tagLineEdit.text()))
        self.loadFavoritos()

    def quitarFav(self):
        if self.favoritosTableWidget.currentRow() < 0: return
        url = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(),2).text()
        query = QSqlQuery("DELETE FROM favoritos WHERE url='%s'" % url)
        self.loadFavoritos()

    def upOrden(self):
        row = self.favoritosTableWidget.currentRow()
        if row < 0: return
        url = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(),2).text()
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
        url = self.favoritosTableWidget.item(self.favoritosTableWidget.currentRow(),2).text()
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
            self.favoritosTableWidget.setItem(rows, 2, QTableWidgetItem(query.value(3)))
            self.favoritosTableWidget.setItem(rows, 3, QTableWidgetItem(query.value(5)))
            self.favoritosTableWidget.item(rows,3).setTextAlignment(Qt.AlignCenter)
            rows+=1

    def loadHistorial(self):
        query = QSqlQuery("SELECT * FROM historial ORDER BY id DESC")
        self.historialTableWidget.setRowCount(0)
        while query.next():
            rows = self.historialTableWidget.rowCount()
            self.historialTableWidget.setRowCount(rows + 1)
            self.historialTableWidget.setItem(rows, 0, QTableWidgetItem(query.value(1)))
            self.historialTableWidget.setItem(rows, 1, QTableWidgetItem(query.value(2)))
            self.historialTableWidget.setItem(rows, 2, QTableWidgetItem(query.value(3)))
            rows+=1

    def loadBusquedas(self):
        self.buscarComboBox.clear()
        query = QSqlQuery("SELECT * FROM busquedas ORDER BY id DESC")
        while query.next():
            self.buscarComboBox.addItem(query.value(1))

    def cambioMetadata(self):
        query = QSqlQuery("SELECT id FROM favoritos WHERE url='%s'" % self.player.currentMedia().request().url().toString())
        query.last()
        if query.isValid():
            query = QSqlQuery("UPDATE favoritos SET subtitle='%s', title='%s', tag='%s' WHERE id='%s'" %
                              (self.subtitleLineEdit.text(), self.titleLineEdit.text(), self.tagLineEdit.text(), query.value(0)))
            self.loadFavoritos()

    def playClipboard(self):
        url = self.cb.text()
        self.play(self.cb.text(), "Clipboard", "Clipboard", "")

    def mediaError(self, error):
        # print(error)
        # print(self.player.errorString())
        self.errorLabel.setText(self.player.errorString())
        self.prueboYoutube()

    def prueboYoutube(self):
        youtubeUrl = self.player.currentMedia().request().url().toString()
        result = subprocess.run(['./get-stream.sh', youtubeUrl], stdout=subprocess.PIPE)
        url = result.stdout.decode('utf-8')
        self.player.setMedia(QtMultimedia.QMediaContent(QUrl(url)))
        self.player.play()
        # print("despues:")
        # print(self.player.MediaStatus())
        # print(self.player.errorString())
        self.ultimoUrl =  youtubeUrl

    def mediaCambio(self):
        self.errorLabel.setText("")
        # self.media = "radio"

    def showVideo(self):
        self.player.setVideoOutput(self.videoWidget)
        self.videoWidget.show()
        self.player.play()
        # print(self.ultimoUrl)

    # def conVideo(self):
    #     print("video disponible")
    #     print(self.player.isVideoAvailable())
    #     self.player.setVideoOutput(self.videoWidget)
    #     self.videoWidget.show()



def main():
    app = QApplication(sys.argv)
    ex = Jardin()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
