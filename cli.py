from urlFinder import UrlFinder
from downloadManager import manager

def cli():
    while True:
        cmd = input(">>").strip()
        if not cmd:
            continue

        parts = cmd.split()
        command = parts[0]
        args = parts[1:]

        if command == "start":
            if len(args) == 0 or args[0] == "all":
                manager.start_all()
            elif len(args) == 1:
                manager.start_individual(args[0])
            else:
                print("Usage: start [all|id]")

        elif command == "add":
            if len(args) == 1:
                UrlFinder("datanodes", [args[0]]).queue_Url()
            else:
                print("Usage: add <url>")

        elif command == "status":
            if len(args) == 0 or args[0] == "all":
                manager.get_status()
            elif len(args) == 1:
                for task in manager.tasks:
                    if task.uniqueChars == args[0]:
                        print(task.get_status())
                        break
                else:
                    print("Task not found.")
            else:
                print("Usage: status <id|all>")

        elif command in ["exit", "quit"]:
            manager.shutdown()
            print("Exiting...")
            break

        elif command == "help":
            print("Commands:")
            print("start all")
            print("start <id>")
            print("pause")
            print("pause <id>")
            print("resume")
            print("resume <id>")
            print("status all")
            print("status <id>")
            print("add <url>")
            print("exit/quit")

        elif command == "pause":
            if len(args) == 0 or args[0]== "all":
                manager.pause_all()
            elif len(args) == 1:
                manager.pause_individual(args[0])
            else:
                print("Usage: pause [id]")

        elif command == "resume":
            if len(args) == 0 or args[0]== "all":
                manager.resume_all()
            elif len(args) == 1:
                manager.resume_individual(args[0])
            else:
                print("Usage: resume [id]")

        else:
            print("Invalid command.")
cli()