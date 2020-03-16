import re
import bs4
import mistune
from whoosh.analysis import StemmingAnalyzer, LowercaseFilter  # StopFilter

from ..util import is_url_whoosh


"""
content.py:
    utilities for parsing, rendering, filtering, and scrubbing the content field
    of documents for displaying on an HTML page.
"""


def get_stemming_analyzer():
    """
    Get a stemming analyzer to use for the content field
    """
    stemming_analyzer = StemmingAnalyzer() | LowercaseFilter()
    return stemming_analyzer


def cap(self, s, l):
    """
    Snip some text if it gets too long
    """
    return s if len(s) <= l else s[0 : l - 3] + "..."


class DontEscapeHtmlInCodeRenderer(mistune.Renderer):
    """
    When turning Markdown into HTML, don't escape existing HTML.
    """

    def __init__(self, **kwargs):
        super(DontEscapeHtmlInCodeRenderer, self).__init__(**kwargs)

    def block_code(self, code, lang):
        if not lang:
            return "<pre><code>%s\n</code></pre>\n" % code
        return '<pre><code class="lang-%s">%s\n</code></pre>\n' % (lang, code)

    def codespan(self, text):
        return "<code>%s</code>" % text.rstrip()


def scrub_markdown(whoosh_search_result, content_field):
    """
    Scrub a Markdown content field of problematic content and HTML,
    then render the Markdown into HTML and return it.
    """
    # Highlights contains the content highlighted for search results
    highlights = whoosh_search_result.highlights(content_field)
    if not highlights:
        # Just use the first 1,000 words of the document
        highlights = cap(whoosh_search_result["content"], 1000)

    # Scrub:
    # Unescape raw HTML appearing in highlights
    import html
    highlights = html.unescape(highlights)

    # Scrub:
    # Look for markdown links following the pattern [link text](link url)
    resrch = re.search(r"\[(.*)\]\((.*)\)", highlights)
    if resrch is not None:
        # Extract the link url and check if it looks like a URL
        u = resrch.groups()[1]
        if not is_url_whoosh(u):
            # This is a relative Markdown link, so we need to break it
            # by putting a space between [link text] and (link url)
            new_highlights = re.sub(r"\[(.*)\]\((.*)\)", r"[\g<1>] (\g<2>)", highlights)
            highlights = new_highlights

    # Scrub:
    # If we have any <table> tags in our search results,
    # we make a BeautifulSoup from the results, which will
    # fill in all missing/unpaired tags, then extract the
    # text from the soup.
    if "<table>" in highlights:
        soup = bs4.BeautifulSoup(highlights, features="html.parser")
        highlights = soup.text
        del soup

    # Render:
    # Turn the markdown content into HTML code
    markdown = mistune.Markdown(renderer=DontEscapeHtmlInCodeRenderer(), escape=False)
    html = markdown(highlights)
    html = re.sub(r"\n", "<br />", html)

    # Scrub:
    # Remove <a> tag from broken links
    soup = bs4.BeautifulSoup(html, features="html.parser")
    for tag in soup.find_all("a"):
        u = tag.get("href")
        if not is_url_whoosh(u):
            tag.replaceWith(tag.text)
    result = str(soup)

    # Unscrub:
    # Fix the relative Markdown links we broke earlier.
    result = re.sub(r"\] \(", r"](", result)

    return result
