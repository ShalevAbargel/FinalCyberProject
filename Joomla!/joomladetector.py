import concurrent.futures
from urllib.parse import urljoin

import requests
import xml.etree.ElementTree as et
from bs4 import BeautifulSoup as bs
from Utils.httpsrequesthandler import HTTPRequestHandler
from Utils.proxy import Proxy
from platformsdetector import PlatformsDetector


class JoomlaDetector(PlatformsDetector):

    def __init__(self, proxies=None):
        """
        Keep here the domain and the test state (tested URLs, detected versions, etc) using protected attributes
        :param proxies: working via HTTP proxies
        """
        super().__init__(proxies)
        self._domain = ""
        if proxies is None:
            self._proxies = proxies
        else:
            tmp = []
            self._proxies = []
            try:
                for proxy in proxies:
                    p = Proxy(proxy)
                    tmp.append(p)
            except Exception as e:
                print(e)
            self._proxies = tmp

    def get_platform_name(self):
        return "Joomla"

    def detect(self, domain, retries=0, timeout=5, aggressive=False, urls=None, proxies=None):
        """
        This function detects if the website on the domain runs over joomla. if it is, it will detect the version
        :param domain: the domain we want to check
        :param aggressive: if aggressive is False, the maximal number of HTTP requests is len(urls) + 2
        :param urls: URLs to analyze; make sure the URLs are relevant for the domain
        :param proxies: working via HTTP proxies. If None, the constructor's proxies are used (if any)
        :param retries: The number of tries that each HTTP request will be sent until it will succeed
        :param timeout: How much time each HTTP request will wait for an answer
        :return: a tuple: (whether the domain operates over JOOMLA!, its version)
        """
        try:
            self._domain = domain
            if proxies is None:
                proxies = self._proxies
            if not aggressive:
                if self.is_joomla(proxies=proxies, timeout=timeout, retries=retries):
                    return 'Joomla', True, self.get_version(timeout=timeout, retries=retries)
            else:
                if self.is_joomla(proxies=proxies, retries=3, timeout=5):
                    return 'Joomla', True, self.get_version(timeout=timeout, retries=retries)
            return 'Joomla', False, 'probably it is not a Joomla! website'
        except Exception as e:
            print(e)

    def set_domain(self, domain):
        self._domain = domain

    def is_joomla(self, urls=None, proxies=None, timeout=5, retries=0):
        """
        This function detects if the website runs over joomla
        :param urls: URLs to analyze; make sure the URLs are relevant for the domain
        :param proxies: working via HTTP proxies. If None, the constructor's proxies are used (if any)
        :param retries: The number of tries that each HTTP request will be sent until it will succeed
        :param timeout: How much time each HTTP request will wait for an answer
        :return: boolean: (whether the domain operates over JOOMLA!)
        """
        try:
            r = HTTPRequestHandler().send_http_request(method='get', url='http://' + str(self._domain))
            url = r.url
            functions = [self.css_jss_detector, self.directory_detector,
                         self.strings_detector, self.template_details_xml_detector]
            optional_results = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_func = {executor.submit(func, url): func for func in functions}
                for future in concurrent.futures.as_completed(future_to_func):
                    optional_results.append(future.result())
            if True in optional_results:
                return True
            return False
        except Exception as e:
            print(e)

    def get_version(self, timeout=5, retries=0):
        """
        detects the version of the JOOMLA!
        :param retries: The number of tries that each HTTP request will be sent until it will succeed
        :param timeout: How much time each HTTP request will wait for an answer
        :return: string: (return the version of this JOMMMLA website)
        """
        try:
            '''figure out if this site is http or https'''
            r = HTTPRequestHandler().send_http_request(method='get', url='http://' + str(self._domain))
            url = r.url
            version =[]
            '''check source code first'''
            response = r.text
            if 'Copyright (C) 2005 - 2008 Open Source Matters' in response or \
                    'Copyright (C) 2005 - 2007 Open Source Matters' in response:
                version.append('1.0')
            elif 'Joomla! 1.5 - Open Source Content Management' in response:
                version.append('1.5')

            '''check response with - /templates/system/css/system.css'''
            try:
                templates_url = url + '/templates/system/css/system.css'
                http_handler = HTTPRequestHandler(proxies=self._proxies, retries=retries, timeout=timeout)
                response = http_handler.send_http_request(method='get', url=templates_url).text
                if 'OpenID icon style' in response or \
                        '@copyright Copyright (C) 2005 – 2010 Open Source Matters' in response:
                    version.append('1.0')
                elif '@version $Id: system.css 20196 2011-01-09 02:40:25Z ian $' in response:
                    version.append('1.6')
                elif '@version $Id: system.css 21322 2011-05-11 01:10:29Z dextercowley $' in response:
                    version.append('1.7')
                elif ' @copyright Copyright (C) 2005 – 2012 Open Source Matters' in response:
                    version.append('2.5')
            except Exception as e:
                print(e)

            '''check response with - /media/system/js/mootools-more.js'''
            try:
                mootools_url = url + '/media/system/js/mootools-more.js'
                http_handler = HTTPRequestHandler(proxies=self._proxies, retries=retries, timeout=timeout)
                response = http_handler.send_http_request(method='get', url=mootools_url).text
                if 'MooTools.More={version:”1.3.0.1″' in response:
                    version.append('1.6')
                elif 'MooTools.More={version:”1.3.2.1″' in response:
                    version.append('1.7')
            except Exception as e:
                print(e)

            '''check response with - /language/en-GB/en-GB.ini'''
            try:
                language_url = url + '/language/en-GB/en-GB.ini'
                http_handler = HTTPRequestHandler(proxies=self._proxies, retries=retries, timeout=timeout)
                response = http_handler.send_http_request(method='get', url=language_url).text
                if '# $Id: en-GB.ini 11391 2009-01-04 13:35:50Z ian $' in response:
                    version.append('1.5.26')
                elif '$Id: en-GB.ini 20196 2011-01-09 02:40:25Z ian $' in response:
                    version.append('1.6.0')
                elif '$Id: en-GB.ini 20990 2011-03-18 16:42:30Z infograf768 $' in response:
                    version.append('1.6.5')
                elif '$Id: en-GB.ini 20990 2011-03-18 16:42:30Z infograf768 $' in response:
                    version.append('1.7.1')
                elif '$Id: en-GB.ini 22183 2011-09-30 09:04:32Z infograf768 $' in response:
                    version.append('1.7.3')
                elif '$Id: en-GB.ini 22183 2011-09-30 09:04:32Z infograf768 $' in response:
                    version.append('1.7.5')
            except Exception as e:
                print(e)

            '''finally check the xml pages of this site'''
            xml_version = ["/administrator/manifests/files/joomla.xml",
                           "/language/en-GB/en-GB.xml", "/modules/custom.xml",
                           '/components/com_mailto/mailto.xml',
                           '/components/com_wrapper/wrapper.xml',
                           '/language/en-GB/install.xml']
            for x in xml_version:
                complete_url = url + x
                try:
                    http_handler = HTTPRequestHandler(proxies=self._proxies, retries=retries, timeout=timeout)
                    r = http_handler.send_http_request(method='get', url=complete_url)
                    root = et.fromstring(r.text)
                    for child in root.iter('version'):
                        version.append(child.text)
                except Exception as e:
                    print(e)
                    continue
            if not version:
                try:
                    r = requests.get(url + '/README.txt')
                    line = r.text.splitlines()
                    if 'version history - https://docs.joomla.org/' in line[3]:
                        start = line[3].find('Joomla!')
                        end = line[3].find('version')
                        start += len('joomla')
                        version.append(line[3][start+1:end-1])
                except Exception as e:
                    print(e)
            try:
                final_version = max(version)
            except Exception as e:
                print(e)
                return 'version not found'
            return final_version
        except Exception as e:
            print(e)
            return 'version not found'

    # all detectors functions
    def directory_detector(self, url):
        try:
            count = 0
            directories = ['/administrator/', '/cache/', '/components/', '/includes/',
                           '/installation/', '/language/', '/libraries/', '/logs/', '/media/', '/modules/',
                           '/plugins/', '/templates/', '/tmp/']
            administrator_str = '<meta name="generator" content="Joomla! - Open Source Content Management" />'
            for directory in directories:
                full_url = url + directory
                try:
                    r = HTTPRequestHandler().send_http_request(method='get', url=full_url)
                    if directory == '/administrator/' and r.ok and r.url == full_url:
                        joomla_count = r.text.lower().count('joomla')
                        if joomla_count >= 6:
                            if administrator_str.replace(' ', '') in r.text.replace(' ', ''):
                                count += 4
                            elif r.text == '<!DOCTYPE html><title></title>\n':
                                count += 2
                    elif r.ok and r.text == '<!DOCTYPE html><title></title>\n' and r.url == full_url:
                        count += 1
                except Exception as e:
                    print(e)
            if count >= 6:
                return True
            return False
        except Exception as e:
            print(e)
            return False

    def template_details_xml_detector(self, url):
        try:
            url = url + '/templates/protostar/templateDetails.xml'
            r = HTTPRequestHandler().send_http_request(method='get', url=url)
            # get all files from /templates/protostar/templateDetails.xml
            template_folder = ['css', 'html', 'images', 'img', 'js', 'language', 'less']
            folders_in_xml = []
            if str(r.status_code) == '200':
                root = et.fromstring(r.text)
                for child in root.iter('folder'):
                    folders_in_xml.append(child.text)
            if folders_in_xml == template_folder:
                return True
            return False
        except Exception as e:
            print(e)
            return False

    def robots_txt_detector(self, url):
        try:
            url = url + '/robots.txt'
            r = HTTPRequestHandler().send_http_request(method='get', url=url)
            templates = ["User-agent: *",
                         "Disallow: /administrator/",
                         "Disallow: /bin/",
                         "Disallow: /cache/",
                         "Disallow: /cli/",
                         "Disallow: /components/",
                         "Disallow: /includes/",
                         "Disallow: /installation/",
                         "Disallow: /language/",
                         "Disallow: /layouts/",
                         "Disallow: /libraries/",
                         "Disallow: /logs/",
                         "Disallow: /modules/",
                         "Disallow: /plugins/",
                         "Disallow: /tmp/"]
            if all(x in r.text for x in templates):
                return True
            return False
        except Exception as e:
            print(e)
            return False

    def css_jss_detector(self, url):
        try:
            # get the HTML content
            html = requests.get(url, timeout=10).content
            # parse HTML using beautiful soup
            soup = bs(html, "html.parser")
            # get the JavaScript files
            script_files = []
            css_files = []
            count = 0
            for script in soup.find_all("script"):
                if script.attrs.get("src"):
                    # if the tag has the attribute 'src'
                    script_url = urljoin(url, script.attrs.get("src"))
                    script_files.append(script_url)
                    if '/media/' in script_url:
                        count += 1
                        break
            for css in soup.find_all("link"):
                if css.attrs.get("href"):
                    # if the link tag has the 'href' attribute
                    css_url = urljoin(url, css.attrs.get("href"))
                    css_files.append(css_url)
                    # print(css_url)
                    if '/templates/' in css_url:
                        count += 1
                        break
            if count == 2:
                return True
            return False
        except Exception as e:
            print(e)
            return False

    def xml_parser(self, url):
        try:
            xml = []
            r = HTTPRequestHandler().send_http_request(method='get', url=url)
            root = et.fromstring(r.text)
            for child in root.iter('author'):
                xml.append(child.text)
            for child in root.iter('authorEmail'):
                xml.append(child.text)
            for child in root.iter('authorUrl'):
                xml.append(child.text)
            strings = ['Joomla! Project', 'admin@joomla.org', 'www.joomla.org']
            if xml == strings:
                return True
            return False
        except Exception as e:
            print(e)
            return False

    def malito_xml_detector(self, url):
        try:
            url = url + '/components/com_mailto/mailto.xml'
            return self.xml_parser(url)
        except Exception as e:
            print(e)

    def wrapper_xml_detector(self, url):
        try:
            url = url + '/components/com_wrapper/wrapper.xml'
            return self.xml_parser(url)
        except Exception as e:
            print(e)

    def language_install_xml_detector(self, url):
        try:
            url = url + '/language/en-GB/install.xml'
            return self.xml_parser(url)
        except Exception as e:
            print(e)

    def language_xml_detector(self, url):
        try:
            url = url + '/language/en-GB/en-GB.xml'
            return self.xml_parser(url)
        except Exception as e:
            print(e)

    def index_php_detector(self, url):
        try:
            url = url + '/index.php'
            strings = ['<meta name="generator" content="Joomla! - Open Source Content Management" />',
                       '<meta name="Generator" content="Joomla! - Copyright (C) 2005 - 2008 Open Source Matters.']
            r = HTTPRequestHandler().send_http_request(method='get', url=url)
            source = r.text.replace(' ', '')
            for s in strings:
                if s.replace(' ', '') in source:
                    return True
            return False
        except Exception as e:
            print(e)
            return False

    def source_code_and_format_equal_feed_detector(self, url):
        try:
            urls = ['', '/?option=com_content&view=category&id=1&format=feed',
                    '/?format=feed']
            strings = ['<!-- generator="Joomla! 1.5 - Open Source Content Management" -->',
                       '<generator>Joomla! 1.5 - Open Source Content Management</generator>',
                       '<meta name="Generator" content="Joomla! - Copyright (C) 2005 - 2008 Open Source Matters.',
                       '<generator>Joomla! - Open Source Content Management</generator>',
                       '<!-- generator="Joomla! - Open Source Content Management" -->',
                       '<meta name="generator" content="Joomla! - Open Source Content Management" />',
                       '<meta name="generator" content="Joomla! 1.5 - Open Source Content Management"/>']
            solution = []
            for u in urls:
                u = url + u
                try:
                    r = HTTPRequestHandler().send_http_request(method='get', url=u)
                    source = r.text.replace(' ', '')
                    for s in strings:
                        if s.replace(' ', '') in source:
                            solution.append(True)
                            break
                except Exception as e:
                    print(e)
            if len(solution) >= 2:
                return True
            return False
        except Exception as e:
            print(e)

    def strings_detector(self, url):
        try:
            functions = [self.source_code_and_format_equal_feed_detector,
                         self.index_php_detector, self.language_xml_detector,
                         self.language_install_xml_detector, self.wrapper_xml_detector,
                         self.malito_xml_detector, self.robots_txt_detector]
            optional_results = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_func = {executor.submit(func, url): func for func in functions}
                for future in concurrent.futures.as_completed(future_to_func):
                    optional_results.append(future.result())
            sum_of_true = sum(bool(x) for x in optional_results)
            if sum_of_true > 3:
                return True
            return False
        except Exception as e:
            print(e)
