#!/usr/bin/python -tt

# import modules used here -- sys is a very standard one
import os
import sys
import re
import random   ##for pseudo-random generation
import time     ##for time functions and sleep
import urllib   ##url fetching
import urlparse ##url parse
import sqlite3  ##sqlite
import hashlib  ##hash md5 sha1...
import pickle   ##pickle to serialize data

# http://wolfprojects.altervista.org/changeua.php
from urllib import FancyURLopener

# Use google bot as user agent
class MyOpener(FancyURLopener):
    version = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'

#namefind is supposed to match a tag name and attributes into groups 1 and 2 respectively.
#the original version of this pattern:
# namefind = re.compile(r'(\S*)\s*(.+)', re.DOTALL)
#insists that there must be attributes and if necessary will steal the last character
#of the tag name to make it so. this is annoying, so let us try:
namefind = re.compile(r'(\S+)\s*(.*)', re.DOTALL)

attrfind = re.compile(
    r'\s*([a-zA-Z_][-:.a-zA-Z_0-9]*)(\s*=\s*'
    r'(\'[^\']*\'|"[^"]*"|[-a-zA-Z0-9./,:;+*%?!&$\(\)_#=~\'"@]*))?')   # this is taken from sgmllib


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


def parseHTMLItemIncrNumber(htmlData):
    item_incr_number_List = []
    regExprString = r'<td align=right valign=top class="title">(.*?)\.</td>'
    item_incr_number_List = re.findall(regExprString, htmlData)
    return item_incr_number_List

def parseHTMLItemId(htmlData):
    item_id_List = []
    regExprString = r'<td><center><a id=up_(.*?) .*?href=".*?"><img src=".*?" border=0 vspace=3 hspace=2></a>'
    item_id_List = re.findall(regExprString, htmlData)
    return item_id_List

def parseHTMLItemMain(htmlData):
    itemMainList = []
    regExprString = r'<td class="title"><a href="([http|item].*?)".*?>(.*?)</a>.*?</td>'
    itemMainList = re.findall(regExprString, htmlData)
    return itemMainList

def parseHTMLItemMainDead(htmlData):
    itemMainDeadList = []
    regExprString = r'<td class="title"> [dead] <a rel="nofollow">(.*?)</a>.*?</td>'
    itemMainDeadList = re.findall(regExprString, htmlData)
    return itemMainDeadList

def parseHTMLItemSub(htmlData):
    itemSubList = []
    regExprString = r'<td class="subtext"><span id=score_.*?>(.*?) point.*?</span> by <a href="(.*?)">(.*?)</a> (.*?)  \| <a href="(.*?)">(.*?)</a></td>'
    itemSubList = re.findall(regExprString, htmlData)
    return itemSubList

def parseHTMLNextLink(htmlData):
    nextLinkList = ''
    regExprString = r'<td colspan=2></td><td class="title"><a href="(.*?)" rel="nofollow">More</a></td>'
    nextLinkList = re.search(regExprString, htmlData)
    return nextLinkList

def parseHTMLTitleUser(htmlData):
    titleUserList = []
    regExprString = r'<tr><td class="title" align="right" valign="top">(.*?)</td>'\
                    r'<td><center><a id="up_(.*?)" href=".*?"><img src=".*?" border="0" hspace="2" vspace="3"></a>'\
                    r'<span id="down_.*?"></span></center></td>'\
                    r'<td class="title"><a href="(.*?)">(.*?)</a><span class="comhead"> \((.*?)\) </span></td></tr>'\
                    r'<tr><td colspan="2"></td>'\
                    r'<td class="subtext"><span id="score_.*?">(.*?) points</span> by'\
                    r'<a href="(.*?)">(.*?)</a> (.*?)  \| <a href="(.*?)">(.*?)</a></td></tr>'

    titleUserList = re.findall(regExprString, htmlData)
    return titleUserList

def nextLinkDelay(startDelay, endDelay):
    randomNum = 0
    randomNum = random.randint(startDelay, endDelay)
    print 'Delaying for ', randomNum, ' sec'
    time.sleep(randomNum)

