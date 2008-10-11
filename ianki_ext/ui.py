# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

from PyQt4 import QtCore, QtGui
from ankiqt.ui.main import AnkiQt
from ankiqt.forms.main import Ui_MainWindow
import web

ankiQt = None
deckQueryRunner = None
urls = None
glob = None

class ThreadedProc:
    def __init__(self, proc, arg):
        self.proc = proc
        self.arg = arg
        self.result = None
        self.e = None
        self.sema = QtCore.QSemaphore(0)
        obj = QtCore.QObject()
        deckQueryRunner.connect(obj, QtCore.SIGNAL("runProc"), deckQueryRunner.runProc)
        obj.emit(QtCore.SIGNAL("runProc"), self)
        self.sema.acquire(1)
        if self.e:
            raise self.e
        
def logMsg(msg):
    def addLog(self, msg):
        self.logText.append(msg)
    ThreadedProc(addLog, msg)

class IAnkiServerDialog(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
                
        if parent.deck is None and parent.deckPath is None:
            # qt on linux incorrectly accepts shortcuts for disabled actions
            return
        
        global ankiQt
        ankiQt = parent
        
        if ankiQt.deck:
            # save first, so we can rollback on failure
            ankiQt.deck.save()
            ankiQt.deck.close()
            ankiQt.deckPath = ankiQt.deck.path
            ankiQt.syncName = ankiQt.deck.syncName or ankiQt.deck.name()
            ankiQt.lastSync = ankiQt.deck.lastSync
            ankiQt.deck = None
            ankiQt.loadAfterSync = True
            
        #import gc; gc.collect()
        #self.bodyView.clearWindow()
        #self.bodyView.flush()
        
        self.d = parent.deck
        self.config = parent.config
        self.server = None
        
        if 'ianki_ip' not in self.config:
            self.config['ianki_ip'] = '0.0.0.0'
        if 'ianki_port' not in self.config:
            self.config['ianki_port'] = '8000'
        
        global deckQueryRunner
        deckQueryRunner = self
        
        self.setObjectName("iAnki Server")
        self.setWindowTitle(_("iAnki Server"))
        self.resize(260, 220)
        
        
        self.vboxlayout = QtGui.QVBoxLayout(self)
        self.vboxlayout.setObjectName("vboxlayout")
        
        ## Settings box
        self.settingsBox = QtGui.QGroupBox("Server settings", self)
        self.settingsLayout = QtGui.QVBoxLayout(self.settingsBox)
        self.vboxlayout.addWidget(self.settingsBox)
        
        # IP settings
        self.iplayout = QtGui.QHBoxLayout(self)
        self.iplayout.setObjectName("iplayout")
        self.iplayout.addWidget(QtGui.QLabel(_('Address'), self))
        self.ipEdit = QtGui.QLineEdit(self)
        self.ipEdit.setObjectName("ipEdit")
        self.ipEdit.setText(_(self.config['ianki_ip']))
        self.ipEdit.setMinimumSize(100, 20)
        self.iplayout.addWidget(self.ipEdit)
        self.iplayout.addWidget(QtGui.QLabel(_('Port'), self))
        self.portEdit = QtGui.QLineEdit(self)
        self.portEdit.setObjectName("portEdit")
        self.portEdit.setText(_(self.config['ianki_port']))
        self.portEdit.setMinimumSize(50, 20)
        self.iplayout.addWidget(self.portEdit)
        
        self.settingsLayout.addLayout(self.iplayout)
        
        self.startButton = QtGui.QPushButton(self)
        self.startButton.setText(_("Start"))
        self.startButton.setDefault(True)
        self.stopButton = QtGui.QPushButton(self)
        self.stopButton.setText(_("Stop"))
        self.stopButton.setEnabled(False)
        self.vboxlayout.addWidget(self.startButton)
        self.vboxlayout.addWidget(self.stopButton)
        
        self.logText = QtGui.QTextEdit(self)
        self.logText.setReadOnly(True)
        self.vboxlayout.addWidget(self.logText)
        
        self.connect(self.startButton, QtCore.SIGNAL("clicked()"), self.startClicked)
        self.connect(self.stopButton, QtCore.SIGNAL("clicked()"), self.stopClicked)        
        self.exec_()
        
        # Reopen after sync finished.
        if ankiQt.loadAfterSync:
            ankiQt.loadDeck(ankiQt.deckPath, sync=False)
            ankiQt.deck.syncName = ankiQt.syncName
            ankiQt.deck.s.flush()
            ankiQt.deck.s.commit()
        else:
            ankiQt.moveToState("noDeck")
        ankiQt.deckPath = None
        ankiQt = None
        
    def closeEvent(self, evt):
        if self.server:
            self.stopClicked()
        QtGui.QDialog.closeEvent(self, evt)
        
    def startClicked(self):
        ip = str(self.ipEdit.text())
        port = str(self.portEdit.text())
        web.wsgi.connectIP = ip+':'+port
        
        global urls, glob
        self.logText.append('Starting server at ' + web.wsgi.connectIP +'.')
        self.server = web.run(urls, glob);
        if self.server:
            self.startButton.setEnabled(False)
            self.stopButton.setEnabled(True)
            self.settingsBox.setEnabled(False)
            self.config['ianki_ip'] = ip
            self.config['ianki_port'] = port
            self.logText.append('Server started.')
        else:
            self.logText.append('Failed to start server.')
        
    def stopClicked(self):
        self.logText.append('Stopping server.')
        self.stopButton.setEnabled(False)
        self.server[0].stop()
        self.server[1].join()
        self.server = None
        global queryRunner
        queryRunner = None
        self.startButton.setEnabled(True)
        self.settingsBox.setEnabled(True)
    
    def runProc(self, threadedProc):
        try:
            threadedProc.result = threadedProc.proc(self, threadedProc.arg)
        except Exception, e:
            threadedProc.e = e
        threadedProc.sema.release(1)
        
    '''
    def runQuery(self, query):
        try:
            query.result = self.d.s.all(query.sql)
        except:
            pass
        query.sema.release(1)
    '''
