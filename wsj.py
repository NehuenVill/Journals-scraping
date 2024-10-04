from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
from common import add_new_items_to_feed
from concurrent.futures import ThreadPoolExecutor
import traceback

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
    }
  ],
  "javascript": True,
}

def get_secret_data():

    load_dotenv()

    key = os.getenv('ZYTE_KEY')
    email = os.getenv('WSJ_EMAIL')
    passw = os.getenv('WSJ_PASS')

    print("Loaded environment variables")

    return email, passw, key

def create_json(r_type:str, email:str=None, passw:str=None, article_url:str=None) -> dict:

    if r_type == "article":

        article_r_json["url"] = article_url
        article_r_json["actions"][4]["text"] = email
        article_r_json["actions"][7]["text"] = passw

        return article_r_json

    else:

        return main_r_json

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
    article_links = tuple(article_links)

    return article_links

def extract_articles_url(html_response:str) -> list[str]:

    soup = BeautifulSoup(html_response["browserHtml"],"html.parser")
    all_articles = soup.find("div", id="latest-stories").find_all("a")

    articles_url = parse_articles_raw(all_articles)

    return articles_url

def get_all_articles_url() -> list[str]:

    _,_,key = get_secret_data()
    r_json = create_json("main")

    while True:

        try:
            html_response = scrape_request(key, r_json)
            print(html_response)
            print(html_response["actions"])
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

    return s.find("section").text

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
    r_json = create_json("article", email, passw,article_url)

    while True:

        try:

            html_response = scrape_request(key, r_json)
            article_information = extract_article_information(html_response, article_url)
            break

        except Exception as e:

            print("Error getting articles infromation, trying again...")
            continue

    print("SUCCESSFULY EXTRACTED ARTICLES INFORMATION\n")
    print("-"*70)
    print("\n")

    return article_information

def excecute_scraping() -> list[dict]:

    print("[Articles Url] Starting scraping process")

    articles_url = get_all_articles_url()
 
    all_articles_info = []

    print("[Articles Info] Starting scraping process")

    with ThreadPoolExecutor() as executor:
        results = executor.map(get_article_information, articles_url[1:3])

        all_articles_info = list(results)

    return all_articles_info

def run():

    all_articles_info = excecute_scraping()

    add_new_items_to_feed("RSS/feed.xml", all_articles_info)


if __name__ == "__main__":

    run()