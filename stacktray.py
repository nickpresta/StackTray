#!/usr/bin/python2.6

from lib.systemtray import SystemTray
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import sys

app = QApplication(sys.argv)

widget = QWidget()
trayIcon = SystemTray(QIcon("./share/common/images/icon.png"), widget)
trayIcon.show()

sys.exit(app.exec_())
