import requests
import re
import csv
import os

STEVILO_STRANI = 100
STEVILO_ELEMENTOV_NA_STRAN = 100
MAIN_PAGE_URL = 'https://www.goodreads.com/list/show/1'
DIRECTORY = 'zajeti_podatki'
MAIN_PAGE_FILENAME = 'index.html'
MAIN_DIRECTORY = 'zbrani_podatki'

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

sort_elements_pattern = re.compile(
    r'<tr(.*?)&emsp;',
    flags=re.DOTALL)


main_pattern = re.compile(
    r'class="number">(?P<list_placement>\d+)</td>.*?'
    r'<div id="(?P<id>\d+)".*?'
    r'https://www.goodreads.com/author/show/(?P<author_id>\d+)\..*?'
    r'<span itemprop="name">(?P<author>.+?)</span>.+?'
    r'</span></span> (?P<avg_rating>.+?) avg rating &mdash; (?P<ratings>.+?) ratings.*?'
    r'>score: (?P<list_score>.+?)</a>.*?'
    r'==&#39;.{20}(?P<list_votes>.+?) pe',
    flags=re.DOTALL
)

title_pattern = re.compile(
    r'<h1 id="bookTitle" class="gr-h1 gr-h1--serif" itemprop="name">(?P<title>.+?)</h1>',
    flags=re.DOTALL
)

pages_pattern = re.compile(
    r'<span itemprop="numberOfPages">(?P<pages>\d+)',
    flags=re.DOTALL
)

date_pattern = re.compile(
    r'<div class="row">Published.+?</div>',
    flags=re.DOTALL
)

series_pattern = re.compile(
    r'<div class="infoBoxRowTitle">Series</div>',
    flags=re.DOTALL
)


def url_to_string(url):
    try:
        page_content = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError:
        print('An error has ocurred while downloading the page.')
        return None
    return page_content.text
    


def save_string_to_file(text, filename, directory):
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return None


def save_url_to_file(url, filename, directory):
    text = url_to_string(url)
    if text:
        save_string_to_file(text, filename, directory)
        return True
    else:
        return False


def read_file_to_string(filename, directory):
    path = os.path.join(directory, filename)
    with open(path, encoding='utf8') as f:
        return f.read()


def collect_elements_from_page(page_content):
    return re.findall(sort_elements_pattern, page_content)


def sort_data_from_element(element):              
    result = re.search(main_pattern, element).groupdict()
    result['list_placement'] = int(result['list_placement'])
    result['id'] = int(result['id'])
    result['author_id'] = int(result['author_id'])
    result['avg_rating'] = float(result['avg_rating'])
    result['ratings'] = int(result['ratings'].replace(',', ''))
    result['list_score'] = int(result['list_score'].replace(',', ''))
    result['list_votes'] = int(result['list_votes'].replace(',', ''))
    

    #title = title_pattern.search(html)
    #if title:
    #    result['title'] = title['title']
    #else:
    #    result['title'] = None


    #pages = pages_pattern.search(html)
    #result['pages'] = pages

    #series = series_pattern.search(html)
    #if series:
    #    result['series'] = True
    #else:
    #    result['series'] = False
    

    return result


def sort_data_from_file(filename, directory):
    text = read_file_to_string(filename, directory)
    elements = collect_elements_from_page(text)
    
    return [
        sort_data_from_element(element) for element in elements
    ]


def list_of_dict_to_csv(list_of_dict, fieldnames, filename, directory):
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, 'w', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dict:
            writer.writerow(row)


def main(redownload=True, reparse=True):
    #for page in range(1, STEVILO_STRANI + 1):
    #    save_url_to_file(
    #        f'https://www.goodreads.com/list/show/1?page={page}',
    #        f'list_page-{page}.html',
    #        DIRECTORY
    #        )
    data = []
    for page in range(1, STEVILO_STRANI + 1):
        sorted_data = sort_data_from_file(f'list_page-{page}.html', DIRECTORY)
        data += sorted_data
    
    id_list = [book['id'] for book in data]
    for book_id in id_list:
        save_url_to_file(
            f'https://www.goodreads.com/book/show/{book_id}',
            f'book-{book_id}.html',
            'zbrane_knjige'
            )


    
    #list_of_dict_to_csv(data, ['list_placement', 'id', 'title', 'author_id', 'author', 'avg_rating', 'ratings', 'list_score', 'list_votes', 'pages', 'series'], 'podatki.csv', MAIN_DIRECTORY)
    

    

if __name__ == '__main__':
    main()