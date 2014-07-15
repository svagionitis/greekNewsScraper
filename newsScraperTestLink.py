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
import posixpath
import sqlite3  ##sqlite
import hashlib  ##hash md5 sha1...
import pickle   ##pickle to serialize data
import json     ##json to serialize data, web friendly?? and read json config file

# http://wolfprojects.altervista.org/changeua.php
from urllib import FancyURLopener

# Global variable for json conf file
jsonConf = {}

# Use google bot as user agent
class MyOpener(FancyURLopener):
    version = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'

def readJsonConfFile(filename):
    global jsonConf
    with open(filename)  as jsonFileHandle:
        jsonConf = json.load(jsonFileHandle)

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
    excludeLink = re.compile(jsonConf['LinksRegEx']['LinksExcluded'])
    if excludeLink.match(localLink):
        print 'Link ', repr(urllib.unquote(localLink)).decode("unicode-escape").encode('latin-1'), ' is excluded. It will not be fetched...'
        return True
    else:
        return False

def getNewsData(htmlData, regexString):
    newsData = None
    newsDataRegEx = re.compile(regexString)
    if newsDataRegEx.search(htmlData):
        newsData = newsDataRegEx.search(htmlData).group(1)
        newsData = replaceEntities(newsData)
        # Remove the images attached
        newsData = re.sub(r'<table.*?>[.\s\S]*?</table>', '', newsData)
        # Remove all the html tags, need a clear text
        newsData = re.sub(r'<[^>]*>', '', newsData)
        # Remove any white spaces in the beginning
        newsData = re.sub(r'^[\s]*', '', newsData)
        # Remove any white spaces at the end
        newsData = re.sub(r'[\s]*$', '', newsData)
        if regexString == jsonConf['NewsRegEx']['NewsKeywords']:
            # Split string in commas
            newsData = re.split(',+', str(newsData))

    else:
        newsData = 'N/A'
    return newsData

def createNewsData(htmlData, fullNewsURL):
    data = {}
    data['DateRetrieved'] = str(datetime.now())

    data['NewsLink'] = repr(urllib.unquote(fullNewsURL)).decode("unicode-escape").encode('latin-1')
    data['HashNewsLink'] = hashlib.sha1(fullNewsURL).hexdigest()

    data['NewsTitle'] = getNewsData(htmlData, jsonConf['NewsRegEx']['NewsTitle'])

    data['NewsAuthor'] = getNewsData(htmlData, jsonConf['NewsRegEx']['NewsAuthor'])

    data['NewsDescription'] = getNewsData(htmlData, jsonConf['NewsRegEx']['NewsDescription'])

    data['NewsKeywords'] = getNewsData(htmlData, jsonConf['NewsRegEx']['NewsKeywords'])

    data['NewsDateCreated'] = getNewsData(htmlData, jsonConf['NewsRegEx']['NewsDateCreated'])
    data['NewsDateUpdated'] = getNewsData(htmlData, jsonConf['NewsRegEx']['NewsDateUpdated'])

    newsText = getNewsData(htmlData, jsonConf['NewsRegEx']['NewsText'])
    data['NewsText'] = newsText
    data['HashNewsText'] = hashlib.sha1(newsText).hexdigest()
    return data

def jsonDump(data, jsonFilename):
    with open(jsonFilename, 'a+') as jsonFileHandle:
        json.dump( data, jsonFileHandle, ensure_ascii = False, sort_keys = True, indent = 4, separators = (',', ': '))

def nextLinkDelay(startDelay, endDelay):
    randomNum = 0
    randomNum = random.randint(startDelay, endDelay)
    print 'Delaying for ', randomNum, ' sec'
    time.sleep(randomNum)


def dumpPickle(LinksToFetch, filename):
    with open(filename, 'wb') as pickleFileHandle:
        pickle.dump(LinksToFetch, pickleFileHandle)

def restorePickle(filename):
    restoredPickle = set([])
    with open(filename, 'rb') as fileHandle:
        restoredPickle = pickle.load(fileHandle)
    return restoredPickle

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

def createAbsoluteURL(home, url):
    home = unicode(home, 'utf-8', errors='ignore')
    url = unicode(url, 'utf-8', errors='ignore')

    print 'Processing home: ', home, 'url: ', url
    join = urlparse.urljoin(home, url)
    parse = urlparse.urlparse(join)
    path = posixpath.normpath(parse[2])

    absolute = urlparse.urlunparse((parse.scheme, parse.netloc, path, parse.params, parse.query, None))

    print 'Absolute: ', absolute
    return absolute

def getLocalLinks(htmlPage, baseURL, fetchedLinks, toBeFetchedLinks):
    localLinks = []
    regExprString = jsonConf['LinksRegEx']['LocalLinks']
    localLinks = re.findall(regExprString, htmlPage)
    # Create the full link
    fullLinks = set([ createAbsoluteURL(baseURL, s) for s in localLinks ])
    return set(fullLinks - (fetchedLinks | toBeFetchedLinks))

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
        print 'Problem reading url:', repr(urllib.unquote(url)).decode("unicode-escape").encode('latin-1')
        sys.exit(1)

def usage():
    print("Usage: %s <json conf file> <link to test>" % sys.argv[0])
    sys.exit(0)

# Gather our code in a main() function
def main():

    if len(sys.argv) != 3:
        usage()

    # Read json conf files
    readJsonConfFile(sys.argv[1])

    baseURL = jsonConf['BaseURL']

    linksToFetch = set([])
    linksFetched = set([])

    # http://stackoverflow.com/questions/16625960/modifying-a-set-while-iterating-over-it
    link = sys.argv[2]
    print 'Link poped...', link

    if excludeLocalLinks(link):
        sys.exit(0)

    if jsonConf['NetworkLocation'] not in urlparse.urlparse(link).netloc:
        print 'Link', repr(urllib.unquote(link)).decode("unicode-escape").encode('latin-1'), ' is not in this domain...'
        sys.exit(0)

    # http://stackoverflow.com/questions/8136788/decode-escaped-characters-in-url
    print 'Fetching...', repr(urllib.unquote(link)).decode("unicode-escape").encode('latin-1'), ' - ', hashlib.sha1(link).hexdigest()

    htmlData = getUrl(link)

    # Check if empty
    if not htmlData:
        print 'Link ', repr(urllib.unquote(link)).decode("unicode-escape").encode('latin-1'), ' appears empty...'
        print 'The content is @@', htmlData, '@@'
        sys.exit(0)

    # Check if it's a news link
    isNewsLink = re.compile(jsonConf['LinksRegEx']['LinksIncluded'])
    if isNewsLink.match(link):
        data = createNewsData(htmlData, link)
        jsonData = json.dumps(data, ensure_ascii = False, sort_keys = True, indent = 4, separators = (',', ': '))
        print jsonData

        # Get the local links from this page and add them to the linksToFetch
    newLinksToFetch = getLocalLinks(htmlData, link, linksFetched, linksToFetch)
    print 'Will be added ', len(newLinksToFetch), ' new links'

# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == '__main__':
  main()