def writeFileDump(htmlData):
    outfilename = 'dump.txt'
    try:
        outfileHandler = open(outfilename, 'a')
        outList = zip(parseHTMLItemIncrNumber(htmlData), parseHTMLItemId(htmlData), \
                      parseHTMLItemMain(htmlData), parseHTMLItemSub(htmlData))
        for temp in outList:
            outfileHandler.write(temp[0]   +' | '+temp[1]   +' | '+temp[2][0]+' | '+temp[2][1]+' | '+\
                                 temp[3][0]+' | '+temp[3][1]+' | '+temp[3][2]+' | '+temp[3][3]+' | '+\
                                 temp[3][4]+' | '+temp[3][5]+'\n')
        outfileHandler.close()
    except IOError:
        print 'Problem reading file for append: ', outfilename
        sys.exit(1)

def dumpLinksToRetrieve(LinksToRetrieve):
#    currDate = time.strftime("%d%m%Y%H%M%S")
#    filename = currDate + '-LinksToRetrieve.pickle'
    with open('LinksToRetrieve.pickle', 'wb') as fileHandle:
        pickle.dump(LinksToRetrieve, fileHandle)

def dumpLinksFetched(LinksFetched):
#    currDate = time.strftime("%d%m%Y%H%M%S")
#    filename = currDate + '-LinksFetched.pickle'
    with open('LinksFetched.pickle', 'wb') as fileHandle:
        pickle.dump(LinksFetched, fileHandle)

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

def putItemsInDict(htmlData):
    itemDict = {}
    return itemDict

def getNewsLinks(htmlPage):
    newsLinks = []
    regExprString = r'<a href="/news/(.*?)"'
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
    url = ''
    url = 'http://www.iefimerida.gr/'

    filename = 'startPageIefimerida.html'
    fileData = ''
    fileData = readFile(filename)
    # writeFileDump(fileData)

    # print fileData
    # print getNewsLinks(fileData), len(getNewsLinks(fileData))

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
        fetchNewsLink = base_url + '/news/' + link
        print 'Fetching...', fetchNewsLink, ' - ', hashlib.sha1(fetchNewsLink).hexdigest()

        htmlData = getUrl(fetchNewsLink)
        writeHTMLToFile(htmlData, 'iefimerida/'+hashlib.sha1(fetchNewsLink).hexdigest()+'.html')

        # Get the news links from this page and add them to the linksRetrieve
        latestRetrievedLinks = getNewsLinks(htmlData)
        print 'Will be added ', len(latestRetrievedLinks), ' new links'
        linksRetrieve.update(latestRetrievedLinks)

        # Add the link if successfully fetched.
        linksFetched.add(link)
        print 'Total links fetched so far ', len(linksFetched)

        nextLinkDelay(11, 21)
        # linksRetrieve.add(fetchNewsLink)
        # htmlData = getUrl(fetchNewsLink)

"""
    while True:
        print url, hashlib.sha1(url).hexdigest(), 
        htmlData = ''
        htmlData = getUrl(url)
        print htmlData
        print parseHTMLItemMain(htmlData), parseHTMLItemMainDead(htmlData)
        #break
        print 'hashData:', hashlib.sha256(htmlData).hexdigest()
        writeFileDump(htmlData)
        nextLink = parseHTMLNextLink(htmlData)
        if nextLink:
            url = base_url + nextLink.group(1)
        else:
            break
        nextLinkDelay(4, 8)
"""
        
    #print fileData
    #print parseHTMLItemIncrNumber(fileData),  parseHTMLItemId(fileData)
    #nextLinkDelay(10, 20)
    #print parseHTMLNextLink(fileData).group(1)
    #print parseHTMLItemMain(fileData), parseHTMLItemSub(fileData)
    #print parseHTMLTitleUser(fileData)
        
    #print fileData
    #match = re.findall(r'<td><center><a id=".*?" onclick=".*?" href=".*?"><img src=".*?" border="0" hspace="2" vspace="3"></a><span id=".*?"></span></center></td>', fileData)
    #print match
      
# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == '__main__':
  main()
  
