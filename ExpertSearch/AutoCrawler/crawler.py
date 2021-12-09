import os
from bs4 import BeautifulSoup
from constants import *
import requests
import re
from urlparse import urlsplit


LAST_KNOWN_BIO_INDEX = 6525


class Crawler:
    data_type_url_mappings = {
        DATA_TYPE_TRAINING: {
            "input": [],
            "output": TRAIN_DATASET_FILE
        },
        DATA_TYPE_TESTING: {
            "input": [],
            "output": TEST_DATASET_FILE
        },
        DATA_TYPE_BIO_TRAINING: {
            "input": [],
            "output": TRAIN_BIO_DATASET_FILE
        },
        DATA_TYPE_BIO_TESTING: {
            "input": [],
            "output": TEST_BIO_DATASET_FILE
        }
    }

    urls_file = None
    data_type = None

    def __init__(self, data_type=DATA_TYPE_TRAINING):
        self.data_type = data_type
        if data_type == DATA_TYPE_TRAINING:
            self.urls_file = TRAIN_URLS_FILE
        elif data_type == DATA_TYPE_TESTING:
            self.urls_file = TEST_URLS_FILE
        elif data_type == DATA_TYPE_BIO_TRAINING:
            self.urls_file = TRAIN_BIO_URLS_FILE
        elif data_type == DATA_TYPE_BIO_TESTING:
            self.urls_file = TEST_BIO_URLS_FILE

        with open(self.urls_file, 'r') as f:
            urls = f.readlines()
            self.data_type_url_mappings[self.data_type]["input"] = urls

    def get_js_soup(self, url):
        resp = None
        try:
            resp = requests.get(url, timeout=5)
        except Exception:
            scheme = url.split('://')[0]
            if scheme not in ['http', 'https']:
                try:
                    print '-' * 5, 'Crawling url : ', 'http://' + url, '-' * 5
                    resp = requests.get('http://' + url, timeout=5)
                except Exception:
                    try:
                        print '-' * 5, 'Crawling url : ', 'https://' + url, '-' * 5
                        resp = requests.get('https://' + url, timeout=5)
                    except Exception:
                        try:
                            print '-' * 5, 'Crawling url : ', 'www.' + url, '-' * 5
                            resp = requests.get('www.' + url, timeout=5)
                        except Exception:
                            print '-' * 5, 'Returning none for url : ', url, '-' * 5
                            return None
            else:
                print '-' * 5, 'Returning none for url : ', url, '-' * 5
                return None

        if resp == None:
            return None

        try:
            soup = BeautifulSoup(resp.text, 'html.parser')
            return soup
        except Exception as e:
            print "Exception in getting soup - ", str(e)

        return None

    def remove_script(self, soup):
        for script in soup(['script', 'style']):
            script.decompose()
        return soup

    def get_url_text(self, url):
        print '-' * 5, 'Crawling url : ', url, '-' * 5
        soup = self.get_js_soup(url)
        # soup = self.remove_script(soup)
        if not soup:
            return ""
        return soup.get_text(strip=True)

    def clean_up_url_content(self, data):
        data_string = self.convert_string_to_ascii(data)
        data_string = re.sub(' +', ' ', data_string)
        data_string = data_string.replace('\n', ' ').replace('\r', ' ').replace('\r\n', ' ')
        if re.findall("403 Forbidden", data_string) or \
                re.findall("404 Component not found", data_string) or \
                re.findall("404 Not Found", data_string) or \
                not data_string:
            data_string = ERROR_CONTENT
        return data_string

    def convert_string_to_ascii(self, input_string):
        output_string = input_string
        try:
            output_string = "".join(c for c in input_string if ord(c) < 128)
            if output_string != input_string:
                print ""
        except Exception:
            print ""

        return output_string

    def create_output_file(self):
        output_file = self.data_type_url_mappings[self.data_type]["output"]
        open(output_file, 'w').close()

    def extract_url_contents(self, start_idx=0, end_idx=None):

        input_urls = self.data_type_url_mappings[self.data_type]["input"]
        if end_idx is None:
            end_idx = len(input_urls)
        # for url in input_urls:
        for i in range(start_idx, end_idx):
            url = input_urls[i]
            if self.data_type == DATA_TYPE_TRAINING or self.data_type == DATA_TYPE_BIO_TRAINING:
                line_parts = url.split('\t')
                tag = line_parts[0]
                url = line_parts[1]
            url = url.strip()
            data = self.get_url_text(url)
            data_string = self.clean_up_url_content(data)
            if self.data_type == DATA_TYPE_TRAINING or self.data_type == DATA_TYPE_BIO_TRAINING:
                data_string = tag + '\t' + data_string

            output_file = self.data_type_url_mappings[self.data_type]["output"]
            with open(output_file, 'a') as f:
                f.write(data_string.encode('utf-8'))
                f.write('\n')
                print ">> URL content saved for : ", url

    def get_links_from_url(self, url):
        print '-' * 5, 'Crawling url : ', url, '-' * 5
        soup = self.get_js_soup(url)

        if not soup:
            return ""
        links = set([])
        for link in soup.find_all('a'):
            href_url = link.get('href')
            href_text = ""
            if link.text.strip() is not None:
                href_text = link.text.strip()
            if self.is_potential_faculty_url(href_url, href_text):
                if href_url.startswith('/'):
                    href_url = self.get_base_url(url) + href_url
                elif href_url.startswith('?'):
                    href_url = url + href_url
                if self.is_valid_homepage(href_url, url):
                    links.add(href_url)
        return links

    def is_potential_faculty_url(self, url, anchor_text):
        is_potential_candidate = False
        if not url:
            return is_potential_candidate

        if url.startswith('/') or url.startswith('?') or url.startswith('http'):
            if not (re.findall('student', url.lower()) and re.findall('student', anchor_text.lower())) \
                    and (re.findall('faculty', url.lower()) or re.findall('faculty', anchor_text.lower())
                    or re.findall('staff', url.lower()) or re.findall('staff', anchor_text.lower())
                    or re.findall('people', url.lower()) or re.findall('people', anchor_text.lower())
                    or re.findall('personnel', url.lower()) or re.findall('personnel', anchor_text.lower())
                    or re.findall('profile', url.lower()) or re.findall('profile', anchor_text.lower())):
                is_potential_candidate = True
        return is_potential_candidate

    def get_base_url(self, url):
        base_url = ''
        parts = urlsplit(url)
        if parts[0] and parts[1]:
            base_url = parts[0] + '://' + parts[1]
        elif parts[2]:
            base_url = parts[2]
        return base_url

    def is_valid_homepage(self, bio_url, dir_url):
        if bio_url.endswith('.pdf'):
            return False
        urls = [re.sub('((http?://) | (www.))', '', url) for url in [bio_url, dir_url]]
        return not (urls[0] == urls[1])

    def crawl_faculty_pages_for_bio(self):
        print "Crawling faculty pages for bio ..."

        this_file_dir = os.path.dirname(os.path.abspath(__file__))
        with open(CLASSIFIED_FACULTY_URLS_FILE, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                faculty_url = line.strip()
                print "Crawling faculty url {} for bio ...".format(faculty_url)
                bio = self.extract_bio(faculty_url)
                new_bio_file_name = str(LAST_KNOWN_BIO_INDEX + i) + '.txt'
                new_bio_file = os.path.join(os.path.dirname(this_file_dir), 'data/compiled_bios', new_bio_file_name)
                open(new_bio_file, 'w').close()
                with open(new_bio_file, 'w') as f:
                    f.write(bio.strip())
                    f.write('\n')

    def extract_bio(self, bio_url):
        bio = ""
        soup = self.get_js_soup(bio_url)
        if soup:
            bio = soup.get_text()
            bio = self.process_bio(bio)
        return bio

    def process_bio(self, bio):
        bio = bio.encode('ascii', errors='ignore').decode('utf-8')
        bio = re.sub('\s+', ' ', bio)
        return bio

    def add_classified_fac_url_to_urls(self):
        print "Adding classified faculty urls to the data/urls file ..."

        this_file_dir = os.path.dirname(os.path.abspath(__file__))
        urls_file_path = os.path.join(os.path.dirname(this_file_dir), 'data', 'urls')
        with open(urls_file_path, 'a') as fo:
            with open(CLASSIFIED_FACULTY_URLS_FILE, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    faculty_url = line.strip()
                    fo.write(faculty_url)
                    fo.write('\n')

        print "Adding classified faculty urls to the data/urls file complete"
