# -*- coding: utf-8 -*-
# The MIT License (MIT)
# Copyright (c) 2020 limkokhole@gmail.com
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

__author__ = 'Lim Kok Hole'
__copyright__ = 'Copyright 2020'
__credits__ = ['Stack Overflow']
__license__ = 'MIT'
__version__ = 1.0
__maintainer__ = 'Lim Kok Hole'
__email__ = 'limkokhole@gmail.com'
__status__ = 'Production'

import sys, os, logging, traceback

PY3 = sys.version_info[0] >= 3
if not PY3:
    print('Sorry, but python 2 already RIP. Abort.')
    sys.exit()

from logging.handlers import QueueHandler, QueueListener

from PySide2 import QtCore
from PySide2.QtCore import Qt, Slot, QProcess
from PySide2.QtWidgets import (QApplication, QMainWindow,
                                QLayout, QHBoxLayout, QVBoxLayout,
                                QWidget, QLabel, 
                                QSpinBox, QRadioButton, QPushButton,
                                QLineEdit, QPlainTextEdit, 
                                QFileDialog)
                               
import multiprocessing

def worker_init(q):
    qh = QueueHandler(q)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    #logger.setLevel(logging.DEBUG)
    logger.addHandler(qh)

class LogEmitterOtherProces(QtCore.QObject):
    sigLog = QtCore.Signal(str)

class LogEmitter(QtCore.QObject):
    sigLog = QtCore.Signal(logging.LogRecord)

class LogHandler(logging.Handler):

    def __init__(self):
        super().__init__()
        self.emitter = LogEmitter()

    def emit(self, record):
        msg = self.format(record)
        self.emitter.sigLog.emit(msg)

class LogHandlerOtherProcess(logging.Handler):

    def __init__(self):
        super().__init__()
        self.emitter =  LogEmitterOtherProces()

    def emit(self, record):
        msg = self.format(record)
        self.emitter.sigLog.emit(msg)

class LoggerWriterOtherProcess():

    def write(self, msg):
        logging.info(msg.strip())
        #logging.debug(msg.strip())

    def flush(self): 
        pass

class LoggerWriter(logging.Handler):

    emitter = LogEmitter()

    def write(self, msg):
        self.emitter.sigLog.emit(msg.strip())

    def flush(self): 
        pass

    def emit(self, record):
        msg = self.format(record)
        self.emitter.sigLog.emit(msg)

