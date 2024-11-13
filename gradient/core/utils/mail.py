import time
import asyncio
import re

from imap_tools import MailBox, AND
from logger import logger


class Mail:
    def __init__(self, email: str, imap_pass: str):
        self.email = email
        self.imap_pass = imap_pass
        self.domain = self.parse_domain()

    def parse_domain(self) -> str:

        domain: str = self.email.split("@")[-1]

        if "hotmail" in domain or "live" in domain:
            domain = "outlook.com"
        # elif domain.startswith("firstmail"):
        elif "firstmail" in domain or "dfirstmail" in domain:
            domain = "firstmail.ltd"
        elif any(sub in domain for sub in ["rambler", "myrambler", "autorambler", "ro.ru"]):
            domain = "rambler.ru"
        elif "gmx" in domain:
            domain = "gmx.com"

        return f"imap.{domain}"

    def get_msg_code(self, subject, delay: int = 60):

        if "outlook" in self.domain:
            email_folder = "JUNK"
        else:
            email_folder = "INBOX"

        with MailBox(self.domain).login(self.email, self.imap_pass, initial_folder=email_folder) as mailbox:
            for _ in range(delay // 3):

                time.sleep(15)

                try:
                    for msg in mailbox.fetch(AND(subject = subject, seen=False), reverse=True):

                        if msg.html:

                            pattern = r'<div class="pDiv">(.*?)</div>'
                            matches = re.findall(pattern, msg.html, re.DOTALL)
                            code = ''.join(match.strip() for match in matches if match.strip())

                            if code:
                                logger.success(f'{self.email} | Successfully received msg code: {code}')
                                return code

                except Exception as error:
                    logger.error(f'{self.email} | Unexpected error when getting code: {str(error)}')

        return False

    async def get_msg_code_async(self, subject, delay: int = 60):
        return await asyncio.to_thread(self.get_msg_code, subject, delay)