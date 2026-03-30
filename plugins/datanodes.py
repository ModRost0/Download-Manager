import requests
def url(url):
    dataFromUrl = url.split('/')
    uniqueChars = dataFromUrl[3]
    fname = dataFromUrl[4]
    payload2 = {
    "op": "download2",
    "id": f"{uniqueChars}",
    "rand": "",
    "referer": "https://fitgirl-repacks.site/",
    "method_free": "Free Download >>",
    "method_premium": "",
    "g_captch__a": "1"}
    res = requests.post('https://datanodes.to/download', data=payload2,timeout=10)
    url = res.content
    return url, fname
