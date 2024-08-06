from http.server import BaseHTTPRequestHandler
from requests.models import Response
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin, urlparse
from socid_extractor import parse, extract
from typing import List

import requests
import re
import string
import requests.exceptions
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        # You would retrieve your parameters from `data` here
        url = data.get('url')
        urls = data.get('urls')
        crawl = data.get('crawl', False)
        sm = data.get('sm', False)
        verbose = data.get('verbose', False)

        # Depending on the parameters, call the respective function
        try:
            if url:
                result = process_url(url, crawl, sm, verbose)
                self.respond_with_json(result)
            elif urls:
                results = process_url_list(urls, crawl, sm, verbose)
                self.respond_with_json(results)
            else:
                self.respond_with_error({"error": "No URL or URLs provided"}, 400)
        except Exception as e:
            self.respond_with_error({"error": str(e)}, 500)

    def respond_with_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def respond_with_error(self, data, status_code):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))


# 处理单个 URL 的函数
def process_url(url, crawl, sm, verbose):
    print(f"Processing URL: {url}")
    domain = url
    try:
        # 确保 URL 是正确格式化的
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "http://" + url
        # 调用 Scrapper 和 InfoReader 类
        scrap = Scrapper(url=url, crawl=crawl)
        IR = InfoReader(content=scrap.getText())
        emails = IR.getEmails()
        # numbers = IR.getPhoneNumber()
        socials = IR.getSocials() if not sm else IR.getSocialsInfo()

        # 构建返回的结果
        result = {
            "Domain": domain,
            "EMails": emails,
            # "Numbers": numbers,
            "SocialMedia": socials
        }
        # print(f"Processing result: {result}")
        return result
    except Exception as e:
        print(str(e))
        # return {"error": "Error processing URL"}
        return {
            "Domain": domain,
            "EMails": [],
            "SocialMedia": []
        }

# 处理 URL 列表的函数
def process_url_list(urls, crawl, sm, verbose):
    results = []
    for url in urls:
        print(f"process_url_list: {url}")
        try:
            # 重用单个 URL 处理的逻辑
            result = process_url(url, crawl, sm, verbose)
            results.append(result)
        except Exception as e:
            print(str(e))
            results.append({"error": f"Error processing URL: {url}"})
    return results

class Scrapper:
    def __init__(self, url: str = None, contents: list = [], crawl=False) -> None:
        self.url = url
        self.urls = []
        self.contents = contents
        self.crawl = crawl

    def clean(self) -> list:
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
        unique_urls = set()
        urls: list = []
        content: str = requests.get(self.url, timeout=8).text
        soup = BeautifulSoup(content, "html.parser")

        for link in soup.find_all('a', href=True):  # href=True filters out <a> tags without href attribute
            href = link['href']
            # Use urljoin to handle both absolute and relative URLs
            full_url = urljoin(self.url, href)
            # Check if the url is a valid HTTP URL
            if urlparse(full_url).scheme in ['http', 'https']:
                unique_urls.add(full_url)

        return list(unique_urls)

    def getText(self) -> dict:
            urls = self.getURLs()
            contents: list = []
            targeted_patterns = [r'contact', r'about']  # Patterns to search in URLs

            if self.crawl:
                for url in urls:
                    try:
                        # Check if URL contains the targeted patterns
                        if url is not None and any(re.search(pattern, url, re.IGNORECASE) for pattern in targeted_patterns):
                            req: Response = requests.get(url, timeout=8)
                            if req.status_code == 200:
                                contents.append(req.text)
                    except requests.exceptions.RequestException as e:
                        print(f"An error occurred: {e}")
            
            try:
                # Check if the base URL contains the targeted patterns
                print(f"IS self.url : {self.url}")
                if any(re.search(pattern, self.url, re.IGNORECASE) for pattern in targeted_patterns):
                    req: Response = requests.get(self.url, timeout=8) # This sets an 8-second timeout
                    if req.status_code == 200:
                        contents.append(req.text)
            except requests.exceptions.RequestException as e:
                print(f"An error occurred: {e}")

            # Clean the scraped contents
            contents = Scrapper(contents=contents).clean()
            return {"text": contents, "urls": urls}

class InfoReader:
    def __init__(self, content: dict = None) -> None:
        if content is None:
            content: dict = {
                "text": [],
                "urls": []
            }

        self.content: list = content
        self.res: dict = {
            "phone": r"/^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,7}$/gm",
            "email": r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b"
        }

    def getPhoneNumber(self) -> list:
        # Doesnt work that good
        numbers: list = []
        texts: list = self.content["text"]

        for text in texts:
            for n in text.split("\n"):
                if re.findall(self.res["phone"], n):
                    for letter in string.ascii_letters:
                        n: object = n.replace(letter, "")
                    numbers.append(n)

        return list(dict.fromkeys(numbers))

    def getEmails(self) -> list:
        emails: list = []
        texts: object = self.content["text"]
        email_pattern = re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b", re.IGNORECASE)

        invalid_patterns = ["@domain.com", "sentry", "@test.com", "@email.com", "admin@"]

        for text in texts:
            found_emails = re.findall(email_pattern, text)
            found_emails = [email for email in found_emails if not any(invalid in email for invalid in invalid_patterns)]
            emails.extend(found_emails)
        
        for link in self.content["urls"]:
            if link is None:
                continue
            if "mailto:" in link:
                email = link.replace("mailto:", "")
                # Check if the email from the mailto link is not invalid
                if not any(invalid in email for invalid in invalid_patterns):
                    emails.append(email)

        return list(set(emails))

    def getSocials(self) -> list:
        sm_accounts: list = []
        socials = [
            "discord.gg",
            "youtube.com",
            "instagram.com",
            "twitter.com",
            "facebook.com",
            "linkedin.com",
            "github.com",
            "medium.com",
            "reddit.com",
            "pinterest.com",
            "tiktok.com"
        ]

        for url in self.content["urls"]:
            for s in socials:
                if url is None:
                    continue
                if s.replace("\n", "").lower() in url.lower():
                    sm_accounts.append(url)
        return list(dict.fromkeys(sm_accounts))

    def getSocialsInfo(self) -> List[dict]:
        urls = self.getSocials()
        sm_info = []
        for url in urls:
            try:
                text, _ = parse(url)
                sm_info.append({"url": url, "info": extract(text)})
            except Exception:  # Quick fix for now
                pass
        return sm_info


# if __name__ == '__main__':
#     app.run(debug=True)  # 启动 Flask 服务器
