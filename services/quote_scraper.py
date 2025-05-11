import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/90.0.4430.93 Safari/537.36"
)
DELAY_BETWEEN_PAGES = 1
REQUEST_TIMEOUT = 10

def extract_slug_from_url(url):
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    return path.split("/")[0] if path else ""

def create_session():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session

def scrape_quotes_for_slug(slug: str, max_pages: int = 10):
    session = create_session()
    quotes = []
    serial_number = 1

    for page_number in range(1, max_pages + 1):
        url = f"https://quotefancy.com/{slug}/page/{page_number}"
        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException:
            break

        soup = BeautifulSoup(response.content, "html.parser")
        containers = soup.find_all("div", class_="q-wrapper")
        if not containers:
            break

        for container in containers:
            quote_div = container.find("div", class_="quote-a")
            quote_text = quote_div.get_text(strip=True) if quote_div \
                else container.find("a", class_="quote-a").get_text(strip=True)

            quote_link = ""
            if quote_div and quote_div.find("a"):
                quote_link = quote_div.find("a").get("href", "")
            elif container.find("a", class_="quote-a"):
                quote_link = container.find("a", class_="quote-a").get("href", "")

            author_div = container.find("div", class_="author-p bylines")
            if author_div:
                author_text = author_div.get_text(strip=True).replace("by ", "").strip()
            else:
                author_p = container.find("p", class_="author-p")
                author_text = author_p.find("a").get_text(strip=True) if author_p and author_p.find("a") else "Anonymous"

            quotes.append({
                "serial": serial_number,
                "quote": quote_text,
                "link": quote_link,
                "author": author_text
            })
            serial_number += 1

        time.sleep(DELAY_BETWEEN_PAGES)

    return quotes

def scrape_quotes_from_urls(urls, max_pages):
    all_quotes = []
    for url in urls:
        slug = extract_slug_from_url(url)
        quotes = scrape_quotes_for_slug(slug, max_pages)
        all_quotes.extend(quotes)
    return all_quotes

def save_quotes_to_postgres(quotes):
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        database=os.getenv("PG_DATABASE"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        port=os.getenv("PG_PORT")
    )
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS scraped_quotes (
            id SERIAL PRIMARY KEY,
            serial INT,
            quote TEXT,
            link TEXT,
            author TEXT,
            status TEXT DEFAULT 'Pending',
            UNIQUE(quote, author)
        );
    """)

    for q in quotes:
        cur.execute("""
            INSERT INTO scraped_quotes (serial, quote, link, author)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (quote, author) DO NOTHING;
        """, (q['serial'], q['quote'], q['link'], q['author']))

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Inserted {len(quotes)} quotes into PostgreSQL with status 'Pending'.")
