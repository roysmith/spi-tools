from collections import namedtuple
import re
import mwparserfromhell


class ArchiveError(ValueError):
    pass

class InvalidIpV4Error(ValueError):
    pass
      

class SpiCase:
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
        """Return an iterable of SpiCaseDays"""
        for code in self.wikicodes:
            for section in code.get_sections(levels=[3]):
                yield SpiCaseDay(section)


    def find_all_ips(self):
        '''Iterates over all the IPs mentioned in checkuser templates.
        Each user is represented as a SpiPInfo.  Order of iteration
        is not guaranteed, and templates are not deduplicated.
        '''
        for day in self.days():
            for ip in day.find_ips():
                yield ip


class SpiCaseDay:
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
        Each user is represented as an SpiUserInfo.  Order of iteration
        is not guaranteed, and templates are not deduplicated.

        '''
        date = self.date()
        templates = self.wikicode.filter_templates(
            matches = lambda n: n.name.matches('checkuser'))
        for t in templates:
            username = t.get('1').value
            yield SpiUserInfo(str(username), str(date))


    def find_ips(self):
        '''Iterates over all the IPs mentioned in checkuser templates.
        Each user is represented as an SpiIpInfo.  Order of iteration
        is not guaranteed, and templates are not deduplicated.
        '''
        date = self.date()
        templates = self.wikicode.filter_templates(
            matches = lambda n: n.name.matches('checkip'))
        for t in templates:
            ip = t.get('1').value
            try:
                yield SpiIpInfo(str(ip), str(date))
            except InvalidIpV4Error:
                pass


class SpiUserInfo:
    def __init__(self, username, date):
        self.username = username
        self.date = date

    def __eq__(self, other):
        return self.username == other.username and self.date == other.date

    def __hash__(self):
        return hash((self.username, self.date))


class SpiIpInfo:
    v4pattern = re.compile(r'^\d+\.\d+\.\d+\.\d+$')

    def __init__(self, ip, date):
        self.ip = ip
        self.date = date
        if not self.is_v4():
            raise(InvalidIpV4Error('ip not a valid IPv4 address'))

    def __eq__(self, other):
        return self.ip == other.ip and self.date == other.date
    
    def __hash__(self):
        return hash((self.ip, self.date))

    def is_v4(self):
        "Return True if this is an IPv4 address"
        return self.v4pattern.match(self.ip)

    def ip_to_binary(self):
        "Return the ip address as a 32-character long string of 0's and 1's"
        string_parts = []
        for ip_part in self.ip.split('.'):
            string_parts.append(format(int(ip_part), '08b'))
        return ''.join(string_parts)
