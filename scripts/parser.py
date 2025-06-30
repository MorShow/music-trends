from constants import KWORB_CONSTANT, REGIONS, DATE_FROM, DATE_TO

import time
from datetime import datetime

import requests
import pandas as pd

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# TODO: uncomment important blocks of code I don`t need now
# TODO: (maybe) add fancy loggings


class KworbParser:
    def __init__(self, url, regions):
        options = Options()
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-blink-features=AutomationControlled')

        self.service = Service(executable_path='chromedriver.exe')
        self._driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self._url = url
        self._regions = regions

        self.driver.get(self.url)
        print(f"URL: {self.url}")

    @property
    def driver(self):
        return self._driver

    @property
    def url(self):
        return self._url

    @property
    def regions(self):
        return self._regions

    def kworb_skip_ad_and_click_again(self, link=None, time_to_wait=2):
        time.sleep(time_to_wait)
        self.driver.execute_script("""
            document.querySelectorAll('.google-auto-placed, .adsbygoogle, .adsbygoogle-noablate, iframe')
                    .forEach(el => el.remove());
        """)
        time.sleep(time_to_wait)

        if link is not None:
            try:
                link.click()
                print("The ad has been removed and link clicked.")
            except StaleElementReferenceException:
                print("You are already on the target page.")
        return True

    def accept_all_cookies(self):
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'fc-button'))
        )

        accept_all_cookies = self.driver.find_element(By.CLASS_NAME, 'fc-button')
        accept_all_cookies.click()

    def section_go(self, section):
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.LINK_TEXT, section))
        )

        section_link = self.driver.find_element(By.LINK_TEXT, section)
        section_link.click()
        self.kworb_skip_ad_and_click_again(section_link)

    def html_to_dataset(self, additional_columns: dict = None, html=None):
        html = self.driver.page_source if html is None else html
        table = pd.read_html(html)[0]
        if additional_columns is not None:
            for column_name, fill_value in additional_columns.items():
                table[column_name] = fill_value
        return table

    def batch_of_htmls_to_dataset(self,
                                  date_from: datetime,
                                  date_to: datetime,
                                  header_periods=False):  # There is some pattern for the pages containing archive data
        urls = self.driver.find_elements(By.TAG_NAME, 'a')
        table = None
        count = 0
        urls = urls[1:]  # the first element is a backlink to https://kworb.net/... (not the html file)
        index = 0

        # The htmls are placed in chronological order so binary search could be used
        l, r = 0, len(urls)
        while l < r:
            index = (l + r) // 2

            href = urls[index].get_attribute('href')
            date = datetime.strptime(href[href.rfind('/') + 1:href.find('.html')], '%Y%m%d')

            if date < date_from:
                l = index + 1
            else:
                r = index

        for url in urls[index:]:
            href = url.get_attribute('href')
            date = datetime.strptime(href[href.rfind('/') + 1:href.find('.html')], '%Y%m%d')
            if date > date_to:
                break
            if count % 50 == 0:
                print(f'Archive data are being processed now: {href} ({date})')
            html = requests.get(href).text
            new_table = self.html_to_dataset({'DATE': date}, html)
            if header_periods:
                new_table.columns = [f'{i} period(s) ago' for i in range(len(list(new_table.columns)))]
            if table is None:
                table = new_table
            else:
                table = pd.concat([table, new_table], ignore_index=True)
            count += 1

        return table

    def process_button(self,
                       button_text: str,
                       archive_link=False,
                       header_periods=False):
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.LINK_TEXT, button_text))
        )

        button = self.driver.find_element(By.LINK_TEXT, button_text)
        button.click()
        self.kworb_skip_ad_and_click_again(button, 3)

        if not archive_link:
            table = self.html_to_dataset()
        else:
            table = self.batch_of_htmls_to_dataset(DATE_FROM, DATE_TO, header_periods=header_periods)

        return table

    def parse_spotify(self):
        print('---- Start parsing Spotify section ----')
        self.section_go('SPOTIFY')

        table_spotify_charts = self.driver.find_element(By.TAG_NAME, 'table')
        rows_spotify_charts = table_spotify_charts.find_elements(By.TAG_NAME, 'tr')
        rows_spotify_charts = [(row, row.find_element(By.TAG_NAME, 'td').text) for row in rows_spotify_charts
                               if row.find_element(By.TAG_NAME, 'td').text in self.regions]

        for row, region in rows_spotify_charts:
            for index, time_range in [(0, 'daily'), (1, 'weekly')]:
                link = row.find_elements(By.LINK_TEXT, 'Totals')[index]
                self.kworb_skip_ad_and_click_again(link, 2)
                time.sleep(2)
                table = self.html_to_dataset({'Region': region})
                table.to_csv(rf'../data/raw/spotify_charts_{time_range}_{region.lower().replace(" ", "_")}.csv',
                             encoding='utf-8')
                self.driver.back()
                time.sleep(2)

        for block in ['Artists', 'Listeners', 'Top Lists']:
            table = self.process_button(block)
            table.to_csv(rf'../data/raw/spotify_{block.lower().replace(" ", "_")}.csv', encoding='utf-8')

        self.driver.get(self.url)

    def parse_itunes(self):
        print('---- Start parsing iTunes section ----')
        self.section_go('ITUNES')

        cumulative_link = self.driver.find_element(By.LINK_TEXT, 'Cumulative')
        cumulative_link.click()
        self.kworb_skip_ad_and_click_again(cumulative_link)
        itunes_chart_cumulative = self.html_to_dataset()
        itunes_chart_cumulative.to_csv(rf'../data/raw/itunes_cumulative_united_states.csv', encoding='utf-8')
        self.driver.back()

        archives_link = self.driver.find_element(By.LINK_TEXT, 'Archives')
        archives_link.click()
        self.kworb_skip_ad_and_click_again(archives_link)

        table = self.batch_of_htmls_to_dataset(DATE_FROM, DATE_TO, True)
        table.to_csv(rf'../data/raw/itunes_archive_united_states.csv', encoding='utf-8')

        self.driver.get(self.url)

    def parse_worldwide(self):
        print('---- Start parsing Worldwide section ----')
        self.section_go('WORLDWIDE')

        tables = []

        for block in ['Worldwide Songs', 'Worldwide Albums', 'European Songs', 'European Albums']:
            for index in 0, 1:
                button = self.driver.find_elements(By.LINK_TEXT, block)[index]
                button.click()
                self.kworb_skip_ad_and_click_again(button)
                tables.append(self.process_button('Archives', archive_link=True))
                self.driver.back()

        prefix = r'../data/raw/'
        filenames = ['itunes_archive_worldwide_songs.csv', 'apple_music_archive_worldwide_songs.csv',
                     'itunes_archive_worldwide_albums.csv', 'apple_music_archive_worldwide_albums.csv',
                     'itunes_archive_european_songs.csv', 'apple_music_archive_european_songs.csv',
                     'itunes_archive_european_albums.csv', 'apple_music_archive_european_albums.csv']

        for table, filename in zip(tables, filenames):
            table.to_csv(prefix + filename, encoding='utf-8')

        self.driver.get(self.url)

    def radio_string_to_date(self):
        date = self.driver.find_element(By.CLASS_NAME, "pagetitle").text.split('|')[1].strip()
        for sym in ' «»':
            date = date.replace(sym, '')
        return datetime.strptime(date, '%Y/%m/%d')

    def radio_walking(self, button_index):
        buttons = self.driver.find_element(By.CLASS_NAME, "pagetitle").find_elements(By.TAG_NAME, 'a')
        button = buttons[button_index]
        button.click()
        self.kworb_skip_ad_and_click_again(button)
        return self.radio_string_to_date()

    def parse_radio(self, date_from, date_to):
        print('---- Start parsing Radio section ----')
        self.section_go('RADIO')
        date = date_from
        table = None
        url_from = self.url + 'radio/archives/' + date_from.strftime("%Y%m%d") + '.html'

        # The navigation system on the webpage is "great"
        self.driver.get(url_from)
        while date <= date_to:
            new_table = self.html_to_dataset(additional_columns={'Date': date})
            if table is None:
                table = new_table
            else:
                table = pd.concat([table, new_table], ignore_index=True)
            date = self.radio_walking(-1)  # Go to the next day page

        table.to_csv(rf'../data/raw/radio_charts_archive.csv', encoding='utf-8')
        self.driver.get(self.url)

    def parse_youtube(self):
        print('---- Start parsing YouTube section ----')
        self.section_go('YOUTUBE')

        button_top_lists = self.driver.find_element(By.LINK_TEXT, 'Top Lists')
        button_top_lists.click()
        self.kworb_skip_ad_and_click_again(button_top_lists)

        links = self.driver.find_elements(
            By.XPATH,
            '//a[starts-with(@href, "topvideos_published_") and contains(@href, ".html")]'
        )
        index = 0

        while index < len(links):
            link = self.driver.find_elements(
                By.XPATH,
                '//a[starts-with(@href, "topvideos_published_") and contains(@href, ".html")]'
                )[index]

            href = link.get_attribute('href')
            year = href[href.find('20'):href.find('.html')]
            link.click()
            self.kworb_skip_ad_and_click_again(link)
            table = self.html_to_dataset(additional_columns={'Publication year': year})
            table.to_csv(f'../data/raw/youtube_top_music_videos_{year}.csv', encoding='utf-8')
            self.driver.back()
            index += 1

        self.driver.get(self.url)

    def parse_kworb(self):
        print('---- Start parsing Kworb ----')
        self.accept_all_cookies()
        time.sleep(3)
        self.parse_spotify()
        time.sleep(3)
        self.parse_itunes()
        time.sleep(3)
        self.parse_worldwide()
        time.sleep(3)
        self.parse_radio(DATE_FROM, DATE_TO)
        time.sleep(3)
        self.parse_youtube()
        time.sleep(3)
        print('---- Finish parsing ----')
        self.driver.quit()
        self._driver = None
        self.service = None
        self._url = None


if __name__ == '__main__':
    kworb_parser = KworbParser(KWORB_CONSTANT, REGIONS)
    kworb_parser.parse_kworb()
