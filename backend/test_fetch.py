import requests
from bs4 import BeautifulSoup

h = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
url = "https://www.amazon.in/product-reviews/B0CTXY8HQV"
r = requests.get(url, headers=h)
soup = BeautifulSoup(r.text, "lxml")
print("STATUS:", r.status_code)
print("TITLE:", soup.title.text if soup.title else None)
print("CAPTCHA?", "captcha" in r.text.lower())
