from bs4 import BeautifulSoup
import sys

with open("test_fetch_output.html", "r", encoding="utf-8") as f:
    html = f.read()

try:
    soup = BeautifulSoup(html, "html.parser")
    # Werkzeug puts the plain text traceback in a textarea with id 'traceback' or similar, or just find the traceback div
    tb = soup.find("textarea")
    if tb:
        print(tb.text)
    else:
        # Just grab the title and h1
        print("TITLE:", soup.title.string)
        print("HEADINGS:", [h.text for h in soup.find_all(['h1', 'h2', 'h3'])])
        print("TEXT:", soup.text[:1000]) # First 1000 chars of text
except Exception as e:
    print("Error parsing:", e)
