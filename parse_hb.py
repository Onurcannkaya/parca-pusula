import json, re

with open('hb.html', 'r', encoding='utf-8') as f:
    t = f.read()

m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', t, re.DOTALL)
print("NEXT_DATA:", bool(m))

if m:
    try:
        data = json.loads(m.group(1))
        props = data.get('props', {}).get('initialState', {})
        print("initialState keys:", list(props.keys()))
        srz = props.get('search', {}).get('searchResults', {}).get('products', [])
        print("products in initialState search:", len(srz))
    except Exception as e:
        print("error NEXT_DATA:", e)

m2 = re.search(r'window\[\'__initialState\'\]\s*=\s*({.*?});', t, re.DOTALL)
if not m2:
    m2 = re.search(r'window\.__initialState\s*=\s*({.*?});', t, re.DOTALL)

print("window.__initialState:", bool(m2))
if m2:
    try:
         st = json.loads(m2.group(1))
         print("keys in state:", list(st.keys()))
         products = st.get('search', {}).get('searchResults', {}).get('products', [])
         print("products from searchResults:", len(products))
         
         if products:
             print("First product sample:")
             p = products[0]
             print("Name:", p.get('name'))
             print("Price:", p.get('price', {}).get('value'))
             print("Image:", p.get('image'))
    except Exception as e:
         print("Error:", e)
