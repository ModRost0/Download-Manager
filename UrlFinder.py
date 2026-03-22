import os
import time
import requests
import urllib.parse
import json
from concurrent.futures import ThreadPoolExecutor
import sys
import threading
s = requests.Session()
import uuid
maxWorkers = 3
class DownloadManager():
     def __init__(self,running = False):
          self.tasks = []
          self.running = running
     def add_task(self,task):
          self.tasks.append(task)
     def start_individual(self,uniqueChars):
          for task in self.tasks:
               if task.uniqueChars == uniqueChars:
                    if task.status == "Pending" or task.status == "Paused":
                         t = threading.Thread(target=task.download)
                         print(f"Starting download for {task.fname}...")
                         t.start()
                    else:
                         print(task.status)
                    return
          print("Task not found.")
     def start_all(self):
          if self.running:
               print("Already running")
               return
          if not self.tasks:
               print("No tasks queued")
               return
          self.running = True
          display_thread = threading.Thread(target=live_display, args=(self,), daemon=True)
          display_thread.start()
          self.executor = ThreadPoolExecutor(max_workers=maxWorkers)
          for task in self.tasks:
               self.executor.submit(task.download_retry, retries=3)
          self.executor.shutdown(wait=True)
          self.running = False
     def pause_all(self):
          for task in self.tasks:
               task.pause()
     def get_status(self):
          return [task.get_status() for task in self.tasks]
     def resume_all(self):
          for task in self.tasks:  
               task.resume()
     def shutdown(self):
          self.pause_all()
          if hasattr(self, 'executor'):
               self.executor.shutdown(wait=False)
          sys.exit(0)
manager = DownloadManager()

def cli():
          while True:
               cmd = input(">>")
               if not cmd.strip():
                    continue
               parts = cmd.split()
               if parts[0] == "start" and len(parts) == 2:
                    if parts[1] == "all":
                         t = threading.Thread(target=manager.start_all)
                         t.start()
                    else:
                         manager.start_individual(parts[1])
                         
               elif parts[0] == "add" and len(parts) == 2:
                    url = parts[1]
                    UrlFinder("datanodes",[url]).queue_Url()
               elif parts[0] == "status" and len(parts) == 2:
                    if parts[1] == "all":
                         for task in manager.tasks:
                              if task.status != "Pending":
                                   print(task.get_status())
                    else:
                         for task in manager.tasks:
                              if task.uniqueChars == str(parts[1]):
                                   print(task.get_status())
                                   break
                         print("Task not found.")
                              
               elif cmd == "exit" or cmd == "quit":
                    manager.shutdown()
                    print("Exiting...")
                    break
               elif cmd == "help":
                    print("Commands:")
                    print("start all - Start all downloads")
                    print("start <id> - Start specific download")
                    print("pause - Pause all downloads")
                    print("pause <id> - Pause specific download")
                    print("resume - Resume all downloads")
                    print("resume <id> - Resume specific download")
                    print("status all - Show status of all downloads")
                    print("status <id> - Show status of specific download")
                    print("add <url> - Add URL to queue")
                    print("exit/quit - Exit the program")
               
               elif parts[0] == "pause" and len(parts) == 2:
                    found = False
                    for task in manager.tasks:
                         if task.uniqueChars == parts[1]:
                              task.pause()
                              found = True
                    if not found:
                         print("Task not found.")
               elif parts[0] == "resume" and len(parts) == 2:
                    found = False
                    for task in manager.tasks:
                         if task.uniqueChars == parts[1]:
                              task.resume()
                              found = True
                    if not found:
                         print("Task not found.")
               elif cmd == "pause":
                    manager.pause_all()
               elif cmd == "resume":
                    manager.resume_all()
               else:
                    print("Invalid command.")


