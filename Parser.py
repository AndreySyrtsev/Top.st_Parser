import urllib.request
from bs4 import BeautifulSoup
import bs4
import iso8601
from dateutil.tz import tzlocal
from selenium import webdriver
import sqlite3
import timeit




USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
ROW_COUNT = 5

def get_html(url):
    headers = {'User-Agent': USER_AGENT}
    request = urllib.request.Request(url, None, headers)

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


def PhantomJS(html):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=800x600')
    options.add_argument("--mute-audio")

    driver = webdriver.Chrome(chrome_options=options)
    driver.set_page_load_timeout(30)
    driver.get(html)

    text = ''
    max_len = 0
    parent = None

    try:
        for p in driver.find_elements_by_xpath('html/body//p'):
            if len(p.text) > max_len:
                if p.location['y'] <= 1500:
                    max_len = len(p.text)
                    size = p.value_of_css_property('font-size')
                    parent = p.parent
                    width = p.size['width']

        for i in parent.find_elements_by_xpath('.//p'):
            if (len(i.text) > 20) and (i.value_of_css_property('font-size') == size) and (i.size['width'] == width):
                text += i.text

    except:
        for div in driver.find_elements_by_xpath('html/body//div[count(br)>0]'):
            if len(div.text) > max_len:
                if div.location['y'] <= 2000 and div.size['width'] > 600:
                    max_len = len(div.text)
                    text = div.text

    finally:
        driver.close()
        return text


def get_links(html, conn, cursor):
    news = []

    soup = BeautifulSoup(html, "html.parser")

    country = soup.find('option', selected="selected")
    list_articles = soup.find('ul', class_='articles')

    for row in list_articles.find_all('li')[0:ROW_COUNT]:
        rating = row.find('em')
        date = row.find('time')
        ref = row.find('a')
        news_id = row.attrs["data-id"]

        parse_date = iso8601.parse_date(date.attrs["datetime"]).astimezone(tzlocal())

        description = get_description(country.attrs["value"], news_id)

        content = 'Краткое описание: ' + description

        cursor.execute("""INSERT INTO buffer VALUES (:country, :title, :description, :content, :ref, :date)""",
                       {"country": country.text,
                        "title": ref.text.replace('\xa0', ' '),
                        "description": description,
                        "content": content,
                        "ref": ref.attrs["href"],
                        "date": parse_date.strftime("%d.%m.%Y %I:%M %p")})
        conn.commit()

def bs4(url):
    html_doc = get_html(url)
    soup = BeautifulSoup(html_doc, "html.parser")

    max_length = 0
    parent = None
    size = 0
    text = ''

    for ref in soup.find_all('a'):
        if ref.parent.name == 'div':
            ref.extract()

    for p in soup.find_all('p'):
        if len(p.text) > max_length:
            max_length = len(p.text)
            parent = p.parent

    for p in soup.find_all('p'):
        if p.parent == parent and len(p.text) >= 100:
            text += p.text

    return text


def get_content(ref, conn, cursor, id):

        try:
            content = bs4(ref)
        except:
            content = ''

        if len(content) > 100:
            cursor.execute("UPDATE buffer SET content = :content WHERE ROWID = :id",
                           {"content": content, "id": id})
            conn.commit()


def get_results(conn, cursor):
    i = 1
    cursor.execute("SELECT COUNT(*) FROM buffer")
    count = cursor.fetchall()
    a = timeit.default_timer()

    while i <= count[0][0]:
        cursor.execute("SELECT reference FROM buffer WHERE ROWID = :id", {"id": i})
        ref = cursor.fetchall()
        print(ref[0][0])
        get_content(ref[0][0], conn, cursor, i)

        if (i % ROW_COUNT == 0):
            cursor.execute("SELECT COUNTRY FROM buffer WHERE ROWID = :id", {"id": i})
            country = cursor.fetchall()
            cursor.execute("SELECT COUNT(*) FROM buffer WHERE CONTENT NOT LIKE 'Краткое описание: %' AND COUNTRY = :country", {"country": country[0][0]})
            res = cursor.fetchall()
            time = timeit.default_timer() - a
            a = timeit.default_timer()
            cursor.execute("""INSERT INTO results VALUES (:country, :time, :result)""",
                           {"country": country[0][0],
                            "time": time,
                            "result": res[0][0]/50*100
                            })
        conn.commit()
        i += 1



def main():
    countries = ['au', 'ar', 'am', 'by', 'bg', 'br', 'gb', 'de', 'gr', 'ge', 'in', 'it', 'kz', 'ca', 'mx', 'nl', 'pt',
                  'ru', 'ro', 'us', 'sg', 'tr', 'uz', 'ua', 'fi', 'fr', 'cz', 'ch', 'ee', 'jp']

    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM buffer")
    cursor.execute("DELETE FROM results")
    conn.commit()

    countries = ['ru', 'us', 'br']
    for country in countries:
        url = 'http://top.st/'+country+'/month'
        get_links(get_html(url), conn, cursor)


    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    get_results(conn, cursor)

if __name__ == '__main__':
    main()