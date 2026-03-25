import time
import os
import requests
import json
import threading
import urllib
import uuid
from concurrent.futures import ThreadPoolExecutor

TEMP_EXT = ".unfinished"

class DownloadTask():
    def __init__(self, url, fname, downloaded=0, total_size=0, status="Pending", event=None):
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
        self.event.set()
        self.executor = ThreadPoolExecutor(max_workers=self.num_of_threads)

    def check_existance(self):
        if os.path.exists(f"../{self.fname}.{TEMP_EXT}"):
            return os.path.getsize(f'../{self.fname}.{TEMP_EXT}')
        else:
            self.status = "Downloading"
            return 0

    def check_accepts_range_headers(self):
        res = requests.head(self.url)
        return res.headers.get("Accept-Ranges", None)

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
                response = requests.get(self.url, stream=True, timeout=(10, None))
                current_time = time.time()
                current_size = start_byte
                self.status = "Downloading"

                with open(f"../{self.fname}.unfinished", 'ab') as f:
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

                self.status = "Completed"

            else:
                self.status = "Downloading"
                self.chunks_data = []
                threading.Thread(target=self.track_speed, daemon=True).start()
                for i in range(self.num_of_threads):
                    start = i * self.length_of_chunks
                    end = start + self.length_of_chunks - 1 if i < self.num_of_threads - 1 else self.total_size - 1
                    self.chunks_data.append([start, end])
                futures = []
                
                for i, chunk in enumerate(self.chunks_data):
                    futures.append(self.executor.submit(self.download_chunk, chunk, i))

                for f in futures:
                    f.result()

                os.rename(f"../{self.fname}.{TEMP_EXT}", f"../{self.fname}")
                self.status = "Completed"
                self.executor.shutdown()

        except Exception as e:
            raise e

    def download_chunk(self, data, thread_num):
        print(f"Download_chunking {self.fname}")
        start = data[0]
        end = data[1]
        print(f'{start},{end},{thread_num}')

        headers = {
            "Range": f"bytes={start}-{end}"
        }

        response = requests.get(self.url, stream=True, headers=headers, timeout=(10, None))

        with open(f'../{self.fname}.{TEMP_EXT}', 'r+b') as f:
            f.seek(start)
            for chunk in response.iter_content(1024 * 1024):
                f.write(chunk)
                self.chunks_data[thread_num][0] += len(chunk)

                with self.lock:
                    self.downloaded += len(chunk)

    def initialize(self, n):
        with open(f"../{self.fname}.{TEMP_EXT}", 'wb') as f:
            length = int(requests.head(self.url).headers.get('Content-Length', 0))
            self.total_size = length
            self.length_of_chunks = int(length // n)
            f.truncate(length)

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
        if self.event:
            self.event.clear()
        print("Download paused.")

    def get_progress(self):
        if self.total_size > 0:
            return (self.downloaded / self.total_size) * 100
        return 0

    def get_status(self):
            return [
            self.uniqueChars,
            self.get_progress(),
            self.speed / 1024,
            self.get_eta()
        ]