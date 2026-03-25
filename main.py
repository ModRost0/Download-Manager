import sys
import threading
from urlFinder import UrlFinder
from downloadManager import manager
Urls = sys.argv[1:] 
Urls = Urls[0].split('\n')
urlfinder = UrlFinder("datanodes",Urls)
urlfinder.queue_Url()
from cli import cli

cli()
