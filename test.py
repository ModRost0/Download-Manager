import requests
import threading
download_chunk_per_thread= 0
start = 0
url = url = "https://tunnel1.dlproxy.uk/download/EWiKZrMPaTbypxhWPBhYijrGt8Hq2Vq0g2NpxYv1er13UPcm6KB_0SymFBQ_dkJ2LTxhNdndwSHk9edhNeoMyoODI_Bh4GNyJE5ZQ--tqVYwvF6oK2flNn9CCDE9dJca1lkWILa73xF1IA23oR1mvLJBDPu-iJG42hoYTtJj9kJeOpGrtNFrYA7o89NJsBE3X0tPd0ZrBinXc6wqPQX7z3amMITB4tsBv26xTHCy8WRalb3IGExzaQhlok9x40tPaIauQQLaCQxceKj-tO1WpWY9NKGWbEPBR6ETGuJ9zjEq5Sa0fVG20YKLmqXyPJJuaDUA1Ai14GvRMVXSmL7HpAFxUoo10h0ErjvmM5B9ZAGEiX48lXyTV4oAGkrTQyEivD9w3CemC5oiY4M6VnlRO4mCoTKAoOWtHg2Hjbqr-y9ftqCyOPkm5ekZYEUBbexgfFEvrS2LqhaTYCFVs-QOfkRMyP9xn0qMpybbP4l3_lfX_C9-JMgPD-pIxUO__V5N3pr3nFQnfzTc4UvWhWP2E8FsanWDzw8USzP-EuMt92v68x3RbH4ieJCMcsqCFQbVcPQ2zSyo9XT4S_lT4UsStwrLjyZqRj0eJBRUiYSKmJVxpEothYJdae8aDpIQ-40-bFGhrn8NCV79HhTcS_4R6g?sig=u5rPBpAHaMT6GtVLho8l4lp-6fNjOLvmM1KHsYnNw0Q"
with open("test.txt", 'wb') as f:
    length = int(requests.head(url).headers.get('Content-Length', 0))
    print(length)
    download_chunk_per_thread = int(length//4)
    new_download_chunk_per_thread = download_chunk_per_thread
    f.truncate(length)
    f.close()
def download_chunk(url,download_chunk_per_thread,start):
    if download_chunk_per_thread > length :
        download_chunk_per_thread = length
    headers = {"Range":f"bytes={start}-{download_chunk_per_thread-1}"}
    res = requests.get(url, stream=True, headers=headers)
    with open(f"test.txt", 'r+b') as f:
        f.seek(start)
        print(f"Starting download for bytes {start} to {download_chunk_per_thread}")
        print(f"Initial file position: {f.tell()} bytes")
        for chunk in res.iter_content(chunk_size=999):
            if chunk:
                f.write(chunk)
                print(f"Current file position: {f.tell()} bytes")
#10000byts
#2500
for i in range(4):
    print(f"Starting {i}")
    threading.Thread(target=download_chunk, args=(url,new_download_chunk_per_thread,start)).start()
    start = new_download_chunk_per_thread
    new_download_chunk_per_thread = download_chunk_per_thread*(i+2)
    