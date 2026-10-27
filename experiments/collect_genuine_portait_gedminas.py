"""Fetch original licensed Mindaugas Gedminas self-uploaded portrait; do not infer identity of other fighters."""
import urllib.request, pathlib, hashlib, json
p=pathlib.Path("licensed_media");p.mkdir(exist_ok=True)
url="https://upload.wikimedia.org/wikipedia/commons/f/ff/Mindaugas_Gedminas_in_2019.jpg"
request=urllib.request.Request(url,headers={"User-Agent":"PUPIS-Shorts-Editorial/1.0 (license provenance check)"})
with urllib.request.urlopen(request,timeout=45) as r:
    data=r.read()
if len(data)<30000 or not data.startswith(b"\\xff\\xd8"):
    raise RuntimeError("Original licensed JPEG did not download correctly")
(p/"Mindaugas_Gedminas_in_2019.jpg").write_bytes(data)
meta={"source":"https://commons.wikimedia.org/wiki/File:Mindaugas_Gedminas_in_2019.jpg",
      "creator":"Mindaugas Gedminas","license":"CC BY-SA 4.0",
      "license_url":"https://creativecommons.org/licenses/by-sa/4.0/",
      "description":"Photograph dated 2019. Sportsnews use with creator and modification attribution",
      "sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)}
(p/"ATTRIBUTION.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf8")
print("LICENSED_PORTRAIT_VERIFIED",meta,flush=True)
