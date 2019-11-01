from collections import namedtuple
import mwparserfromhell

SPICheckUser = namedtuple('SPICheckUser', 'username, date')
SPICheckIP = namedtuple('SPICheckIP', 'ip, date')


class ArchiveError(ValueError):
    pass
      

class SPICase:
    def __init__(self, *wikitexts):
        """A case can be made up of multiple source documents.  In practice,
        there will usually be two; the currently active page, and the archive
        page.
        """
        self.wikitexts = list(wikitexts)
        self.wikicodes = [mwparserfromhell.parse(t) for t in wikitexts]

        master_names = set(str(self.find_master_name(code)) for code in self.wikicodes)
        if len(master_names) == 0:
            raise ArchiveError("No sockmaster name found")
        if len(master_names) > 1:
            raise ArchiveError("Multiple sockmaster names found: %s" % master_names)
        self._master_name = master_names.pop()


    def master_name(self):
        return self._master_name


    @staticmethod
    def find_master_name(wikicode):
        """Return the name of the sockmaster, parsed from a
        {{SPIarchive notice}} template.  Raises ArchiveError if the
        template is not found, or if multiple such templates are
        found.

        """
        templates = wikicode.filter_templates(
            matches = lambda n: n.name.matches('SPIarchive notice'))
        n = len(templates)
        if n == 1:
            return templates[0].get('1').value
        raise ArchiveError("Expected exactly 1 {{SPIarchive notice}}, found %d" % n)


    def days(self):
        """Return an iterable of SPICaseDays"""
        for code in self.wikicodes:
            for section in code.get_sections(levels=[3]):
                yield SPICaseDay(section)


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
