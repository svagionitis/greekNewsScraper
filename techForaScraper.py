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
    with open(filename) as jsonFileHandle:
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


def getUserData(regEx, htmlData):
    userData = ''
    userDataRegEx = re.compile(regEx)
    if userDataRegEx.search(htmlData):
        userData = userDataRegEx.search(htmlData).group(1)
        userData = replaceEntities(userData)
        # Remove any white spaces in the beginning
        userData = re.sub(r'^[\s]*', '', userData)
        # Remove any white spaces at the end
        userData = re.sub(r'[\s]*$', '', userData)
    else:
        userData = 'N/A'
    return userData


def createUsersData(htmlData, url):
    data = {}
    data['URL'] =           url
    data['HashURL'] =       hashlib.sha1(url).hexdigest()
    data['DateRetrieved'] = str(datetime.now())
    data['UserName'] =      getUserData(jsonConf['UsersRegEx']['UserName'], htmlData)
    data['HashUserName'] =  hashlib.sha1(data['UserName']).hexdigest()
    data['DateCreated'] =   getUserData(jsonConf['UsersRegEx']['DateCreated'], htmlData)
    data['Karma'] =         getUserData(jsonConf['UsersRegEx']['Karma'], htmlData)
    data['Avg'] =           getUserData(jsonConf['UsersRegEx']['Avg'], htmlData)
    data['About'] =         getUserData(jsonConf['UsersRegEx']['About'], htmlData)
    data['HashAbout'] =     hashlib.sha1(data['About']).hexdigest()
    return repr(data).decode("unicode-escape").encode('latin-1')

def getStoriesData(regEx, htmlData):
    storiesData = ''
    storiesDataRegEx = re.compile(regEx)
    if storiesDataRegEx.search(htmlData):
        storiesData = storiesDataRegEx.search(htmlData).group(1)
        storiesData = replaceEntities(storiesData)
        # Remove any white spaces in the beginning
        storiesData = re.sub(r'^[\s]*', '', storiesData)
        # Remove any white spaces at the end
        storiesData = re.sub(r'[\s]*$', '', storiesData)
    else:
        storiesData = 'N/A'
    return storiesData

def createStoriesData(htmlData, url):
    data = {}
    data['URL'] =               url
    data['HashURL'] =           hashlib.sha1(url).hexdigest()
    data['DateRetrieved'] =     str(datetime.now())
    data['Number'] =            getStoriesData(jsonConf['StoriesRegEx']['Number'], htmlData)
    data['Id'] =                getStoriesData(jsonConf['StoriesRegEx']['Id'], htmlData)
    data['Title'] =             getStoriesData(jsonConf['StoriesRegEx']['Title'], htmlData)
    data['HashTitle'] =         hashlib.sha1(data['Title']).hexdigest()
    data['Link'] =              getStoriesData(jsonConf['StoriesRegEx']['Link'], htmlData)
    data['HashLink'] =          hashlib.sha1(data['Link']).hexdigest()
    data['ShortLink'] =         getStoriesData(jsonConf['StoriesRegEx']['ShortLink'], htmlData)
    data['Score'] =             getStoriesData(jsonConf['StoriesRegEx']['Score'], htmlData)
    data['UserSubmitted'] =     getStoriesData(jsonConf['StoriesRegEx']['UserSubmitted'], htmlData)
    data['HashUserSubmitted'] = hashlib.sha1(data['UserSubmitted']).hexdigest()
    data['TimeSubmitted'] =     getStoriesData(jsonConf['StoriesRegEx']['TimeSubmitted'], htmlData)
    data['NumberOfComments'] =  getStoriesData(jsonConf['StoriesRegEx']['NumberOfComments'], htmlData)
    return repr(data).decode("unicode-escape").encode('latin-1')

def getCommentsData(regEx, htmlData):
    commentsData = ''
    commentsDataRegEx = re.compile(regEx)
    if commentsDataRegEx.search(htmlData):
        commentsData = commentsDataRegEx.search(htmlData).group(1)
        commentsData = replaceEntities(commentsData)
        # Remove all the html tags, need a clear text
        commentsData = re.sub(r'<[^>]*>', '', commentsData)
        # Remove any white spaces in the beginning
        commentsData = re.sub(r'^[\s]*', '', commentsData)
        # Remove any white spaces at the end
        commentsData = re.sub(r'[\s]*$', '', commentsData)
    else:
        commentsData = 'N/A'
    return commentsData

def createCommentsData(htmlData, url):
    data = {}
    data['URL'] =               url
    data['HashURL'] =           hashlib.sha1(url).hexdigest()
    data['DateRetrieved'] =     str(datetime.now())
    data['Id'] =                getCommentsData(jsonConf['CommentsRegEx']['Id'], htmlData)
    data['UserCommented'] =     getCommentsData(jsonConf['CommentsRegEx']['UserCommented'], htmlData)
    data['HashUserCommented'] = hashlib.sha1(data['UserCommented']).hexdigest()
    data['TimeCommented'] =     getCommentsData(jsonConf['CommentsRegEx']['TimeCommented'], htmlData)
    data['ParentId'] =          getCommentsData(jsonConf['CommentsRegEx']['ParentId'], htmlData)
    data['Comment'] =           getCommentsData(jsonConf['CommentsRegEx']['Comment'], htmlData)
    data['HashComment'] =       hashlib.sha1(data['Comment']).hexdigest()
    return repr(data).decode("unicode-escape").encode('latin-1')


