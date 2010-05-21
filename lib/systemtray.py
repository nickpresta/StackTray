from PyQt4.QtGui import *
from PyQt4.QtCore import *

import urllib2
import json
import os
import webbrowser
import time
import datetime
import math

import settings

class SystemTray(QSystemTrayIcon):

    """ Creates our System Tray icon and calls our worker to get new data """

    def __init__(self, icon, parent=None):
        QSystemTrayIcon.__init__(self, icon, parent)
        self.setToolTip("Text")

        menu = QMenu(parent)
        updateAction = menu.addAction("Update")
        exitAction = menu.addAction("Quit")
        QObject.connect(updateAction, SIGNAL("triggered()"), self.update)
        QObject.connect(exitAction, SIGNAL("triggered()"), qApp, SLOT("quit()"))

        self.setContextMenu(menu)

        # delta in hours
        self.delta = 24
        self.rep = None
        self.badges = None

        self.id = settings.id
        self.refresh = settings.refresh * 6000 * settings.refresh

        self.fetch()

        self.timer = QTimer()
        QObject.connect(self.timer, SIGNAL("timeout()"), self.fetch)
        self.timer.start(self.refresh)

    def fetch(self):
        """ Fetch the latest data """

        self.thread = Worker()
        self.connect(self.thread, SIGNAL("data"), self.run)
        self.thread.getData(self.id)

    def update(self):
        """ Manually update"""

        self.fetch()

    def run(self, data):
        """ The real "work" """

        try:
            rep = data['users'][0]['reputation']
        except KeyError:
            rep = None

        if not self.rep:
            self.rep = rep

        if self.rep == rep:
            pass

        self.showMessage("Total Reputation",
                "You have %d reputation!" % self.rep, msecs=5000)
        self.connect(self, SIGNAL("messageClicked()"), self.goto_site)

        latest_rep = self.get_latest_rep()
        new_badges = self.get_badges()
        msg = "You have %d reputation (%d new in the last 24 hours)\n" \
              "You have %d badges total (%d new)" % (self.rep, latest_rep, self.badges, new_badges)
        self.setToolTip(msg)

    def get_badges(self):
        """ Grab your total badges. Returns the "new" badges since running this program """

        data = json.load(urllib2.urlopen("http://api.stackoverflow.com/0.8/users/%d/badges" % self.id))
        try:
            data = data['badges']
        except KeyError:
            data = {}

        new = 0
        if not self.badges:
            self.badges = len(data)
            new = 0

        if self.badges != len(data):
            new = math.abs(len(data) - self.badges)
            self.badges = len(data)

        return new

    def get_latest_rep(self):
        """ Gets your latest reputation from a certain time delta """

        data = json.load(urllib2.urlopen("http://api.stackoverflow.com/0.8/users/%d/reputation" % self.id))
        try:
            data = data['rep_changes']
        except KeyError:
            data = {}

        # unix time since now() - X hours ago
        time_delta = time.mktime((datetime.datetime.now() - datetime.timedelta(hours=self.delta)).timetuple())

        net_rep = 0
        for c in data:
            if (c['on_date'] >= time_delta):
                net_rep += c['negative_rep']
                net_rep += c['positive_rep']

        return net_rep

    def goto_site(self):
        """ Open in browser """

        webbrowser.open_new_tab("http://stackoverflow.com/users/recent/%d" % self.id)

class Worker(QThread):
    """ Our worker thread """

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.exiting = False
        self.data = {}

    def __del__(self):
        self.exiting = True
        self.wait()

    def getData(self, id):
        self.id = id
        self.start()

    def run(self):
        while not self.exiting or not self.data:
            try:
                self.data = json.load(urllib2.urlopen("http://api.stackoverflow.com/0.8/users/%s" % self.id))
                #print self.data
            except urllib2.HTTPError:
                self.exiting = True
            self.emit(SIGNAL("data"), self.data)
            self.exiting = True

