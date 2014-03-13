#!/usr/bin/env python

"""

    client for Magic Card Market API

    requires python 2.6 or higher (v3 not supported yet)

    API docs: https://www.mkmapi.eu/ws/documentation


    L.S. Keijser <leon@gotlinux.nl> - 2014

"""

# imports
import cStringIO
import operator
import sys
import urllib2
import apicreds
import xml.etree.ElementTree as ET
from optparse import OptionParser

# version
mkmtool_ver = '0.1-alpha'

# configuration
API_KEY = apicreds.API_KEY
MKM_USER = apicreds.MKM_USER

API_URL = 'https://www.mkmapi.eu/ws/{0}/{1}/'.format(MKM_USER, API_KEY)


# start main script 

def main():

    # Parse commandline options:
    parser = OptionParser(usage="%prog [ -h ]",version="%prog " + mkmtool_ver)
    parser.add_option("-l", "--list",
            action="store_true",
            dest="games_list",
            help="Returns a collection of all games that are supported by MKM.")
    parser.add_option("-s", "--search",
            action="store",
            dest="search",
            help="Search MKM for a specific item")
    parser.add_option("-a", "--lang",
            action="store",
            dest="language",
            default="1",
            help="Specify which language to use [1: english, 2: french, 3: german, 4: spanish, 5: italian]")
    parser.add_option("-i", "--id",
            action="store",
            dest="gameid",
            default="1",
            help="Specify which game ID to use (for list, use --list")
    parser.add_option("-g", "--img",
            action="store_true",
            dest="get_image",
            help="Retrieve the URI to the card image.")
    parser.add_option("-p", "--product",
            action="store",
            dest="product",
            help="Returns detailed information about a single product.")
    (options, args) = parser.parse_args()

    p = ParseMKM()
    # values we got from optparse:
    p.games_list    = options.games_list
    p.search        = options.search
    p.language      = options.language
    p.gameid        = options.gameid
    p.get_image     = options.get_image
    p.product       = options.product

    p.run()


class ParseMKM:

    def __init__(self):
        """
            Constructor. Arguments will be filled in by optparse
        """

        self.games_list = None
        self.search     = None
        self.language   = None
        self.gameid     = None
        self.product    = None
        self.get_image  = None
    
    # options
    def get_games_list(self):
        resp = urllib2.urlopen(API_URL + 'games')
        return resp.read()

    def item_search(self):
        resp = urllib2.urlopen(API_URL + 'products/' + self.search + '/' + self.gameid + '/' + self.language + '/false')
        return resp.read()

    def get_product(self):
        resp = urllib2.urlopen(API_URL + 'product/' + self.product)
        return resp.read()
    
    # helper
    def indent(self, rows, hasHeader=False, headerChar='-', delim=' | ', justify='left',
               separateRows=False, prefix='', postfix='', wrapfunc=lambda x:x):
        # closure for breaking logical rows to physical, using wrapfunc
        def rowWrapper(row):
            newRows = [wrapfunc(item).split('\n') for item in row]
            return [[substr or '' for substr in item] for item in map(None,*newRows)]
        # break each logical row into one or more physical ones
        logicalRows = [rowWrapper(row) for row in rows]
        # columns of physical rows
        columns = map(None,*reduce(operator.add,logicalRows))
        # get the maximum of each column by the string length of its items
        maxWidths = [max([len(str(item)) for item in column]) for column in columns]
        rowSeparator = headerChar * (len(prefix) + len(postfix) + sum(maxWidths) + \
                                     len(delim)*(len(maxWidths)-1))
        # select the appropriate justify method
        justify = {'center':str.center, 'right':str.rjust, 'left':str.ljust}[justify.lower()]
        output=cStringIO.StringIO()
        if separateRows: print >> output, rowSeparator
        for physicalRows in logicalRows:
            for row in physicalRows:
                print >> output, \
                    prefix \
                    + delim.join([justify(str(item),width) for (item,width) in zip(row,maxWidths)]) \
                    + postfix
            if separateRows or hasHeader: print >> output, rowSeparator; hasHeader=False
        return output.getvalue()


    # main
    def run(self):

        if self.games_list:
            xml = self.get_games_list()
            root = ET.fromstring(xml)
            games_list = {}
            for game in root.findall('game'):
                name = game.find('name').text
                gameid = game.find('idGame').text
                games_list[gameid] = name
            print "ID\tName"
            print "--\t----"
            # return a sorted (by id) list of games
            for i,n in sorted(games_list.iteritems(), key=operator.itemgetter(0)):
                print "%s\t%s" % (i, n)

        if self.search:
            self.search = self.search.replace(' ', '%20')
            # should we do a check for req. params?
            #if not (self.item and self.gameid and self.language):
            #    sys.exit('Error: you need to specify a Game ID and a language')
            xml = self.item_search()
            root = ET.fromstring(xml)
            rows = []
            if self.get_image:
                rows.append(('ID', 'Name', 'Expansion', 'Rarity', 'Price (low)', 'Price (avg)', 'Image URL'))
            else:
                rows.append(('ID', 'Name', 'Expansion', 'Rarity', 'Price (low)', 'Price (avg)'))
            for product in root.findall('product'):
                idp = product.find('idProduct').text.encode('utf-8')
                pname = product.find('name').find('productName').text.encode('utf-8')
                expansion = product.find('expansion').text.encode('utf-8')
                rarity = product.find('rarity').text.encode('utf-8')
                # no idea what this (Price Sell) means , do disabled it:
                #price_sell = product.find('priceGuide').find('SELL').text.encode('utf-8')
                price_low = product.find('priceGuide').find('LOW').text.encode('utf-8')
                price_avg = product.find('priceGuide').find('AVG').text.encode('utf-8')
                if self.get_image:
                    image = product.find('image').text.encode('utf-8')
                    image = list(image)
                    image[0] = ''
                    image = 'https://www.magiccardmarket.eu' + "".join(image)
                    rows.append((idp, pname, expansion, rarity, price_low, price_avg, image))
                else:
                    rows.append((idp, pname, expansion, rarity, price_low, price_avg))
            print self.indent(rows, hasHeader=True)
            
        if self.product:
            xml = self.get_product()
            root = ET.fromstring(xml)
            print "ID\tExpansion\tName"
            for product in root.findall('product'):
                idp = product.find('idProduct').text
                expansion = product.find('expansion').text
                name = product.find('name').find('productName').text
                print "%s\t%s\t%s" % (idp, expansion, name)


# all systems GO!
if __name__ == '__main__':
    main()


