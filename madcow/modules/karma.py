"""Infobot style karma"""

from madcow.util import Module
import re
import pdb
from learn import Main as Learn

class KarmaResponse(object):

    def __init__(self, reply, matched):
        self.reply = reply
        self.matched = matched


class Karma(object):

    """Karma and Ranking"""

    _adjust_pattern_pos = re.compile(r'\S+(?=\+\+)')
    _adjust_pattern_neg = re.compile(r'\S+(?=\-\-)')
    _query_pattern = re.compile(r'^\s*karma\s+(\S+)\s*\?*\s*$')
    _rank_pattern = re.compile(r'^\s*rank(\s+\d+)?')
    _dbname = u'karma'

    def __init__(self, madcow):
        self.learn = Learn(madcow)

    def process(self, nick, input):

        adjusted = False
        kr = KarmaResponse(reply='', matched=False)
        # see if someone is trying to adjust karma
        try:
            pos = self._adjust_pattern_pos.findall(input)
            neg = self._adjust_pattern_neg.findall(input)
            for item in pos:
                if nick.lower() != item:
                    adjusted = self.adjust(nick=item, adjustment='++')
                    karma = self.query(nick=item)
                    kr.reply += u"%s now has %s points of karma\n" % (item, karma)
            for item in neg:
                if nick.lower() != item:
                    adjusted = self.adjust(nick=item, adjustment='--')
                    karma = self.query(nick=item)
                    kr.reply += u"%s now has %s points of karma\n" % (item, karma)
        except AttributeError:
            pass

        # detect a query for someone's karma
        try:
            target = Karma._query_pattern.search(input).group(1)
            karma = self.query(nick=target)
            kr.matched = True
            kr.reply = u"%s: %s's karma is %s" % (nick, target, karma)
        except AttributeError:
            pass

        try:
            rank_match = Karma._rank_pattern.search(input)
            number = 10
            if rank_match.group(1) is not None:
                number = int(rank_match.groups()[0])
            keys = self.allkeys()
            self.orderedKarmaList(keys, number, kr)
        except AttributeError:
            pass

        return kr

    def set(self, nick, karma):
        self.learn.set(Karma._dbname, nick.lower(), unicode(karma))

    def adjust(self, nick, adjustment):
        karma = self.query(nick)
        value = None

        if adjustment[:2] == u'++':
            value = u'+'
        elif adjustment[:2] == u'--':
            value = u'-'

        if value:
            exec(u'karma ' + value + u'= 1')
            self.set(nick=nick, karma=karma)
            return True

    def allkeys(self):
        return self.learn.dbm(Karma._dbname).keys()

    def orderedKarmaList(self, keys, number, kr):
        rank_list = []

        for key in keys:
            karma = self.learn.lookup(Karma._dbname, key.lower())
            rank_list.append((key.lower(), karma))

        rank_list.sort(key=lambda tuple: int(tuple[1]))
        rank_list.reverse()

        for x in rank_list[:number]:
            kr.reply += str(x[0]) + " has " + str(x[1]) + " points of karma.\n"
                
            
 
    def query(self, nick):
        karma = self.learn.lookup(Karma._dbname, nick.lower())
        if karma is None:
            karma = 0
            self.set(nick=nick, karma=karma)
        return int(karma)


class Main(Module):

    pattern = Module._any
    require_addressing = False
    help = u'\n'.join([
        u"<nick>[++/--] - adjust someone's karma",
        u"karma <nick> - see what someone's karma is",
        ])
    allow_threading = False

    def init(self):
        self.karma = Karma(self.madcow)

    def response(self, nick, args, kwargs):
        """This function should return a response to the query or None."""
        input = args[0]
        kr = self.karma.process(nick, input)
        # Allow us to continue to parse other modules by setting matched equal to False
        kwargs[u'req'].matched = False
        if kr.reply is not '':
            return unicode(kr.reply)
