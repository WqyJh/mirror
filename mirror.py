import os
import sys
import re
import validators
from urllib.parse import urlparse, urljoin, urlunparse
import requests
from bs4 import BeautifulSoup

first_url = ''
url_base_path = ''
site_host = ''
site_abspath = ''

DIRS = ('img', 'js', 'css', 'font', 'html')


class Entity(object):
    def __init__(self, filename='', url='', type='', ext=''):
        super(Entity, self).__init__()
        self.filename = filename
        self.url = url
        self.type = type
        self.ext = ext

    @property
    def relative_file_path(self):
        return os.path.join(self.type, self.filename)

    @property
    def url_path(self):
        parsed = urlparse(self.url)
        return urlunparse(parsed._replace(scheme='', netloc='', path='/' + self.relative_file_path))

    def __repr__(self):
        return 'Entity[(filename=%s, url=%s, type=%s, ext=%s)]' \
               % (self.filename, self.url, self.type, self.ext)


download_queue = []
entity_list = []


def find_entity_by_url(url, entitylist):
    for entity in entitylist:
        if urlparse(url).path == urlparse(entity.url).path:
            return entity


def create_dirs():
    try:
        os.mkdir(site_abspath)
        os.chdir(site_abspath)
        for d in DIRS:
            os.mkdir(d)
    except Exception as e:
        print(e)
        exit(1)


def url_to_path(url):
    return urlparse(url).path


def url_to_filename(url):
    '''
    Generate a filename for this url
    :param url:
    :return:
    '''
    return os.path.basename(url_to_path(url)) or 'file'


def has_extension(filename):
    return '.' in filename


def entity_filename(entity):
    base = os.path.basename(url_to_path(entity.url)) or entity.type
    base = postfix_filename(base, len(entity_list))
    if not has_extension(base):
        base = base + '.' + entity.ext if entity.ext else base
    return base


def url_is_anchor(url):
    return urlparse(url).fragment


def check_scheme(url):
    '''
    Only http and https protocols are allowed. Empty scheme is regarded the same as http or https
    :param url:
    :return:
    '''
    return re.match('^(https?|)$', urlparse(url).scheme)


def url_in_current_dir(url):
    '''
    Ensure the url is under the same dir or the sub dirs with the first url
    :param url:
    :return: True means the url is under the same dir or the sub dirs with the first url
    '''
    path = urlparse(url).path
    if not path.startswith('/'):
        path = '/' + path
    l = [urlparse(first_url).path or '/', path]
    return url_base_path == os.path.commonpath(l)


def parse_url(url, current_url):
    '''
    Convert the relative url to absolute url.
    :param url:
    :param current_url:
    :return: (converted_url, same_host). same_host is True means url and current_url is under same host.
    '''
    parsed = urlparse(url)
    netloc = parsed.netloc
    if not netloc or netloc == site_host:
        return urljoin(current_url, url), True
    if netloc and not parsed.scheme:
        url = urlunparse(parsed._replace(scheme='http'))
    return url, False


def postfix_filename(filename, postfix):
    '''
    Add postfix to filename at the place before the right most '.' if the filename has extension.
    :param filename:
    :param postfix:
    :return:
    '''
    strs = filename.rsplit('.', maxsplit=1)
    strs[0] += '-' + str(postfix)
    return ''.join([strs[0], '.', strs[1]]) if len(strs) == 2 else strs[0]


def content_type_ext(response):
    content_type = response.headers['Content-Type']
    if 'text/html' in content_type:
        return 'html', 'html'
    elif 'javascript' in content_type:
        return 'js', 'js'
    elif 'text/css' in content_type:
        return 'css', 'css'
    elif 'image/png' in content_type:
        return 'img', 'png'
    elif 'image/jpg' in content_type or 'image/jpeg' in content_type:
        return 'img', 'jpg'
    else:
        filename = os.path.basename(url_to_path(response.url)) or 'file'
        strs = filename.rsplit('.', maxsplit=1)
        ext = strs[1] if len(strs) == 2 else ''
        type = 'font' if ext in 'ttf woff' else 'unknown'
        return type, ext


