# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2021 Neongecko.com Inc. | All Rights Reserved
#
# Notice of License - Duplicating this Notice of License near the start of any file containing
# a derivative of this software is a condition of license for this software.
# Friendly Licensing:
# No charge, open source royalty free use of the Neon AI software source and object is offered for
# educational users, noncommercial enthusiasts, Public Benefit Corporations (and LLCs) and
# Social Purpose Corporations (and LLCs). Developers can contact developers@neon.ai
# For commercial licensing, distribution of derivative works or redistribution please contact licenses@neon.ai
# Distributed on an "AS IS” basis without warranties or conditions of any kind, either express or implied.
# Trademarks of Neongecko: Neon AI(TM), Neon Assist (TM), Neon Communicator(TM), Klat(TM)
# Authors: Guy Daniels, Daniel McKnight, Regina Bloomstine, Elon Gasper, Richard Leeds
#
# Specialized conversational reconveyance options from Conversation Processing Intelligence Corp.
# US Patents 2008-2021: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending

import requests
from bs4 import BeautifulSoup
from abc import ABC
from html.parser import HTMLParser

from requests.exceptions import ConnectTimeout

from neon_utils.logger import LOG


def strip_tags(html):  # TODO: Document this! DM
    class MLStripper(HTMLParser, ABC):
        def __init__(self):
            super().__init__()
            self.reset()
            self.strict = False
            self.convert_charrefs = True
            self.fed = []

        def handle_data(self, d):
            self.fed.append(d)

        def get_data(self):
            return ''.join(self.fed)

    s = MLStripper()
    s.feed(html)
    return s.get_data()


def chunks(l, n):  # TODO: Document this! DM
    return [l[i:i + n] for i in range(0, len(l), n)]


def scrape_page_for_links(url: str) -> dict:
    """
    Scrapes the passed url for any links and returns a dictionary of link labels to URLs
    :param url: Web page to scrape
    :return: Lowercase names to links on page
    """
    import unicodedata
    available_links = {}
    retry_count = 0

    def _get_links(url):
        LOG.debug(url)
        if not str(url).startswith("http"):
            url = f"http://{url}"
        LOG.debug(url)
        html = requests.get(url, timeout=2.0).text
        soup = BeautifulSoup(html, 'lxml')
        # LOG.debug(html)
        # LOG.debug(soup)

        # Look through the page and find all anchor tags
        for i in soup.find_all("a", href=True):
            # LOG.debug(f"DM: found link: {i.text.rstrip()}")
            # LOG.debug(f"DM: found href: {i['href']}")

            if '://' not in i['href']:
                # Assume this is a relative address
                href = url + i['href'].lower()
            elif url.split('://')[1] in i['href']:
                href = i['href'].lower()
            else:
                href = None

            if href:
                available_links[unicodedata.normalize('NFKD', i.text.rstrip()
                                                      .replace(u'\u2013', '')
                                                      .replace(u'\u201d', '')
                                                      .replace(u'\u201c', '')
                                                      .replace('"', "")
                                                      .replace("'", "")
                                                      .replace("&apos;", "")
                                                      .lower())] = href
                LOG.debug("found link: " + unicodedata.normalize("NFKD", i.text.rstrip().replace(u"\u2013", "")
                                                                 .replace(u"\u201d", "").replace(u"\u201c", "")
                                                                 .replace('"', "").replace("'", "")
                                                                 .replace("&apos;", "").replace("\n", "").lower()))
                LOG.debug("found href: " + href)

        LOG.debug(available_links)

    try:
        _get_links(url)
    except ConnectTimeout:
        retry_count += 1
        if retry_count < 8:
            _get_links(url)
        else:
            raise ConnectTimeout
    except Exception as x:
        LOG.error(x)
        LOG.debug(available_links)
        raise ReferenceError
    return available_links
