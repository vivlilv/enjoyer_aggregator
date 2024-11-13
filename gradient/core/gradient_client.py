import time
import uuid
import random
import warnings
import asyncio
import json
import re
import socks
import paho.mqtt.client as mqtt

from logger import logger
from curl_cffi.requests import AsyncSession
from tenacity import retry, stop_after_attempt, wait_fixed

# Suppress the specific warning
# warnings.filterwarnings("ignore", category=UserWarning, message="Curlm already closed!")


class GradientClient:
    def __init__(self, email: str = '', password: str = '', username: str = '', proxy: str = '', user_agent: str = '', uid: str = None, node_password: str = None, client_id: str = None,):
        self.email = email
        self.password = password
        self.username = username
        self.client_id = client_id
        self.node_password = node_password
        self.uid = uid
        self.user_agent = user_agent
        self.proxy = proxy
        self.client = None
        self.timestamp = int(time.time() * 1000)

    async def __aenter__(self):
        await self.create_client()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.safe_close()

    # ------------------------
    # MQTT AND HTTP Protocol Methods
    # ------------------------

    async def create_client(self):
        try:
            self.client = AsyncSession(verify=False, impersonate='chrome')
            if self.proxy:
                self.client.proxies.update({'http': self.proxy, 'https': self.proxy})
        except Exception as e:
            logger.error(f'Error session initialization for {self.email}: {e}')
            raise

    async def mqtt_client(self, message_data):

        try:

            proxy = self._proxy_parse()

            publish_topic = f'client/online/{self.client_id}'
            subscribe_topic = f'client/task/{self.client_id}'

            client = mqtt.Client(client_id = self.client_id, transport="websockets", protocol=mqtt.MQTTv5)

            client.proxy_set(proxy_type = proxy['protocol'], proxy_addr = proxy['host'], proxy_port = proxy['port'], proxy_username = proxy['username'], proxy_password = proxy['password'])

            def on_connect(client, userdata, flags, rc, properties=None):
                if rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.success(f'Node Mined {self.email} | Status: {rc}')
                else:
                    logger.warning(f'Node Mined {self.email} | Status: {rc}')

            client.on_connect = on_connect

            # Set the WebSocket path
            client.ws_set_options(path="/mqtt")
            # TLS/SSL for secure connection
            client.tls_set()
            # Set credentials if needed
            client.username_pw_set(username=self.uid, password=self.node_password)

            # Connect to gradient MQTT broker
            client.connect("wss.gradient.network", port=443)

            # Start the loop in a separate thread
            asyncio.get_event_loop().run_in_executor(None, client.loop_start)

            # Subscribe and publish on topic
            client.subscribe(subscribe_topic)
            
            # Publish every 10 min for an 1 h
            for _ in range(5):
                client.publish(publish_topic, payload = json.dumps(message_data))
                await asyncio.sleep(30)

        except Exception as e:
            raise Exception(f'Error Node Mined: {e}')

        finally:
            if client:
                client.loop_stop()
                client.disconnect()


    async def safe_close(self):
        try:
            if self.client:
                await asyncio.shield(self.client.close())
        except Exception as e:
            logger.error(f'Error closing session for {self.email}: {e}')
        finally:
            self.client = None

    # ------------------------
    # Gradient API Methods
    # ------------------------

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
    async def signup(self):
        try:
            logger.info(f'{self.email} | Sign Up')
            response = await self.client.post('https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=AIzaSyCWz-svq_InWzV9WaE3ez4XqxCE0C34ddI', json={
                'clientType': 'CLIENT_TYPE_WEB',
                'email': self.email,
                'password': self.password,
                'returnSecureToken': True
            }, headers=self._headers())
            data = self._validate_response(response, 'Sign Up')

            if data == 'EMAIL_EXISTS':
                uid, access_token = await self.login()
            else:
                access_token = data['idToken']

            return access_token
        
        except Exception as e:
            raise Exception(f'Error Sign Up: {e}')
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
    async def send_verify_email(self, access_token, Captcha):
        try:
            logger.info(f'{self.email} | Send Verify Email')
            captcha = await Captcha.get_captcha_token_async()
            response = await self.client.post('https://api.gradient.network/api/user/send/verify/email', json={
                'code': captcha
            }, headers=self._auth_headers(access_token))
            self._validate_response(response, 'Captcha Verify')
        except Exception as e:
            raise Exception(f'Error Captcha Verify: {e}')
        
    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
    async def verify_email(self, access_token: str, email_code: str):
        try:
            logger.info(f'{self.email} | Verify Email')
            response = await self.client.post('https://api.gradient.network/api/user/verify/email', json={
                'code': email_code
            }, headers=self._auth_headers(access_token))
            self._validate_response(response, 'Verify Email')

        except Exception as e:
            raise Exception(f'Error Verify Email: {e}')

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
    async def register(self, REF_CODE, access_token):
        try:
            logger.info(f'{self.email} | Registration')
            response = await self.client.post('https://api.gradient.network/api/user/register', json={
                'code': random.choice(['4X6TN1', REF_CODE]),
            }, headers=self._auth_headers(access_token))
            self._validate_response(response, 'Registration')
        except Exception as e:
            raise Exception(f'Error Registration: {e}')
    
    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
    async def login(self):
        try:
            logger.info(f'{self.email} | Login')
            response = await self.client.post('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCWz-svq_InWzV9WaE3ez4XqxCE0C34ddI', json={
                'clientType': 'CLIENT_TYPE_WEB',
                'email': self.email,
                'password': self.password,
                'returnSecureToken': True
                }, headers=self._headers())
            data = self._validate_response(response, 'Login')
            return data['localId'], data['idToken']
        except Exception as e:
            raise Exception(f'Error Login: {e}')

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
    async def mining(self, access_token: str):

        try:
            
            if not self.client_id or not self.node_password:
                self.client_id, self.node_password = await self.node_register(access_token)
            
            # status = await self.node_status(access_token)

            # if status == 'banned':
            #     self.client_id, self.node_password = await self.node_register(access_token)

            message_data = {
                'type': 'online',
                'clientid': self.client_id,
                'account': self.uid,
                'timestamp': self.timestamp
            }

            for _ in range(12):
                await self.mqtt_client(message_data)
                await asyncio.sleep(150)

            points = await self.info(access_token)

            return points, self.client_id, self.node_password
        
        except Exception as e:
            raise Exception(e)
    
    # @retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
    # async def node_status(self, access_token):
    #     try:
    #         logger.info(f'{self.email} | Get Sentry Node')
    #         response = await self.client.get(f'https://api.gradient.network/api/sentrynode/get/{self.client_id}', headers=self._auth_headers(access_token))
    #         data = self._validate_response(response, 'Get Sentry Node')

    #         if data['data']['active'] and data['data']['connect']:
    #             status = 'Mined'
    #         elif data['data']['banned']:
    #             status = f"Banned | {data['data']['bannedReason']}"
    #         else:
    #             status = 'Disabled or Disconnect'

    #         return status

    #     except Exception as e:
    #         raise Exception(f'Error Sentry Node: {e}')
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
    async def node_register(self, access_token):
            
        try:

            logger.info(f'{self.email} | Register Sentry Node')
            response = await self.client.post('https://api.gradient.network/api/sentrynode/register', json={}, headers=self._auth_headers(access_token))
            data = self._validate_response(response, 'Register Sentry Node')
            return data['clientid'], data['password']

        except Exception as e:
            raise Exception(f'Error Register Sentry Node: {e}')


    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
    async def info(self, access_token: str):
        try:
            if not self.client:
                await self.create_client()

            response = await self.client.post('https://api.gradient.network/api/user/profile', headers=self._auth_headers(access_token))
            data = self._validate_response(response, 'Info')
            return data['data']['point']['total']/100000
        
        except Exception as e:
            raise Exception(f'Error Info: {e}')

    def _headers(self):
        return {'Content-Type': 'application/json', 'User-Agent': self.user_agent,
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Origin': 'https://app.gradient.network',
                'X-Client-Data': 'CJG2yQEIpLbJAQipncoBCOyDywEIlqHLAQiFoM0BCLvIzQEI0sfOAQinyM4BCIfJzgEImcrOARj0yc0B',
                'X-Client-Version': 'Chrome/JsCore/10.13.0/FirebaseCore-web',
                'X-Firebase-Gmpid': '1:236765003043:web:4300552603f2d14908a096'}
    
    def _auth_headers(self, token: str):
        headers = self._headers()
        headers['Authorization'] = f'Bearer {token}'
        headers.update({
            'Referer': 'https://app.gradient.network/'
        })
        return headers

    def _validate_response(self, response, operation):

        data = response.json()
        if response.status_code != 200 or data is None or data.get('code') is not None and data.get('code') != 200:
            message = data.get('error', {}).get('message') or data.get('error', {}).get('msg') or data.get('msg')

            if 'EMAIL_EXISTS' in message:
                return 'EMAIL_EXISTS'

            if not message:
                message = 'Unknow Gradient API Error'  
            if not data:
                message = 'No data' 

            raise Exception(message)
        
        return data
    
    def _proxy_parse(self):
        # parse proxy from any string format
        proxy_pattern = re.compile(
            r'^(?:(socks5|https?)://)?'                             # protocol (default http)
            r'(?:(?P<username>[^:@]+)(?::(?P<password>[^@]+))?@)?'  # username and password
            r'(?P<host>[a-zA-Z0-9.-]+|\d{1,3}(?:\.\d{1,3}){3})'     # ip or host
            r'(?::(?P<port>\d+))?'                                  # port (optional)
        )

        match = proxy_pattern.match(self.proxy)

        if match:

            protocol = match.group(1) or socks.HTTP  # default http
            if protocol == 'http' or protocol == 'https':
                protocol = socks.HTTP
            elif protocol == 'socks5':
                protocol = socks.SOCKS5
            
            return {
                'protocol': protocol,
                'username': match.group('username'),
                'password': match.group('password'),
                'host': match.group('host'),
                'port': int(match.group('port')) or 80  # default 80
            }

        else:
            raise ValueError("Invalid proxy format")
