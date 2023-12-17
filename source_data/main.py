from scrapper.scrapper import Scraper
import requests
import pandas as pd


class DataPrep:
    CONSTANTS = {
        'CVE_URL': "https://cve.mitre.org/data/downloads/allitems.csv",
        'CVE_FILE': "data/cve_data.csv",
        'EXPLOIT_URL': "https://gitlab.com/exploit-database/exploitdb/-/raw/main/files_exploits.csv",
        'EXPLOIT_FILE': "data/exploits.csv",
        'SCRAPPED_DATA_FILE': 'data/segu-info.csv',
        'SCRAPPED_DATA_URL': 'https://blog.segu-info.com.ar/sitemap.xml',
        'DROP_END_ROWS': 7,
        'DROP_STARTING_ROWS': 2
    }

    def __init__(self):
        self.scraper = Scraper(url=self.CONSTANTS['SCRAPPED_DATA_URL'],
                               output_file=self.CONSTANTS['SCRAPPED_DATA_FILE'])

    def download_and_process_data(self):
        self.scraper.run()
        self.download_file_from_url(self.CONSTANTS['CVE_URL'], self.CONSTANTS['CVE_FILE'])
        self.load_and_process_csv(self.CONSTANTS['CVE_FILE'], skip_rows=self.CONSTANTS['DROP_STARTING_ROWS'])
        self.download_file_from_url(self.CONSTANTS['EXPLOIT_URL'], self.CONSTANTS['EXPLOIT_FILE'])

    @staticmethod
    def download_file_from_url(url, file_name):
        response = requests.get(url)
        if response.status_code == 200:
            DataPrep.write_content_to_file(file_name, response.content)
        else:
            print(f"Could not download file. Status code: {response.status_code}")

    @staticmethod
    def write_content_to_file(file_name, content):
        with open(file_name, 'wb') as file:
            file.write(content)
        print(f"File downloaded as {file_name}")

    def load_and_process_csv(self, file_path, skip_rows):
        df = pd.read_csv(file_path, skiprows=skip_rows, encoding='latin-1')
        df = df.drop(index=range(0, self.CONSTANTS['DROP_END_ROWS']))
        df.to_csv(file_path, index=False)
