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
from urlparse import urljoin
from urlparse import urlparse
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

def replaceEntities(inData):
    # Source http://dev.w3.org/html5/html-author/charref
    data = inData
    data = re.sub(r'&nbsp;|&#160;', ' ', data)
    data = re.sub(r'&lt;|&#.*?60;', '<', data)
    data = re.sub(r'&gt;|&#.*?62;', '>', data)
    data = re.sub(r'&amp;|&#.*?38;', '&', data)
    data = re.sub(r'&apos;|&#.*?39;', '\'', data)
    data = re.sub(r'&quot;|&#.*?34;', '"', data)
    data = re.sub(r'&tilde;|&#.*?732;', '~', data)
    data = re.sub(r'&circ;|&#.*?710;', '^', data)
    data = re.sub(r'&excl;|&#.*?33;', '!', data)
    data = re.sub(r'&num;|&#.*?35;', '#', data)
    data = re.sub(r'&percnt;|&#.*?37;', '%', data)
    return data

def excludeLocalLinks(localLink):
    # Regex for excluded links
    excludeLink = re.compile('.*?file.ashx.*?|.*?javascript.*?|.*?mailto:.*?|.*?xml.*?')
    if excludeLink.match(localLink):
        print 'Link ', urllib.unquote(localLink), ' is excluded. It will not be fetched...'
        return True
    else:
        return False


def getNewsTitle(htmlData):
    newsTitle = ''
    regExprString = r'<h1 class="article_title">\s*?(.*?)</h1>'
    if re.search(regExprString, htmlData):
        newsTitle = re.search(regExprString, htmlData).group(1)
        newsTitle = replaceEntities(newsTitle)
        # Remove any white spaces in the beginning
        newsTitle = re.sub(r'^[\s]*', '', newsTitle)
        # Remove any white spaces at the end
        newsTitle = re.sub(r'[\s]*$', '', newsTitle)
    else:
        newsTitle = 'N/A'
    return newsTitle

def getNewsAuthor(htmlData):
    newsAuthor = ''
    regExprString = r'.*?<div class="author">\s*(.*?)\s*?</div>'
    if re.search(regExprString, htmlData):
        newsAuthor = re.search(regExprString, htmlData).group(1)
    else:
        newsAuthor = 'N/A'
    return newsAuthor

def getNewsDescription(htmlData):
    newsDescription = ''
    regExprString = r'<meta name="description" content="(.*?)" />'
    # Check if group exists
    if re.search(regExprString, htmlData):
        newsDescription = re.search(regExprString, htmlData).group(1)
        newsDescription = replaceEntities(newsDescription)
    else:
        newsDescription = 'N/A'
    return newsDescription

def getNewsKeywords(htmlData):
    newsKeywords = []
    regExprString = r'<meta name="keywords" content="(.*?)" />'
    if re.search(regExprString, htmlData):
        newsKeywords = re.search(regExprString, htmlData).group(1)
        newsKeywords = replaceEntities(newsKeywords)
        # Split string in commas
        newsKeywords = re.split(',+', str(newsKeywords))
    else:
        newsKeywords = 'N/A'
    return newsKeywords

def getNewsDateCreated(htmlData):
    newsDateCreated = ''
    regExprString = r'<div class="top_date">\s*?.*?: (.*?)\s*?</div>'
    if re.search(regExprString, htmlData):
        newsDateCreated = re.search(regExprString, htmlData).group(1)
    else:
        newsDateCreated = 'N/A'
    return newsDateCreated

def getNewsDateUpdated(htmlData):
    newsDateUpdated = ''
    regExprString = r'<div class="date">\s*?<p>\s*?.*?: (.*?)</p>\s*?</div>'
    if re.search(regExprString, htmlData):
        newsDateUpdated = re.search(regExprString, htmlData).group(1)
    else:
        newsDateUpdated = 'N/A'
    return newsDateUpdated

def getNewsText(htmlData):
    newsText = ''
    regExprString = r'.*?<div class="description">\s([.\s\S]*?)\s.*?</div>'
    if re.search(regExprString, htmlData):
        newsText = re.search(regExprString, htmlData).group(1)
        newsText = replaceEntities(newsText)
        # Remove all the html tags, need a clear text
        newsText = re.sub(r'<[^>]*>', '', newsText)
        # Remove any white spaces in the beginning
        newsText = re.sub(r'^[\s]*', '', newsText)
        # Remove any white spaces at the end
        newsText = re.sub(r'[\s]*$', '', newsText)
    else:
        newsText = 'N/A'
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
    data['NewsDateUpdated'] = getNewsDateUpdated(htmlData)
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


