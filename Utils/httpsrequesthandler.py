import time
import requests

from Utils.proxy import Proxy


class HTTPRequestHandler(object):
    def __init__(self, cookies=None, payload=None, proxies=None, timeout=5, retries=0):
        """
        This function initializes the http request handler with parameters
        :param payload:Dictionary. {k:v,k:v}
        :param proxies: list. proxies to send the http request via
        :param timeout: int. how much time to wait if we don't get an answer
        :param retries: int. how many time to resend the request if we don't get an answer
        :param cookies: dictionary. the cookies you want to send with the request exp: {name:value}
        """
        self._proxies = proxies
        self._timeout = timeout
        self._retries = retries
        self._payload = payload
        self._cookies = cookies
        self._user_agent = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149'}


    def send_http_request(self, method, url):
        """
        This function handles the https requests and send a post/get message with proxies,timeout and retries
        :param method: string get/post
        :param url: string. the url to send the message to
        :return: requests.models.Response
        """
        try:
            if not url:
                raise Exception("you didn't give an URL")
            if self._retries == 0:
                if not self._proxies:
                    proxy_dict = {}
                else:
                    proxy_dict = Proxy.prepare_proxy_to_requests(proxy=Proxy.get_random_proxy(list_of_proxies=self._proxies))
                try:
                    r = None
                    if method == 'get':
                        r = requests.get(url, timeout=self._timeout, proxies=proxy_dict, headers=self._user_agent)
                    if method == 'post':
                        r = requests.post(url, timeout=self._timeout, proxies=proxy_dict, data=self._payload, cookies=self._cookies, headers=self._user_agent)
                    return r
                except Exception as e:
                    print(e)
            else:
                for i in range(self._retries):
                    if not self._proxies:
                        proxy_dict = {}
                    else:
                        proxy_dict = Proxy.prepare_proxy_to_requests(proxy=Proxy.get_random_proxy(list_of_proxies=self._proxies))
                    try:
                        r = None
                        if method == 'get':
                            r = requests.get(url, timeout=self._timeout, proxies=proxy_dict, headers=self._user_agent)
                        if method == 'post':
                            r = requests.post(url, timeout=self._timeout, proxies=proxy_dict, data=self._payload, cookies=self._cookies, headers=self._user_agent)
                        return r
                    except Exception as e:
                        print(e)
                    time.sleep(0.1)
        except Exception as e:
            print(e)