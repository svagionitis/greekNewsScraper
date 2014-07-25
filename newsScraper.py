#!/usr/bin/python -tt

# import modules used here -- sys is a very standard one
import os
import io
import sys
import re
import random   ##for pseudo-random generation
import time     ##for time functions and sleep
from datetime import datetime ##get time
# http://wolfprojects.altervista.org/changeua.php
import urllib   ##url fetching, FancyURLopener see 
import urlparse ##url parse
import posixpath
import sqlite3  ##sqlite
import hashlib  ##hash md5 sha1...
import pickle   ##pickle to serialize data
import json     ##json to serialize data, web friendly?? and read json config file

# Global variable for json conf file
jsonConf = {}

# Use google bot as user agent
class MyOpener(urllib.FancyURLopener):
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
        # Remove the script tags
        newsData = re.sub(r'<script.*?>[.\s\S]*?</script>', '', newsData)
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
    data['HashNewsLink'] = hashlib.sha1(fullNewsURL.encode('latin-1')).hexdigest()

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
    # Check the type of the home and url. If they are strings
    # convert them to utf-8
    if type(home) is str:
        home = unicode(home, 'latin-1', errors='ignore')
    if type(url) is str:
        url = unicode(url, 'latin-1', errors='ignore')

    join = urlparse.urljoin(home, url)
    parse = urlparse.urlparse(join)
    path = posixpath.normpath(parse[2])

    absolute = urlparse.urlunparse((parse.scheme, parse.netloc, path, parse.params, parse.query, None))

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
        openedUrl = myopener.open(url.encode('latin-1'))

        try:
            htmlData = openedUrl.read()
        finally:
            openedUrl.close()

        return htmlData
    except IOError, err:
        print 'Problem reading url:', repr(urllib.unquote(url)).decode("unicode-escape").encode('latin-1'), 'URL error: ', err
        sys.exit(1)

def usage():
    print("Usage: %s <json conf file>" % sys.argv[0])
    sys.exit(0)

# Gather our code in a main() function
def main():

    if len(sys.argv) != 2:
        usage()

    # Read json conf files
    readJsonConfFile(sys.argv[1])

    baseURL = jsonConf['BaseURL']

    linksToFetch = set([])
    linksFetched = set([])
    localLinksRetrieve = set([])
    # Retrieve the links from the base url if the pickle files are not present
    if os.path.isfile(jsonConf['Filenames']['LinksFetched']) and os.path.isfile(jsonConf['Filenames']['LinksToFetch']):
        print jsonConf['Filenames']['LinksFetched'], 'and',  jsonConf['Filenames']['LinksToFetch'], 'are present. Restoring...'
        linksToFetch = restorePickle(jsonConf['Filenames']['LinksToFetch'])
        linksFetched = restorePickle(jsonConf['Filenames']['LinksFetched'])
    else:
        baseHtmlData = getUrl(baseURL)
        linksToFetch = getLocalLinks(baseHtmlData, baseURL, linksFetched, linksToFetch)
        linksFetched.add(baseURL)

    print 'Initial unique links to be retrieved ', len(linksToFetch)

    # http://stackoverflow.com/questions/16625960/modifying-a-set-while-iterating-over-it
    while linksToFetch:
        link = linksToFetch.pop()
        print 'Link poped...', link
        print 'Remaining links to be fetched ', len(linksToFetch)

        if type(link) is str:
            link = unicode(link, 'latin-1', errors='ignore')

        if link in linksFetched:
            print 'Link ', repr(urllib.unquote(link)).decode("unicode-escape").encode('latin-1'), ' already fetched...'
            continue

        if excludeLocalLinks(link):
            continue

        if jsonConf['NetworkLocation'] not in urlparse.urlparse(link).netloc:
            print 'Link', repr(urllib.unquote(link)).decode("unicode-escape").encode('latin-1'), ' is not in this domain...'
            linksFetched.add(link)
            continue

        # http://stackoverflow.com/questions/8136788/decode-escaped-characters-in-url
        print 'Fetching...', repr(urllib.unquote(link)).decode("unicode-escape").encode('latin-1'), ' - ', hashlib.sha1(link.encode('latin-1')).hexdigest()

        htmlData = getUrl(link)

        # Check if empty
        if not htmlData:
            print 'Link ', repr(urllib.unquote(link)).decode("unicode-escape").encode('latin-1'), ' appears empty...'
            print 'The content is @@', htmlData, '@@'
            continue

        # Check if it's a news link
        isNewsLink = re.compile(jsonConf['LinksRegEx']['LinksIncluded'])
        if isNewsLink.match(link):
            # writeHTMLToFile(htmlData, 'iefimerida/'+hashlib.sha1(link).hexdigest()+'.html')

            # http://stackoverflow.com/questions/5648573/python-print-unicode-strings-in-arrays-as-characters-not-code-points
            # print repr(createNewsData(htmlData, fetchNewsLink)).decode("unicode-escape").encode('latin-1')

            data = createNewsData(htmlData, link)
            jsonData = json.dumps(data, ensure_ascii = False, sort_keys = True, indent = 4, separators = (',', ': '))
            print jsonData

            jsonDump(data, jsonConf['Filenames']['NewsJSON'])

        # Get the local links from this page and add them to the linksToFetch
        newLinksToFetch = getLocalLinks(htmlData, link, linksFetched, linksToFetch)
        print 'Will be added ', len(newLinksToFetch), ' new links'
        linksToFetch.update(newLinksToFetch)

        # Add the link if successfully fetched.
        linksFetched.add(link)
        print 'Total links fetched so far ', len(linksFetched)

        nextLinkDelay(jsonConf['DelayRange'][0], jsonConf['DelayRange'][1])

        dumpPickle(linksToFetch, jsonConf['Filenames']['LinksToFetch'])
        dumpPickle(linksFetched, jsonConf['Filenames']['LinksFetched'])

# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == '__main__':
  main()

