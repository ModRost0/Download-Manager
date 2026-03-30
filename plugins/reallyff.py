import requests
def url(url):
    res = requests.get(url, timeout=10)
    location = res.content.find(b"https://fu")
    print(location)
    with open("plugins/scrapable.html", "w+b") as f:
        f.write(res.content)
        f.seek(location)
        url = f.read().split(b'"')[0].decode()
        f.seek(res.content.find(b"<title>") + len(b"<title>"))
        fname = f.read().split(b"<")[0].decode()
    return url,fname