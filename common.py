import feedparser
from feedgen.feed import FeedGenerator
from datetime import datetime
import pytz
import os

def get_feed(feed_file_path):

    if os.path.exists(feed_file_path):
        with open(feed_file_path, 'r', encoding='utf-8') as feed_file:
            existing_feed = feed_file.read()
    else:
        existing_feed = None

    return existing_feed

def parse_feed(existing_feed):

    parsed_feed = feedparser.parse(existing_feed) if existing_feed else None

    return parsed_feed

def already_exists_in_feed(parsed_feed, new_item):

    existing_links = [entry.link for entry in parsed_feed.entries]
    
    return new_item["link"] in existing_links

def start_feed_with_previous_data(parsed_feed):

    fg = FeedGenerator()
    
    if parsed_feed and parsed_feed.feed:

        fg.title(parsed_feed.feed.title)
        fg.link(href=parsed_feed.feed.link, rel='self')
        fg.description(parsed_feed.feed.description)

        fg = add_existing_items(fg, parsed_feed)

    else:

        fg = create_default_feed(fg)

    return fg

def add_existing_items(fg, parsed_feed):

    for entry in parsed_feed.entries:
        fe = fg.add_entry()
        fe.title(entry.title)
        fe.link(href=entry.link)
        fe.extension("content", entry.content)
        fe.extension('extractionDate', entry.extractionDate)

    return fg

def create_default_feed(fg):

    fg.title("My RSS Feed")
    fg.description("This is an example RSS feed")

    return fg

def write_to_file(feed_file_path, fg):

    with open(feed_file_path, 'w', encoding='utf-8') as updated_feed_file:
        updated_feed_file.write(fg.rss_str(pretty=True).decode('utf-8'))

def add_new_item(fg, new_item, feed_file_path):

    fe = fg.add_entry()
    fe.title(new_item["title"])
    fe.link(href=new_item["link"])
    fe.extension("content", new_item["content"])
    extraction_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    fe.extension('extractionDate', extraction_date)

    write_to_file(feed_file_path, fg)

def add_new_items_to_feed(feed_file_path:str, new_items:list):

    for new_item in new_items:

        parsed_feed = parse_feed(get_feed(feed_file_path))

        if already_exists_in_feed(parsed_feed, new_item):

            continue

        add_new_item(start_feed_with_previous_data(parsed_feed),new_item, feed_file_path)

if __name__ == "__main__":

    add_new_items_to_feed("RSS/feed.xml", [{"title":"atr", "link":"www.link.com", "content": "sample_1"}])