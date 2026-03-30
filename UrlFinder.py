from downloadTask import DownloadTask
import requests
from plugins import reallyff, datanodes
s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0"})
from downloadManager import manager
class UrlFinder():
     def __init__(self,Urls):
          self.Urls = Urls
          self.pluggin = self.find_url_host()
     def find_url_host(self):
          for url in self.Urls:
               if url.split('//')[1].startswith("datanodes"):
                    return "datanodes"
               elif url.split('//')[1].startswith("fuckingfast"):
                    return "reallyff"
          return "normal"
     def queue_Url(self):
          if self.pluggin == "normal":
               for item in self.Urls:
                    self.normal_download(item)
          elif self.pluggin == "datanodes":
               for item in self.Urls:
                    self.crawl_datanodes(item)
          elif self.pluggin == "reallyff":
               for item in self.Urls:
                    self.crawl_reallyff(item)
     def normal_download(self,url):
          manager.add_task(DownloadTask(url,"test.rar"))
     def crawl_datanodes(self, url):
          url,fname = datanodes.url(url) 
          manager.add_task(DownloadTask(url,fname))
     def crawl_reallyff(self,url):
          url,fname = reallyff.url(url)
          manager.add_task(DownloadTask(url,fname))