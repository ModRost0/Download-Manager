a very simple download manager, inspired from jdownloader2
to use it just excecute main.py <"links">
pluggins are built for reallyff and datanodes.in. it will auto-detect and download the files.(infamous for downloading repacks)
if the link isnt from these sites, it will download(i.e get request) directly from the link.

it has multithreaded download.---> if supported.
a empty file of requested size will be created.
each file will be divided according to set params(hardcoded in DownloadTasks.py for now). then that number of thread will begin downloading specific chunks of data. eg Thread 1 will download from 0 to 33%, Therad 2 from 33 to 66....
and there will be multiple files downloading.
everything can be adminstered from cli, use 'help' command to know more
its safe-locked so corruption chances are low(i think).


more pluggins will be added in future, its open-source