def download_recursively(entity):
    '''
    Recursively
    :param entity:
    :return:
    '''

    try:
        response = requests.get(entity.url)
    except Exception as e:
        print(e)
        return None

    entity.type, entity.ext = content_type_ext(response)
    entity.filename = entity_filename(entity)
    entity_list.append(entity)

    print(entity)

    file_content = response.content

    def update_tag_link(tag, key, current_url, same_host=False, no_parent=False):
        '''

        :param tag:
        :param key:
        :param current_url:
        :param same_host:
        :param no_parent:
        :param ignore_anchor: True means if the url is anchor, don't update it.
        :return:
        '''
        tagurl, is_same_host = parse_url(tag[key], current_url)

        # same_host constraint
        if same_host and not is_same_host:
            return

        # no_parent constraint
        if no_parent and not url_in_current_dir(tagurl):
            return

        e = find_entity_by_url(tagurl, entity_list) or download_recursively(Entity(url=tagurl))

        if e:
            tag[key] = e.url_path
            print('newurl', tag[key])

    if entity.type == 'html':
        soup = BeautifulSoup(response.text, 'html.parser')
        for atag in soup.find_all('a', attrs={'href': True}):
            # aurl, same_host = parse_url(atag['href'], entity.url)
            #
            # # Same-host and No-parent constraint
            # if not (url_in_current_dir(aurl) and same_host):
            #     continue
            #
            # e = find_entity_by_url(aurl, entity_list)
            # if not e and not url_is_anchor(aurl):
            #     e = download_recursively(Entity(url=aurl))
            #
            # if e:
            #     atag['href'] = urljoin('/', e.relative_path)
            #     print('newurl', atag['href'])
            update_tag_link(atag, 'href', entity.url, same_host=True, no_parent=True)

        for csstag in soup.find_all(name='link', rel='stylesheet'):
            # cssurl, _ = parse_url(csstag['href'], entity.url)
            #
            # e = find_entity_by_url(cssurl, entity_list) or download_recursively(Entity(url=cssurl))
            # if e:
            #     csstag['href'] = urljoin('/', e.relative_path)
            #     print('newurl', csstag['href'])
            update_tag_link(csstag, 'href', entity.url)

        for scripttag in soup.find_all(name='script', attrs={'src': True}):
            # scripturl, _ = parse_url(scripttag['src'], entity.url)
            #
            # e = find_entity_by_url(scripturl, entity_list) or download_recursively(Entity(url=scripturl, type='js'))
            # if e:
            #     scripttag['src'] = urljoin('/', e.relative_path)
            #     print('newurl', scripttag['src'])
            update_tag_link(scripttag, 'src', entity.url)

        for imgtag in soup.find_all(name='img'):
            # imgurl, _ = parse_url(imgtag['src'], entity.url)
            #
            # e = find_entity_by_url(imgurl, entity_list) or download_recursively(Entity(url=imgurl, type='img'))
            # if e:
            #     imgtag['src'] = urljoin('/', e.relative_path)
            #     print('newurl', imgtag['src'])
            update_tag_link(imgtag, 'src', entity.url)

        # print([atag['href'] for atag in soup.find_all('a', attrs={'href': True})])
        # print([csstag['href'] for csstag in soup.find_all(name='link', rel='stylesheet')])
        # print([scripttag['src'] for scripttag in soup.find_all(name='script', attrs={'src': True})])
        # print([imgtag['src'] for imgtag in soup.find_all(name='img')])

        file_content = soup.prettify('utf-8')

    with open(entity.relative_file_path, 'wb') as f:
        f.write(file_content)

    return entity


if __name__ == '__main__':
    if not (len(sys.argv) >= 2 and validators.url(sys.argv[1])):
        print('Usage: python3 download_site.py <first_url> [dest]')
        exit(1)

    first_url = sys.argv[1]
    site_host = urlparse(first_url).netloc
    url_base_path = os.path.dirname(urlparse(first_url).path)
    site_dir = 'site_downloaded' if len(sys.argv) == 2 else sys.argv[2]
    site_abspath = os.path.abspath(site_dir)

    if os.path.exists(site_abspath):
        print('"%s" exists, please input another directory' % site_dir)
        exit(1)

    create_dirs()
    os.chdir(site_abspath)

    entity = Entity(url=first_url)
    download_recursively(entity)