# Import the modules
import os, time, urllib2, xbmc, xbmcaddon, xbmcgui, xbmcvfs

# Constants
ACTION_PREVIOUS_MENU = 10
ACTION_BACKSPACE = 110
ACTION_NAV_BACK = 92
ADD_ON_ID = 'script.securitycam'

# Set plugin variables
__addon__    = xbmcaddon.Addon()
__cwd__      = __addon__.getAddonInfo('path').decode("utf-8")
__icon__     = xbmc.translatePath(os.path.join(__cwd__, 'icon.png').encode("utf-8")).decode("utf-8")
__profile__  = xbmc.translatePath(__addon__.getAddonInfo('profile')).decode("utf-8")
__resource__ = xbmc.translatePath(os.path.join(__cwd__, 'resources').encode("utf-8")).decode("utf-8")
__snapshot_dir__ = xbmc.translatePath(os.path.join(__profile__, 'snapshots').encode("utf-8")).decode("utf-8")

# Get settings
url        = __addon__.getSetting('url')
username   = __addon__.getSetting('username')
password   = __addon__.getSetting('password')
authtype   = __addon__.getSetting('authtype')
width      = int(float(__addon__.getSetting('width')))
height     = int(float(__addon__.getSetting('height')))
xoffset    = int(float(__addon__.getSetting('xoffset')))
yoffset    = int(float(__addon__.getSetting('yoffset')))
interval   = int(float(__addon__.getSetting('interval')))
autoclose  = (__addon__.getSetting('autoclose') == 'true')
duration   = int(float(__addon__.getSetting('duration')) * 1000)
slidespeed = int(float(__addon__.getSetting('slidespeed')))

# Utils

def log(message,loglevel=xbmc.LOGNOTICE):
    xbmc.log((ADD_ON_ID + ": " + message).encode('UTF-8','replace'),level=loglevel)

# Classes
class CamPreviewDialog(xbmcgui.WindowDialog):
    def __init__(self):
        log('CamPreviewDialog Initialized \n', xbmc.LOGDEBUG)
        COORD_GRID_WIDTH = 1280
        COORD_GRID_HEIGHT = 720
        scaledWidth = int(float(COORD_GRID_WIDTH) / self.getWidth() * width)
        scaledHeight = int(float(COORD_GRID_HEIGHT) / self.getHeight() * height)
        self.image = xbmcgui.ControlImage(COORD_GRID_WIDTH - scaledWidth - xoffset, COORD_GRID_HEIGHT - scaledHeight - yoffset, scaledWidth, scaledHeight, __icon__)
        self.addControl(self.image)
        self.image.setAnimations([('WindowOpen', 'effect=slide start=%(start)d time=%(time)d tween=cubic easing=in' % {'start': scaledWidth + xoffset,'time': slidespeed}),('WindowClose', 'effect=slide end=%(end)d time=%(time)d tween=cubic easing=in' % {'end': scaledWidth + xoffset,'time': slidespeed})])

    def start(self, autoclose, duration, interval, url, destination):
        log('CamPreviewDialog Started \n', xbmc.LOGDEBUG)
        self.isRunning = bool(1)
        snapshot = ''
        startTime = time.time()
        shown = False
        while(not autoclose or (time.time() - startTime) * 1000 <= duration):
            if xbmcvfs.exists(snapshot):
                os.remove(snapshot)

            snapshot = self.downloadSnapshot(url, destination)

            if snapshot != '':
                self.update(snapshot)

            if not shown:
                self.show()
                shown = True

            xbmc.sleep(interval)
            if not self.isRunning:
                break
        self.close()

    def downloadSnapshot(self, url, destination):
        log('Retreiving Image \n', xbmc.LOGDEBUG)
        try:
            imgData = urllib2.urlopen(url).read()
            filename = snapshot = xbmc.translatePath( os.path.join( destination, 'snapshot' + str(time.time()) + '.jpg' ).encode("utf-8") ).decode("utf-8")
            output = open(filename,'wb')
            log('Saving Image To: [' + filename + ']\n', xbmc.LOGDEBUG)
            output.write(imgData)
            output.close()
            return filename
        except:
            return ''

    def onAction(self, action):
        log('Received Action: ' + str(action.getId()) + '\n', xbmc.LOGDEBUG)
        if action in (ACTION_PREVIOUS_MENU, ACTION_BACKSPACE, ACTION_NAV_BACK):
            self.isRunning = bool(0)
            self.close()

    def update(self, image):
        log('Updating Image \n', xbmc.LOGDEBUG)
        self.image.setImage(image, bool(0))

# Main execution

log('Autoclose: [' + str(autoclose) + ']\n', xbmc.LOGDEBUG)
log('Duration: [' + str(duration) + ']\n', xbmc.LOGDEBUG)
log('Interval: [' + str(interval) + ']\n', xbmc.LOGDEBUG)
log('Width: [' + str(width) + ']\n', xbmc.LOGDEBUG)
log('Height: [' + str(height) + ']\n', xbmc.LOGDEBUG)
log('Original URL: [' + url + ']\n', xbmc.LOGDEBUG)

# Add Basic Authentication Headers
if (username is not None and username != ''):
    passwordManager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passwordManager.add_password(None, url, username, password)
    if authtype == 'Basic': authhandler = urllib2.HTTPBasicAuthHandler(passwordManager)
    if authtype == 'Digest': authhandler = urllib2.HTTPDigestAuthHandler(passwordManager)
    opener = urllib2.build_opener(authhandler)
    urllib2.install_opener(opener)

# Replace URL agruments
argCount = len(sys.argv)
for i in xrange(1, argCount):
    search = '{%d}'%(i - 1)
    replace = sys.argv[i]
    url.replace(search, replace)

log('Final URL: [' + url + ']\n', xbmc.LOGDEBUG)

xbmcvfs.mkdir(__snapshot_dir__)

camPreview = CamPreviewDialog()
camPreview.start(autoclose, duration, interval, url, __snapshot_dir__)
del camPreview

dirs, files = xbmcvfs.listdir(__snapshot_dir__)
for file in files:
    log('Delete remaining snapshot: [' + file + ']\n', xbmc.LOGDEBUG)
    xbmcvfs.delete(os.path.join(__snapshot_dir__, file))
