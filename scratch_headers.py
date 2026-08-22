import urllib.request
response = urllib.request.urlopen("https://data-t-two.vercel.app")
print("Headers:")
print(response.headers)
