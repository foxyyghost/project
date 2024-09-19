import requests
from bs4 import BeautifulSoup
import time
import urllib.robotparser
import sqlite3
import argparse

class SimpleCrawler:
    def __init__(self, seed_url, max_pages=100, max_depth=2):
        self.seed_url = seed_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited = set()
        self.to_visit = [(seed_url, 0)]  # Store (url, depth) tuples
        self.allowed_domains = [requests.utils.urlparse(seed_url).netloc]  # Add allowed domains
        self.blocked_domains = []  # You can add blocked domains here
        self.init_db()  # Initialize the database

    def init_db(self):
        """Initialize the SQLite database to store crawled data."""
        self.conn = sqlite3.connect('crawled_data.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY,
                url TEXT UNIQUE,
                title TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def store_page(self, url, title, content):
        """Store crawled data in the database."""
        try:
            self.cursor.execute('INSERT OR IGNORE INTO pages (url, title, content) VALUES (?, ?, ?)', (url, title, content))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def is_allowed(self, url):
        """Check if crawling is allowed by robots.txt."""
        parsed_url = requests.utils.urlparse(url)
        rp = urllib.robotparser.RobotFileParser()
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        try:
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch("*", url)
        except Exception as e:
            print(f"Error reading robots.txt for {robots_url}: {e}")
            return True  # Default to allowed if robots.txt can't be fetched

    def is_valid_domain(self, url):
        """Check if the URL is in allowed domains and not in blocked domains."""
        parsed_url = requests.utils.urlparse(url)
        domain = parsed_url.netloc
        
        if any(blocked in domain for blocked in self.blocked_domains):
            return False
        if not any(allowed in domain for allowed in self.allowed_domains):
            return False
        return True

    def fetch_page(self, url):
        """Fetch a web page and return its content."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
            return None

    def parse_page(self, url, html, depth):
        """Parse a page to extract links and content."""
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string if soup.title else "No Title"
        
        print(f"Visiting: {url} | Title: {title} | Depth: {depth}")

        # Store the crawled data
        self.store_page(url, title, html)

        # Extract links
        for link in soup.find_all('a', href=True):
            full_link = requests.compat.urljoin(url, link['href'])
            if full_link not in self.visited and self.is_allowed(full_link) and self.is_valid_domain(full_link):
                self.to_visit.append((full_link, depth + 1))  # Append with increased depth

    def crawl(self):
        """Main crawling loop."""
        print("Starting the crawl...")
        while self.to_visit and len(self.visited) < self.max_pages:
            url, depth = self.to_visit.pop(0)  # Pop a URL and its depth
            print(f"Current URL: {url} | Current Depth: {depth}")
            if url not in self.visited and self.is_allowed(url) and depth <= self.max_depth:
                html = self.fetch_page(url)
                if html:
                    self.parse_page(url, html, depth)
                    self.visited.add(url)
                else:
                    print(f"Failed to fetch or parse: {url}")
            time.sleep(1)  # Be polite to the server
        print("Crawl finished.")
        self.conn.close()  # Close the database connection

def main():
    parser = argparse.ArgumentParser(description='Simple Web Crawler')
    parser.add_argument('seed_url', type=str, help='The starting URL for the crawler')
    parser.add_argument('--max_pages', type=int, default=100, help='Maximum number of pages to crawl')
    parser.add_argument('--max_depth', type=int, default=2, help='Maximum depth to crawl')
    args = parser.parse_args()

    crawler = SimpleCrawler(args.seed_url, args.max_pages, args.max_depth)
    crawler.crawl()

if __name__ == "__main__":
    main()
