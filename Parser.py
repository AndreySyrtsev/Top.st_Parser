import urllib.request
from bs4 import BeautifulSoup
import iso8601
from dateutil.tz import tzlocal
import re

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)' \
             ' Chrome/62.0.3202.94 Safari/537.36'


def get_html(url):
    headers = {'User-Agent': USER_AGENT}
    request = urllib.request.Request(url, headers)

    response = urllib.request.urlopen(request)

    return response.read()


def get_description(country, news_id):
    post_data = urllib.parse.urlencode({'country': country, 'id': news_id, 'period': "online", 'type': "news"}).encode('utf-8')

    headers = {'User-Agent': USER_AGENT}
    req = urllib.request.Request('https://top.st/api/v1/article', post_data, headers)
    res = urllib.request.urlopen(req)

    html = res.read()

    response_parse = html.decode('utf-8')
    index = response_parse.index('description', 0, -1)
    index2 = response_parse.index('<', index, -1)

    description = response_parse[index + 14:index2]
    return description.replace("\\", "")


def get_inform(url, description):
    # soup2 = BeautifulSoup(get_html(ref.attrs["href"]), "html.parser")

    # result = ''

    # result = soup2.find_all(text=re.compile('^'+description[0:5]))
    # if (soup2.find('p', text=re.compile(description[0:])) != None):
    #    parent = soup2.find('p', text=re.compile(description[0:16]))

    # for str in parent.find_all('p'):
    #    result += str.text + '\n'
    # print(result)

    pass


def parse(html):
    news = []

    soup = BeautifulSoup(html, "html.parser")

    country = soup.find('option', selected="selected")
    list_articles = soup.find('ul', class_='articles')

    for row in list_articles.find_all('li')[0:3]:
        rating = row.find('em')
        date = row.find('time')
        ref = row.find('a')
        news_id = row.attrs["data-id"]

        parse_date = iso8601.parse_date(date.attrs["datetime"]).astimezone(tzlocal())

        description = get_description(country.attrs["value"], news_id)

        news.append({
            'country': country.text,
            'rating': rating.text,
            'title': ref.text,
            'text': description,
            'reference': ref.attrs["href"],
            'date': parse_date.strftime("%d.%m.%Y %I:%M %p")
        })

    for element in news:
        print(element)


def main():
    parse(get_html('http://top.st/'))


if __name__ == '__main__':
    main()