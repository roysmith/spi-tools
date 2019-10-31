import mwparserfromhell

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
        if n ==  1:
            return templates[0].get('1').value
        raise ArchiveError("Expected exactly 1 {{SPIarchive notice}}, found %d" % n)
