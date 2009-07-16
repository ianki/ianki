# Copyright (C) 2008 Victor Miura
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

__version__ = "0.4.5"

from PyQt4 import QtCore, QtGui
from ankiqt.ui.main import AnkiQt
from ankiqt.forms.main import Ui_MainWindow
from anki import DeckStorage
import web
import sys

ankiQt = None
deckQueryRunner = None
urls = None
glob = None
sync_cards = 500
sync_days = 1
font_scaling = 100
sync_paths = []
sync_names = []

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

        '''if parent.deck is None and parent.deckPath is None:
            # qt on linux incorrectly accepts shortcuts for disabled actions
            return
        '''
        global ankiQt
        ankiQt = parent

        '''
        if ankiQt.deck:
            # save first, so we can rollback on failure
            ankiQt.deck.save()
            ankiQt.deckPath = ankiQt.deck.path
            ankiQt.syncName = ankiQt.deck.syncName or ankiQt.deck.name()
            ankiQt.lastSync = ankiQt.deck.lastSync
            ankiQt.deck.close()
            ankiQt.deck = None
            ankiQt.loadAfterSync = True
        '''
        
        ankiQt.saveAndClose(hideWelcome=True)
        ankiQt.deck = None
        ankiQt.moveToState("noDeck")

        #import gc; gc.collect()
        #self.bodyView.clearWindow()
        #self.bodyView.flush()

        #self.d = parent.deck
        self.config = parent.config
        self.server = None

        if 'ianki_ip' not in self.config:
            self.config['ianki_ip'] = 'localhost'
        if 'ianki_port' not in self.config:
            self.config['ianki_port'] = '8000'

        if 'ianki_sync_cards' not in self.config:
            self.config['ianki_sync_cards'] = sync_cards
        if 'ianki_sync_days' not in self.config:
            self.config['ianki_sync_days'] = sync_days
        if 'ianki_font_scaling' not in self.config:
            self.config['ianki_font_scaling'] = font_scaling

        global deckQueryRunner
        deckQueryRunner = self

        self.setObjectName("iAnki Server")
        self.setWindowTitle(_("iAnki Server (%s)" % __version__))
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

        # Sync settings
        self.slayout = QtGui.QHBoxLayout(self)
        self.slayout.setObjectName("iplayout")
        self.slayout.addWidget(QtGui.QLabel(_('Max cards'), self))
        self.scards = QtGui.QLineEdit(self)
        self.scards.setObjectName("cardsEdit")
        self.scards.setText(_(self.config['ianki_sync_cards']))
        self.scards.setMinimumSize(50, 20)
        self.slayout.addWidget(self.scards)
        self.slayout.addWidget(QtGui.QLabel(_('Days of reviews'), self))
        self.sdays = QtGui.QLineEdit(self)
        self.sdays.setObjectName("daysEdit")
        self.sdays.setText(_(self.config['ianki_sync_days']))
        self.sdays.setMinimumSize(50, 20)
        self.slayout.addWidget(self.sdays)
        
        # Scaling
        self.scalelayout = QtGui.QHBoxLayout(self)
        self.scalelayout.setObjectName("iplayout")
        self.scalelayout.addWidget(QtGui.QLabel(_('Font scaling (%)'), self))
        self.fontScale = QtGui.QLineEdit(self)
        self.fontScale.setObjectName("scaleEdit")
        self.fontScale.setText(_(self.config['ianki_font_scaling']))
        self.fontScale.setMinimumSize(50, 20)
        self.scalelayout.addWidget(self.fontScale)

        self.settingsLayout.addLayout(self.iplayout)
        self.settingsLayout.addLayout(self.slayout)
        self.settingsLayout.addLayout(self.scalelayout)

        # Todo: add card sync parameter settings
        '''
        self.maxCards = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.maxCards.setMinimumSize(100, 20)
        self.maxCards.setMinimum(0)
        self.maxCards.setMaximum(1000)
        self.maxCards.setValue(500)
        self.maxCards.setSingleStep(1)
        self.settingsLayout.addWidget(self.maxCards)
        '''

        #self.useGears = QtGui.QCheckBox(self)
        #self.useGears.setObjectName("useGears")
        #self.useGears.setChecked(self.config['ianki_useGears'])
        #self.useGears.setText(_('Enable Gears'))
        #self.settingsLayout.addWidget(self.useGears)
        
        #d = QtGui.QCheckListItem(self, "hello", QCheckListItem.CheckBox)
        
        #self.deckList = QtGui.QListView(self)
        #self.deckList.addColumn("Sync deck")
        
        ## Decks box
        self.decksBox = QtGui.QGroupBox("Sync decks", self)
        self.decksLayout = QtGui.QVBoxLayout(self.decksBox)
        self.vboxlayout.addWidget(self.decksBox)
        
        if not 'ianki_decks' in self.config:
            self.config['ianki_decks'] = []
        
        self.decks = []
        for dp in self.config['recentDeckPaths']:
            try:
                deck = DeckStorage.Deck(dp)
                try:
                    syncName = deck.syncName
                    if syncName != None:
                        cb = QtGui.QCheckBox(syncName, self)
                        if dp in self.config['ianki_decks']:
                            cb.setCheckState(2)
                        self.decks.append([cb, dp, syncName])
                        self.decksLayout.addWidget(self.decks[-1][0])
                except:
                    pass
                deck.close()
            except:
                pass
        
        #self.deckItems.append(QtGui.QCheckListItem(self.deckList, "hello", QCheckListItem.CheckBox))
        
        

        self.startButton = QtGui.QPushButton(self)
        self.startButton.setText(_("Start"))
        self.startButton.setDefault(True)
        self.stopButton = QtGui.QPushButton(self)
        self.stopButton.setText(_("Stop"))
        self.stopButton.setEnabled(False)
        self.closeButton = QtGui.QPushButton(self)
        self.closeButton.setText(_("Close"))
        self.vboxlayout.addWidget(self.startButton)
        self.vboxlayout.addWidget(self.stopButton)
        self.vboxlayout.addWidget(self.closeButton)

        self.logText = QtGui.QTextEdit(self)
        self.logText.setReadOnly(True)
        self.vboxlayout.addWidget(self.logText)

        self.connect(self.startButton, QtCore.SIGNAL("clicked()"), self.startClicked)
        self.connect(self.stopButton, QtCore.SIGNAL("clicked()"), self.stopClicked)
        self.connect(self.closeButton, QtCore.SIGNAL("clicked()"), self.closeClicked)
        #self.connect(self.useGears, QtCore.SIGNAL("clicked()"), self.useGearsChanged)
        self.exec_()

        # Reopen after sync finished.
        '''
        if ankiQt.loadAfterSync:
            ankiQt.loadDeck(ankiQt.deckPath, sync=False)
            ankiQt.deck.syncName = ankiQt.syncName
            ankiQt.deck.s.flush()
            ankiQt.deck.s.commit()
        else:
            ankiQt.moveToState("noDeck")
        ankiQt.deckPath = None
        '''
        ankiQt = None

    #def useGearsChanged(self):
    #    global useGears
    #    useGears = self.useGears.isChecked()
    #    self.config['ianki_useGears'] = useGears

    def closeEvent(self, evt):
        if self.server:
            self.stopClicked()
        QtGui.QDialog.closeEvent(self, evt)

    def reject(self):
        if self.server:
            self.stopClicked()
        QtGui.QDialog.reject(self)

    def startClicked(self):
        ip = str(self.ipEdit.text())
        port = str(self.portEdit.text())
        global sync_cards
        global sync_days
        global sync_paths
        global sync_names
        global font_scaling
        
        try:
            sync_cards = int(self.scards.text())
        except:
            sync_cards = 1
        try:
            sync_days = int(self.sdays.text())
        except:
            sync_days = 1
        try:
            font_scaling = int(self.fontScale.text())
        except:
            font_scaling = 100
        
        if sync_cards < 1:
            sync_cards = 1
        elif sync_cards > 1000:
            sync_cards = 1000
        if sync_days < 1:
            sync_days = 1
        elif sync_days > 4:
            sync_days = 4
        if font_scaling < 10:
            font_scaling = 10
        elif font_scaling > 1000:
            font_scaling = 1000

        sync_paths = [d[1] for d in reversed(self.decks) if (d[0].checkState())]
        sync_names = [d[2] for d in reversed(self.decks) if (d[0].checkState())]

        self.config['ianki_ip'] = ip
        self.config['ianki_port'] = port
        self.config['ianki_sync_cards'] = sync_cards
        self.config['ianki_sync_days'] = sync_days
        self.config['ianki_decks'] = sync_paths
        self.config['ianki_font_scaling'] = font_scaling
        
        #if deck.syncName in self.config['ianki_decks']:

        self.scards.setText(_(str(sync_cards)))
        self.sdays.setText(_(str(sync_days)))
        web.wsgi.connectIP = ip+':'+port

        global urls, glob
        self.logText.append('Starting server at ' + web.wsgi.connectIP +'.')
        self.server = web.run(urls, glob);
        if self.server:
            self.startButton.setEnabled(False)
            self.stopButton.setEnabled(True)
            self.settingsBox.setEnabled(False)
            self.decksBox.setEnabled(False)
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
        self.decksBox.setEnabled(True)

    def closeClicked(self):
        self.close()

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

