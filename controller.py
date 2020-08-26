import datetime
# noinspection PyUnresolvedReferences
from xml.dom import minidom

from drupal.drupaldetector import drupalDetector
from joomla.joomladetector import JoomlaDetector
from mydb import MyDB
from squarespace.squarespacedetector import SquarspaceDetector
from wordpress.wpdetector import WPDetector
from model import Model


class Controller(object):

    def __init__(self):
        wordpress_detector = WPDetector()
        joomla_detector = JoomlaDetector()
        squarespace_detector = SquarspaceDetector()
        drupal_detector = drupalDetector()
        detectors = [wordpress_detector, joomla_detector, squarespace_detector, drupal_detector]
        self._mydb = MyDB()
        self._mydb.connect()
        self._model = Model(detectors)

    def read_xml(self, xml_file_path):
        """
        :param xml_file_path: xml file with relevant data
        :return:list. record from db: platform,domain,version and date of last detection.
        """
        try:
            mydoc = minidom.parse(xml_file_path)
            items = mydoc.getElementsByTagName('item')
            formdata = {}
            for item in items:
                formdata[item.attributes['name'].value] = item.firstChild.data
            domain = formdata.get("domain")
            cache = formdata['usecache']
            return self.check_platform(domain, cache)
        except Exception as e:
            print(e)

    def check_platform(self, domain, cache, platform=None):
        """
        :param platform:string. the user know platform is the website, he looks for the version.
        :param cache: boolean. weather user want to use cache or not.
        :param domain: string. the domain that the user want to check.
        if user want record from cache then check if it exist in db
        if exist then check if the last date is relevant
        else run check_platform method in model
        :return:string. record(line) from db.
        """
        try:
            # user don't want record from db at all
            if not cache:
                if len(self._mydb.select(domain)) > 0:
                    self._mydb.delete(domain)
                if platform is None:
                    sol = self._model.check_platform(domain)
                else:
                    sol = self._model.check_platform(domain, platform)
                if not sol[0]:
                    return sol[1]
                else:
                    self._mydb.insert_data(domain=domain, platform=sol[0], version=sol[1])
                    return self._mydb.select(domain)
            # user want record from db
            else:
                record = self._mydb.select(domain)
                # record not found, run this method again with no cache-check
                if not record:
                    cache = False
                    if platform is None:
                        return self.check_platform(domain, cache)
                    else:
                        return self.check_platform(domain, cache, platform)
                # record found
                else:
                    # if date is relevant(last check less then 6 month)
                    if self._check_date(domain, record):
                        return record
                    # date is not relevant, run this method again with no cache-check
                    else:
                        cache = False
                        if platform is None:
                            return self.check_platform(domain, cache)
                        else:
                            return self.check_platform(domain, cache, platform)
        except Exception as e:
            print(e)

    def _check_date(self, domain, record):
        """
        :param domain:string. the domain of the specific record.
        :param record:tuple. record for specific domain from db.
        :return: boolean. true if the date is relevant(less then 6 month from last check)
                           or false if it is not relevant
        """
        try:
            today = str(datetime.date.today()).split("-")
            today_year = today[0]
            today_month = today[1]
            date = str(record[0][3]).split(" ")
            date_t = date[0].split("-")
            year = date_t[0]
            month = date_t[1]
            if int(year) < int(today_year):
                self._mydb.delete(domain)
                return False
            elif int(year) == int(today_year):
                if int(today_month) > int(month) + 6:
                    self._mydb.delete(domain)
                    return False
            return True
        except Exception as e:
            print(e)