class Widget(QWidget):

    movie_url_label_text = "粘贴有 dailymotion 版的連續劇网址 (例子: https://dramaq.de/cn191023b/): "

    def __init__(self):
        QWidget.__init__(self)

        self.q = None
        self.pool = None

        self.top = QHBoxLayout()
        self.top.setMargin(10)

        self.middle = QVBoxLayout()
        self.middle.setMargin(10)

        self.radioButtonDailyMotionDrama = QRadioButton("有 Dailymotion Drama 的網站")
        self.radioButtonAny = QRadioButton("其它類型網站 (例如 YouTube)")

        self.top.addWidget(self.radioButtonDailyMotionDrama)
        self.top.addWidget(self.radioButtonAny)

        self.url_label = QLabel()
        self.url = QLineEdit()
        self.url_label.setBuddy(self.url)
        self.middle.addWidget(self.url_label)
        self.middle.addWidget(self.url)

        self.browse_folder_label = QLabel("下載到：")
        self.browseFolder = QPushButton("選擇目錄")
        self.browse_folder_label.setBuddy(self.browseFolder)
        self.middle.addWidget( self.browse_folder_label)
        self.middle.addWidget( self.browseFolder)
        self.browse_folder_value = ""

        self.bk_cinemae_spin_from = 1
        self.bk_cinemae_spin_to = 1
        self.fromEpSpinBox = QSpinBox()
        self.fromEpSpinBox.setMinimum(1)
        self.fromEpSpinBox.setMaximum(2147483647)
        self.fromEpLabel = QLabel("&從第幾集開始下載：")
        self.fromEpLabel.setBuddy(self.fromEpSpinBox)

        self.toEpSpinBox = QSpinBox()
        self.toEpSpinBox.setMinimum(1)
        self.toEpSpinBox.setMaximum(2147483647)
        self.toEpLabel = QLabel("&到第幾集停止下載：")
        self.toEpLabel.setBuddy(self.toEpSpinBox)

        self.cinema_ly = QHBoxLayout()
        #self.cinema_ly.setMargin(10)
        self.cinema_ly.addWidget(self.fromEpLabel)
        self.cinema_ly.addWidget(self.fromEpSpinBox)
        self.cinema_ly.addWidget(self.toEpLabel)
        self.cinema_ly.addWidget(self.toEpSpinBox)
        self.middle.addLayout(self.cinema_ly)

        self.add = QPushButton("開始下載")
        self.add.setEnabled(False)
        self.middle.addWidget(self.add)

        self.stop_me = QPushButton("停止下載")
        self.stop_me.setEnabled(False)
        self.middle.addWidget(self.stop_me)

        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumBlockCount(1000)
        self.middle.addWidget(self.log_area)

        #self.table_view.setSizePolicy(size)
        #self.layout.addWidget(self.table)
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.top)
        self.layout.addLayout(self.middle)
        self.setLayout(self.layout)

        self.radioButtonDailyMotionDrama.toggled.connect(self.choose_DailyMotionDrama_widgets)
        self.radioButtonAny.toggled.connect(self.choose_Any_widgets)
        self.url.textChanged[str].connect(self.check_disable_download)
        self.browseFolder.clicked.connect(self.add_folder)
        self.add.clicked.connect(self.start_download)
        self.stop_me.clicked.connect(self.stop_download)

        self.radioButtonDailyMotionDrama.setChecked(True) #set default only after .connect above

        # TESTING PURPOSE
        '''
        self.url.setText('https://journalflash.com/cn191023b/')
        self.browse_folder_value = 'C:/Users/Administrator/Documents/duboku'
        '''

        #set current process (not queue that one) log handler:
        logger = logging.getLogger(__name__)
        handler2 = LoggerWriter()
        logger.addHandler(handler2)
        logger.setLevel(logging.INFO) #DEBUG
        handler2.emitter.sigLog.connect(self.log_area.appendPlainText)
        sys.stdout = handler2 #LoggerWriter()
        #sys.stderr = handler2 #Seems no difference
        #handler2.emitter.sigLog.emit('hihi')

    @Slot()
    def choose_DailyMotionDrama_widgets(self):

        if self.radioButtonDailyMotionDrama.isChecked():

            self.fromEpLabel.setEnabled(True)
            self.toEpLabel.setEnabled(True)

            self.fromEpSpinBox.setEnabled(True)
            self.toEpSpinBox.setEnabled(True)

            self.fromEpSpinBox.setValue(self.bk_cinemae_spin_from)
            self.toEpSpinBox.setValue(self.bk_cinemae_spin_to)
            self.fromEpLabel.setDisabled(True)
            self.toEpLabel.setDisabled(True)

    @Slot()
    def choose_Any_widgets(self):

        if self.radioButtonAny.isChecked():

            self.fromEpSpinBox.setDisabled(True)
            self.toEpSpinBox.setDisabled(True)

            self.bk_cinemae_spin_from = self.fromEpSpinBox.value()
            self.bk_cinemae_spin_to = self.toEpSpinBox.value()
            self.fromEpSpinBox.setValue(1)
            self.toEpSpinBox.setValue(1)

    @Slot()
    def add_folder(self, s):

        #fname = QFileDialog.getOpenFileName(self, 'Open file', "c:\'", "Image files (*.jpg *.gif)")
        #fname = QFileDialog.getOpenFileName(self, 'Open file', '', QFileDialog.ShowDirsOnly)
        fname = QFileDialog.getExistingDirectory(self, '選擇下載至什麼目錄', '', QFileDialog.ShowDirsOnly)
        #print('repr: ' + repr(fname))
        if fname and fname.strip():
            fname = fname.strip()
            self.browse_folder_value = fname
            #if getOpenFileName, will return ('/home/xiaobai/Pictures/disco.jpg', 'Image files (*.jpg *.gif)')
            #, while if getExistingDirectory, will return single path string only
            self.browseFolder.setText(fname)
            self.check_disable_download(fname)
        #else:
        #    print('User cancel')

    @Slot()
    def check_disable_download(self, s):

        if self.url.text() and self.browse_folder_value:
            self.add.setEnabled(True)
        else:
            self.add.setEnabled(False)

    def task_done(self, retVal):
        self.add.setEnabled(True)
        self.stop_me.setEnabled(False)

    @Slot()
    def stop_download(self):
        if self.q:
            self.q.close()
        if self.pool:
            self.pool.terminate()
        self.add.setEnabled(True)
        self.stop_me.setEnabled(False)
        print('下載停止。')

    @Slot()
    def start_download(self):

        if self.fromEpSpinBox.value() > self.toEpSpinBox.value():
            self.log_area.setPlainText('[!] 從第幾集必須小於或等於到第幾集。')
            return

        #No need worry click twice too fast, it seems already handle by PySide2
        self.add.setEnabled(False)
        self.stop_me.setEnabled(True)
        self.log_area.clear()

        dest_full_path = self.browse_folder_value
        '''
        print('dest_full_path: ' + repr(dest_full_path))
        print('self.url.text(): ' + repr(self.url.text()))
        print('self.fromEpSpinBox.value(): ' + repr(self.fromEpSpinBox.value()))
        print('self.toEpSpinBox.value(): ' + repr(self.toEpSpinBox.value()))
        '''

        import drama_dailymotion_console

        #Windows can't set like that bcoz not update for args.url, must put explicitly
        #drama_dailymotion_console.redirect_stdout_to_custom_stdout(arg_url, ...etc, LoggerWriter())

        #failed other process
        handler = LogHandlerOtherProcess()
        handler.emitter.sigLog.connect(self.log_area.appendPlainText)

        ''' #ref current process:
        logger = logging.getLogger(__name__)
        handler2 = LoggerWriter()
        logger.addHandler(handler2)
        logger.setLevel(logging.DEBUG)
        handler2.emitter.sigLog.connect(self.log_area.appendPlainText)
        sys.stdout = handler2 #LoggerWriter()
        #handler2.emitter.sigLog.emit('hihi')
        '''

        #handler = LoggerWriter()
        #handler.emitter.sigLog.connect(self.log_area.appendPlainText)

        self.q = multiprocessing.Queue()
        self.ql = QueueListener(self.q, handler)
        self.ql.start()

        self.pool = multiprocessing.Pool(1, worker_init, [self.q])

        if self.radioButtonDailyMotionDrama.isChecked():
            self.pool.apply_async(drama_dailymotion_console.main, args=(dest_full_path, 
                self.fromEpSpinBox.value(), self.toEpSpinBox.value(), self.url.text(), LoggerWriterOtherProcess(), False)
                , callback=self.task_done)
        else:
            self.pool.apply_async(drama_dailymotion_console.main, args=(dest_full_path, 
                self.fromEpSpinBox.value(), self.toEpSpinBox.value(), self.url.text(), LoggerWriterOtherProcess(), True)
                , callback=self.task_done)

class MainWindow(QMainWindow):
    def __init__(self, widget):
        QMainWindow.__init__(self)
        self.setWindowTitle("dailymotion 連續劇下載器")
        self.setCentralWidget(widget)
        self.widget = widget

    def closeEvent(self, event):
        if self.widget.q:
            self.widget.close()
        if self.widget.pool:
            # To avoid child process drama_dailymotion_console still running
            self.widget.pool.terminate()
        QMainWindow.closeEvent(self, event)

if __name__ == "__main__":

    # Prevent closing pyside2 window then automatically re-open until closed console window
    # https://stackoverflow.com/questions/24944558/pyinstaller-built-windows-exe-fails-with-multiprocessing
    # On Windows calling this function is necessary.
    multiprocessing.freeze_support()

    app = QApplication(sys.argv)
    widget = Widget()
    window = MainWindow(widget)
    #window.setStyleSheet('* { font-family: "Times New Roman", Times, serif;}')
    # Better look of chinese character:
    window.setStyleSheet('* { font-family: Tahoma, Helvetica, Arial, "Microsoft Yahei","微软雅黑", STXihei, "华文细黑", sans-serif;}')
    window.show()
    sys.exit(app.exec_())
