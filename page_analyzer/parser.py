from bs4 import BeautifulSoup


def parse_html(content):
    soup = BeautifulSoup(content, "html.parser")

    h1 = soup.h1.get_text(strip=True) if soup.h1 else None
    title = soup.title.get_text(strip=True) if soup.title else None

    description = None
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag and desc_tag.get("content"):
        description = desc_tag["content"].strip()

    return h1, title, description
