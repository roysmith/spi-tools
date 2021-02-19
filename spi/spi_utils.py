from dataclasses import dataclass
from typing import List
from ipaddress import IPv4Address, IPv4Network

from mwparserfromhell import parse
from mwparserfromhell.wikicode import Wikicode


class ArchiveError(ValueError):
    pass

class InvalidIpV4Error(ValueError):
    pass


@dataclass(frozen=True)
class SpiDocumentBase:
    page_title: str

    def master_name(self):
        parts = self.page_title.split('/')
        if parts[-1] == 'Archive':
            parts.pop()
        return parts[-1]


@dataclass(frozen=True)
class SpiSourceDocument(SpiDocumentBase):
    wikitext: str


@dataclass(frozen=True)
class SpiParsedDocument(SpiDocumentBase):
    page_title: str
    wikicode: Wikicode


@dataclass
class SpiCase:
    parsed_docs: List[SpiParsedDocument]
    _master_name: str


    @staticmethod
    def for_master(wiki, master_name):
        """Build and return an SPICase for the given sock master.

        The active page and any archives are used and combined.

        """
        case_title = f'Wikipedia:Sockpuppet investigations/{master_name}'
        case_doc = SpiSourceDocument(case_title, wiki.page(case_title).text())
        docs = [case_doc]

        archive_title = f'{case_title}/Archive'
        archive_text = wiki.page(archive_title).text()
        if archive_text:
            archive_doc = SpiSourceDocument(archive_title, archive_text)
            docs.append(archive_doc)

        return SpiCase(*docs)


    def __init__(self, *sources):
        """A case can be made up of multiple source documents.  In practice,
        there will usually be two; the currently active page, and the
        archive page.  New cases, however, may not have an archive
        yet, and in exceptional cases, there may be multiple archives.

        Each source is SpiSourceDocument.
        """
        self.parsed_docs = [SpiParsedDocument(s.page_title, parse(s.wikitext, skip_style_tags=True))
                            for s in sources]

        master_names = set(doc.master_name() for doc in self.parsed_docs)
        if len(master_names) == 0:
            raise ArchiveError("No sockmaster name found")
        if len(master_names) > 1:
            raise ArchiveError("Multiple sockmaster names found: %s" % master_names)
        self._master_name = master_names.pop()


    def master_name(self):
        return self._master_name


    def days(self):
        """Return an iterable of SpiCaseDays"""
        for doc in self.parsed_docs:
            for section in doc.wikicode.get_sections(levels=[3]):
                yield SpiCaseDay(section, doc.page_title)


    def find_all_ips(self):
        '''Iterates over all the IPs mentioned in checkuser templates.
        Each user is represented as a SpiIpInfo.  Order of iteration
        is not guaranteed, and templates are not deduplicated.
        '''
        for day in self.days():
            for ip_address in day.find_ips():
                yield ip_address


    def find_all_users(self):
        '''Iterates over all the users mentioned in checkuser templates.
        Each user is represented as a SpiUserInfo.  Order of iteration
        is not guaranteed, and templates are not deduplicated.

        The master is included as a user, with date set to None.

        '''
        yield SpiUserInfo(self.master_name(), None)
        for day in self.days():
            for user in day.find_users():
                yield user


@dataclass(frozen=True)
class SpiCaseDay:
    wikicode: Wikicode
    page_title: str


    def date(self):
        '''Return the date of this section as a string.  Leading and
        trailing whitespace is stripped from the sring.

        '''
        headings = self.wikicode.filter_headings(matches=lambda h: h.level == 3)
        h3_count = len(headings)
        if h3_count == 1:
            return headings[0].title.strip_code().strip()
        raise ArchiveError("Expected exactly 1 level-3 heading, found %d" % h3_count)


    def find_users(self):
        '''Iterates over all the accounts mentioned in checkuser templates.
        Each user is represented as an SpiUserInfo.  Order of iteration
        is not guaranteed, and templates are not deduplicated.

        '''
        date = self.date()
        templates = self.wikicode.filter_templates(
            matches=lambda n: n.name.matches(['checkuser',
                                              'user',
                                              'checkip',
                                              'SPIarchive notice']))
        for template in templates:
            username = template.get('1').value
            yield SpiUserInfo(str(username), str(date))


    def find_unique_users(self):
        '''Iterates over all the unique accounts mentioned in checkuser
        templates.  Each user is represented as an SpiUserInfo.  Order
        of iteration is not guaranteed, but unlike find_users(),
        templates are deduplicated.

        '''
        seen = set()
        for user in self.find_users():
            if user not in seen:
                seen.add(user)
                yield user


    def find_ips(self):
        '''Iterates over all the IPs mentioned in checkuser templates.
        Each ip is represented as an SpiIpInfo.  Order of iteration
        is not guaranteed, and templates are not deduplicated.
        '''
        date = self.date()
        templates = self.wikicode.filter_templates(
            matches=lambda n: n.name.matches('checkip'))
        for template in templates:
            ip_str = template.get('1').value
            try:
                yield SpiIpInfo(str(ip_str), str(date), self.page_title)
            except InvalidIpV4Error:
                pass


@dataclass(order=True, unsafe_hash=True)
class SpiUserInfo:
    username: str
    date: str


@dataclass(order=True, unsafe_hash=True)
class SpiIpInfo:
    ip_address: IPv4Address
    date: str
    page_title: str

    def __init__(self, ip_str, date, page_title):
        try:
            self.ip_address = IPv4Address(ip_str)
        except ValueError as error:
            raise InvalidIpV4Error(str(error))
        self.date = date
        self.page_title = page_title


    @staticmethod
    def find_common_network(infos):
        ips = [int(i.ip_address) for i in infos]
        bits = [list(map(int, format(i, '032b'))) for i in ips]
        slices = zip(*bits)
        bit_sets = [set(s) for s in slices]
        prefix = 0
        prefix_length = 0
        done = False
        for bit_set in bit_sets:
            prefix <<= 1
            if done:
                continue
            if len(bit_set) > 1:
                done = True
                continue
            prefix_length += 1
            prefix |= bit_set.pop()
        return IPv4Network((prefix, prefix_length))


def get_current_case_names(wiki, template_name):
    """Return a list of the currently active SPI case names as strings.

    It is possible for the source template to have duplicates.  Only
    the unique names are returned.

    Cases with '/' in them are disallowed.  See
    https://github.com/roysmith/spi-tools/issues/133 for details.

    """
    overview = wiki.page(template_name).text()
    wikicode = parse(overview)
    templates = wikicode.filter_templates(matches=lambda n: n.name.matches('SPIstatusentry'))
    raw_names = {str(t.get(1)) for t in templates}
    return [name for name in raw_names if '/' not in name]


def find_active_case_template(wiki):
    """Return the name of the curently active template listing SPI cases.

    Returns None if the template can't be determined.

    """
    spi_page = wiki.page('Wikipedia:Sockpuppet investigations').text()
    wikicode = parse(spi_page)
    template_names = [t.name for t in wikicode.filter_templates()]
    candidates = ['Wikipedia:Sockpuppet investigations/Cases/Overview',
                  'User:AmandaNP/SPI case list']
    for name in candidates:
        if name in template_names:
            return name
    return None
