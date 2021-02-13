import requests
import re
import csv
import os
import time

STEVILO_STRANI = 10
STEVILO_ELEMENTOV_NA_STRAN = 100
MAIN_PAGE_URL = 'https://www.goodreads.com/list/show/1'
PAGE_DIRECTORY = 'zajeti_podatki'
BOOK_DIRECTORY = 'zbrane_knjige'
MAIN_DIRECTORY = 'zbrani_podatki'


headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36 Edg/86.0.622.63'}


sort_elements_pattern = re.compile(
    r'<tr(.*?)&emsp;',
    flags=re.DOTALL
)

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
    r'<h1 id="bookTitle" class="gr-h1 gr-h1--serif" itemprop="name">\s+'
    r'(?P<title>.+?)'
    r'\n</h1>',
    flags=re.DOTALL
)

pages_pattern = re.compile(
    r'<span itemprop="numberOfPages">(?P<pages>\d+)',
    flags=re.DOTALL
)

date_pattern = re.compile(
    r'<div class="row">\s+'
    r'Published\s+'
    r'(?P<date>.+?)'
    r'</div>',
    flags=re.DOTALL
)

get_date_pattern = re.compile(
    r'\d{3,4}',
    flags=re.DOTALL
)

series_pattern = re.compile(
    r'<div class="infoBoxRowTitle">Series</div>',
    flags=re.DOTALL
)

genre_pattern = re.compile(
    r'<a class="actionLinkLite bookPageGenreLink" href="/genres/.+?>(?P<genre>.+?)</a>'
)

review_pattern = re.compile(
    r'<meta itemprop="reviewCount" content="\d+" />\n    (?P<reviews>.+?)\s',
    flags=re.DOTALL
)


def get_date(string):
    year_list = re.findall(get_date_pattern, string)
    if year_list == []:
        return None
    if len(year_list) == 1:
        return year_list[0]
    else:
        return year_list[1]


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
    return result


def sort_data_from_book(book):
    result = {}
    title = title_pattern.search(book)
    if title:
        result['title'] = title['title']
    else:
        result['title'] = None

    pages = pages_pattern.search(book)
    if pages:
        result['pages'] = int(pages['pages'])
    else:
        result['pages'] = None
    
    date = date_pattern.search(book)
    if date:
        result['date'] = get_date(date['date'])

    series = series_pattern.search(book)
    if series:
        result['series'] = True
    else:
        result['series'] = False
    
    reviews = review_pattern.search(book)
    result['reviews'] = int(reviews['reviews'].replace(',', ''))

    return result


def sort_data_from_file(filename, directory):
    text = read_file_to_string(filename, directory)
    elements = collect_elements_from_page(text)
    
    return [
        sort_data_from_element(element) for element in elements
    ]


def sort_book_data_from_file(filename, directory):
    text = read_file_to_string(filename, directory)
    return sort_data_from_book(text)


def list_of_dict_to_csv(list_of_dict, fieldnames, filename, directory):
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, 'w', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dict:
            writer.writerow(row)


def save_id_list_to_directory(id_list, directory):   
    for book_id in sorted(id_list): 
        save_url_to_file(
            f'https://www.goodreads.com/book/show/{book_id}',
            f'book-{book_id}.html',
            directory
            )
        time.sleep(5)


def main(redownload=True, reparse=True):
    #for page in range(1, STEVILO_STRANI + 1):
    #    save_url_to_file(
    #        f'https://www.goodreads.com/list/show/1?page={page}',
    #        f'list_page-{page}.html',
    #        PAGE_DIRECTORY
    #        )

    main_data = []
    for page in range(1, STEVILO_STRANI + 1):
        sorted_data = sort_data_from_file(f'list_page-{page}.html', PAGE_DIRECTORY)
        main_data += sorted_data
    
    id_list = [book['id'] for book in main_data]

    
    list_of_book_data, genre_list = [], []
    for book_id in id_list:
        filename = f'book-{book_id}.html'
        book_data = sort_book_data_from_file(filename, BOOK_DIRECTORY)
        list_of_book_data.append(book_data)
        
        genres = re.findall(genre_pattern, read_file_to_string(filename, BOOK_DIRECTORY))
        genres_without_repetition = list(set(genres))
        for genre in genres_without_repetition:
            genre_list.append({'id': book_id, 'genre': genre})
    
    list_of_dict_to_csv(genre_list,
        ['id', 'genre'],
        'zanri.csv',
        MAIN_DIRECTORY)

    all_data = []
    for i in range(STEVILO_STRANI * STEVILO_ELEMENTOV_NA_STRAN):
        dic1 = main_data[i]
        dic2 = list_of_book_data[i]
        dic1.update(dic2)
        all_data.append(dic1)

    list_of_dict_to_csv(all_data,
        ['id', 'title', 'list_placement', 'author_id', 'author', 'pages', 'date', 'series', 'avg_rating', 'ratings', 'reviews', 'list_score', 'list_votes'],
        'podatki.csv',
        MAIN_DIRECTORY)


'''---Napisal kodo, ki mi je ponovno poskusila shraniti datoteke, ki se niso pravilno nalozile (le-te so imele najmanjso velikost)---'''   
    
    #book_directory = 'BOOK_DIRECTORY'
    #n = 2               #izbere prvih n najmanjsih datotek
    #file_id_pattern = re.compile(r'\d+')
    #files = os.listdir(book_directory)
    #files_sorted_by_size = sorted(files, key=lambda filename: os.path.getsize(os.path.join(book_directory, filename)))  
    #nsmallest_files = files_sorted_by_size[:n] 
    #sez_id = []
    #for f in nsmallest_files:
    #    file_id = int(re.search(file_id_pattern, f).group())
    #    sez_id.append(file_id)
    #save_id_list_to_directory(sez_id, book_directory)  #ponovno nalozi prvih n najmanjsih datotek

'''-----------------------------------------------------------------------------------------------------------------------------'''

    
if __name__ == '__main__':
    main()