#!/bin/python3
from typing import List, Optional

import pandas as pd
import requests
import lxml.html


# https://en.wikipedia.org/wiki/List_of_people_pardoned_or_granted_clemency_by_the_president_of_the_United_States
# https://www.justice.gov/pardon/search-clemency-case-status-since-1989
# https://www.justice.gov/pardon/clemency-denials
# https://www.justice.gov/pardon/clemencyrecipients


def retrieve_clemency_denial_urls() -> List[dict]:
    return clemency_helper("https://www.justice.gov/pardon/clemency-denials",
                           "/html/body/section[3]/div[2]/div/div/div/article/div[1]/div/div/div/p")


def retrieve_clemency_recipient_urls() -> List[dict]:
    return clemency_helper("https://www.justice.gov/pardon/clemencyrecipients",
                           "/html/body/section[3]/div[2]/div/div/div/div[1]/div/div/div[1]/div/div/div/div/div/div/p")


def retrieve_archive_clemency_document_url() -> Optional[str]:
    url: str = "https://www.justice.gov/pardon/search-clemency-case-status-since-1989"
    xpath: str = "/html/body/section[3]/div[2]/div/div/div/div[1]/div/div[3]/div[1]/div/div/div/div/div/div/p[2]/a/@href"

    archive_page: requests.Response = requests.get(url=url)
    archive_document: lxml.html.HtmlElement = lxml.html.fromstring(archive_page.text)
    document_url: List[lxml.html.HtmlElement] = archive_document.xpath(xpath)

    if len(document_url) < 1:
        return None

    # lxml.html.HtmlElement Or lxml.etree._ElementUnicodeResult
    return str(document_url[0])


def clemency_helper(clemency_recipients_url: str, xpath: str) -> List[dict]:
    clemency_recipients_page: requests.Response = requests.get(url=clemency_recipients_url)

    clemency_recipients_document: lxml.html.HtmlElement = lxml.html.fromstring(clemency_recipients_page.text)
    clemency_recipients_list: List[lxml.html.HtmlElement] = clemency_recipients_document.xpath(xpath)

    clemency_recipients_links: List[dict] = []
    for cr_list in clemency_recipients_list:
        link_text_list: List[str] = cr_list.xpath("a/text()")
        year_text_list: List[str] = cr_list.xpath("text()")
        link_list: List[str] = cr_list.xpath("a/@href")

        for item in range(0, len(link_text_list)):
            link_text: str = link_text_list[item].replace(u'\xa0', u' ').rstrip().lstrip()
            link: str = link_list[item]

            clemency_recipients_link: dict = {
                "link_text": link_text,
                "link": link
            }

            if len(year_text_list) > 0 and year_text_list[item].replace(u'\xa0', u' ').rstrip().lstrip() != "":
                clemency_recipients_link["year_text"] = year_text_list[item].replace(u'\xa0', u' ').rstrip().lstrip()
                # print(f"{link_text} '{clemency_recipients_link['year_text']}' - {link}")

            clemency_recipients_links.append(clemency_recipients_link)

    return clemency_recipients_links


# Multiple HTML Tables Per Page
# retrieve_clemency_recipient_urls()
# retrieve_clemency_denial_urls()

# Will Be XLS Document As Of January 2021 - Try pd.read_excel(...)
# retrieve_archive_clemency_document_url()

# TODO: Loop Through All Pages For Tables And Format For Repo, Then Import XLS Document And Do The Same (Unique Values Please)
# TODO: Note: The HTML Tables Should Be Unique From The Standard DOJ XLS, Mark The Granter/Denier For Each Row
# Example With Multiple Tables (25 Tables): https://www.justice.gov/pardon/pardons-denied-president-george-w-bush-2001-2009
# https://pbpython.com/pandas-html-table.html
tables: List[pd.DataFrame] = pd.read_html(io="https://www.justice.gov/pardon/pardons-denied-president-george-w-bush-2001-2009")
print(tables)
