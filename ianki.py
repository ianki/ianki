# Copyright (C) 2008 Victor Miura
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

import sys
import ianki_ext
from ankiqt.forms.main import Ui_MainWindow
from PyQt4 import QtCore, QtGui

# Override Ui_MainWindow.setupUi to add our menu item
setupUiBk = Ui_MainWindow.setupUi

def Ui_MainWindow_setupUi(self, MainWindow):
    setupUiBk(self, MainWindow)

    self.actionRunIAnki = QtGui.QAction(MainWindow)
    self.actionRunIAnki.setObjectName("actionRunIAnki")
    self.actionRunIAnki.setText(_("&iAnki Server"))
    try:
        menu = self.menuPlugins
    except:
        menu = self.menuTools
    menu.addSeparator()
    menu.addAction(self.actionRunIAnki)

    def iankiWindow():
        ianki_ext.unload()
        reload( sys.modules['ianki_ext'] )
        ianki_ext.ui.IAnkiServerDialog(MainWindow)

    MainWindow.connect(self.actionRunIAnki, QtCore.SIGNAL("triggered()"), iankiWindow)

Ui_MainWindow.setupUi = Ui_MainWindow_setupUi
