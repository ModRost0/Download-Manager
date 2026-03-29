import time
import os
import requests
import threading
import urllib
import uuid
import json
from concurrent.futures import ThreadPoolExecutor
TEMP_EXT = ".unfinished"
s = requests.Session()
headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Encoding": "identity",
        "Connection": "keep-alive"
    }
s.headers.update(headers)
class DownloadTask():
    def __init__(self, url, fname, downloaded=0, total_size=0, status="Pending", event=None):
        try:
            self.url = json.loads(urllib.parse.unquote(url))["url"]
        except Exception as e:
            print(e)
            self.url = url
        self.speed = 0
        self.fname = fname
        self.status = status
        self.downloaded = downloaded
        self.total_size = total_size
        self.event = threading.Event()
        self.cancel_event = threading.Event()
        self.uniqueChars = str(uuid.uuid4())[:8]
        self.accepts_range_headers = None
        self.length_of_chunks = 0
        self.num_of_threads = 3
        self.lock = threading.Lock()
        self.event.set()
        self.executor = ThreadPoolExecutor(max_workers=self.num_of_threads)
        self.chunks_data = []
    def check_accepts_range_headers(self):
        try:
            res = s.head(self.url)
            return res.headers.get("Accept-Ranges", None)
        except Exception as e:
            print(e)
            response = s.get(self.url, stream=True, timeout=10)
            response.close()
            res = response.headers.get("Accept-Ranges", None)
            return res
    def resume(self):
        self.status = "Downloading"
        if self.event:
            self.event.set()
        print("Resuming download...")

    def get_eta(self):
        if self.speed > 0:
            eta = (self.total_size - self.downloaded) / self.speed
            return time.strftime("%H:%M:%S", time.gmtime(eta))

    def download_retry(self, retries=3):
        for attempt in range(retries):
            try:
                if self.cancel_event.is_set():
                    self.status = "Cancelled"
                    print("Download cancelled.")
                    return
                self.download()
                if self.status == "Completed" or self.status == "Cancelled":
                    return
            except Exception as e:
                if self.cancel_event.is_set():
                    self.status = "Cancelled"
                    print("Download cancelled.")
                    return
                self.status = 'Retrying'
                if attempt < retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Attempt {attempt + 1} failed. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    self.status = "Failed"
                    print(f"Failed after {retries} attempts: {e}")
    def check_existence(self):
        if(os.path.exists(f'../{self.fname}')):
            return True
        else:
            return False
    def download(self):
        try:
            bool_range = self.check_accepts_range_headers()
            if self.total_size == 0:
                self.initialize(self.num_of_threads)
            if bool_range != "bytes":
                    print(f"Downloading {self.fname}...")
                    response = s.get(self.url, stream=True, timeout=(10, None))
                    current_time = time.time()
                    current_size = 0
                    self.status = "Downloading"
                    with open(f"../{self.fname}{TEMP_EXT}", 'ab') as f:
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
                    os.rename(f"../{self.fname}{TEMP_EXT}", f"../{self.fname}")
                    self.status = "Completed"
            else:
                    print(self.chunks_data)
                    if self.status != 'Downloading' and self.status != 'Retrying':
                        for i in range(self.num_of_threads):
                            start = i * self.length_of_chunks
                            end = start + self.length_of_chunks - 1 if i < self.num_of_threads - 1 else self.total_size - 1
                            self.chunks_data.append([start, end])
                        self.status = 'Downloading'
                    threading.Thread(target=self.track_speed, daemon=True).start()
                    futures = []
                    for i, chunk in enumerate(self.chunks_data):
                        futures.append(self.executor.submit(self.download_chunk, chunk, i,))
                    for f in futures:
                        f.result()
                    if self.cancel_event.is_set():
                        self.status = "Cancelled"
                        print("Download cancelled.")
                        return
                    os.rename(f"../{self.fname}{TEMP_EXT}", f"../{self.fname}")
                    self.status = "Completed"
        except Exception as e:
            if self.cancel_event.is_set():
                self.status = "Cancelled"
                print("Download cancelled.")
                return
            print(f'download lvl {e}')
            raise
    def download_chunk(self, data, thread_num):
        try:
            print(f"Download_chunking {self.fname}")
            start = data[0]
            end = data[1]
            headers = {
                "Range": f"bytes={start}-{end}"
            }
            if self.cancel_event.is_set():
                return
            response = s.get(self.url, stream=True, headers=headers, timeout=(5,5 ))
            with open(f'../{self.fname}{TEMP_EXT}', 'r+b') as f:
                f.seek(start)
                for chunk in response.iter_content(1024 * 512):
                    if self.cancel_event.is_set():
                        response.close()
                        return
                    with self.lock:
                        f.write(chunk)
                        self.chunks_data[thread_num][0] += len(chunk)
                        self.downloaded += len(chunk)
        except Exception as e:
            print(f'chunk lvl {e}')
            raise
    def initialize(self, n):
        try:
            with open(f"../{self.fname}{TEMP_EXT}", 'wb') as f:
                length = int(s.head(self.url).headers.get('Content-Length', 0))
                self.total_size = length
                self.length_of_chunks = int(length // n)
                f.truncate(length)
        except Exception as e:
            with open(f"../{self.fname}{TEMP_EXT}", 'wb') as f:
                response = s.get(self.url, stream=True, timeout=10)
                response.close()
                self.total_size = response.headers.get('Content-Length', 0)
                self.length_of_chunks = int(self.total_size/n)
                f.truncate(self.total_size)
    def track_speed(self):
        last_downloaded = self.downloaded
        speeds = []

        while self.status == "Downloading":
            time.sleep(1)
            self.speed = self.downloaded - last_downloaded
            last_downloaded = self.downloaded
            speeds.append(self.speed)
            if len(speeds) > 10:
                speeds.pop(0)
            self.speed = (sum(speeds) / len(speeds))

    def pause(self):
        self.status = "Paused"
        self.event.clear()
    def get_progress(self):
        if self.total_size > 0:
            return (self.downloaded / self.total_size) * 100
        return 0
    def cancel(self):
        self.cancel_event.set()
        print("Cancelling download...")
        try:
            self.executor.shutdown(wait=False, cancel_futures=True)
        except:
            pass
        self.status = "Cancelled"  
    def get_status(self):
            return [
            self.uniqueChars,
            self.get_progress(),
            self.speed / 1024,
            self.get_eta()
        ]