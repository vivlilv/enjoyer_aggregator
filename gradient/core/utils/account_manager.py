# account_manager.py
import asyncio
from faker import Faker
from logger import logger
from core.models.account import Account
from core.gradient_client import GradientClient
from core.captcha import CaptchaService
from core.utils.file_manager import str_to_file
from core.utils.proxy_manager import ProxyManager
from core.utils.mail import Mail
from pyuseragents import random as random_useragent
import random

from database import update_account_points, update_account_client_id, update_account_node_password, get_account_node


class AccountManager:
    def __init__(self, threads, ref_codes, captcha_service, proxy_manager, user_id):
        self.user_id = user_id
        self.ref_codes = ref_codes + ['4X6TN1']
        self.threads = threads
        self.semaphore = asyncio.Semaphore(self.threads)
        self.fake = Faker()
        self.captcha_service = captcha_service
        self.should_stop = False
        self.proxy_manager = proxy_manager

    async def register_account(self, email: str, password: str, imap_pass: str = None):

        async with self.semaphore:

            if self.should_stop:
                return
            
            proxy_url = await self.proxy_manager.get_proxy()

            try:

                if not imap_pass:
                    imap_pass = password

                username = self.fake.user_name()
                user_agent = random_useragent()
                ref_code = random.choice(self.ref_codes)
                mail = Mail(email, imap_pass)
                client = GradientClient(email, password, username, proxy_url, user_agent)

                async with client:
                        
                    access_token = await client.signup()

                    if access_token:

                        await client.send_verify_email(access_token, self.captcha_service)
                        await asyncio.sleep(15)
                        email_code = await mail.get_msg_code_async('Here is your verification code.')
                        if email_code:

                            await client.verify_email(access_token, email_code)
                            uid, access_token = await client.login()
                            await client.register(ref_code, access_token)
                            # str_to_file('data/new_accounts.txt', f'{email}:{password}')
                            logger.info(f'Успешно зарегистрировано | {email}')

            except Exception as e:

                error_message = str(e)

                if "curl: (7)" in error_message or "curl: (28)" in error_message:
                    logger.error(f'{email} | Proxy failed: {proxy_url} | {e}')
                    return await self.register_account(email, password, imap_pass)
                elif "curl: (35)" in error_message or "EOF" in error_message:
                    logger.error(f"{email} | SSL or Protocol Error: {proxy_url} | {e}")
                    return await self.register_account(email, password, imap_pass)
                
                logger.error(f'{email} | {e}')

    async def login_account(self, email: str, password: str):
        async with self.semaphore:
            if self.should_stop:
                return None
            proxy_url = await self.proxy_manager.get_proxy()
            user_agent = random_useragent()
            try:
                client = GradientClient(email=email, password=password, proxy=proxy_url, user_agent=user_agent)
                async with client:
                    uid, access_token = await client.login()
                    logger.success(f'Successfully logged in | {email}')
                    account_data = Account(
                        email=email,
                        password=password,
                        uid=uid,
                        access_token=access_token,
                        user_agent=user_agent,
                        proxy_url=proxy_url
                    )
                    return account_data
            except Exception as e:
                error_message = str(e)
                if "curl: (7)" in error_message or "curl: (28)" in error_message:
                    logger.error(f'{email} | Proxy failed: {proxy_url} | {e}')
                    return await self.login_account(email, password)
                logger.error(f'{email} | {e}')
                return None

    async def mining_loop(self, account: Account):

        while not self.should_stop:
            logger.info(f"Starting mining for account {account}")
            await self.start_mining(account)
            await asyncio.sleep(150)

    async def start_mining(self, account: Account):

        if self.should_stop:
            return
        
        client = None

        if not account.access_token:
            logger.warning(f"No access token for account {account.email}")
            return
        
        async with self.semaphore:

            try:

                account_client_id, account_node_password = get_account_node(self.user_id, account.email)

                client = GradientClient(email=account.email, proxy=account.proxy_url, user_agent=account.user_agent, uid = account.uid, node_password = account_node_password, client_id = account_client_id)

                async with client:
                    
                    points, client_id, node_password = await client.mining(account.access_token)
                    logger.info(f"[{account.email}] | Mined Finished | Sleep before start | Total Points: {points}")

                    if  client_id != account_client_id:
                        update_account_client_id(self.user_id, account.email, client_id)

                    if node_password != account_node_password:
                        update_account_node_password(self.user_id, account.email, node_password)

                    update_account_points(self.user_id, account.email, points)

            except Exception as e:
                if client:
                    await client.safe_close()
                error_message = str(e).lower()
                if "curl: (7)" in error_message or "curl: (28)" in error_message or "proxy" in error_message or "CONNECT tunnel failed" in error_message:
                    logger.error(f'{account.email} | Proxy failed: {account.proxy_url} | {e}')
                    account.proxy_url = await self.proxy_manager.get_proxy()
                    return await self.start_mining(account)
                elif "timed out" in error_message:
                    logger.warning(f"{account} | Timed out to connection: {account.proxy_url} | {e}")
                    return await self.start_mining(account)
                elif "empty document" in error_message:
                    logger.warning(f"{account} | Empty response: Wait before trying again")
                    asyncio.sleep(300)
                    return await self.start_mining(account)
                elif "curl: (35)" in error_message or "EOF" in error_message:
                    logger.error(f"{account} | SSL or Protocol Error: {account.proxy_url} | {e}")
                    return await self.start_mining(account)
                else:
                    logger.error(f'Mining error for {account.email}: {e}')

    def stop(self):
        self.should_stop = True


class TokenError(Exception):
    pass
