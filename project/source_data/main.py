from project.scrapper.scrapper import Scraper
import requests
import pandas as pd


class DataPrep:
    CONSTANTS = {
        'CVE_URL': "https://cve.mitre.org/data/downloads/allitems.csv",
        'CVE_FILE': "data/cve_data.csv",
        'EXPLOIT_URL': "https://gitlab.com/exploit-database/exploitdb/-/raw/main/files_exploits.csv",
        'EXPLOIT_FILE': "data/exploits.csv",
        'SCRAPPED_DATA_FILE': 'data/segu-info.txt',
        'SCRAPPED_DATA_URL': 'https://blog.segu-info.com.ar/sitemap.xml',
        'DROP_END_ROWS': 7,
        'DROP_STARTING_ROWS': 2
    }

    def __init__(self):
        self.scraper = Scraper(
            url=self.CONSTANTS['SCRAPPED_DATA_URL'],
            output_file=self.CONSTANTS['SCRAPPED_DATA_FILE'])

    def download_and_process_data(self):
        print('start Scrapper')
        # self.scraper.run() esto esta comentado porque lleva mucho tiempo
        print('Downloading CVE')
        self.download_file_from_url(self.CONSTANTS['CVE_URL'], self.CONSTANTS['CVE_FILE'])
        print('start load csv of CVE')
        self.load_and_process_csv(self.CONSTANTS['CVE_FILE'], skip_rows=self.CONSTANTS['DROP_STARTING_ROWS'])
        print('finish load csv CVE')
        print('Downloading exploit DB')
        self.download_file_from_url(self.CONSTANTS['EXPLOIT_URL'], self.CONSTANTS['EXPLOIT_FILE'])
        print('finished Scrapper')


    @staticmethod
    def download_file_from_url(url, file_name):
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(file_name, 'wb') as file:
                    file.write(response.content)
                print(f"File downloaded successfully: {file_name}")
            else:
                print(f"Could not download file. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading file: {e}")

    def load_and_process_csv(self, file_path, skip_rows):
        df = pd.read_csv(file_path, skiprows=skip_rows, encoding='latin-1')
        df = df.drop(index=range(0, self.CONSTANTS['DROP_END_ROWS']))
        df.to_csv(file_path, index=False)
