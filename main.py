import sys
from concurrent.futures import ThreadPoolExecutor
from urlFinder import UrlFinder
from cli import cli
Urls = sys.argv[1:] 
Urls = Urls[0].split('\n')
UrlFinder(Urls).queue_Url()
cli()
