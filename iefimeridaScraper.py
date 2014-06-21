#!/usr/bin/python -tt

# import modules used here -- sys is a very standard one
import os
import io
import sys
import re
import random   ##for pseudo-random generation
import time     ##for time functions and sleep
from datetime import datetime ##get time
import urllib   ##url fetching
import urlparse ##url parse
import sqlite3  ##sqlite
import hashlib  ##hash md5 sha1...
import pickle   ##pickle to serialize data
import json     ##json to serialize data, web friendly??

# http://wolfprojects.altervista.org/changeua.php
from urllib import FancyURLopener

# Use google bot as user agent
class MyOpener(FancyURLopener):
    version = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'


def readFile(filename):
    """Read a filename. Output is the content of the file as a string"""
    output = ''
    try:
        fileHandler = open(filename, 'rU')
        output = fileHandler.read()
        fileHandler.close()
        return output
    except IOError:
        print 'Problem reading file: ', filename

def replaceEntities(htmlData):
    data = htmlData
    data = re.sub(r'&nbsp;|&#160;', ' ', data)
    data = re.sub(r'&lt;|&#60;', '<', data)
    data = re.sub(r'&gt;|&#62;', '>', data)
    data = re.sub(r'&amp;|&#38;', '&', data)
    data = re.sub(r'&#039;', '\'', data)
    return data

def getNewsLink(baseURL, newsURL):
    url = baseURL + newsURL
    return url

def getNewsTitle(htmlData):
    newsTitle = ''
    regExprString = r'.*?<div class="views-field-title">\s.*?<span class="field-content"><h1>(.*?)</h1></span>\s.*?</div>'
    newsTitle = re.search(regExprString, htmlData).group(1)
    return newsTitle

def getNewsAuthor(htmlData):
    newsAuthor = 'Anonymous'
    return newsAuthor

def getNewsDescription(htmlData):
    newsDescription = ''
    regExprString = r'<meta name="description" content="(.*?)" />'
    newsDescription = re.search(regExprString, htmlData).group(1)
    newsDescription = replaceEntities(newsDescription)
    return newsDescription

def getNewsKeywords(htmlData):
    newsKeywords = []
    regExprString = r'<meta name="keywords" content="(.*?)" />'
    newsKeywords = re.search(regExprString, htmlData).group(1)
    # Split string in commas
    newsKeywords = re.split(',+', str(newsKeywords))
    return newsKeywords

def getNewsDateCreated(htmlData):
    newsDateCreated = ''
    regExprString = r'.*?<div class="views-field-created">\s.*?<span class="field-content">(.*?)</span>\s.*?</div>'
    newsDateCreated = re.search(regExprString, htmlData).group(1)
    return newsDateCreated

def getNewsText(htmlData):
    newsText = ''
    regExprString = r'.*?<div class="content clear-block">\s([.\s\S]*?)\s.*?</div>'
    newsText = re.search(regExprString, htmlData).group(1)
    newsText = replaceEntities(newsText)
    # Remove the images attached
    newsText = re.sub(r'<table.*?>[.\s\S]*?</table>', '', newsText)
    # Remove all the html tags, need a clear text
    newsText = re.sub(r'<[^>]*>', '', newsText)
    # Remove any white spaces in the beginning
    newsText = re.sub(r'^[\s]*', '', newsText)
    # Remove any white spaces at the end
    newsText = re.sub(r'[\s]*$', '', newsText)
    return newsText

def createNewsData(htmlData, fullNewsURL):
    data = {}
    data['DateRetrieved'] = str(datetime.now())
    data['NewsLink'] = urllib.unquote(fullNewsURL)
    data['HashNewsLink'] = hashlib.sha1(fullNewsURL).hexdigest()
    data['NewsTitle'] = getNewsTitle(htmlData)
    data['NewsAuthor'] = getNewsAuthor(htmlData)
    data['NewsDescription'] = getNewsDescription(htmlData)
    data['NewsKeywords'] = getNewsKeywords(htmlData)
    data['NewsDateCreated'] = getNewsDateCreated(htmlData)
    data['NewsText'] = getNewsText(htmlData)
    data['HashNewsText'] = hashlib.sha1(getNewsText(htmlData)).hexdigest()
    return data

def jsonDump(data, jsonFilename):
    with open(jsonFilename, 'a+') as jsonFileHandle:
        json.dump( data, jsonFileHandle, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': '))

