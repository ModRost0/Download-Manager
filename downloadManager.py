from concurrent.futures import ThreadPoolExecutor

class DownloadManager:
    def __init__(self, running=False):
        self.tasks = []
        self.running = running
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.futures = {}
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
        if self.running:
            print("Already running")
            return

        if not self.tasks:
            print("No tasks queued")
            return

        self.running = True

        for task in self.tasks:
            if task.status in ["Pending", "Paused"]:
                task.event.set()
                self.executor.submit(task.download)
    def pause_all(self):
        for task in self.tasks:
            task.pause()

    def pause_individual(self, uniqueChars):
        for task in self.tasks:
            if task.uniqueChars == uniqueChars:
                task.pause()
                return
        print("Task not found.")

    def resume_all(self):
        for task in self.tasks:
            task.resume()

    def resume_individual(self, uniqueChars):
        for task in self.tasks:
            if task.uniqueChars == uniqueChars:
                task.resume()
                return
        print("Task not found.")

    def get_status(self):
        for task in self.tasks:
            if task.status == "Downloading":
                items = task.get_status()
                print(
                f"{items[0]}, "
                f"status={task.status}, "
                f"progress={items[1]:.2f}%, "
                f"speed={items[2]:.2f} KB/s, "
                f"eta={items[3]}")

    def shutdown(self):
        self.pause_all()
        self.running = False
        self.executor.shutdown(wait=False)

manager = DownloadManager()