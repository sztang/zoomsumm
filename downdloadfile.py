from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
import configparser
from time import sleep
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def run():
    options = webdriver.ChromeOptions()
    options.add_argument('--load-extension=enable')
    # options.add_argument('--headless')
    options.add_experimental_option("prefs", {
        "download.default_directory": ROOT_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    driver = webdriver.Chrome('./chromedriver', options=options)
    url = 'https://nyu.zoom.us/rec/play/UKPXKO2LUQA6ysW8ogVJ5rkihlQ7VvMTG_oEJiPM043SFe5SennJZH5jcns0FMArfFhw7IluTVdVaMcf.ZBgkgKliJdnSdPfM?continueMode=true'
    if not url:
        url = input('Hurl the URL this way my guy:\n')
    driver.get(url)
    print(driver.title)

    config = configparser.ConfigParser()
    config.read('credentials.ini')
    USERNAME = config.get('ZOOM','USER')
    PASSWORD = config.get('ZOOM','PASS')

    def nyulogin():
        driver.find_element_by_class_name('login-btn-sso').click()
        # sleep(1.5)

        domain = driver.find_element_by_name('domain')
        domain.clear()
        domain.send_keys('nyu')
        driver.find_element_by_class_name('submit').click()
        # sleep(1.5)
    
        username = driver.find_element_by_id("username")
        username.clear()
        username.send_keys(USERNAME)

        password = driver.find_element_by_id("password")
        password.clear()
        password.send_keys(PASSWORD)
        
        driver.find_element_by_name('_eventId_proceed').click()
        # sleep(1.5)

        driver.switch_to.frame(driver.find_element_by_id('duo_iframe'))
        # if ('Choose an authentication method' in driver.page_source):
        #     print('text exists')
        driver.find_element_by_xpath("//button[contains(text(), 'Push')]").click()

    if ('Sign In' in driver.page_source):
        print('Need to sign in')
        nyulogin()
        sleep(10) # wait for user to do 2FA

    """
    Improvement: after sleep (waiting for user 2FA), listen for video page to load.
    Once loaded, stop the sleep and go straight to download actions.
    """
    
    video = driver.find_element_by_tag_name("video")
    videosrc = video.get_attribute('src')
    videodate = videosrc.split('GMT',1)[1]
    videodate = videodate.split('-',1)[0]
    title = driver.title
    if ' Zoom' in title:
        title = title.replace(' Zoom','')
    for c in [':',' ','-']:
        title = title.replace(c,'_')
    if title[-1] != '_':
        title = title + '_'
    filename = title + videodate
    for x in ['__','___']:
        filename = filename.replace(x,'_')
    print(filename)

    # selenium right click on video, pynput simulate keyboard
    # down arrow x4 (to reach 'Save Video As'), enter, enter again at save window
    from pynput.keyboard import Key, Controller
    keyboard = Controller()
    action = ActionChains(driver)
    action.context_click(video).perform()
    sleep(1.5)

    for _ in range(4):
        keyboard.press(Key.down)
        keyboard.release(Key.down)
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)
    sleep(5)

    keyboard.type(ROOT_DIR+"/file_io") # enter download directory
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)
    sleep(1)

    keyboard.type(filename) # enter download name
    keyboard.press(Key.enter) # confirm download
    keyboard.release(Key.enter)

    sleep(15) # wait for download to finish
    driver.close()

if __name__ == "__main__":
    run()

"""
Zoom recording page has some kind of auth - cannot download file from link.
Must download from page itself after auth.
Page has right click disabled - must disable javascript through Chrome DevTools
For safari: Develop -> Disable Javascript
Right click and save video as

Different method:
package as app
input url
open a browser window
take control of keys/mouse to download vid
"""