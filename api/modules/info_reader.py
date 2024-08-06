import re
import string

import requests.exceptions
from socid_extractor import parse, extract
from typing import List


class InfoReader:
    """
    InfoReader Class
    """

    def __init__(self, content: dict = None) -> None:
        """Contructor

        Args:
            content (dict): [description]. Defaults to None.
            # social_path (str): [description]. Defaults to "./socials.txt".
        """

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
        """getPhoneNumber function

        Returns:
            list: [description]
        """
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
        """getEmails Function

        Returns:
            list: [description]
        """
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
        """getSocials Function

        Returns:
            list: [description]
        """
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
