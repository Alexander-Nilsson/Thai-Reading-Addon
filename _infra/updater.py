import time

from anki.hooks import wrap
from aqt import addons, mw

from . import show_info

addonId = 1051095155
dledIds = []


def shutdownDB(parent, mgr, ids, on_done, client):
    global dledIds
    dledIds = ids
    if addonId in ids and hasattr(mw, "ThaiReading"):
        show_info(
            "Thai Reading's database will be disconnected so that the update may proceed. "
            "The add-on will not function properly until Anki is restarted after the update."
        )
        mw.ThaiReading.db.closeConnection()
        mw.ThaiReading.db = False
        time.sleep(2)


def restartDB(*args):
    if addonId in dledIds and hasattr(mw, "ThaiReading"):
        show_info(
            "Thai Reading has been updated. Thai Reading will not function properly until Anki is restarted. "
            "Please restart Anki to start using the new version now!"
        )


def wrapOnDone(self, log):
    self.mgr.mw.progress.timer(50, lambda: restartDB(), False)


addons.download_addons = wrap(addons.download_addons, shutdownDB, "before")
addons.DownloaderInstaller._download_done = wrap(addons.DownloaderInstaller._download_done, wrapOnDone)
