import base64
import os
import re

html_path = r'c:\Users\lp4mdaeniker\Desktop\python\news_learning\index.html'
assets_dir = r'c:\Users\lp4mdaeniker\Desktop\python\news_learning\assets'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

matches = re.findall(r'"assets/([^"]+\.png)"', html)
print(f"Found {len(set(matches))} unique asset references.")

count = 0
for m in set(matches):
    img_path = os.path.join(assets_dir, m)
    if os.path.exists(img_path):
        with open(img_path, 'rb') as img:
            b64 = "data:image/png;base64," + base64.b64encode(img.read()).decode('utf-8')
            html = html.replace(f'"assets/{m}"', f'"{b64}"')
            count += 1
            print(f"Injected base64 for {m}")
    else:
        print(f"Warning: {m} not found in assets dir!")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
    
print(f"Successfully injected {count} images.")
