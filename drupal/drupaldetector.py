import re
import requests
from Utils.httpsrequesthandler import HTTPRequestHandler
from Utils.proxy import Proxy
from bs4 import BeautifulSoup as bs

from platformsdetector import PlatformsDetector

_DRUPAL_DETECTABLE_URL = ["/changelog.txt", "/misc/drupal.js", "/misc/druplicon.png", "/user"]
_DRUPAL_DETECTABLE_FOLDER = ["/core", "/sites"]


class drupalDetector(PlatformsDetector):
    def __init__(self, proxies=None):
        '''
            Keep here the domain and the test state (tested URLs, detected versions, etc) using protected attributes
            :param domain:
            :param proxies: working via HTTP proxies
            '''
        super().__init__(proxies)
        self._domain = ''
        if proxies is None:
            self._proxies = proxies
        else:
            tmp = []
            self._proxies = []
            for proxy in proxies:
                p = Proxy(proxy)
                tmp.append(p)
            self._proxies = tmp
        self._urls = _DRUPAL_DETECTABLE_URL


    def get_platform_name(self):
        return "Drupal"

    def detect(self, domain, retries=0, timeout=5, aggressive=False, urls=None, proxies=None):
        '''
            This function detects if the website on the domain runs over drupal. if it is, it will detect the version
            :param domain: The domain we are checking
            :param retries: The number of tries that each HTTP request will be sent until it will succeed
            :param timeout: How much time each HTTP request will wait for an answer
            :param aggressive: if aggressive is False, the maximal number of HTTP requests is len(urls) + 2
            :param urls: URLs to analyze; make sure the URLs are relevant for the domain
            :param proxies: working via HTTP proxies. If None, the constructor's proxies are used (if any)
            :return: a tuple: (whether the domain operates over Drupal, its version)
            '''
        try:
            self._domain = domain
            if urls is None:
                urls = self._urls
            if proxies is None:
                proxies = self._proxies
            if not aggressive:
                if self.is_drupal(urls=urls, proxies=proxies, timeout=timeout, retries=retries):
                    return ('Drupal',) + (True, self.get_version(timeout=timeout, retries=retries))
            else:
                if self.is_drupal(urls=urls, proxies=proxies, timeout=5, retries=3):
                    return ('Drupal',) + (True, self.get_version(timeout=timeout, retries=retries))
            return ('Drupal',) + (False, 'probably it is not a drupal website')
        except Exception as e:
            return ('Drupal',) + (False, 'probably it is not a drupal website')

    def is_drupal(self, urls=None, proxies=None, timeout=5, retries=0):
        '''
            This function detects if the website runs over drupal
            :param urls: URLs to analyze; make sure the URLs are relevant for the domain
            :param proxies: working via HTTP proxies. If None, the constructor's proxies are used (if any)
            :param timeout: The number of tries that each HTTP request will be sent until it will succeed
            :param retries:  How much time each HTTP request will wait for an answer
            :return: a tuple: (whether the domain operates over Wordpress, its version)
            '''
        url = 'https://' + self._domain
        if not urls:
            http_handler = HTTPRequestHandler(proxies=proxies, retries=retries, timeout=timeout)
            response = http_handler.send_http_request(method='get', url=url)
            if response is None:
                pass
            elif str(response.status_code) != ('200' or '403'):
                return False
            else:
                if "drupal" in str(response.content).lower():
                    return True
                for fold in _DRUPAL_DETECTABLE_FOLDER:
                    if fold in str(response.content).lower():
                        return True
        else:
            http_handler = HTTPRequestHandler(proxies=proxies, retries=retries, timeout=timeout)
            response = http_handler.send_http_request(method='get', url=url)
            if response:
                if self.header_check(response):
                    return True
                if self.resources_detector(response, url):
                    return True
                for u in urls:
                    complete_url = url + u
                    http_handler = HTTPRequestHandler(proxies=proxies, retries=retries, timeout=timeout)
                    response = http_handler.send_http_request(method='get', url=complete_url)
                    if response is None:
                        pass
                    else:
                        if str(response.status_code) != ('200' or '403' or '401'):
                            pass
                        else:
                            if "drupal" in str(response.content).lower():
                                return True
                            for fold in _DRUPAL_DETECTABLE_FOLDER:
                                if fold in str(response.content).lower():
                                    return True
            return False

    def get_version(self, timeout=5, retries=0):
        """
            detects the version of the drupal
            :param timeout:How much time each HTTP request will wait for an answer
            :param retries:The number of tries that each HTTP request will be sent until it will succeed
            :return: string: (return the version of this drupal website)
            """

        url = 'https://' + self._domain
        http_handler = HTTPRequestHandler(proxies=self._proxies, retries=retries, timeout=timeout)
        response = http_handler.send_http_request(method='get', url=url)
        if response.text.__contains__('/sites') or response.text.__contains__('drupal 7'):
            return 'version 7'
        if response.text.__contains__('/core'):
            return 'version 8'
        return "Could'nt detect version"

    def resources_detector(self, response, url):
        """
        This function detects if the domain runs on Drupal by the resources - js or a tag
        :param response:
        :return: Boolean: true/false
        """
        try:
            s = bs(response.content, "html.parser")
            for script in s.find_all("script"):
                if script.attrs.get("data-drupal-selector"):
                    return True
            for a in s.find_all("a"):
                if a.attrs.get("data-drupal-selector"):
                    return True
            return False
        except Exception as e:
            return False

    def header_check(self, response):
        """
        This Function checks which Drupal version is running according to the php version that runs on tje domain
        :param response_headers: Dict. The headers that returned with the HTTP response
        :return: Boolean: true/false
        """
        try:
            res= response.headers.get('X-Generator')
        except Exception as e:
            return False
        if "Drupal" in res:
            return True
        return False
