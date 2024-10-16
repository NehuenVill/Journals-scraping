from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
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

def add_new_items_to_feed(feed_file_path:str, new_items:set):

    for new_item in new_items:

        tree = get_feed(feed_file_path)

        root, channel = parse_feed(tree)

        add_new_item(root, channel, new_item, feed_file_path)

        print(f"[SUCCESS] {new_item['link']} uploaded to the feed.")

def get_links_from_xml(xml_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    links = []

    for item in root.findall(".//item"):
        link = item.find('link')
        if link is not None:
            links.append(link.text.replace("\n", "").strip())

    return set(links)


def delete_old_items_from_xml(xml_file, days_old=3):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    current_date = datetime.now()

    cutoff_date = current_date - timedelta(days=days_old)

    for channel in root.findall('channel'):
        for item in channel.findall('item'):
            pub_date_text = item.find('extractionDate').text.replace("\n", "").strip()
            pub_date = datetime.strptime(pub_date_text, "%Y-%m-%d %H:%M:%S")

            if pub_date < cutoff_date:
                channel.remove(item)

    tree.write(xml_file)

if __name__ == "__main__":

    add_new_items_to_feed("RSS/feedxx.xml", [{"title":"atrfff", "link":"www.agsaassASDsddsd.com", "content": "sample1_12"}])
    # print(get_links_from_xml("RSS/feed.xml"))
    pass