from concurrent.futures import ThreadPoolExecutor
import os
import time
import json
import threading
class DownloadManager:
    def __init__(self, running=False):
        self.tasks = []
        self.running = running
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.futures = []
        self.meta_data = {}
        self.progress_running = False
    def add_task(self, task):
        self.tasks.append(task)

    def start_individual(self, uniqueChars):
        for task in self.tasks:
            if task.uniqueChars == uniqueChars:
                if task.status in ["Pending", "Paused"]:
                    print(f"Starting download for {task.fname}...")
                    task.event.set()
                    self.executor.submit(task.download)
                else:
                    print(task.status)
                return
        print("Task not found.")

    def start_all(self):
        if not self.tasks:
            print("No tasks queued")
            return
        for task in self.tasks:
            if task.status in ["Pending", "Paused"] and task.check_existence() == False:
                self.load_progress(task)
                task.event.set()
                self.executor.submit(task.download_retry)
                if not self.progress_running:
                    self.progress_running = True
                    threading.Thread(target=self.dump_progress,args=['back_ground'], daemon=True).start()  
            else: 
                print(task.get_status())       
    def load_progress(self,task):
        try:
            with open('meta_data.json', 'r') as f:
                meta_data = json.load(f)
            for i, task_data in meta_data.items():
                    if task.fname == task_data['fname']:
                        task.chunks_data = task_data['data']
                        task.status = task_data['status']
                        task.downloaded = task_data['downloaded']
            return True
        except FileNotFoundError:
            return False
    def pause_all(self):
        self.dump_progress('instant')
        for task in self.tasks:
            task.pause()
    def dump_progress(self,mode):
        tmp_path = 'meta_data.json.temp'
        final_path = 'meta_data.json'
        if mode != 'instant':
            while True:
                if self.progress_running == False:
                    return
                time.sleep(5)
                for i,task in enumerate(self.tasks):
                        self.meta_data[i] = {"data" : task.chunks_data,
                                            "fname":task.fname,
                                            "status":task.status,
                                            "downloaded":task.downloaded}
                with open(tmp_path,'w') as f:
                    json.dump(self.meta_data,f)
                os.replace(tmp_path,final_path)
        else:
            for i,task in enumerate(self.tasks):
                        self.meta_data[i] = {"data" : task.chunks_data,
                                            "fname":task.fname,
                                            "status":task.status,
                                            "downloaded":task.downloaded}
            with open(tmp_path,'w') as f:
                json.dump(self.meta_data,f)
            os.replace(tmp_path,final_path)

    def pause_individual(self, uniqueChars):
            for task in self.tasks:
                if task.uniqueChars == uniqueChars:
                    self.dump_progress('instant')
                    task.pause()
                    return
            print("Task not found.")

    def resume_all(self):
        for task in self.tasks:
            self.load_progress(task)
            task.resume()

    def resume_individual(self, uniqueChars):
        for task in self.tasks:
            if task.uniqueChars == uniqueChars:
                self.load_progress(task)
                task.resume()
                return
        print("Task not found.")

    def get_status(self):
        speeds = []
        sizes = []
        progresses = []
        for task in self.tasks:
            if task.status == "Downloading":
                items = task.get_status()
                speeds.append(items[2])

                print(
                    f"{items[0]}, "
                    f"status={task.status}, "
                    f"progress={items[1]:.2f}%, "
                    f"speed={items[2]:.2f} KB/s, "
                    f"eta={items[3]}"
                )

            sizes.append(int(task.total_size))
            progresses.append(int(task.downloaded))

        total_progress = sum(progresses)/1024
        total_size = sum(sizes)/1024
        total_speed = sum(speeds)

        print("\n--- Overall ---")
        print(f"Speed: {total_speed:.2f} KB/s")
        print(f'Total downloaded :{total_progress/1024}')
        print(f'Total size :{total_size/1024}')
        print(f'remaining{total_size/1024 - total_progress/1024}')

    def shutdown(self):
        for task in self.tasks:
            task.cancel()
        self.running = False
        self.executor.shutdown(wait=False)
        return

manager = DownloadManager()