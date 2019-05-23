# coding: utf-8'''
import os
import sys
import requests
import re
import click
from bs4 import BeautifulSoup


'''
Define the paramteter
'''
req = requests.session()
https_domain = 'https://www.ptt.cc'
board = 'Beauty'
images_url = set()


'''
Use for get the article's content, to get_image_url
'''


def get_article(page_number, push_rate):

    print('Now parse the {}th pages.'.format(page_number))
    url = '{}/bbs/{}/index{}.html'.format(https_domain,
                                          board, page_number)
    response = req.get(url)
    if response.status_code == requests.codes.ok:
        soup = BeautifulSoup(response.text, 'html.parser')
    else:
        print('Somethings wrong, go to next page.')
        return

    for article in soup.find_all(class_="r-ent"):
        try:
            article_url = article.find('a')['href']
        except TypeError:
            continue

        rate = 0
        rate_text = article.find(class_="nrec").text
        if rate_text:
            if rate_text.startswith('爆'):
                rate = 100
            elif rate_text.startswith('X'):
                rate = -1 * int(rate_text[1])
            else:
                rate = int(rate_text)

        if rate >= push_rate:
            get_image_url(article_url)


'''
get the image url and add in images_url
'''


def get_image_url(article_url):

    response = req.get(https_domain + article_url)
    if response.status_code == requests.codes.ok:
        soup = BeautifulSoup(response.text, 'html.parser')
    else:
        print('Somethings wrong, go to next article.')
        return

    for img in soup.find_all("a"):
        link = validate_url_and_suffix(img['href'])

        if link is not None:
            images_url.add(link)


'''
validate the image url, only get the imgur file for data correctness.
'''


def validate_url_and_suffix(image_url):
    '''
    filter the gif, only accept jpeg/png
    '''
    images_suffix = ['.jpg', '.png', '.jpeg']

    if len(image_url) != 31:
        return None

    if not image_url.startswith('https://i.imgur.com'):
        return None

    for suffix in images_suffix:
        if image_url.endswith(suffix):
            return image_url
        else:
            return None


@click.command()
@click.option('--verbose', is_flag=True, help="Will print verbose messages.")
@click.option('--download', prompt='Your download directory, default is images.', help='download directory loaction.')
@click.option('--numbers', prompt='Your download target images.', default=100, help='Number of download images, default is 100.')
@click.option('--rate', default=10, help='Number of push rates, default is 10.')
def main(verbose, download, numbers, rate):

    if verbose:
        click.echo("We are in the verbose mode.")

    target = numbers

    if rate in range(0, 100):
        push_rate = rate
    else:
        push_rate = 10

    img_dir_name = download

    print('Start grab images from Beauty board.')
    print('The target is above {} images.'.format(target))
    print('The criteria is above {}.'.format(push_rate))
    print('The download directory  is {}.'.format(img_dir_name))

    if not os.path.isdir(img_dir_name):
        os.makedirs(img_dir_name)

    response = req.get('{}/bbs/{}/index.html'.format(https_domain, board))
    if response.status_code == requests.codes.ok:
        soup = BeautifulSoup(response.text, 'html.parser')
    else:
        print('Please check your network connection.')
        sys.exit()

    newest_page_number = int(re.findall(
        r'\d+', soup.select('.btn.wide')[1]['href'])[0])+1

    idx = newest_page_number
    while len(images_url) <= target:
        get_article(idx, push_rate)
        idx -= 1
        if idx == 0:
            print('There are no more pages.')
            sys.exit()

    print('Total got {} images'.format(len(images_url)))

    while len(images_url) > 0:
        try:
            url = images_url.pop()
        except KeyError:
            print('There are no more image urls.')
            sys.exit()

        file_name = os.path.join(img_dir_name, url.split('/')[-1])
        response = req.get(url, stream=True)
        if response.status_code == requests.codes.ok:
            try:
                with open(file_name, 'wb') as fp:
                    fp.write(response.content)
                    fp.close()
            except IOError:
                print('Please check your disk space.')
                return None
            print('save {} successful.'.format(file_name))


if __name__ == '__main__':
    main()
