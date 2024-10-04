from datetime import datetime
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import pytz
import os


def get_feed(feed_file_path):

    if os.path.exists(feed_file_path):
        tree = ET.parse(feed_file_path)
    else:
        tree = None

    return tree

def parse_feed(tree):

    root = tree.getroot()
    channel = root.find('channel')

    return root,channel

def already_exists_in_feed(channel, new_item):

    existing_links = {item.find('link').text for item in channel.findall('item')}
    
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

def write_to_file(feed_file_path, root):

    pretty_xml = prettify_xml(root)
    with open(feed_file_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

def add_new_item(root, channel, raw_item, feed_file_path):

    new_item = ET.SubElement(channel, 'item')

    title = ET.SubElement(new_item, 'title')
    title.text = raw_item["title"]

    link = ET.SubElement(new_item, 'link')
    link.text = raw_item["link"]

    content = ET.SubElement(new_item, 'content')
    content.text = raw_item["content"]

    date = ET.SubElement(new_item, 'extractionDate')
    date.text = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    write_to_file(feed_file_path, root)

def prettify_xml(root):
    xml_data = ET.tostring(root, encoding='utf-8', method='xml')
    soup = BeautifulSoup(xml_data, 'xml')
    return soup.prettify()

def add_new_items_to_feed(feed_file_path:str, new_items:list):

    for new_item in new_items:

        tree = get_feed(feed_file_path)

        root, channel = parse_feed(tree)

        if already_exists_in_feed(channel, new_item):

            print(f"{new_item['link']} Already exists in feed.")

            continue

        add_new_item(root, channel, new_item, feed_file_path)

        print(f"[SUCCESS] {new_item['link']} uploaded to the feed.")

if __name__ == "__main__":

    add_new_items_to_feed("RSS/feed.xml", [{"title":"atrff", "link":"www.asaassASDsddsd.com", "content": "sample_12"}])