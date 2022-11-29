import requests

captcha_img = open('captcha.png', 'rb')

url = 'http://captcha.newsoft.kr/'
files = {'file': captcha_img}
res = requests.post(url, files=files)
res.raise_for_status() # 문제시 프로그램 종료
res = res.json()

print(res)