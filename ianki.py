# Copyright (C) 2008 Victor Miura
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

import sys
import ianki_ext
from ankiqt import mw
from PyQt4 import QtCore, QtGui

def init():
    mw.actionRunIAnki = QtGui.QAction(mw)
    mw.actionRunIAnki.setObjectName("actionRunIAnki")
    mw.actionRunIAnki.setText(_("&iAnki Server"))
    try:
        menu = mw.mainWin.menuPlugins
    except:
        menu = mw.mainWin.menuTools
    menu.addSeparator()
    menu.addAction(mw.actionRunIAnki)

    def iankiWindow():
        ianki_ext.unload()
        reload(sys.modules['ianki_ext'])
        ianki_ext.ui.IAnkiServerDialog(mw)

    mw.connect(mw.actionRunIAnki, QtCore.SIGNAL("triggered()"), iankiWindow)

init()
