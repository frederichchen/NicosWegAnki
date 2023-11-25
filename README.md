# NicosWegAnki: A tool to make vocabulary Anki flashcards from DW Nicos Weg

# NicosWegAnki：一个从 DW 网站下载 Nicos Weg 词汇表并制作 Anki 闪卡的小工具

Nicos Weg is a wonderful resource to learn German. I use this program to download vocabularies and make flashcards for Anki to help me learn German. This program is a modification of [brkhrdt's dw_anki](https://github.com/brkhrdt/dw_anki).

Nicos Weg 是德国之声推出的非常好的学习德语的课程，这个程序就是用来从网页上爬取相应的词汇做成Anki闪卡，帮我学习和背单词。本程序修改自 [brkhrdt's dw_anki](https://github.com/brkhrdt/dw_anki)。


## Installation 安装

1. Open Anki and Install [AnkiConnect](https://ankiweb.net/shared/info/2055492159) plugin.
2. Install programs and python packages for this program: Chrome, chrome_driver, selenium 4, lxml, requests 
3. Modify the hardcoded constants in GenCards.py, e.g deckName, modelName, fields, path of lame etc.
4. execute python GenCards.py

1. 打开 Anki ，并安装 [AnkiConnect](https://ankiweb.net/shared/info/2055492159) 插件
2. 安装程序运行需要的软件和Python包：Chrome、chrome_driver、selenium 4、lxml 以及 requests 。
3. 修改 GenCards.py 中硬编码的那些数值，比如 deckName, modelName, fields 以及 lame 的路径等等。
4. 执行 python GenCards.py