'''
import anki
def onCardStats(self):
    self.addHook("showQuestion", self.onCardStats)
    self.addHook("helpChanged", self.removeCardStatsHook)
    txt = ""
    card = None
    if self.currentCard:
        txt += _("<h1>Current card</h1>")
        txt += anki.stats.CardStats(self.deck, self.currentCard).report()
        card  = self.currentCard

        if card:
            s = self.deck.s.all("select reps, time, delay, ease, thinkingTime, lastInterval, nextInterval from reviewHistory where cardId=:id", id=card.id)

            stats = anki.stats.CardStats(self.deck, card)
            txt += '<br>'
            for x in s:
                time = stats.strTime(x[1])
                txt += 'rep %d time %s delay %f ease %d think %f<br>' % (x[0], time, x[2], x[3], x[4])
    if self.lastCard and self.lastCard != self.currentCard:
        txt += _("<h1>Last card</h1>")
        txt += anki.stats.CardStats(self.deck, self.lastCard).report()
        card  = self.lastCard

        if card:
            s = self.deck.s.all("select reps, time, delay, ease, thinkingTime, lastInterval, nextInterval from reviewHistory where cardId=:id", id=card.id)

            stats = anki.stats.CardStats(self.deck, card)
            txt += '<br>'
            for x in s:
                time = stats.strTime(x[1])
                txt += 'rep %d time %s delay %f ease %d think %f<br>' % (x[0], time, x[2], x[3], x[4])
    if not txt:
        txt = _("No current card or last card.")



    self.help.showText(txt, key="cardStats")

AnkiQt.onCardStats = onCardStats
'''
