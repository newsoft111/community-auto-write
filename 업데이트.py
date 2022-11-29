import requests
print("업데이트중")
url = 'http://marco.newsoft.kr/커뮤니티 매크로.exe'
file = requests.get(url, allow_redirects=True)
open('커뮤니티 매크로.exe', 'wb').write(file.content)