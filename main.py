#!/bin/python3
from typing import List, Optional

import pandas as pd
import requests
import lxml.html

# Clemency Sources
# https://en.wikipedia.org/wiki/List_of_people_pardoned_or_granted_clemency_by_the_president_of_the_United_States
# https://www.justice.gov/pardon/search-clemency-case-status-since-1989
# https://www.justice.gov/pardon/clemency-denials
# https://www.justice.gov/pardon/clemencyrecipients

# Example With Multiple Tables (25 Tables): https://www.justice.gov/pardon/pardons-denied-president-george-w-bush-2001-2009
# https://pbpython.com/pandas-html-table.html
from dateutil.parser import ParserError
from lxml.etree import XMLSyntaxError

root_site: str = "https://www.justice.gov"


def retrieve_clemency_denial_urls() -> List[dict]:
    denied: List[dict] = clemency_helper(root_site + "/pardon/clemency-denials",
                                         "/html/body/section[3]/div[2]/div/div/div/article/div[1]/div/div/div/p")

    for page in denied:
        if page["link"].startswith("/"):
            page["link"] = root_site + page["link"]

    return denied


def retrieve_clemency_recipient_urls() -> List[dict]:
    granted: List[dict] = clemency_helper(root_site + "/pardon/clemencyrecipients",
                                          "/html/body/section[3]/div[2]/div/div/div/div[1]/div/div/div[1]/div/div/div/div/div/div/p")

    for page in granted:
        if page["link"].startswith("/"):
            page["link"] = root_site + page["link"]

    return granted


def retrieve_archive_clemency_document_url() -> Optional[str]:
    doc_url: str = root_site + "/pardon/search-clemency-case-status-since-1989"
    xpath: str = "/html/body/section[3]/div[2]/div/div/div/div[1]/div/div[3]/div[1]/div/div/div/div/div/div/p[2]/a/@href"

    archive_page: requests.Response = requests.get(url=doc_url)
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


def add_to_clemency_table(page_url: str, full_table: pd.DataFrame) -> Optional[pd.DataFrame]:
    try:
        tables: List[pd.DataFrame] = pd.read_html(io=page_url)
    except ValueError:
        print(f"ValueError Trying To Load Table(s) From Page {page_url}")

        exit(1)
        return None
    except XMLSyntaxError:
        print(f"XMLSyntaxError Trying To Load Table(s) From Page {page_url}")

        exit(1)
        return None

    for table in tables:
        table.columns = table.iloc[0]
        table.drop(0, inplace=True)

        fixed_table: pd.DataFrame = pd.Series(table.values.ravel('F')).to_frame("name").dropna()

        try:
            fixed_table["date"] = pd.to_datetime(table.columns[0])
        except ParserError as e:
            print(f"Failed Convert To Date!!! URL: {page_url} - Value: '{table.columns[0]}'")
            # exit(1)
            return None

        full_table = pd.concat([full_table, fixed_table], ignore_index=True)

    full_table.sort_values(by=['date', 'name'], inplace=True)
    full_table.reset_index(inplace=True, drop=True)
    return full_table


# Multiple HTML Tables Per Page
# approved_president_urls: List[dict] = retrieve_clemency_recipient_urls()
denied_president_urls: List[dict] = retrieve_clemency_denial_urls()

# Will Be XLS Document As Of January 2021 - Try pd.read_excel(...)
# clemency_url: Optional[str] = retrieve_archive_clemency_document_url()

# TODO: Loop Through All Pages For Tables And Format For Repo, Then Import XLS Document And Do The Same (Unique Values Please)
# TODO: Note: The HTML Tables Should Be Unique From The Standard DOJ XLS, Mark The Granter/Denier For Each Row

clemency_table: pd.DataFrame = pd.DataFrame(columns=["date", "name"])
for url in denied_president_urls:
    temp_table: Optional[pd.DataFrame] = add_to_clemency_table(page_url=url["link"], full_table=clemency_table)

    if temp_table is not None:
        temp_table["judge"] = url["link_text"].split("President ")[1]
        temp_table["status"] = "denied"
        clemency_table = temp_table

print(clemency_table)