class DownloadTask():
     def __init__(self,url,fname,downloaded=0,total_size=0,status="Pending",event=None):
          self.url = json.loads(urllib.parse.unquote(url))["url"]
          self.fname = fname
          self.status = status
          self.downloaded = downloaded
          self.total_size = total_size
          self.event = threading.Event()
          self.uniqueChars = str(uuid.uuid4())[:8]
     def check_resume(self):
          if os.path.exists(self.fname):
               return os.path.getsize(self.fname)
          else:
               self.status = "Downloading"
               return 0
     def resume(self):
          self.status = "Downloading"
          if self.event:
               self.event.set()
          print("Resuming download...")
     def download_retry(self, retries=3):
          for attempt in range(retries):
               try:
                    self.status = "Downloading" if attempt == 0 else "Retrying"
                    self.download()
                    if self.status == "COMPLETED":
                         return
               except Exception as e:
                    if attempt < retries - 1:
                         wait_time = 2 ** attempt
                         print(f"Attempt {attempt + 1} failed. Retrying in {wait_time}s...")
                         time.sleep(wait_time)
                    else:
                         self.status = "Failed"
                         print(f"Failed to download {self.fname} after {retries} attempts: {e}")
                         return    
     def download(self):
          try:
               print(f"Downloading {self.fname}...")
               start_byte = self.check_resume()
               self.downloaded = start_byte
               response = requests.get(self.url,headers={'Range': f'bytes={start_byte}-'},stream=True,timeout=(10,None))
               total_size = int(response.headers.get('content-length', 0))
               self.total_size = total_size
               with open(f"../{self.fname}",'ab') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                         if self.event and not self.event.is_set():
                              print("Download paused. Waiting to resume...")
                              self.event.wait()
                         self.downloaded += len(chunk)
                         f.write(chunk)
                         
               self.status = "COMPLETED"
          except Exception as e:
               raise  # Re-raise for retry logic to handle
                         
     def pause(self):
          self.status = "Paused"
          if self.event:
               self.event.clear()
          print("Download paused.")
     def get_progress(self):
          if self.total_size > 0:
               return (self.downloaded / self.total_size) * 100
          else:
               return 0
     def get_status(self):
          return f"{self.uniqueChars}: {self.status} - {self.get_progress():.2f}%"

class UrlFinder():
     def __init__(self,pluggin,Urls):
          self.Urls = Urls
          self.pluggin = pluggin
     def queue_Url(self):
          if self.pluggin == "datanodes":
               for item in self.Urls:
                    self.crawl_datanodes(item)
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
Urls = sys.argv[1:] 
Urls = Urls[0].split('\n')
urlfinder = UrlFinder("datanodes",Urls)
urlfinder.queue_Url()
cli()
# def downloadFile(url,fname):
#     decoded_url = urllib.parse.unquote(url)
#     downloadUrl = json.loads(decoded_url)["url"]
#     if os.path.exists(fname):
#         start_byte = os.path.getsize(fname)
#     else:
#          start_byte = 0
#     response = requests.get(downloadUrl,headers={'Range': f'bytes={start_byte}-'},stream=True)
#     total_size = int(response.headers.get('content-length', 0))
#     print(total_size)
#     with open(fname,'ab') as f:
#          for chunk in  tqdm.tqdm(response.iter_content(chunk_size=8192),total=total_sizes/1024,unit='KB'):
#             f.write(chunk)
#             if keyboard.is_pressed('q'):
#                 print("Download paused. Press 'r' to resume.")
#                 while True:
#                     if keyboard.is_pressed('r'):
#                         print("Resuming download...")
#                         break
            
# start_byte = 0
# def Urlfinder(item): 
#         toCrawl = item
#         dataFromUrl = toCrawl.split('/')
#         uniqueChars = dataFromUrl[3]
#         fname = dataFromUrl[4]
#         payload2 = {
#         "op": "download2",
#         "uniqueChars": f"{uniqueChars}",
#         "rand": "",
#         "referer": "https://fitgirl-repacks.site/",
#         "method_free": "Free Download >>",
#         "method_premium": "",
#         "g_captch__a": "1"}
#         down2 = s.post('https://datanodes.to/download',data=payload2)
#         url = down2.content
#         print(f"Queuing {fname}")
# payload = {
#     "op": "download1",
#     "usr_login": "",
#     "uniqueChars": f"{uniqueChars}",
#     "fname":f"{fname}",
#     "referer": "https://fitgirl-repacks.site/",
#     "method_free": "Free Download"
# }

# r = s.get('https://datanodes.to/vkbt2kwqfgex/Pizza_Slice_--_fitgirl-repacks.site_--_.part1.rar')
# print(requests.utils.dict_from_cookiejar(r.cookies))
# down1 = s.post('https://datanodes.to/download',payload)
# file = (down1.content)