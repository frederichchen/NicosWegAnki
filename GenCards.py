import time
import requests
import os
import json
import base64
import re
import shutil
import logging
import subprocess
import operator
from urllib.request import unquote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from DWAnkiCards import DWAnkiCards

# Those are some constants of this program, please set them for your own.
TOP_URLS = {
    "DW Nicos Weg A1": "https://learngerman.dw.com/zh/nicos-weg/c-47993645",
    "DW Nicos Weg A2": "https://learngerman.dw.com/zh/nicos-weg/c-47993807",
}
# Choose which course to download
DECK_NAME = "DW Nicos Weg A1"
IMAGES_DIR = "images"
AUDIO_DIR = "audio"
# We need proxies to visit Deutsche Welle
PROXIES = {"http": "http://127.0.0.1:1080", "https": "http://127.0.0.1:1080"}


# Visit the course list page to get the url for each lesson
def getLessonURLs(browser, url):
    browser.get(url)
    WebDriverWait(browser, 10, 1).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "section.course"))
    )
    lessonURLS = browser.find_elements(By.XPATH, '//*[@id="courses"]//a')
    lessons = []
    for lesson in lessonURLS:
        link = lesson.get_attribute("href")
        # exclude the link for test page
        if unquote(link, "utf-8").find("考试") == -1:
            lessons.append(link + "/lv")
    return lessons


# Get the German word from each vocabulary row
def getGermanFromRow(row):
    try:
        word = row.find_element(By.XPATH, ".//strong").text  # 德语单词
        notes = row.find_elements(By.XPATH, ".//span")  # 如果下面还有复数、比较级之类的注释
        if len(notes) == 2:
            return (word, notes[0].text)
        else:
            return (word, None)
    except:
        log.warning("No German word found!")
        return (None, None)


# Get the Chinese meaning from each vocabulary row
def getChineseFromRow(row):
    word = row.find_element(By.XPATH, ".//span/p").text
    if word:
        return word
    log.warning("No Chinese meaning found!")
    return None


# Get the image url from each vocabulary row if it exists
def getImageURLFromRow(row):
    img_urls = row.find_elements(By.XPATH, ".//img")
    if len(img_urls) >= 1:
        return img_urls[1].get_attribute("src")
    else:
        return ""


# Get the pronunciation audio url from each vocabulary row
def getAudioURLFromRow(row):
    audio_urls = row.find_elements(By.XPATH, './/source[@type="audio/MP3"]')
    if not audio_urls:
        return ""
    return audio_urls[0].get_attribute("src")