def dumpLinksToFetch(LinksToFetch):
    with open('LinksToFetch.pickle', 'wb') as pickleFileHandle:
        pickle.dump(LinksToFetch, pickleFileHandle)

def dumpLinksFetched(LinksFetched):
    with open('LinksFetched.pickle', 'wb') as pickleFileHandle:
        pickle.dump(LinksFetched, pickleFileHandle)

def restoreLinksToFetch():
    restoredLinksToFetch = set([])
    with open('LinksToFetch.pickle', 'rb') as fileHandle:
        restoredLinksToFetch = pickle.load(fileHandle)
    return restoredLinksToFetch

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

def getLocalLinks(htmlPage, baseURL):
    localLinks = []
    regExprString = r'<a href="(.*?)(#.*?)*"'
    localLinksTemp = re.findall(regExprString, htmlPage)
    # Get the link without the hasgtag anchor
    localLinks = set([ seq[0] for seq in localLinksTemp ])
    fullLinks = set([ urljoin(baseURL, s) for s in localLinks ])
    return fullLinks

def getNewsLinks(htmlPage):
    newsLinks = []
    regExprString = r'<a href="(/news/.*?)(#.*?)*"'
    newsLinksTemp = re.findall(regExprString, htmlPage)
    # Use set in order to get the unique elements and not dublicates
    newsLinks = set([ seq[0] for seq in newsLinksTemp ])
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
    baseURL = 'http://www.zougla.gr/'

    linksToFetch = set([])
    linksFetched = set([])
    localLinksRetrieve = set([])
    # Retrieve the links from the base url if the pickle files are not present
    if os.path.isfile('LinksFetched.pickle') and os.path.isfile('LinksToFetch.pickle'):
        print 'LinksFetched.pickle and LinksToFetch.pickle are present. Restoring...'
        linksToFetch = restoreLinksToFetch()
        linksFetched = restoreLinksFetched()
    else:
        baseHtmlData = getUrl(baseURL)
        linksToFetch = getLocalLinks(baseHtmlData, baseURL)
        linksFetched.add(baseURL)

    print 'Initial unique links to be retrieved ', len(linksToFetch)

    # http://stackoverflow.com/questions/16625960/modifying-a-set-while-iterating-over-it
    while linksToFetch:
        link = linksToFetch.pop()
        print 'Remaining links to be fetched ', len(linksToFetch)

        if link in linksFetched:
            print 'Link ', urllib.unquote(link), ' already fetched...'
            continue

        if excludeLocalLinks(link):
            # Add in the fetched although is not fetched!!!
            linksFetched.add(link)
            continue

        if urlparse(link).netloc != 'www.zougla.gr':
            print 'Link', urllib.unquote(link), ' is not in this domain...'
            linksFetched.add(link)
            continue

        # http://stackoverflow.com/questions/8136788/decode-escaped-characters-in-url
        print 'Fetching...', urllib.unquote(link), ' - ', hashlib.sha1(link).hexdigest()

        htmlData = getUrl(link)

        # Check if it's a news link
        isNewsLink = re.compile('.*?/article/.*?')
        if isNewsLink.match(link):
            writeHTMLToFile(htmlData, 'zougla/'+hashlib.sha1(link).hexdigest()+'.html')

            # http://stackoverflow.com/questions/5648573/python-print-unicode-strings-in-arrays-as-characters-not-code-points
            # print repr(createNewsData(htmlData, fetchNewsLink)).decode("unicode-escape").encode('latin-1')

            jsonData = json.dumps(createNewsData(htmlData, link), sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': '))
            print jsonData

            jsonDump(createNewsData(htmlData, link), 'zougla.json')

        # Get the local links from this page and add them to the linksToFetch
        newLinksToFetch = getLocalLinks(htmlData, link)
        print 'Will be added ', len(newLinksToFetch), ' new links'
        linksToFetch.update(newLinksToFetch)

        # Add the link if successfully fetched.
        linksFetched.add(link)
        print 'Total links fetched so far ', len(linksFetched)

        nextLinkDelay(11, 21)

        dumpLinksToFetch(linksToFetch)
        dumpLinksFetched(linksFetched)

# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == '__main__':
  main()

