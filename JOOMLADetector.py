import re

import requests

from WP.https_request_handler import HTTPRequestHandler
from WP.proxy import Proxy

_JOOMLA_DETECTABLE_URLS = ["", "/?option=com_content&view=category&id=1&format=feed",
                           "/?format=feed", "/language/en-GB/en-GB.ini", "/components/com_mailto/mailto.xml",
                           "/components/com_wrapper/wrapper.xml", "/htaccess.txt", "/language/en-GB/en-GB.xml",
                           "/language/en-GB/install.xml", "/templates/protostar/templateDetails.xml",
                           "/web.config.txt"]


class JOOMLADetector(object):

    def __init__(self, domain, proxies=None):
        '''
        Keep here the domain and the test state (tested URLs, detected versions, etc) using protected attributes
        :param domain:
        :param proxies: working via HTTP proxies
        '''
        self._domain = domain
        if proxies is None:
            self._proxies = proxies
        else:
            tmp = []
            self._proxies = []
            for proxy in proxies:
                p = Proxy(proxy)
                tmp.append(p)
            self._proxies = tmp
        self._urls = _JOOMLA_DETECTABLE_URLS

    def detect(self, retries=0, timeout=5, aggressive=False, urls=None, proxies=None):
        '''
        This function detects if the website on the domain runs over joomla. if it is, it will detect the version
        :param aggressive: if aggressive is False, the maximal number of HTTP requests is len(urls) + 2
        :param urls: URLs to analyze; make sure the URLs are relevant for the domain
        :param proxies: working via HTTP proxies. If None, the constructor's proxies are used (if any)
        :param retries: The number of tries that each HTTP request will be sent until it will succeed
        :param timeout: How much time each HTTP request will wait for an answer
        :return: a tuple: (whether the domain operates over JOOMLA!, its version)
        '''
        if urls is None:
            urls = self._urls
        if proxies is None:
            proxies = self._proxies
        if not aggressive:
            if self.is_joomla(urls=urls, proxies=proxies, timeout=timeout, retries=retries):
                return 'True', self.get_version(timeout=timeout, retries=retries)
        else:
            if self.is_joomla(urls=urls, proxies=proxies, retries=3, timeout=5):
                return 'True', self.get_version(timeout=timeout, retries=retries)
        return 'False', 'probably it is not a Joomla! website'

    def is_joomla(self, urls=None, proxies=None, timeout=5, retries=0):
        '''
        This function detects if the website runs over joomla
        :param urls: URLs to analyze; make sure the URLs are relevant for the domain
        :param proxies: working via HTTP proxies. If None, the constructor's proxies are used (if any)
        :param retries: The number of tries that each HTTP request will be sent until it will succeed
        :param timeout: How much time each HTTP request will wait for an answer
        :return: boolean: (whether the domain operates over JOOMLA!)
        '''
        r = requests.get('http://' + str(self._domain))
        url = r.url
        if not urls:
            http_handler = HTTPRequestHandler(proxies=proxies, retries=retries, timeout=timeout)
            response = http_handler.send_http_request(method='get', url=url)
            if response is None:
                pass
            elif str(response.status_code) != ('200' or '403'):
                return False
            else:
                if "joomla!" in str(response.content).lower():
                    return True
        else:
            for u in urls:
                complete_url = url + u
                http_handler = HTTPRequestHandler(proxies=proxies, retries=retries, timeout=timeout)
                response = http_handler.send_http_request(method='get', url=complete_url)
                if response is None:
                    break
                if str(response.status_code) != ('200' or '403' or '401'):
                    break
                else:
                    if "joomla!" in str(response.content).lower():
                        return True
        '''finaly if i cant detect whether it is joomla or not'''
        url = 'http://jornot.com/index.php?check-site=' +str(self._domain)
        http_handler = HTTPRequestHandler(proxies=proxies, retries=retries, timeout=timeout)
        response = http_handler.send_http_request(method='get', url=url)
        if response.text.__contains__('Yes, this is Joomla!'):
            return True
        return False

    def get_version(self, timeout=5, retries=0):
        '''
        detects the version of the JOOMLA!
        :param retries: The number of tries that each HTTP request will be sent until it will succeed
        :param timeout: How much time each HTTP request will wait for an answer
        :return: string: (return the version of this JOMMMLA website)
        '''
        '''fegure out if this site is http or https'''
        r = requests.get('http://' + str(self._domain))
        url = r.url

        '''check source code first'''
        http_handler = HTTPRequestHandler(proxies=self._proxies, retries=retries, timeout=timeout)
        response = http_handler.send_http_request(method='get', url=url)
        if response.text.__contains__('Copyright (C) 2005 - 2008 Open Source Matters') or \
                response.text.__contains__('Copyright (C) 2005 - 2007 Open Source Matters'):
            return '1.0'
        elif response.text.__contains__('Joomla! 1.5 - Open Source Content Management'):
            return '1.5'

        '''check response with - /templates/system/css/system.css'''
        templates_url = url + '/templates/system/css/system.css'
        http_handler = HTTPRequestHandler(proxies=self._proxies, retries=retries, timeout=timeout)
        response = http_handler.send_http_request(method='get', url=templates_url)
        if response.text.__contains__('OpenID icon style') or \
                response.text.__contains__('@copyright Copyright (C) 2005 – 2010 Open Source Matters'):
            return '1.0'
        elif response.text.__contains__('@version $Id: system.css 20196 2011-01-09 02:40:25Z ian $'):
            return '1.6'
        elif response.text.__contains__('@version $Id: system.css 21322 2011-05-11 01:10:29Z dextercowley $'):
            return '1.7'
        elif response.text.__contains__(' @copyright Copyright (C) 2005 – 2012 Open Source Matters'):
            return '2.5'

        '''check response with - /media/system/js/mootools-more.js'''
        mootools_url = url + '/media/system/js/mootools-more.js'
        http_handler = HTTPRequestHandler(proxies=self._proxies, retries=retries, timeout=timeout)
        response = http_handler.send_http_request(method='get', url=mootools_url)
        if response.text.__contains__('MooTools.More={version:”1.3.0.1″'):
            return '1.6'
        elif response.text.__contains__('MooTools.More={version:”1.3.2.1″'):
            return '1.7'

        '''check response with - /language/en-GB/en-GB.ini'''
        language_url = url + '/language/en-GB/en-GB.ini'
        http_handler = HTTPRequestHandler(proxies=self._proxies, retries=retries, timeout=timeout)
        response = http_handler.send_http_request(method='get', url=language_url)
        if response.text.__contains__('# $Id: en-GB.ini 11391 2009-01-04 13:35:50Z ian $'):
            return '1.5.26'
        elif response.text.__contains__('$Id: en-GB.ini 20196 2011-01-09 02:40:25Z ian $'):
            return '1.6.0'
        elif response.text.__contains__('$Id: en-GB.ini 20990 2011-03-18 16:42:30Z infograf768 $'):
            return '1.6.5'
        elif response.text.__contains__('$Id: en-GB.ini 20990 2011-03-18 16:42:30Z infograf768 $'):
            return '1.7.1'
        elif response.text.__contains__('$Id: en-GB.ini 22183 2011-09-30 09:04:32Z infograf768 $'):
            return '1.7.3'
        elif response.text.__contains__('$Id: en-GB.ini 22183 2011-09-30 09:04:32Z infograf768 $'):
            return '1.7.5'

        '''finally check the xml pages of this site'''
        version = ""
        temp = ""
        xml_version = ["/administrator/manifests/files/joomla.xml",
                       "/language/en-GB/en-GB.xml", "/modules/custom.xml"]
        for xml in xml_version:
            complete_url = url + xml
            http_handler = HTTPRequestHandler(proxies=self._proxies, retries=retries, timeout=timeout)
            response = http_handler.send_http_request(method='get', url=complete_url)
            if response is None:
                break
            if str(response.status_code) != ('200' or '403' or '401'):
                break
            else:
                start_res = re.search('<version>', response.text)
                end_res = re.search('</version>', response.text)
                temp = response.text[start_res.end():end_res.start()]
                if version:
                    numbers_of_temp = temp.split('.')
                    numbers_of_version = version.split('.')
                    if numbers_of_temp[2] > numbers_of_version[2]:
                        version = temp
                else:
                    version = temp
        if version:
            return version
        return 'version not found'