# Compress the audio from 128kbps to 32kbps for space sake
def reduceAudioSize(path):
    backupDir = "{}/{}".format(AUDIO_DIR, "backup")
    if not os.path.isdir(backupDir):
        os.mkdir(backupDir)
    fileName = os.path.basename(path)
    backupFilePath = "{}/{}".format(backupDir, fileName)
    if not os.path.isfile(backupFilePath):
        shutil.copyfile(path, backupFilePath)
    # PLEASE SET THE PATH OF LAME ACCORDING TO YOUR OWN SETTINGS
    res = subprocess.run(
        ["D:/Anki/lame.exe", "-b", "32", backupFilePath, path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if res.returncode != 0:
        log.error("Failed to reduce audio size: " + path)
        log.error(res.stderr)
    return


# Download file from given url
def downloadFromURL(url, path):
    if os.path.isfile(path):
        return 1
    try:
        r = requests.get(url, proxies=PROXIES, stream=True)
        if r.status_code == 200:
            with open(path, "wb") as f:
                for chunk in r:
                    f.write(chunk)
            return 1
        return 0
    except:
        return 0


def fileToBase64(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode()


# Give request to AnkiConnect to store the media file
def storeMediaFileJSON(filename, data64):
    request = {
        "action": "storeMediaFile",
        "version": 6,
        "params": {"filename": filename, "data": data64},
    }
    return json.dumps(request)


# Interact with AnkiConnect
def invoke(requestJson):
    response = (requests.post("http://localhost:8765", requestJson)).json()
    if len(response) != 2:
        raise Exception("response has an unexpected number of fields")
    if "error" not in response:
        raise Exception("response is missing required error field")
    if "result" not in response:
        raise Exception("response is missing required result field")
    if response["error"] is not None:
        raise Warning(response["error"])
    return response["result"]


# Store image to local file system
def storeImage(imgURL):
    if not imgURL:
        return None
    imgFilename = re.sub(r"\s+", "_", os.path.basename(imgURL))
    imgPath = "{}/{}".format(IMAGES_DIR, imgFilename)
    log.info("Downloading image: " + imgURL)
    dlSuccess = downloadFromURL(imgURL, imgPath)
    if dlSuccess:
        img64 = fileToBase64(imgPath)
        log.info("Saving image to Anki: " + imgFilename)
        res = invoke(storeMediaFileJSON(imgFilename, img64))
        if res:
            return imgFilename
    return None


# 存储音频
def storeAudio(audioURL):
    if not audioURL:
        return None
    audioFilename = re.sub(r"\s+", "_", os.path.basename(audioURL))
    audioPath = "{}/{}".format(AUDIO_DIR, audioFilename)
    log.info("Downloading audio: " + audioURL)
    dlSuccess = downloadFromURL(audioURL, audioPath)
    if dlSuccess:
        reduceAudioSize(audioPath)
        audio64 = fileToBase64(audioPath)
        log.info("Saving audio to Anki: " + audioFilename)
        res = invoke(storeMediaFileJSON(audioFilename, audio64))
        if res:
            return audioFilename
    log.warning("The audio file does not exist " + audioURL)
    return None


def buildAnkiFromURL(browser, cards, vocabURL):
    try:
        lessonName = (re.search(r"zh\/([^\/]+)\/", vocabURL)).group(1)
    except AttributeError:
        log.critical("Cannot find any lesson: " + vocabURL)
        raise SystemExit(1)

    tag = lessonName
    print("Lesson: " + tag)
    browser.get(vocabURL)
    WebDriverWait(browser, 10, 1).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.knowledge-wrapper"))
    )
    # Scroll the page three times in order for the browser to load all the picutres
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight/3)")
    time.sleep(2)
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight/2)")
    time.sleep(1)
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    vocab_rows = browser.find_elements(
        By.XPATH, "//div[@class='knowledge-wrapper']/div[@class='sc-dRGAjo kiDMro']"
    )
    for row in vocab_rows:
        de, note = getGermanFromRow(row)
        ch = getChineseFromRow(row)
        if ch == None or de == None:
            log.info("No vocabulary found, possibly a blank div.")
            continue

        log.info("Processing Anki Card %s -> %s ..." % (de, ch))
        card = DWAnkiCards(DECK_NAME)
        card.addTag(tag)
        imgUrl = getImageURLFromRow(row)
        imgFilename = storeImage(imgUrl)
        audioUrl = getAudioURLFromRow(row)
        audioFilename = storeAudio(audioUrl)
        # Add Content to card, if the word is a noun, then I add the plural form to the back of the card.
        de_noun = re.match(r"^(der|das|die) (\S+)", de.replace(",", ""))
        if de_noun:
            if note:
                card.addChinese(
                    ch + " <br>" + de + " <br><small><i>" + note,
                    imgFilename,
                    audioFilename,
                )
                card.addGerman(de_noun[2])
            else:
                card.addChinese(ch + " <br>" + de, imgFilename, audioFilename)
                card.addGerman(de_noun[2])
        else:
            if note:
                card.addChinese(
                    ch + " <br><small><i>" + note, imgFilename, audioFilename
                )
                card.addGerman(de)
            else:
                card.addChinese(ch, imgFilename, audioFilename)
                card.addGerman(de)

        if de in cards:
            log.info(de + " already exists, add content to the existing card. ")
            (cards[de]).addChinese(card.getChinese())
        else:
            cards[de] = card


def createDeckJSON(deck):
    request = {"action": "createDeck", "version": 6, "params": {"deck": deck}}
    return json.dumps(request)


def addNoteJSON(deck, tags, front, back):
    request = {
        "action": "addNote",
        "version": 6,
        "params": {
            "note": {
                "deckName": deck,
                # YOU SHOULD MODIFY THE modelName and fields according to your Anki settings.
                "modelName": "问答题",
                "fields": {"正面": front, "背面": back},
                "options": {"allowDuplicate": True},
                "tags": tags,
            }
        },
    }
    return json.dumps(request)


def storeCards(cards):
    for card in sorted(cards.values(), key=operator.attrgetter("cardNumber")):
        req = addNoteJSON(card.deck, card.tags, card.getGerman(), card.getChinese())
        try:
            res = invoke(req)
            if card.hasImage:
                log.info("card added {}: {}".format(res, card.getGerman()))
            else:
                log.info("card added {}: {}".format(res, card.getGerman()))
        except Warning as err:
            log.warning(err.args[0] + ": " + card.getChinese())
        except Exception as err:
            log.error(err.args[0] + ": " + card.getChinese())


# The program starts with making directories.
if not os.path.isdir(IMAGES_DIR):
    os.mkdir(IMAGES_DIR)
if not os.path.isdir(AUDIO_DIR):
    os.mkdir(AUDIO_DIR)

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler("run.log"), logging.StreamHandler()],
)

option = webdriver.ChromeOptions()
# I used my own user-data-dir to start chrome in order to use proxy plugin.
option.add_argument(
    "--user-data-dir=C:/Users/Administrator/AppData/Local/Google/Chrome/User Data"
)
browser = webdriver.Chrome(options=option)

log.info("Creating Deck: " + DECK_NAME)
invoke(createDeckJSON(DECK_NAME))
lessonURLs = getLessonURLs(browser, TOP_URLS[DECK_NAME])
cards = {}
for url in lessonURLs:
    log.info("Downloading cards from %s ..." % url)
    buildAnkiFromURL(browser, cards, url)
    log.info("Finish downloading from page: " + url)

log.info("Creating cards in Anki...")
storeCards(cards)
log.info("Finished!")
browser.quit()
