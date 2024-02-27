import multiprocessing
import random
import re

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import logging
import socks
import socket


def remove_p_with_a(tag):
    return tag.name == 'p' and tag.find('a')


def remove_p_with_span(tag):
    return tag.name == 'p' and tag.find('span')


def extract_elements(div_with_classes, element_name, condition=None):
    elements = div_with_classes.find_all(element_name) if not condition else div_with_classes.find_all(condition)
    for elem in elements:
        elem.extract()


def clean_text(text):
    text = text.replace('\n', '')
    text = re.sub(r'[,|\t]', ' ', text)
    return text


def has_unwanted_elements(element):
    unwanted_tags = ['noscript', 'img', 'script', 'div', 'section', 'span']
    return element.name in unwanted_tags


def clean_p(div_with_classes):
    if any(div_with_classes.find_all(has_unwanted_elements)):
        return clean_text(div_with_classes.get_text(strip=True, separator=' '))

    tags = ['noscript', 'img', 'script', 'div', 'section', 'span']
    extract_elements(div_with_classes, tags)

    extract_elements(div_with_classes, ['p'], remove_p_with_a)
    extract_elements(div_with_classes, ['p'], remove_p_with_span)

    paragraphs = div_with_classes.find_all('p')
    text = ''.join(paragraph.text for paragraph in paragraphs)
    text = clean_text(text)
    return text


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 '
    'Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 '
    'Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110'
    'Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 '
    'Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100'
    'Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 '
    'Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 '
    'Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 '
    'Safari/537.36'
]

PROXI = [
    {'ip': '145.239.85.58', 'port': 9300},
    {'ip': '46.4.96.137', 'port': 1080},
    {'ip': '47.91.88.100', 'port': 1080},
    {'ip': '45.77.56.114', 'port': 30205},
    {'ip': '82.196.11.105', 'port': 1080}

]


def get_random_user_agent():
    """
        Obtiene un User-Agent aleatorio de la lista de User-Agents.
        Returns:
            str: User-Agent aleatorio.
    """
    return random.choice(USER_AGENTS)


class Scraper:
    def __init__(self, output_file, url, request_delay=1):
        """
        constructor de la clase Scraper con las URLs de los sitios a trabajar.

        Args:
            request_delay: tiempo entre peticion
            output_file (str): Nombre del archivo CSV de salida.
            url (str): URL de noticias de seguridad .xml.

        """
        self.security_url = url
        self.output_file = output_file
        self.request_delay = request_delay

        logging.basicConfig(filename='scraper.log', level=logging.INFO,
                            format='%(asctime)s [%(levelname)s]: %(message)s')

    def get_news_urls(self, url):
        try:

            headers = {'User-Agent': get_random_user_agent()}
            response = requests.get(url, headers=headers, stream=True)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                url_list = []
                for url_elem in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
                    loc_elem = url_elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                    if loc_elem is not None:
                        url = loc_elem.text
                        url_list.append(url)
                return url_list
        except Exception as e:
            logging.error(f"Error al obtener URLs de noticias: {e}")
            return []

    def _contains_xml(self, url):
        try:
            headers = {'User-Agent': get_random_user_agent()}
            response = requests.get(url, headers=headers, stream=True)
            if response.status_code == 200:
                response_text = response.text
                if '.xml' in response_text:
                    return True, response_text
                else:
                    return False, None
        except Exception as e:
            logging.error(f"Error al obtener url {e}")
            return None

    @staticmethod
    def _get_link_xml(xml_content):
        root = ET.fromstring(xml_content)
        for sitemap in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"):
            yield sitemap.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text

    def scrape_url(self, url, body='post-body entry-content', category='Seguridad Informatica'):
        try:
            headers = {'User-Agent': get_random_user_agent()}
            response_url = requests.get(url, headers=headers, stream=True)
            if response_url.status_code == 200:
                soup = BeautifulSoup(response_url.text, 'html.parser')

                if category == 'Seguridad Informatica':
                    title = soup.find('h2', class_='post-title entry-title')
                    if title:
                        title = title.text.replace('\n', '').lstrip()
                    else:
                        title = "No title found"
                else:
                    title = soup.h1.text
                    title = title.replace('\n', '').lstrip()
                div_with_classes = soup.find('div', class_=body)
                if div_with_classes:
                    text = clean_p(div_with_classes)
                    _file = open(self.output_file, 'a')
                    _file.write(title + '\n')
                    _file.write(text + '\n')
                    _file.close()
        except Exception as e:
            return self.scrape_url_with_proxy(url, body, category)

    def scrape_url_with_proxy(self, url, body='post-body entry-content', category='Seguridad Informatica'):
        try:
            socks_proxy = PROXI[0]
            print(socks_proxy['ip'], socks_proxy['port'])
            socks.set_default_proxy(socks.SOCKS5, socks_proxy['ip'], socks_proxy['port'])
            socket.socket = socks.socksocket
            headers = {'User-Agent': get_random_user_agent()}
            response_url = requests.get(url, headers=headers, stream=True)
            if response_url.status_code == 200:
                soup = BeautifulSoup(response_url.text, 'html.parser')
                if category == 'Seguridad Informatica':
                    title = soup.find('h2', class_='post-title entry-title')
                    if title:
                        title = title.text.replace('\n', '').lstrip()
                    else:
                        title = "No title found"
                else:
                    title = soup.h1.text
                    title = title.replace('\n', '').lstrip()
                div_with_classes = soup.find('div', class_=body)
                if div_with_classes:
                    text = clean_p(div_with_classes)
                    _file = open(self.output_file, 'a')
                    _file.write(title + '\n')
                    _file.write(text + '\n')
                    _file.close()

        except Exception as e:
            socks_proxy = PROXI[3]
            print(socks_proxy['ip'], socks_proxy['port'])
            socks.set_default_proxy(socks.SOCKS5, socks_proxy['ip'], socks_proxy['port'])
            socket.socket = socks.socksocket
            headers = {'User-Agent': get_random_user_agent()}
            response_url = requests.get(url, headers=headers, stream=True)
            if response_url.status_code == 200:
                soup = BeautifulSoup(response_url.text, 'html.parser')

                if category == 'Seguridad Informatica':
                    title = soup.find('h2', class_='post-title entry-title')
                    if title:
                        title = title.text.replace('\n', '').lstrip()
                    else:
                        title = "No title found"
                else:
                    title = soup.h1.text
                    title = title.replace('\n', '').lstrip()
                div_with_classes = soup.find('div', class_=body)
                if div_with_classes:
                    text = clean_p(div_with_classes)
                    _file = open(self.output_file, 'a')
                    _file.write(title + '\n')
                    _file.write(text + '\n')
                    _file.close()
            logging.error(f"Error al obtener noticias usando proxy: {e}")

    def scrape_security_news(self, site_url):
        security_news_urls = self.get_news_urls(site_url)
        processes = [
            multiprocessing.Process(
                target=self.scrape_url, args=(url, 'post-body entry-content', 'Seguridad Informatica')) for url in
            security_news_urls
        ]
        for process in processes:
            process.start()
        for process in processes:
            process.join()

    def run(self):
        constains_xml, sub_xml = self._contains_xml(self.security_url)
        if constains_xml:
            for link in self._get_link_xml(sub_xml):
                self.scrape_security_news(link)
