from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
from ipaddress import IPv4Address, IPv4Network
from itertools import chain
import re

from mwparserfromhell import parse
from mwparserfromhell.wikicode import Wikicode

from django.core.cache import cache

# pylint: disable=invalid-name


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


@dataclass(frozen=True)
class CacheableSpiCase:
    master_name: str
    rev_id: int = None
    users: List[SpiUserInfo] = field(default_factory=list)
    ip_addresses: List[SpiIpInfo] = field(default_factory=list)


    @staticmethod
    def get(wiki, master_name):
        titles = (f'Wikipedia:Sockpuppet investigations/{master_name}{suffix}' for suffix in ['', '/Archive'])
        revisions = chain.from_iterable([wiki.page(t).revisions(count=1) for t in titles])
        rev_id = max(r.rev_id for r in revisions)
        key = f'spi.CacheableSpiCase.{master_name}'
        case = cache.get(key, version=rev_id)
        if case is None:
            spi_case = SpiCase.for_master(wiki, master_name)
            case = CacheableSpiCase(master_name,
                                    rev_id,
                                    list(spi_case.find_all_users()),
                                    list(spi_case.find_all_ips()))
            cache.set(key, case, version=rev_id)
        return case


@dataclass
class SpiCase:
    parsed_docs: List[SpiParsedDocument]
    master_name: str


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

        To accomodate both new and old style formatting, any old-style
        (level-5) headers are mappedto new style (level-3) headers
        before parsing.  This is an ugly hack, but doing it correctly
        is just too painful.

        en.wikipedia.org/w/index.php?oldid=1039087434#Header_levels_on_SPI_report_template
        has some history on why this uses such strange formatting.

        """
        self.parsed_docs = []
        map_5_to_3_pattern = re.compile(r"^=====<big>([a-zA-Z 0-9]*)</big>=====$", re.MULTILINE)
        for s in sources:
            mapped_text = map_5_to_3_pattern.sub(r'===\1===', s.wikitext)
            parsed_text = parse(mapped_text, skip_style_tags=True)
            self.parsed_docs.append(SpiParsedDocument(s.page_title, parsed_text))

        master_names = set(doc.master_name() for doc in self.parsed_docs)
        if len(master_names) == 0:
            raise ArchiveError("No sockmaster name found")
        if len(master_names) > 1:
            raise ArchiveError("Multiple sockmaster names found: %s" % master_names)
        self.master_name = master_names.pop()


    def days(self):
        """Return an iterable of SpiCaseDays"""
        for doc in self.parsed_docs:
            for section in doc.wikicode.get_sections(levels=[3]):
                yield SpiCaseDay(section, doc.page_title)


    def find_all_ips(self):
        '''Iterates over all the IPs mentioned in checkuser or checkip
        templates.  Each user is represented as a SpiIpInfo.  Order of
        iteration is not guaranteed, and templates are not
        deduplicated.

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
        yield SpiUserInfo(self.master_name, None)
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
        titles = tuple(h.title for h in headings)
        raise ArchiveError(f"Expected exactly 1 level-3 heading, found {h3_count} {titles}")


    def parse_socklist(self):
        '''Iterates over all the users mentioned in socklist templates.
        Each user is represented as a SpiUserIngo.  Order of iteration
        is not guaranteed, and users are not deduplicated
        
        '''
        date = self.date()
        templates = self.wikicode.filter_templates(
            matches=lambda n: n.name.matches(['sock list', 'socklist']))
        for template in templates:
            for param_key, param_value in template.params.items():
                if param_key.removeprefix('sock').removeprefix('ip').isdigit():
                    yield SpiUserInfo(str(param_value), str(date))


    def find_users(self):
        '''Iterates over all the users mentioned in checkuser or checkip
        templates.  Each user is represented as a SpiUserInfo.  Order
        of iteration is not guaranteed, and templates are not
        deduplicated.

        '''
        date = self.date()
        templates = self.wikicode.filter_templates(
            matches=lambda n: n.name.matches(['checkuser',
                                              'user',
                                              'checkip',
                                              'checkIP',
                                              'SPIarchive notice']))
        for template in templates:
            username = template.get('1').value
            yield SpiUserInfo(str(username), str(date))
        yield from self.parse_socklist()


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
        '''Iterates over all the IPs mentioned in checkuser or checkip
        templates.  Each ip is represented as an SpiIpInfo.  Order of
        iteration is not guaranteed, and templates are not
        deduplicated.

        The normal case-mapping rules supoprt either checkip or
        Checkip.  We also allow checkIP and CheckIP, since those are
        available on enwiki via a redirect.

        '''
        date = self.date()
        templates = self.wikicode.filter_templates(
            matches=lambda n: n.name.matches(['checkip', 'checkIP']))
        for template in templates:
            ip_str = template.get('1').value
            try:
                yield SpiIpInfo(str(ip_str), str(date), self.page_title)
            except InvalidIpV4Error:
                pass
        for account in self.parse_socklist():
            try:
                yield account
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


def get_current_case_names(wiki):
    """Return a list of the currently active SPI case names as strings.

    It is possible for the source template to have duplicates.  Only
    the unique names are returned.

    Cases with '/' in them are disallowed.  See
    https://github.com/roysmith/spi-tools/issues/133 for details.

    """
    template_name = _find_active_case_template(wiki)
    overview = wiki.page(template_name).text()
    wikicode = parse(overview)
    templates = wikicode.filter_templates(matches=lambda n: n.name.matches('SPIstatusentry'))
    raw_names = {str(t.get(1)) for t in templates}
    return [name for name in raw_names if '/' not in name]


def _find_active_case_template(wiki):
    """Return the name of the curently active template listing SPI cases.

    Returns None if the template can't be determined.

    """
    spi_page = wiki.page('Wikipedia:Sockpuppet investigations').text()
    wikicode = parse(spi_page)
    template_names = [t.name for t in wikicode.filter_templates()]
    candidates = ['Wikipedia:Sockpuppet investigations/Cases/Overview',
                  'User:AmandaNP/SPI case list',
                  'User:Mz7/SPI case list']
    for name in candidates:
        if name in template_names:
            return name
    return None
