#import cgitb; cgitb.enable()
#import sys

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
    self.menuTools.addSeparator()
    self.menuTools.addAction(self.actionRunIAnki)
    
    def iankiWindow():
        ianki_ext.unload()
        reload( sys.modules['ianki_ext'] )
        ianki_ext.ui.IAnkiServerDialog(MainWindow)
    
    MainWindow.connect(self.actionRunIAnki, QtCore.SIGNAL("triggered()"), iankiWindow)

Ui_MainWindow.setupUi = Ui_MainWindow_setupUi
