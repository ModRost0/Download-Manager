import sys
from concurrent.futures import ThreadPoolExecutor
from urlFinder import UrlFinder
from cli import cli
Urls = sys.argv[1:] 
Urls = Urls[0].split('\n')
urlFinder = UrlFinder("datanodes",Urls)
# url_test = "https://nbg1-speed.hetzner.com/100MB.bin"
# urlFinder = UrlFinder("normal",[url_test])
urlFinder.queue_Url()
cli()
