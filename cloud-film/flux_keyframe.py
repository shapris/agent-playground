"""0 EUR professional keyframe from public Flux.2 Klein 4B ZeroGPU Space.
The still frame is an ORIGINAL imaginary fighter and is intended only as the input
to the independently proven Wan image-to-video trial. No billing or tokens.
Fail closed: never mislabel placeholder art as AI-generated.
"""
import json
import time
from pathlib import Path
import requests
from PIL import Image

BASE=Path(__file__).resolve().parent
OUT=BASE/"output"
OUT.mkdir(exist_ok=True)
HOST="https://black-forest-labs-flux-2-klein-4b.hf.space"
PROMPT=(
  "Premium cinematic painted 2D ANIMATED FILM KEYFRAME for original independent "
  "adult boxing sports comic movie, high-fidelity graphic novel still, "
  "full vertical portrait 9:16, stunning hand-drawn illustrative animation "
  "art direction, sophisticated anatomical drawing and richly painterly linework, "
  "not crude vector clip art. Original fictional adult boxer, three-quarter "
  "body visible, distinctive masculine face with sharp high cheekbones, "
  "dark hair tied in a short bun with one platinum-white streak, a subtle "
  "small left brow scar, muscular but believable build, turquoise sleeveless "
  "training outfit with dark navy edges, GOLDEN YELLOW AND COBALT boxing gloves. "
  "Fighter in dynamic low guard stance about to deliver a sharp jab, "
  "left shoulder forward, rear heel lifted, dramatic realistic weight shift, "
  "correctly drawn two arms and two gloves, five fingers inside gloves, "
  "no extra limbs. Immersive professional world-building: moody nighttime "
  "boxing ring, atmospheric turquoise haze, amber spotlights with rays, "
  "crowd bokeh, dramatic speed-line accents and volumetric painted dust. "
  "High-contrast heroic silhouette, cinematic camera angle, animation "
  "background artists quality, advanced hand-drawn compositing, beautiful "
  "carefully designed character face, gorgeous lighting and shadow patterns. "
  "Original character, no real sportspeople, no identifiable celebrity, "
  "no copied film franchise style. Absolutely NO text, no signs, no subtitles, "
  "no logo, no watermarks, no photographic stills."
)
STATUS={"model":"black-forest-labs/FLUX.2-klein-4B","backend":HOST,
        "source":"original fictional boxer","success":False,
        "budget_eur":0,"time_s":None,"error":None}

def sse_infer(endpoint, data, max_wait=270):
    start=time.monotonic()
    resp=requests.post(f"{HOST}/gradio_api/call/{endpoint}",
        json={"data":data},timeout=(15,80))
    resp.raise_for_status()
    event=resp.json().get("event_id")
    if not event:raise RuntimeError("no gradio event_id: "+resp.text[:300])
    print("FLUX_SUBMITTED",event,flush=True)
    event_type=""
    with requests.get(f"{HOST}/gradio_api/call/{endpoint}/{event}",
                      headers={"Accept":"text/event-stream"},
                      stream=True,timeout=(20,300)) as r:
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if time.monotonic()-start>max_wait:
                raise TimeoutError("free Gradio Space did not complete within limit")
            if not line:continue
            if line.startswith("event:"):
                event_type=line[6:].strip()
            if line.startswith("data:") and event_type in ("complete","error"):
                o=json.loads(line[5:].strip())
                if event_type=="error":raise RuntimeError("provider error: "+str(o)[:700])
                return o
    raise RuntimeError("stream closed without complete event")

def main():
    start=time.monotonic()
    print("FLUX_INFO_BEGIN",flush=True)
    info=requests.get(HOST+"/gradio_api/info",timeout=40)
    info.raise_for_status()
    data=info.json()
    named=data.get("named_endpoints") or {}
    print("FLUX_ENDPOINTS",list(named),flush=True)
    endpoint=("infer" if "/infer" in named else
              next((k.strip("/") for k,v in named.items()
                    if "infer" in k.lower()),None))
    if not endpoint:
        raise RuntimeError("No verified /infer API endpoint; abstaining")
    # Ten arguments in the precise Gradio 'gr.on' input order from the space app.py.
    values=[PROMPT,[],"Distilled (4 steps)",20261027,False,
            576,1024,4,1.0,False]
    result=sse_infer(endpoint,values)
    print("FLUX_RETURN_SUMMARY",str(result)[:950],flush=True)
    first=result[0] if isinstance(result,list) and result else result
    if isinstance(first,dict):
        url=first.get("url")
        if not url and first.get("path"):
            url=f"{HOST}/gradio_api/file="+first["path"]
    elif isinstance(first,str): url=first
    else: url=None
    if not url or not url.startswith(("https://","http://")):
        raise RuntimeError("No verified output image URL")
    rr=requests.get(url,timeout=(15,90))
    rr.raise_for_status()
    img=OUT/"first_frame.png"
    img.write_bytes(rr.content)
    im=Image.open(img)
    im.load()
    if im.width<512 or im.height<768:
        raise RuntimeError("generated image undersize %sx%s"%(im.width,im.height))
    if im.width>=im.height:
        raise RuntimeError("generated image is not portrait")
    if im.mode!="RGB":im=im.convert("RGB")
    im.save(img)
    STATUS.update({"success":True,"image_size":[im.width,im.height],
                   "output_path":str(img),"output_bytes":img.stat().st_size})
    print("FLUX_ORIGINAL_KEYFRAME_OK",im.size,img.stat().st_size,flush=True)
try:
    main()
except Exception as ex:
    STATUS["error"]=str(ex)[:1600]
    print("FLUX_ORIGINAL_KEYFRAME_FAILED",STATUS["error"],flush=True)
finally:
    STATUS["time_s"]=round(time.monotonic()-(globals().get("start") or time.monotonic()),2)
    (OUT/"FLUX_STATUS.json").write_text(json.dumps(STATUS,indent=2,ensure_ascii=False))
if not STATUS["success"]:
    raise SystemExit(2)
