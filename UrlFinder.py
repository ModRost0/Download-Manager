from downloadTask import DownloadTask
import requests
s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0"})
from downloadManager import manager
class UrlFinder():
     def __init__(self,pluggin,Urls):
          self.Urls = Urls
          self.pluggin = pluggin
     def queue_Url(self):
          if self.pluggin == "normal":
               for item in self.Urls:
                    self.normal_download(item)
          elif self.pluggin == "datanodes":
               for item in self.Urls:
                    self.crawl_datanodes(item)
     def normal_download(self,url):
          manager.add_task(DownloadTask(url,"test.rar"))
     def crawl_datanodes(self, url):
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
          try:
               down2 = s.post('https://datanodes.to/download',data=payload2,timeout=10)
               url = down2.content
               print(f"crawling {fname[:50]}...")
               manager.add_task(DownloadTask(url,fname))
          except Exception as e:
               print(f"Error crawling {fname}: {e}")
