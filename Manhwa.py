import os
import json
import time
import sqlite3
import threading

from bs4 import BeautifulSoup
import urllib3

MANHWA_BOOKMARK_FOLDER_NAME = 'Manhwa'

APP_DATA = os.getenv('LOCALAPPDATA')
GOOGLE_CHROME_DATA = os.path.join(APP_DATA, 'Google', 'Chrome', 'User Data', 'Default')

CHROME_BOOKMARKS_LOCATION =  os.path.join(GOOGLE_CHROME_DATA, 'Bookmarks')
CHROME_HISTORY_LOCATION = os.path.join(GOOGLE_CHROME_DATA, 'History')

history = []

dynamic_pages = []
dynamic_pages_lock = threading.Lock()

unread_manhwa = []
unread_manhwa_lock = threading.Lock()

http = urllib3.PoolManager(num_pools=100)

def main():
    global history
    history = get_chrome_history()

    if not os.path.isfile(CHROME_BOOKMARKS_LOCATION):
        raise Exception(' Bookmarks File not found!')

    with open(CHROME_BOOKMARKS_LOCATION, 'r', encoding='cp932', errors='ignore') as data_file:
        bookmarks = json.load(data_file)

    process(bookmarks)

def process(bookmarks):
    manhwa_folder = get_manhwa_folder(bookmarks['roots']['bookmark_bar']['children'])
    manhwas_list = get_manhwa_name_and_url(manhwa_folder)
    get_unread_manhwa(manhwas_list)
    print_dynamic_pages()
    print_unread_manhwa()

def get_manhwa_folder(bookmarks_folders):
    for folder in bookmarks_folders:
        if folder['type'] == 'folder' and folder['name'] == MANHWA_BOOKMARK_FOLDER_NAME:
            return folder['children']
    raise Exception(' Manhwa Bookmark folder not found!')

def get_manhwa_name_and_url(manhwa_folder):
    clean_list = []
    for manhwa in manhwa_folder:
        if manhwa['type'] == 'url':
            clean_list.append({ 'name': manhwa['name'], 'url': manhwa['url'] })
    return clean_list

def get_unread_manhwa(manhwa_list):
    global dynamic_pages
    global unread_manhwa

    threads = []
    for i, manhwa in enumerate(manhwa_list):
        thread = threading.Thread(target=append_unread_chapter, args=(i, manhwa,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    dynamic_pages.sort(key=lambda tup:tup[0])
    unread_manhwa.sort(key=lambda tup:tup[0])

def append_unread_chapter(order, manhwa):
    try:
        webpage = get_webpage(manhwa['url'])
    except:
        return append_failed_manhwa(order, manhwa)

    urls = get_urls(webpage)
    chapter_urls = filter_chapter_urls(urls)
    if len(chapter_urls) > 0:
        lastest_chapter = get_latest_chapter(chapter_urls)
        if not lastest_chapter['url'] in history:
            append_unread_manhwa(order, manhwa)
    else:
        append_failed_manhwa(order, manhwa)

def get_webpage(url):
    global http
    page = http.request('GET', url, timeout=60)
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

    latest_chapter_index = 0
    latest_chapter_number = chapters[0]['number']
    for i, chapter in enumerate(chapters):
        if chapter['number'] > latest_chapter_number:
            latest_chapter_number = chapter['number']
            latest_chapter_index = i

    return chapters[latest_chapter_index]

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
        number_index = url.get_text().lower().find('#') + 1
    return number_index

def append_unread_manhwa(order, manhwa):
    global unread_manhwa
    global unread_manhwa_lock
    unread_manhwa_lock.acquire()
    unread_manhwa.append((order, manhwa['name']))
    unread_manhwa_lock.release()

def append_failed_manhwa(order, manhwa):
    global dynamic_pages
    global dynamic_pages_lock
    dynamic_pages_lock.acquire()
    dynamic_pages.append((order, manhwa['name']))
    dynamic_pages_lock.release()

def get_chrome_history():
    if not os.path.isfile(CHROME_HISTORY_LOCATION):
        raise Exception(' History File not found!')

    try:
        con = sqlite3.connect(CHROME_HISTORY_LOCATION)
        c = con.cursor()
        c.execute('select url from urls')
        results = c.fetchall()
        con.close()
    except:
        raise Exception(' Failed to connect to Chrome history DB, Please make sure Chrome is closed!')

    real_results = []
    for result in results:
        real_results.append(result[0])
    return real_results

def print_dynamic_pages():
    print()
    for page in dynamic_pages:
        print(' Failed: ' + page[1])
    print()

def print_unread_manhwa():
    print()
    for i, manhwa in enumerate(unread_manhwa):
        print(' ' + str(i + 1) + ') ' + manhwa[1])
    print()

if __name__ == "__main__":
    start_time = time.time()

    try:
        main()
    except Exception as err:
        print()
        print(err)
        print()

    end_time = time.time()
    time_taken = '{:.2f}'.format(end_time - start_time)
    print(' Finished in ' + time_taken + ' sec')
    input()
