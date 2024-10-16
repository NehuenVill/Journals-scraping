from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
from common import add_new_items_to_feed, get_links_from_xml
from concurrent.futures import ThreadPoolExecutor
from concurrent import futures
import threading

main_r_json = {
  "url": "https://www.wsj.com/news/markets/oil-gold-commodities-futures?mod=md_cmd_news_all",
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
        "type": "xpath",
        "value": "//*[@id='latest-stories']"
      },
      "timeout": 5,
      "onError": "continue"
    },
    {
      "action": "waitForSelector",
      "selector": {
        "type": "xpath",
        "value": "//*[@id='latest-stories']"
      },
      "timeout": 5,
      "onError": "continue"
    }
    ]
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
      "action": "waitForSelector",
      "selector": {
        "type": "xpath",
        "value": "//a[contains(text(), \"Sign\")]"
      },
      "timeout": 5,
      "onError": "return"
    },
    {
      "action": "click",
      "selector": {
        "type": "xpath",
        "value": "//a[contains(text(), \"Sign\")]"
      },
      "onError": "return"
    },
    {
      "action": "waitForSelector",
      "selector": {
        "type": "xpath",
        "value": "//*[@id=\"emailOrUsername\"]"
      },
      "timeout": 5,
      "onError": "return"
    },
    {
      "action": "type",
      "selector": {
        "type": "xpath",
        "value": "//*[@id=\"emailOrUsername\"]"
      },
      "delay": 0.15,
      "onError": "return",
      "text": None
    },
    {
      "action": "keyPress",
      "onError": "return",
      "key": "Enter"
    },
    {
      "action": "waitForSelector",
      "selector": {
        "type": "xpath",
        "value": "//input[@type=\"password\"]"
      },
      "timeout": 5,
      "onError": "return"
    },
    {
      "action": "type",
      "selector": {
        "type": "xpath",
        "value": "//input[@type=\"password\"]"
      },
      "delay": 0.15,
      "onError": "return",
      "text": None
    },
    {
      "action": "keyPress",
      "onError": "return",
      "key": "Enter"
    },
    {
      "action": "waitForSelector",
      "selector": {
        "type": "xpath",
        "value": "//*[@id=\"root\"]/section/div/div[2]/button[2]"
      },
      "timeout": 5,
      "onError": "return"
    },
    {
      "action": "click",
      "selector": {
        "type": "xpath",
        "value": "//*[@id=\"root\"]/section/div/div[2]/button[2]"
      },
      "delay": 0.5,
      "button": "left",
      "onError": "return"
    },
    {
      "action": "waitForTimeout",
      "timeout": 1,
      "onError": "continue"
    },
    {
      "action": "waitForSelector",
      "selector": {
        "type": "xpath",
        "value": "//*[@id=\"latest-stories\"]/article[1]/div[2]/div[2]/h2/a"
      },
      "timeout": 5,
      "onError": "continue"
    },
    {
      "action": "scrollBottom"
    }
  ],
  "javascript": True,
}

lock = threading.Lock()

def get_secret_data():

    load_dotenv()

    key = os.getenv('ZYTE_KEY')
    email = os.getenv('WSJ_EMAIL')
    passw = os.getenv('WSJ_PASS')

    print("Loaded environment variables")

    return email, passw, key

def create_json(r_type:str, data_json:dict, email:str=None, passw:str=None, article_url:str=None) -> dict:

    if r_type == "article":

        data_json["url"] = article_url
        data_json["actions"][4]["text"] = email
        data_json["actions"][7]["text"] = passw.replace("\\", "")

        return data_json

    else:

        return data_json

def scrape_request(key:str, r_json:dict):

    print("\nStarting request")

    api_response = requests.post(
    "https://api.zyte.com/v1/extract",
    auth = (key, ""),
    json = r_json
    )   
    response = api_response.json()

    print("\nRequest finished Successfuly")

    return response

def parse_articles_raw(articles):

    article_links = []

    for article in articles:

        if "/news/markets/oil-gold-commodities-futures?page=2" not in article.attrs["href"]:

            article_links.append(article.attrs["href"])

    article_links = set(article_links)
    article_links = list(article_links)

    return article_links

def extract_articles_url(html_response:str) -> list[str]:

    soup = BeautifulSoup(html_response["browserHtml"],"html.parser")
    all_articles = soup.find("div", id="latest-stories").find_all("a")

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

            print("Error getting articles URL, trying again...")

            continue

    print("SUCCESSFULY EXTRACTED ARTICLES URL\n")
    print("-"*70)
    print("\n")

    return articles_url

def get_article_title(s):

    return s.find("h1").text

def get_article_content(s):

    section = s.find("section")

    content = ""

    for p in section.find_all("p"):

      content += f"{p.text} \n"

    return content

def extract_article_information(html_response:str, url:str) -> dict:

    soup = BeautifulSoup(html_response["browserHtml"],"html.parser")

    if soup.find("div", id="cx-snippet-overlay-container"):

      raise Exception("Was not able to log in correctly")
    
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

                print(f"Error: {e}")
                print("Error getting articles infromation, trying again...")
                continue

        print("SUCCESSFULY EXTRACTED ARTICLES INFORMATION\n")
        print("-"*70)
        print("\n")

        return article_information

def excecute_scraping() -> list[dict]:

    print("[Articles Url] Starting scraping process")

    articles_url = set(get_all_articles_url())
 
    while True:

      if articles_url:

        break

      else:

        articles_url = set(get_all_articles_url())

    new_articles_url = articles_url - get_links_from_xml("RSS/feed.xml")

    print("[Articles Info] Starting scraping process")

    with ThreadPoolExecutor() as executor:
        jobs = []
        all_articles_info = []

        print(new_articles_url)

        for url in new_articles_url:

          jobs.append(executor.submit(get_article_information, url, all_articles_info))
          print(url)

        for job in futures.as_completed(jobs):
            result = job.result()
            print(result)
            all_articles_info.append(result)

    return set(all_articles_info)


def run():

    all_articles_info = excecute_scraping()

    add_new_items_to_feed("RSS/feed.xml", all_articles_info)


if __name__ == "__main__":

    run()