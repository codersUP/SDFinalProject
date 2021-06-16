import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

links_attr = ['href', 'src']

def get_url_from_html(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    
    url_list = []
    for tag in soup.find_all(filter_tags):
        for attr in links_attr:
            if tag.has_attr(attr):
                url_list.append(urljoin(url, tag[attr]))
    return url_list

def get_html_from_url(url):
    for i in range(3):
        try:
            response = requests.get(url)
        except:
            if i == 2:
                print(f'Failed to download {url}')
            continue
        
        return response.content, 0
    return '', 1


def filter_tags(tag):
    return any(tag.has_attr(attr) for attr in links_attr)
