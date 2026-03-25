import requests

url = "https://www.youtube.com/youtubei/v1/get_watch?prettyPrint=false"

response = requests.post("https://api.vidssave.com/api/contentsite_api/media/parse",{"link":"https://youtu.be/csjtgP96AZo?si=KOhVC7Sn335zC4Qb"})
print(response.status_code)
print(response.__dict__)