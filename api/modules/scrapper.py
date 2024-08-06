from typing import Any
import requests
from requests.models import Response
from bs4 import BeautifulSoup, Comment
import re
from urllib.parse import urljoin, urlparse

class Scrapper:
    """
    Scrapper Class
    """

    def __init__(self, url: str = None, contents: list = [], crawl=False) -> None:
        """Contructor

        Args:
            url (str): [description]. Defaults to None.
            contents (list, optional): Defaults to [].
            crawl (bool): Defaults to False.
        """

        self.url = url
        self.urls = []
        self.contents = contents
        self.crawl = crawl

    def clean(self) -> list:
        """clean function

        Returns:
            list: Cleaned contents with script content preserved.
        """
        cleaned_contents = []

        for content in self.contents:
            soup = BeautifulSoup(content, "html.parser")

            # Step 2: Extract script contents
            script_texts = []
            for script in soup.find_all("script"):
                if script.string:  # Check if the script tag contains anything
                    script_texts.append(script.string)
                elif script.contents:
                    # Sometimes script contents are not picked up as string
                    # but rather as a list of NavigableString or Comment objects
                    for elem in script.contents:
                        if isinstance(elem, Comment):
                            # This is to handle the HTML comments in script tags
                            script_texts.append(str(elem))
                        else:
                            script_texts.append(str(elem))

            # Step 3: Remove the script and style tags from the soup
            for script_or_style in soup(["script", "style"]):
                script_or_style.extract()

            # Extract other text
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = '\n'.join(chunk for chunk in chunks if chunk)

            # Step 4: Combine script contents with the rest of the text
            full_content = "\n".join(script_texts) + "\n" + text_content

            cleaned_contents.append(full_content)

        return cleaned_contents

    def getURLs(self) -> list:
        """getURLs function

        Returns:
            list: [description]
        """
        unique_urls = set()
        urls: list = []
        content: str = requests.get(self.url).text
        soup = BeautifulSoup(content, "html.parser")

        for link in soup.find_all('a', href=True):  # href=True filters out <a> tags without href attribute
            href = link['href']
            # Use urljoin to handle both absolute and relative URLs
            full_url = urljoin(self.url, href)
            # Check if the url is a valid HTTP URL
            if urlparse(full_url).scheme in ['http', 'https']:
                unique_urls.add(full_url)
        # for link in soup.find_all('a'):
        #     if link.get("href") is not None:
        #         if self.url not in link.get("href"):
        #             if "http" not in link.get("href") and "https" not in link.get("href") and "mailto:" not in link.get(
        #                     "href"):
        #                 urls.append(self.url + link.get('href'))
        #                 continue
        #     urls.append(link.get("href"))

        return list(unique_urls)

    def getText(self) -> dict:
            """getText function
            Returns:
                dict
            """
            urls = self.getURLs()
            contents: list = []
            targeted_patterns = [r'contact', r'about']  # Patterns to search in URLs

            if self.crawl:
                for url in urls:
                    try:
                        # Check if URL contains the targeted patterns
                        if url is not None and any(re.search(pattern, url, re.IGNORECASE) for pattern in targeted_patterns):
                            req: Response = requests.get(url)
                            if req.status_code == 200:
                                contents.append(req.text)
                    except requests.exceptions.RequestException as e:
                        print(f"An error occurred: {e}")
            try:
                # Check if the base URL contains the targeted patterns
                print(f"IS self.url : {self.url}")
                if any(re.search(pattern, self.url, re.IGNORECASE) for pattern in targeted_patterns):
                    req: Response = requests.get(self.url)
                    if req.status_code == 200:
                        contents.append(req.text)
            except requests.exceptions.RequestException as e:
                print(f"An error occurred: {e}")

            # Clean the scraped contents
            contents = Scrapper(contents=contents).clean()
            return {"text": contents, "urls": urls}

