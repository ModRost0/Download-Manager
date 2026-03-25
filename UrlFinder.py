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
          self.executor = ThreadPoolExecutor(max_workers=maxWorkers)
          for task in self.tasks:
               task.event.set()
               self.executor.submit(task.download)
     def pause_all(self):
          for task in self.tasks:
               task.pause()
     def pause_individual(self,uniqueChars):
          for task in self.tasks:
               if task.uniqueChars == uniqueChars:
                    task.pause()
                    return
          print("Task not found.")
     def get_status(self):
          return [t.get_status() for t in self.tasks if t.status == "Downloading"]
     def resume_all(self):
          for task in self.tasks:  
               task.resume()
     def resume_individual(self,uniqueChars):
          for task in self.tasks:
               if task.uniqueChars == uniqueChars:
                    task.resume()
                    return
          print("Task not found.")
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
                         for item in manager.get_status():
                              print(f'{item[0]}\nProgress : {item[1]} speed : {item[2]} eta : {item[3]}')  
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
               
               elif parts[0] == "pause":
                    if len(parts) == 1:
                         manager.pause_all()
                    else:
                         manager.pause_individual(parts[1])
               elif parts[0] == "resume":
                    if len(parts) == 1:
                         manager.resume_all()
                    else:
                         manager.resume_individual(parts[1])
               else:
                    print("Invalid command.")

class DownloadTask():
     def __init__(self,url,fname,downloaded=0,total_size=0,status="Pending",event=None):
          self.url = json.loads(urllib.parse.unquote(url))["url"]
          self.speed = 0
          self.fname = fname
          self.status = status
          self.downloaded = downloaded
          self.total_size = total_size
          self.event = threading.Event()
          self.uniqueChars = str(uuid.uuid4())[:8]
          self.accepts_range_headers = None
          self.download_chunk_per_thread = 0
          self.num_of_threads = 3
          self.lock = threading.Lock()
     def check_existance(self):
          if os.path.exists(f"../{self.fname}.Unfinished"):
               return(os.path.getsize(f'../{self.fname}.Unfinished'))
          else:
               self.status = "Downloading"
               return 0
     def check_accepts_range_headers(self):
          res = s.head(self.url)
          return res.headers.get("Accept-Ranges",None)
     def resume(self):
          self.status = "Downloading"
          if self.event:
               self.event.set()
          print("Resuming download...")
     def get_eta(self):
          if self.speed>0:
               eta = (self.total_size/1024 - self.downloaded/1024 )/ self.speed
               return time.strftime("%H:%M:%S", time.gmtime(eta))
     def download_retry(self, retries=3):
          for attempt in range(retries):
               try:
                    self.status = "Downloading" if attempt == 0 else "Retrying"
                    self.download()
                    if self.status == "Completed":
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
          if self.total_size == 0:
               self.initialize(3)
          try:
               if self.check_accepts_range_headers() != "bytes":
                    print(f"Downloading {self.fname}...")
                    start_byte = self.check_existance()
                    self.downloaded = start_byte
                    response = requests.get(self.url,stream=True,timeout=(10,None))
                    current_time = time.time()
                    current_size = start_byte
                    with open(f"../{self.fname}.unfinished",'ab') as f:
                         for chunk in response.iter_content(chunk_size=1024 * 1024):
                              if self.event and not self.event.is_set():
                                   print("Download paused. Waiting to resume...")
                                   self.event.wait()
                              self.downloaded += len(chunk)
                              f.write(chunk)
                              now = time.time()
                              elapsed = now - current_time
                              if elapsed >= 1:
                                   self.speed = (self.downloaded - current_size) / elapsed
                                   current_time = now
                                   current_size = self.downloaded
                    os.rename(f"../{self.fname}.Unfinished", f"../{self.fname}")       
                    self.status = "Completed"
               else:
                    print(f"Download_chunking {self.fname}")
                    self.status = "Downloading"
                    threads = []
                    for i in range(self.num_of_threads):
                         start = self.download_chunk_per_thread * (i)
                         download_chunk_per_thread = self.download_chunk_per_thread * (i+1)
                         if download_chunk_per_thread > self.total_size:
                              download_chunk_per_thread = self.total_size
                         if i == self.num_of_threads - 1:
                              download_chunk_per_thread = self.total_size
                         t = threading.Thread(target=self.download_chunk, args=(download_chunk_per_thread,start))
                         threads.append(t)
                         t.start()
                    threading.Thread(target=self.track_speed).start()
                    for t in threads:
                         t.join()
               os.rename(f"../{self.fname}.Unfinished", f"../{self.fname}")
               self.status = "Completed"                   
          except Exception as e:
               raise e
     def initialize(self,n):
            with open(f"../{self.fname}.Unfinished", 'wb') as f:
               length = int(requests.head(self.url).headers.get('Content-Length', 0))
               self.total_size = length
               self.download_chunk_per_thread = int(length//n)
               self.num_of_threads = n
               self.global_download_chunk_per_thread = self.download_chunk_per_thread
               f.truncate(length)
               f.close()
     def track_speed(self):
          last_downloaded = self.downloaded
          speeds = []
          while self.status == "Downloading":
               time.sleep(1)
               self.speed = self.downloaded - last_downloaded
               last_downloaded = self.downloaded
               speeds.append(self.speed/1024)
               if len(speeds) > 10:
                    speeds.pop(0)
               self.speed = (sum(speeds)/len(speeds))
     def download_chunk(self,download_chunk_per_thread,start):
          try:
               if self.check_existance() > 0:
                    start = start + self.check_existance()//4
               print(start)
               headers = {"Range":f"bytes={start}-{download_chunk_per_thread-1}"}
               res = requests.get(self.url, stream=True, headers=headers)
               with open(f"../{self.fname}.Unfinished", 'r+b') as f:
                    f.seek(start)
                    if download_chunk_per_thread == self.total_size:
                         chunk_size = 1024*128
                    else:
                         chunk_size = 1024*512
                    for chunk in res.iter_content(chunk_size):
                         if self.event and not self.event.is_set():
                              self.event.wait()
                         if chunk:
                              f.write(chunk)
                              with self.lock:
                                   self.downloaded += len(chunk)
          except Exception as e:
               print(e)
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
          if self.status == "Downloading":
               return [self.uniqueChars,self.get_progress(),self.speed,self.get_eta()]
          else:
               return
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