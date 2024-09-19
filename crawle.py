import requests
from bs4 import BeautifulSoup
import time
import urllib.robotparser

class SimpleCrawler:
    def __init__(self, seed_url, max_pages=100):
        self.seed_url = seed_url
        self.max_pages = max_pages
        self.visited = set()
        self.to_visit = [seed_url]

    def is_allowed(self, url):
        """Check if crawling is allowed by robots.txt"""
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

    def fetch_page(self, url):
        """Fetch a web page and return its content"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
            return None

    def parse_page(self, url, html):
        """Parse a page to extract links and content"""
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string if soup.title else "No Title"
        
        print(f"Visiting: {url} | Title: {title}")  # Print the URL and title
        
        # Extract links
        for link in soup.find_all('a', href=True):
            full_link = requests.compat.urljoin(url, link['href'])
            if full_link not in self.visited and self.is_allowed(full_link):
                self.to_visit.append(full_link)

    def crawl(self):
        """Main crawling loop"""
        print("Starting the crawl...")  # Debug statement
        while self.to_visit and len(self.visited) < self.max_pages:
            url = self.to_visit.pop(0)
            print(f"Current URL: {url}")  # Debug statement
            if url not in self.visited and self.is_allowed(url):
                html = self.fetch_page(url)
                if html:
                    self.parse_page(url, html)
                    self.visited.add(url)
                else:
                    print(f"Failed to fetch or parse: {url}")  # Debug statement
            time.sleep(1)  # Be polite to the server
        print("Crawl finished.")

if __name__ == "__main__":
    seed_url = "https://duckduckgo.com"  # Changed to a more suitable URL
    crawler = SimpleCrawler(seed_url)
    crawler.crawl()
