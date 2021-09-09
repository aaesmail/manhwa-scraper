import os
import json
import time
import sqlite3

from bs4 import BeautifulSoup
import urllib3

CHROME_BOOKMARKS_LOCATION = 'C:\\Users\\user\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Bookmarks'
CHROME_HISTORY_LOCATION = 'C:\\Users\\user\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History'

history = []

def main():
    global history
    history = get_chrome_history()

    if not os.path.isfile(CHROME_BOOKMARKS_LOCATION):
        raise('Bookmarks File not found!')

    with open(CHROME_BOOKMARKS_LOCATION, 'r', encoding='cp932', errors='ignore') as data_file:
        bookmarks = json.load(data_file)

    process(bookmarks)

def process(bookmarks):
    manhwa_folder = get_manhwa_folder(bookmarks['roots']['bookmark_bar']['children'])
    manhwas_list = get_manhwa_name_and_url(manhwa_folder)
    unread_manhwa_list = get_unread_manhwa(manhwas_list)
    print_unread_manhwa(unread_manhwa_list)

def get_manhwa_folder(bookmarks_folders):
    for folder in bookmarks_folders:
        if folder['type'] == 'folder' and folder['name'] == 'Manhwa':
            return folder['children']
    raise Exception('Manhwa Bookmark folder not found!')

def get_manhwa_name_and_url(manhwa_folder):
    clean_list = []
    for manhwa in manhwa_folder:
        if manhwa['type'] == 'url':
            clean_list.append({ 'name': manhwa['name'], 'url': manhwa['url'] })
    return clean_list

def get_unread_manhwa(manhwa_list):
    unread_manhwa = []
    for manhwa in manhwa_list:
        webpage = get_webpage(manhwa['url'])
        urls = get_urls(webpage)
        chapter_urls = filter_chapter_urls(urls)
        if len(chapter_urls) > 0:
            lastest_chapter = get_latest_chapter(chapter_urls)
            if not lastest_chapter['url'] in history:
                unread_manhwa.append(manhwa['name'])
        else:
            print(' Dynamically rendered page: ' + manhwa['name'])
    return unread_manhwa

def get_webpage(url):
    page = urllib3.PoolManager().request('GET', url)
    return BeautifulSoup(page.data, 'html.parser')

def get_urls(webpage):
    content = webpage.select('div.main-col a')

    if len(content) > 0:
        return content
    else:
        return webpage.select('body a')

def filter_chapter_urls(urls):
    chapter_urls = []
    for url in urls:
        if url.get_text().lower().find('chapter') >= 0 or url.get_text().lower().find('ep.') >= 0:
            chapter_urls.append(url)
    return chapter_urls

def get_latest_chapter(chapters_urls):
    chapters = []
    for chapter_url in chapters_urls:
        chapter_number = get_chapter_number(chapter_url)
        chapters.append({ 'number': chapter_number, 'url': chapter_url['href'] })
    chapters = sorted(chapters, key=lambda item: item['number'])

    return chapters[len(chapters) - 1]

def get_chapter_number(chapter_url):
    number_index = get_number_starting_position(chapter_url)
    number_string = '0'
    chapter_url_string = chapter_url.get_text()
    
    while True:
        if number_index >= len(chapter_url_string):
            break
        if chapter_url_string[number_index] < '0' or chapter_url_string[number_index] > '9':
            break
        number_string += chapter_url_string[number_index]
        number_index += 1

    return int(number_string)

def get_number_starting_position(url):
    chapter_index = url.get_text().lower().find('chapter')
    ep_index = url.get_text().lower().find('ep.')
    number_index = -1
    if chapter_index >= 0:
        number_index = chapter_index + 8
    elif ep_index >= 0:
        number_index = ep_index + 4
    return number_index

def get_chrome_history():
    if not os.path.isfile(CHROME_HISTORY_LOCATION):
        raise('History File not found!')
    con = sqlite3.connect(CHROME_HISTORY_LOCATION)
    c = con.cursor()
    c.execute('select url from urls')
    results = c.fetchall()
    con.close()
    real_results = []
    for result in results:
        real_results.append(result[0])
    return real_results

def print_unread_manhwa(unread_manhwa_list):
    print()
    for i, manhwa in enumerate(unread_manhwa_list):
        print(' ' + str(i + 1) + ') ' + manhwa)
    print()

if __name__ == "__main__":
    start_time = time.time()
    print()
    main()
    end_time = time.time()
    time_taken = '{:.2f}'.format(end_time - start_time)
    print(' Finished in ' + time_taken + ' sec')
    input()
