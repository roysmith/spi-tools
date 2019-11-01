from collections import namedtuple
import mwparserfromhell

SPICheckUser = namedtuple('SPICheckUser', 'username, date')
SPICheckIP = namedtuple('SPICheckIP', 'ip, date')


class ArchiveError(ValueError):
    pass
      

class SPICase:
    def __init__(self, wikitext):
        self.wikitext = wikitext
        self.wikicode = mwparserfromhell.parse(wikitext)


    def master_name(self):
        """Return the name of the sockmaster, parsed from a {{SPIarchive
        notice}} template.  Raises ArchiveError if the template is not
        found, or if multiple such templates are found.
        """
        templates = self.wikicode.filter_templates(
            matches = lambda n: n.name.matches('SPIarchive notice'))
        n = len(templates)
        if n == 1:
            return templates[0].get('1').value
        raise ArchiveError("Expected exactly 1 {{SPIarchive notice}}, found %d" % n)


    def days(self):
        """Return an iterable of SPICaseDays"""
        sections = self.wikicode.get_sections(levels=[3])
        return [SPICaseDay(s) for s in sections]


class SPICaseDay:
    def __init__(self, wikicode):
        self.wikicode = wikicode


    def date(self):
        headings = self.wikicode.filter_headings(matches = lambda h: h.level == 3)
        n = len(headings)
        if n == 1:
            return headings[0].title
        raise ArchiveError("Expected exactly 1 level-3 heading, found %d" % n)


    def find_users(self):
        '''Iterates over all the accounts mentioned in checkuser templates.
        Each user is represented as a SpiCheckUser tuple.  Order of iteration
        is not guaranteed, and templates are not deduplicated.
        '''
        date = self.date()
        templates = self.wikicode.filter_templates(
            matches = lambda n: n.name.matches('checkuser'))
        for t in templates:
            username = t.get('1').value
            yield SPICheckUser(username, date)


    def find_ips(self):
        '''Iterates over all the IPs mentioned in checkuser templates.
        Each user is represented as a SpiCheckIP tuple.  Order of iteration
        is not guaranteed, and templates are not deduplicated.
        '''
        date = self.date()
        templates = self.wikicode.filter_templates(
            matches = lambda n: n.name.matches('checkip'))
        for t in templates:
            ip = t.get('1').value
            yield SPICheckIP(ip, date)