def nextLinkDelay(startDelay, endDelay):
    randomNum = 0
    randomNum = random.randint(startDelay, endDelay)
    print 'Delaying for ', randomNum, ' sec'
    time.sleep(randomNum)


def dumpLinksToRetrieve(LinksToRetrieve):
    with open('LinksToRetrieve.pickle', 'wb') as pickleFileHandle:
        pickle.dump(LinksToRetrieve, pickleFileHandle)

def dumpLinksFetched(LinksFetched):
    with open('LinksFetched.pickle', 'wb') as pickleFileHandle:
        pickle.dump(LinksFetched, pickleFileHandle)

def restoreLinksToRetrieve():
    restoredLinksToRetrieve = set([])
    with open('LinksToRetrieve.pickle', 'rb') as fileHandle:
        restoredLinksToRetrieve = pickle.load(fileHandle)
    return restoredLinksToRetrieve

def restoreLinksFetched():
    restoredLinksFetched = set([])
    with open('LinksFetched.pickle', 'rb') as fileHandle:
        restoredLinksFetched = pickle.load(fileHandle)
    return restoredLinksFetched

def writeHTMLToFile(htmlData, filename):
    # Check if directory exists, if not create it
    dir = os.path.dirname(filename)
    if not os.path.exists(dir):
        os.makedirs(dir)
    try:
        fileHandler = open(filename, 'w')
        fileHandler.write(htmlData)
        fileHandler.close()
    except IOError:
        print 'Problem writing to file ', filename
        sys.exit(1)

def getNewsLinks(htmlPage):
    newsLinks = []
    regExprString = r'<a href="(/news/.*?)"'
    # Use set in order to get the unique elements and not dublicates
    newsLinks = set(re.findall(regExprString, htmlPage))
    return newsLinks

## Version that uses try/except to print an error message if the
## urlopen() fails.
def getUrl(url):
    myopener = MyOpener()

    try:
        #ufile = urllib.urlopen(url)
        ufile = myopener.open(url)
        if ufile.info().gettype() == 'text/html':
            return ufile.read()
    except IOError:
        print 'Problem reading url:', url
        sys.exit(1)


# Gather our code in a main() function
def main():
    base_url = 'http://www.iefimerida.gr'

    linksRetrieve = []
    linksFetched = set([])
    # Retrieve the links from the base url
    baseHtmlData = getUrl(base_url)
    linksRetrieve = getNewsLinks(baseHtmlData)

    print 'Initial unique links to be retrieved ', len(linksRetrieve)

    # http://stackoverflow.com/questions/16625960/modifying-a-set-while-iterating-over-it
    while linksRetrieve:
        link = linksRetrieve.pop()
        print 'Remaining links to be retrieved ', len(linksRetrieve)

        if link in linksFetched:
            print 'Link ', link, ' already retieved...'
            continue

        # Construct the news link
        fetchNewsLink = getNewsLink(base_url, link)
        # http://stackoverflow.com/questions/8136788/decode-escaped-characters-in-url
        print 'Fetching...', urllib.unquote(fetchNewsLink), ' - ', hashlib.sha1(fetchNewsLink).hexdigest()

        htmlData = getUrl(fetchNewsLink)
        writeHTMLToFile(htmlData, 'iefimerida/'+hashlib.sha1(fetchNewsLink).hexdigest()+'.html')

        # http://stackoverflow.com/questions/5648573/python-print-unicode-strings-in-arrays-as-characters-not-code-points
        # print repr(createNewsData(htmlData, fetchNewsLink)).decode("unicode-escape").encode('latin-1')

        jsonData = json.dumps(createNewsData(htmlData, fetchNewsLink), sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': '))
        print jsonData

        jsonDump(createNewsData(htmlData, fetchNewsLink), 'iefimerida.json')

        # Get the news links from this page and add them to the linksRetrieve
        latestRetrievedLinks = getNewsLinks(htmlData)
        print 'Will be added ', len(latestRetrievedLinks), ' new links'
        linksRetrieve.update(latestRetrievedLinks)

        # Add the link if successfully fetched.
        linksFetched.add(link)
        print 'Total links fetched so far ', len(linksFetched)

        nextLinkDelay(11, 21)

        dumpLinksToRetrieve(linksRetrieve)
        dumpLinksFetched(linksFetched)

# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == '__main__':
  main()

