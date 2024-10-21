from datetime import datetime
import os
import requests
from bs4 import BeautifulSoup
from common import add_new_items_to_feed, get_links_from_xml
from concurrent.futures import ThreadPoolExecutor
from concurrent import futures
import threading
import logging


logging.basicConfig(
    filename='nyt_log.txt',              
    level=logging.INFO,               
    format='%(asctime)s - %(levelname)s - %(message)s'
)

main_r_json = {
  "url": "https://www.nytimes.com/topic/subject/oil-and-gasoline",
  "screenshot": True,
  "browserHtml": True,
  "actions": [
    {
      "action": "waitForNavigation",
      "waitUntil": "load",
      "timeout": 31,
      "onError": "continue"
    },
    {
      "action": "waitForSelector",
      "selector": {
        "type": "css",
        "value": 'h3'
      },
      "timeout": 5,
      "onError": "continue"
    },
    {
      "action": "waitForTimeout",
      "timeout": 2,
      "onError": "continue"
    }
    ],
    "screenshotOptions":{
      "fullPage" : True
    }
}

article_r_json = {
  "url": None,
  "screenshot": True,
  "browserHtml": True,
  "actions": [
    {
      "action": "waitForNavigation",
      "waitUntil": "load",
      "timeout": 31,
      "onError": "continue"
    },
    {
      "action": "interaction",
      "id": "Others-www.bloomberg.com",
      "args": {
        "email": None,
        "pass": None
        }
    },
    {
      "action": "waitForSelector",
      "selector": {
        "type": "css",
        "value": "#story > section > div:nth-child(1) > div > p:nth-child(1)"
      },
      "timeout": 5,
      "onError": "return"
    },
    {
      "action": "waitForTimeout",
      "timeout": 5,
      "onError": "continue"
    },
    {
      "action": "scrollBottom"
    }
  ],
}

lock = threading.Lock()

def get_secret_data():

    key = os.getenv('ZYTE_KEY')
    email = os.getenv('NYT_EMAIL')
    passw = os.getenv('NYT_PASS')


    return email, passw, key

def create_json(r_type:str, data_json:dict, email:str=None, passw:str=None, article_url:str=None) -> dict:

    if r_type == "article":

        data_json["url"] = article_url
        data_json["actions"][1]["args"]["email"] = email
        data_json["actions"][1]["args"]["pass"] = passw.replace("\\", "")

        return data_json

    else:

        return data_json

def scrape_request(key:str, r_json:dict):

    api_response = requests.post(
    "https://api.zyte.com/v1/extract",
    auth = (key, ""),
    json = r_json
    )   
    response = api_response.json()


    return response

def parse_articles_raw(articles):

    article_links = []

    for article in articles:

        article_links.append(f'https://www.nytimes.com{article.find("a").attrs["href"]}')

    article_links = set(article_links)
    article_links = list(article_links)

    return article_links

def extract_articles_url(html_response:str) -> list[str]:

    soup = BeautifulSoup(html_response["browserHtml"],"html.parser")
    all_articles = soup.find_all("ol")[0].find_all("li")

    articles_url = parse_articles_raw(all_articles)

    return articles_url

def get_all_articles_url() -> list[str]:

    _,_,key = get_secret_data()
    r_json = create_json("main", main_r_json)

    while True:

        try:
            html_response = scrape_request(key, r_json)
            articles_url = extract_articles_url(html_response)

            break

        except Exception as e:

            continue

    return articles_url

def get_article_title(s):

    return s.select_one("h1[data-testid='headline']").text

def get_article_content(s):

    content = ""

    for i in s.select('div[data-testid*="companionColumn"]'):

        for j in i.find_all("p"):

            content += f"{j}\n"

def extract_article_information(html_response:str, url:str) -> dict:

    soup = BeautifulSoup(html_response["browserHtml"],"html.parser")
    
    title = get_article_title(soup)
    content = get_article_content(soup)

    return {
        "title": title,
        "content": content,
        "link": url
    }

def get_article_information(article_url:str) -> dict:

    email,passw,key = get_secret_data()

    global article_r_json

    with lock:

        r_json = create_json("article", article_r_json, email, passw,article_url)

        while True:

            try:

                html_response = scrape_request(key, r_json)

                article_information = extract_article_information(html_response, article_url)
                break

            except Exception as e:

                continue

        return article_information

def excecute_scraping() -> list[dict]:

    logging.info("[NYT] " +f"LOGGING TIME: {datetime.now()}",)

    logging.info("[NYT] " +"[Articles Url] Starting scraping process")

    articles_url = set(get_all_articles_url())
 
    while True:

      if articles_url:

        break

      else:

        articles_url = set(get_all_articles_url())

    new_articles_url = articles_url - get_links_from_xml("RSS/feed.xml")

    logging.info("[NYT] " +"[Articles Url] Extracted successfully\n")


    logging.info("[NYT] " +"[Articles Info] Starting scraping process")

    with ThreadPoolExecutor() as executor:
        jobs = []
        all_articles_info = []

        logging.info("[NYT] " +new_articles_url)

        for url in new_articles_url:

          jobs.append(executor.submit(get_article_information, url))

        for job in futures.as_completed(jobs):
            result = job.result()
            all_articles_info.append(result)

    logging.info("[NYT] " +"[Articles Info] Extracted successfully\n")

    return all_articles_info

def run():

    try:

        all_articles_info = excecute_scraping()

        logging.info("[NYT] " +"[Adding To Feed] Starting...")

        for item in all_articles_info:

            logging.info("[NYT] " +f"[Adding To Feed] Adding Item: {item['link']}")

        add_new_items_to_feed("RSS/feed.xml", all_articles_info)

        logging.info("[NYT] " +"[Adding To Feed] Added successfully\n")

    except Exception as e:

        logging.info("[NYT] " +f"[ERROR] Check scraping process, error: {e}")

if __name__ == "__main__":

    run()