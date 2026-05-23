import http.cookiejar, urllib.request, urllib.parse, json

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin123'}).encode()
opener.open('http://127.0.0.1:5001/login', data)
resp = opener.open('http://127.0.0.1:5001/api/qrcodes/all')
for qr in json.loads(resp.read().decode()):
    print(qr['url'])
