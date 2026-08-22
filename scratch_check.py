import urllib.request
import re

try:
    html = urllib.request.urlopen("https://data-t-two.vercel.app").read().decode("utf-8")
    js_file = re.search(r'src="(/assets/index-[^"]*\.js)"', html).group(1)
    js_content = urllib.request.urlopen("https://data-t-two.vercel.app" + js_file).read().decode("utf-8")
    
    # Try to find what Vite replaced it with
    # It usually looks like: const e="https://unihack-backend.onrender.com"||"http://localhost:8000"
    match = re.search(r'="([^"]+)"\|\|"http://localhost:8000"', js_content)
    if match:
        print("Vite injected URL is:", match.group(1))
    else:
        # Check if the whole export is there
        print("Couldn't extract the exact URL, but here is a snippet near localhost:8000:")
        idx = js_content.find('localhost:8000')
        if idx != -1:
            start = max(0, idx - 50)
            end = min(len(js_content), idx + 30)
            print(js_content[start:end])
        else:
            print("localhost:8000 not found at all in the bundle.")
except Exception as e:
    print("Error:", e)