def jsonDump(data, jsonFilename):
    with open(jsonFilename, 'a+') as jsonFileHandle:
        json.dump( data, jsonFileHandle, ensure_ascii = False, sort_keys = True, indent = 4, separators = (',', ': '))

def nextLinkDelay(startDelay, endDelay):
    randomNum = 0
    randomNum = random.randint(startDelay, endDelay)
    print 'Delaying for ', randomNum, ' sec'
    time.sleep(randomNum)


def dumpLinksToFetch(LinksToFetch):
    with open(jsonConf['Filenames']['LinksToFetch'], 'wb') as pickleFileHandle:
        pickle.dump(LinksToFetch, pickleFileHandle)

def dumpLinksFetched(LinksFetched):
    with open(jsonConf['Filenames']['LinksFetched'], 'wb') as pickleFileHandle:
        pickle.dump(LinksFetched, pickleFileHandle)

def restoreLinksToFetch():
    restoredLinksToFetch = set([])
    with open(jsonConf['Filenames']['LinksToFetch'], 'rb') as fileHandle:
        restoredLinksToFetch = pickle.load(fileHandle)
    return restoredLinksToFetch

def restoreLinksFetched():
    restoredLinksFetched = set([])
    with open(jsonConf['Filenames']['LinksFetched'], 'rb') as fileHandle:
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

def createAbsoluteURL(home, url):
    join = urlparse.urljoin(home, url)
    parse = urlparse.urlparse(join)
    path = posixpath.normpath(parse[2])

    absolute = urlparse.urlunparse((parse.scheme, parse.netloc, path, parse.params, parse.query, None))

    return absolute

def getLocalLinks(htmlPage, baseURL, fetchedLinks, toBeFetchedLinks):
    localLinks = []
    regExprString = jsonConf['LinksRegEx']['LocalLinks']
    if htmlPage: # If not empty
        localLinks = re.findall(regExprString, htmlPage)
        # Create the full link
        fullLinks = set([ createAbsoluteURL(baseURL, s) for s in localLinks ])
    else: # If empty
        fullLinks = localLinks
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
        linksToFetch = restoreLinksToFetch()
        linksFetched = restoreLinksFetched()
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

        if link in linksFetched:
            print 'Link ', repr(urllib.unquote(link)).decode("unicode-escape").encode('latin-1'), ' already fetched...'
            continue

        if excludeLocalLinks(link):
            continue

        # Check if it's in the same domain.
        if urlparse.urlparse(link).netloc != jsonConf['NetworkLocation']:
            print 'Link', repr(urllib.unquote(link)).decode("unicode-escape").encode('latin-1'), ' is not in this domain...'
            linksFetched.add(link)
            continue

        # http://stackoverflow.com/questions/8136788/decode-escaped-characters-in-url
        print 'Fetching...', repr(urllib.unquote(link)).decode("unicode-escape").encode('latin-1'), ' - ', hashlib.sha1(link).hexdigest()

        htmlData = getUrl(link)

        # Check if it's in included links
        isIncludedLink = re.compile(jsonConf['LinksRegEx']['LinksIncluded'])
        if isIncludedLink.match(link):
            # Check here if it's a story, comment or user link

            # writeHTMLToFile(htmlData, 'iefimerida/'+hashlib.sha1(link).hexdigest()+'.html')

            # http://stackoverflow.com/questions/5648573/python-print-unicode-strings-in-arrays-as-characters-not-code-points
            # print repr(createNewsData(htmlData, fetchNewsLink)).decode("unicode-escape").encode('latin-1')

            # JSON users
            if re.match(jsonConf['LinksRegEx']['LinksUser'], link):
                usersData = createUsersData(htmlData, link)
                print usersData
                jsonUsersData = json.dumps(usersData, ensure_ascii = False, sort_keys = True, indent = 4, separators = (',', ': '))
                print jsonUsersData
                jsonDump(usersData, jsonConf['Filenames']['UsersJSON'])
            else:
                # JSON stories
                # If there is a parent id it's a comment. If not it's a story
                if getCommentsData(jsonConf['CommentsRegEx']['ParentId'], htmlData) == 'N/A':
                    storiesData = createStoriesData(htmlData, link)
                    print storiesData
                    jsonStoriesData = json.dumps(storiesData, ensure_ascii = False, sort_keys = True, indent = 4, separators = (',', ': '))
                    print jsonStoriesData
                    jsonDump(storiesData, jsonConf['Filenames']['StoriesJSON'])
                else:
                    # JSON comments
                    commentsData = createCommentsData(htmlData, link)
                    print commentsData
                    jsonCommentsData = json.dumps(commentsData, ensure_ascii = False, sort_keys = True, indent = 4, separators = (',', ': '))
                    print jsonCommentsData
                    jsonDump(commentsData, jsonConf['Filenames']['CommentsJSON'])

        # Get the local links from this page and add them to the linksToFetch
        newLinksToFetch = getLocalLinks(htmlData, link, linksFetched, linksToFetch)
        print 'Will be added ', len(newLinksToFetch), ' new links'
        linksToFetch.update(newLinksToFetch)

        # Add the link if successfully fetched.
        linksFetched.add(link)
        print 'Total links fetched so far ', len(linksFetched)

        nextLinkDelay(31, 37)

        dumpLinksToFetch(linksToFetch)
        dumpLinksFetched(linksFetched)

# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == '__main__':
  main()

