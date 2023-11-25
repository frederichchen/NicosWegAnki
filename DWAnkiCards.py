class DWAnkiCards:
    card_count = 0

    def __init__(self, deck):
        self.deck = deck
        self.tags = []
        self.chinese = []
        self.german = []
        self.hasImage = 0
        self.hasAudio = 0
        self.cardNumber = DWAnkiCards.card_count
        DWAnkiCards.card_count += 1

    def addTag(self, tag):
        (self.tags).append(tag)

    # Add Chinese meanings of the words together with audios and images to the back of Anki Flashcards
    def addChinese(self, chinese, imgFilename=None, audioFilename=None):
        audioHTML = ""
        chineseHTML = chinese
        imgHTML = ""
        if audioFilename:
            audioHTML = "[sound:{}]".format(audioFilename)
        if imgFilename:
            imgHTML = '<br><img src="' + imgFilename + '" width="50%" height="50%">'
        (self.chinese).append(audioHTML + chineseHTML + imgHTML)

    # Add German words to the front of Anki Flashcards
    def addGerman(self, german, audioFilename=None, imgFilename=None):
        audioHTML = ""
        germanHTML = german
        imgHTML = ""
        if audioFilename:
            audioHTML = "[sound:{}]".format(audioFilename)
        if imgFilename:
            imgHTML = '<img src="' + imgFilename + '" width="50%" height="50%"><br>'
        (self.german).append(audioHTML + germanHTML + imgHTML)

    def getChinese(self):
        entries = list(set(self.chinese))
        return "<br><br>".join(entries)

    def getGerman(self):
        entries = list(set(self.german))
        return "<br><br>".join(entries)
