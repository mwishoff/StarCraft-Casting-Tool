"""Control all other modules."""
import logging

# create logger
module_logger = logging.getLogger('scctool.controller')

try:
    from scctool.matchdata import matchData
    from scctool.tasks.apithread import SC2ApiThread, ToggleScore
    from scctool.tasks.webapp import FlaskThread
    from scctool.settings.version import CheckVersionThread
    from scctool.settings.placeholders import PlaceholderList
    from scctool.tasks.ftpuploader import FTPUploader
    from scctool.tasks.obs import WebsocketThread
    import scctool.settings
    import scctool.tasks.twitch
    import scctool.tasks.nightbot
    import scctool.tasks.obs
    import webbrowser
    import os
    import shutil

    from PyQt5.QtGui import QIcon
    from PyQt5.QtCore import Qt


except Exception as e:
    module_logger.exception("message")
    raise


class MainController:
    """Control all other modules."""

    def __init__(self):
        """Init controller and connect them with other modules."""
        try:
            self.matchData = matchData(self)
            self.SC2ApiThread = SC2ApiThread(self)
            self.checkVersionThread = CheckVersionThread(
                scctool.settings.versionControl)
            self.webApp = FlaskThread()
            self.webApp.signal_twitch.connect(self.webAppDone_twitch)
            self.webApp.signal_nightbot.connect(self.webAppDone_nightbot)
            self.ftpUploader = FTPUploader()
            self.websocketThread = WebsocketThread()
            self.placeholderSetup()
            self._warning = False

        except Exception as e:
            module_logger.exception("message")
            raise

    def placeholderSetup(self):
        """Define and connect placeholders."""
        self.placeholders = PlaceholderList()
        self.placeholders.addConnection("Team1",
                                        lambda: self.matchData.getTeam(0))
        self.placeholders.addConnection("Team2",
                                        lambda: self.matchData.getTeam(1))
        self.placeholders.addConnection("URL", self.matchData.getURL)
        self.placeholders.addConnection(
            "BestOf", lambda: str(self.matchData.getBestOfRaw()))
        self.placeholders.addConnection("League", self.matchData.getLeague)
        self.placeholders.addConnection("Score", self.matchData.getScoreString)

    def setView(self, view):
        """Connect view."""
        self.view = view
        try:
            self.matchData.readJsonFile()
            self.view.trigger = False
            self.updateForms()
            self.view.trigger = True
            self.setCBs()
            self.view.resizeWindow()
        except Exception as e:
            module_logger.exception("message")

    def updateForms(self):
        """Update data in froms."""
        try:
            if(self.matchData.getProvider() == "Custom"):
                self.view.tabs.setCurrentIndex(1)
            else:
                self.view.tabs.setCurrentIndex(0)

            self.view.cb_allkill.setChecked(self.matchData.getAllKill())

            index = self.view.cb_bestof.findText(str(self.matchData.getBestOfRaw()),
                                                 Qt.MatchFixedString)
            if index >= 0:
                self.view.cb_bestof.setCurrentIndex(index)

            index = self.view.cb_minSets.findText(str(self.matchData.getMinSets()),
                                                  Qt.MatchFixedString)
            if index >= 0:
                self.view.cb_minSets.setCurrentIndex(index)

            self.view.le_url.setText(self.matchData.getURL())
            self.view.le_url_custom.setText(self.matchData.getURL())
            self.view.le_league.setText(self.matchData.getLeague())
            self.view.sl_team.setValue(self.matchData.getMyTeam())
            for i in range(2):
                self.view.le_team[i].setText(self.matchData.getTeam(i))

            for i in range(min(self.view.max_no_sets, self.matchData.getNoSets())):
                for j in range(2):
                    self.view.le_player[j][i].setText(
                        self.matchData.getPlayer(j, i))
                    self.view.cb_race[j][i].setCurrentIndex(
                        scctool.settings.race2idx(self.matchData.getRace(j, i)))

                self.view.le_map[i].setText(self.matchData.getMap(i))

                self.view.sl_score[i].setValue(self.matchData.getMapScore(i))

            for i in range(self.matchData.getNoSets(), self.view.max_no_sets):
                for j in range(2):
                    self.view.le_player[j][i].hide()
                    self.view.cb_race[j][i].hide()
                self.view.le_map[i].hide()
                self.view.sl_score[i].hide()
                self.view.label_set[i].hide()

            for i in range(min(self.view.max_no_sets, self.matchData.getNoSets())):
                for j in range(2):
                    self.view.le_player[j][i].show()
                    self.view.cb_race[j][i].show()
                self.view.le_map[i].show()
                self.view.sl_score[i].show()
                self.view.label_set[i].show()

        except Exception as e:
            module_logger.exception("message")
            raise

    def updateLogos(self):
        """Updata team logos in  view."""
        pixmap = QIcon(self.linkFile(scctool.settings.OBSdataDir + '/logo1'))
        self.view.qb_logo1.setIcon(pixmap)

        pixmap = QIcon(self.linkFile(scctool.settings.OBSdataDir + '/logo2'))
        self.view.qb_logo2.setIcon(pixmap)

        self.updateLogosHTML()

    def updateData(self):
        """Update match data from input of views."""
        try:
            self.matchData.setMyTeam(self.view.sl_team.value())
            self.matchData.setLeague(self.view.le_league.text())

            for i in range(2):
                self.matchData.setTeam(i, self.view.le_team[i].text())

            for i in range(min(self.view.max_no_sets, self.matchData.getNoSets())):
                for j in range(2):
                    self.matchData.setPlayer(
                        j, i, self.view.le_player[j][i].text())
                    self.matchData.setRace(j, i, scctool.settings.idx2race(
                        self.view.cb_race[j][i].currentIndex()))

                self.matchData.setMap(i, self.view.le_map[i].text())
                self.matchData.setMapScore(
                    i, self.view.sl_score[i].value(), True)

        except Exception as e:
            module_logger.exception("message")

    def applyCustom(self, bestof, allkill, minSets, url):
        """Apply a custom match format."""
        msg = ''
        try:

            self.matchData.setCustom(bestof, allkill)
            self.matchData.setMinSets(minSets)
            self.matchData.setURL(url)
            self.matchData.writeJsonFile()
            self.updateForms()
            self.view.resizeWindow()
            self.updateOBS()

        except Exception as e:
            msg = str(e)
            module_logger.exception("message")

        return msg

    def resetData(self):
        """Reset data."""
        msg = ''
        try:

            self.matchData.resetData()
            self.matchData.writeJsonFile()
            self.updateForms()
            self.updateOBS()

        except Exception as e:
            msg = str(e)
            module_logger.exception("message")

        return msg

    def refreshData(self, url):
        """Load data from match grabber."""
        msg = ''
        try:
            self.matchData.parseURL(url)
            self.matchData.grabData()
            self.matchData.autoSetMyTeam()
            self.matchData.writeJsonFile()
            try:
                self.matchData.downloadLogos()
            except:
                pass
            try:
                self.matchData.downloadBanner()
            except:
                pass
            self.updateLogos()
            self.updateForms()
            self.view.resizeWindow()
        except Exception as e:
            msg = str(e)
            module_logger.exception("message")

        return msg

    def setCBs(self):
        """Update value of check boxes from config."""
        try:
            if(scctool.settings.config.scoreUpdate):
                self.view.cb_autoUpdate.setChecked(True)

            if(scctool.settings.config.toggleScore):
                self.view.cb_autoToggleScore.setChecked(True)

            if(scctool.settings.config.toggleProd):
                self.view.cb_autoToggleProduction.setChecked(True)

            if(scctool.settings.config.playerIntros):
                self.view.cb_playerIntros.setChecked(True)

            self.view.cb_autoFTP.setChecked(
                scctool.settings.config.parser.getboolean("FTP", "upload"))
        except Exception as e:
            module_logger.exception("message")

    def updateOBS(self):
        """Update txt-files and ioncs for OBS."""
        try:
            self.updateData()
            self.matchData.updateMapIcons()
            self.matchData.updateScoreIcon()
            self.matchData.createOBStxtFiles()
            self.matchData.updateLeagueIcon()
            self.matchData.writeJsonFile()
            self.matchData.resetChanged()
        except Exception as e:
            module_logger.exception("message")

    def allkillUpdate(self):
        """In case of allkill move the winner to the next set."""
        self.updateData()
        if(self.matchData.allkillUpdate()):
            self.updateForms()

    def webAppDone_nightbot(self):
        """Call to return of nightbot token."""
        try:
            self.view.mysubwindow1.nightbotToken.setTextMonitored(
                FlaskThread._single.token_nightbot)

            self.view.raise_()
            self.view.show()
            self.view.activateWindow()

            self.view.mysubwindow1.raise_()
            self.view.mysubwindow1.show()
            self.view.mysubwindow1.activateWindow()

        except Exception as e:
            module_logger.exception("message")

    def webAppDone_twitch(self):
        """Call to return of twitch token."""
        try:
            self.view.mysubwindow1.twitchToken.setTextMonitored(
                FlaskThread._single.token_twitch)

            self.view.raise_()
            self.view.show()
            self.view.activateWindow()

            self.view.mysubwindow1.raise_()
            self.view.mysubwindow1.show()
            self.view.mysubwindow1.activateWindow()

        except Exception as e:
            module_logger.exception("message")

    def getNightbotToken(self):
        """Get nightbot token."""
        try:
            self.webApp.start()
            webbrowser.open("http://localhost:65010/nightbot")
        except Exception as e:
            module_logger.exception("message")

    def getTwitchToken(self):
        """Get twitch token."""
        try:
            self.webApp.start()
            webbrowser.open("http://localhost:65010/twitch")
        except Exception as e:
            module_logger.exception("message")

    def updateNightbotCommand(self):
        """Update nightbot commands."""
        try:
            msg = ''
            self.updateData()
            message = scctool.settings.config.parser.get("NightBot", "message")
            message = self.placeholders.replace(message)
            msg = scctool.tasks.nightbot.updateCommand(message)
        except Exception as e:
            msg = str(e)
            module_logger.exception("message")
            pass

        return msg

    def updateTwitchTitle(self):
        """Update twitch title."""
        try:
            msg = ''
            self.updateData()
            try:
                title = scctool.settings.config.parser.get(
                    "Twitch", "title_template")
                title = self.placeholders.replace(title)
                msg = scctool.tasks.twitch.updateTitle(title)
            except Exception as e:
                msg = str(e)
                module_logger.exception("message")
                pass
            self.matchData.writeJsonFile()
        except Exception as e:
            module_logger.exception("message")

        return msg

    def openURL(self, url):
        """Open URL in Browser."""
        if(len(url) < 5):
            url = "http://alpha.tl/match/2392"
        try:
            webbrowser.open(url)
        except Exception as e:
            module_logger.exception("message")

    def runSC2ApiThread(self, task):
        """Start task in thread that monitors SC2-Client-API."""
        try:
            if(not self.SC2ApiThread.isRunning()):
                self.SC2ApiThread.startTask(task)
            else:
                self.SC2ApiThread.cancelTerminationRequest(task)

        except Exception as e:
            module_logger.exception("message")

    def stopSC2ApiThread(self, task):
        """Stop task in thread thats monitors SC2-Client-API."""
        try:
            self.SC2ApiThread.requestTermination(task)
        except Exception as e:
            module_logger.exception("message")

    def runWebsocketThread(self):
        """Run OBS websocket thread."""
        if(not self.websocketThread.isRunning()):
            self.websocketThread.start()
        else:
            self.websocketThread.cancelKillRequest()

    def stopWebsocketThread(self):
        """Stop OBS websocket thread."""
        try:
            self.websocketThread.requestKill()
        except Exception as e:
            module_logger.exception("message")

    def cleanUp(self):
        """Clean up all threads and save config to close program."""
        try:
            self.SC2ApiThread.requestTermination("ALL")
            self.webApp.terminate()
            self.saveConfig()
            self.ftpUploader.kill()
            self.websocketThread.requestKill()
            module_logger.info("cleanUp called")
        except Exception as e:
            module_logger.exception("message")

    def saveConfig(self):
        """Save the settings to the config file."""
        try:
            scctool.settings.config.parser.set("Form", "scoreupdate", str(
                self.view.cb_autoUpdate.isChecked()))
            scctool.settings.config.parser.set("Form", "togglescore", str(
                self.view.cb_autoToggleScore.isChecked()))
            scctool.settings.config.parser.set("Form", "toggleprod", str(
                self.view.cb_autoToggleProduction.isChecked()))
            scctool.settings.config.parser.set("Form", "playerintros", str(
                self.view.cb_playerIntros.isChecked()))
            scctool.settings.config.parser.set(
                "FTP", "upload", str(self.view.cb_autoFTP.isChecked()))

            cfgfile = open(scctool.settings.cfgFile, 'w')
            scctool.settings.config.parser.write(cfgfile)
            cfgfile.close()
        except Exception as e:
            module_logger.exception("message")

    def requestScoreUpdate(self, newSC2MatchData):
        """Update score based on result of SC2-Client-API."""
        try:
            print("Trying to update the score")

            self.updateData()
            newscore = 0
            for i in range(self.matchData.getNoSets()):
                found, newscore = newSC2MatchData.compare_returnScore(
                    self.matchData.getPlayer(0, i),
                    self.matchData.getPlayer(1, i))
                if(found and newscore != 0):
                    if(self.view.setScore(i, newscore)):
                        break
                    else:
                        continue
        except Exception as e:
            module_logger.exception("message")

    def refreshButtonStatus(self):
        """Enable or disable buttons depending on config."""
        if(not scctool.settings.config.twitchIsValid()):
            self.view.pb_twitchupdate.setEnabled(False)
            self.view.pb_twitchupdate.setAttribute(Qt.WA_AlwaysShowToolTips)
            self.view.pb_twitchupdate.setToolTip(
                'Specify your Twitch Settings to use this feature')
        else:
            self.view.pb_twitchupdate.setEnabled(True)
            self.view.pb_twitchupdate.setAttribute(Qt.WA_AlwaysShowToolTips)
            self.view.pb_twitchupdate.setToolTip('')

        if(not scctool.settings.config.nightbotIsValid()):
            self.view.pb_nightbotupdate.setEnabled(False)
            self.view.pb_nightbotupdate.setAttribute(Qt.WA_AlwaysShowToolTips)
            self.view.pb_nightbotupdate.setToolTip(
                'Specify your NightBot Settings to use this feature')
        else:
            self.view.pb_nightbotupdate.setEnabled(True)
            self.view.pb_nightbotupdate.setAttribute(Qt.WA_AlwaysShowToolTips)
            self.view.pb_nightbotupdate.setToolTip('')

        if(not scctool.settings.config.ftpIsValid()):
            self.view.cb_autoFTP.setEnabled(False)
            self.view.cb_autoFTP.setAttribute(Qt.WA_AlwaysShowToolTips)
            self.view.cb_autoFTP.setToolTip(
                'Specify your FTP Settings to use this feature')
        else:
            self.view.cb_autoFTP.setEnabled(True)
            self.view.cb_autoFTP.setAttribute(Qt.WA_AlwaysShowToolTips)
            self.view.cb_autoFTP.setToolTip('')

    def requestToggleScore(self, newSC2MatchData, swap=False):
        """Check if SC2-Client-API players are present and toggle score accordingly."""
        try:
            self.updateData()

            for i in range(self.matchData.getNoSets()):
                found, order = newSC2MatchData.compare_returnOrder(
                    self.matchData.getPlayer(0, i),
                    self.matchData.getPlayer(1, i))

                if(found):
                    score = self.matchData.getScore()
                    if(swap):
                        order = not order

                    if(order):
                        ToggleScore(score[0], score[1],
                                    self.matchData.getBestOf())
                    else:
                        ToggleScore(score[1], score[0],
                                    self.matchData.getBestOf())

                    return

            ToggleScore(0, 0, self.matchData.getBestOf())

        except Exception as e:
            module_logger.exception("message")

    def linkFile(self, file):
        """Return correct img file ending."""
        for ext in [".png", ".jpg"]:
            if(os.path.isfile(file + ext)):
                return file + ext
        return ""

    def updateLogosHTML(self):
        """Update html files with team logos."""
        for idx in range(2):
            filename = scctool.settings.OBShtmlDir + \
                "/data/logo" + str(idx + 1) + "-data.html"
            with open(scctool.settings.OBShtmlDir + "/data/logo-template.html", "rt") as fin:
                logo = self.linkFile(
                    scctool.settings.OBSdataDir + "/" + "logo" + str(idx + 1))
                if logo == "":
                    logo = scctool.settings.OBShtmlDir + "/src/SC2.png"
                with open(filename, "wt") as fout:
                    for line in fin:
                        line = line.replace('%LOGO%', logo)
                        fout.write(line)

        self.ftpUploader.cwd(scctool.settings.OBShtmlDir)

        for file in ["logo1-data.html", "logo2-data.html"]:
            self.ftpUploader.upload(
                scctool.settings.OBShtmlDir + "/data/" + file, file)

        self.ftpUploader.cwd("..")

    def updatePlayerIntros(self, newData):
        """Update player intro files."""
        module_logger.info("updatePlayerIntros")
        self.updateData()

        for player_idx in range(2):
            team1 = newData.playerInList(
                player_idx, self.matchData.getPlayerList(0))
            team2 = newData.playerInList(
                player_idx, self.matchData.getPlayerList(1))

            if((team1 and team2) or not (team1 or team2)):
                team = ""
                logo = ""
                display = "none"
            elif(team1):
                team = self.matchData.getTeam(0)
                logo = self.linkFile(
                    scctool.settings.OBSdataDir + "/" + "logo1")
                display = "block"
            elif(team2):
                team = self.matchData.getTeam(1)
                logo = self.linkFile(
                    scctool.settings.OBSdataDir + "/" + "logo2")
                display = "block"

            if logo == "":
                logo = scctool.settings.OBShtmlDir + "/src/SC2.png"

            filename = scctool.settings.OBShtmlDir + \
                "/intro" + str(player_idx + 1) + ".html"
            with open(scctool.settings.OBShtmlDir + "/data/intro-template.html", "rt") as fin:
                with open(filename, "wt") as fout:
                    for line in fin:
                        line = line.replace(
                            '%NAME%', newData.getPlayer(player_idx))
                        line = line.replace(
                            '%RACE%', newData.getPlayerRace(player_idx) + ".png")
                        line = line.replace('%TEAM%', team)
                        line = line.replace('%DISPLAY%', display)
                        line = line.replace('%LOGO%', logo)
                        fout.write(line)

        self.ftpUploader.cwd(scctool.settings.OBShtmlDir)

        for file in ["intro1.html", "intro2.html"]:
            self.ftpUploader.upload(
                scctool.settings.OBShtmlDir + "/" + file, file)

        self.ftpUploader.cwd("..")

    def getMapImg(self, map, fullpath=False):
        """Get map image from map name."""
        mapimg = os.path.normpath(os.path.join(
            scctool.settings.OBSmapDir, "src/maps", map.replace(" ", "_")))
        mapimg = os.path.basename(self.linkFile(mapimg))
        if not mapimg:
            mapimg = "TBD.jpg"
            self.displayWarning("Warning: Map '{}' not found!".format(map))

        if(fullpath):
            return scctool.settings.OBSmapDir + "/src/maps/" + mapimg
        else:
            return mapimg

    def addMap(self, file, mapname):
        """Add a new map via file and name."""
        _, ext = os.path.splitext(file)
        map = mapname.strip().replace(" ", "_") + ext
        newfile = os.path.normpath(os.path.join(
            scctool.settings.OBSmapDir, "src/maps", map))
        shutil.copy(file, newfile)
        scctool.settings.maps.append(mapname)

        self.ftpUploader.cwd(scctool.settings.OBSmapDir + "/src/maps")
        self.ftpUploader.upload(newfile, self.getMapImg(mapname))
        self.ftpUploader.cwd("../../..")

    def deleteMap(self, map):
        """Delete map and file."""
        self.ftpUploader.cwd(scctool.settings.OBSmapDir + "/src/maps")
        self.ftpUploader.delete(self.getMapImg(map))
        self.ftpUploader.cwd("../../..")

        os.remove(self.getMapImg(map, True))
        scctool.settings.maps.remove(map)

    def displayWarning(self, msg="Warning: Something went wrong..."):
        """Display a warning in status bar."""
        self._warning = True
        self.view.statusBar().showMessage(msg)

    def resetWarning(self):
        """Display or reset warning now."""
        warning = self._warning
        # print(str(warning))
        self._warning = False
        return warning

    def testVersion(self):
        """Run version check."""
        self.checkVersionThread.newVersion.connect(self.newVersionTrigger)
        self.checkVersionThread.start()

    def newVersionTrigger(self, version):
        """Call back to display new version in status bar."""
        version = version.replace("v", "")
        self.view.statusBar().showMessage("At https://github.com/pheenix/StarCraft-Casting-Tool the new version " + version +
                                          " is available!")
