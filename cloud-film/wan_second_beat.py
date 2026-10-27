"""One follow-on animated beat from same verified FLUX original image.
No personal data, API tokens, paid inference or private media.
"""
import json,time,requests
from pathlib import Path

BASE=Path(__file__).resolve().parent
OUT=BASE/"output"
OUT.mkdir(exist_ok=True)
HOST="https://cbensimon-wan2-2-fp8da-aoti-preview2.hf.space"
PROMPT=("Hand-drawn graphic novel cinematic CHARACTER ANIMATION, same fictional "
 "adult boxer from reference still, same distinctive hair and face with white hair "
 "streak, gold gloves, turquoise outfit, same ring background and lights. "
 "He now performs a dynamic authentic boxing defense-to-counter: bends his knees, "
 "ducks his head and shoulders, weaves to his left, shifts his back foot, "
 "then performs a sharp rising RIGHT UPPERCUT, elbow properly bent, glove "
 "traveling upward close to his body, and returns to guard. Clearly actual "
 "articulated sequential character movement, not pans or zooms. Dramatic "
 "hand-drawn animation quality, cinematic anatomy, professional choreography, "
 "natural coherent arms, one single character, no real fighter likeness, "
 "no logos, no overlays, no captions.")
NEG="extra hands, extra fingers, deformed anatomy, morphing clothing, duplicate heads, text, still picture, camera-only pan"
STATUS={"model_proved":False,"source":"same original FLUX.2 keyframe","budget_eur":0,"error":None}
START=time.monotonic()

def run():
    img=OUT/"first_frame.png"
    if not img.exists():raise RuntimeError("source frame not downloaded")
    with img.open("rb") as f:
        r=requests.post(HOST+"/gradio_api/upload",files={"files":("source.png",f,"image/png")},timeout=60)
    r.raise_for_status()
    remote=r.json()[0]
    data={"path":remote,"url":HOST+"/gradio_api/file="+remote,"orig_name":"source.png",
          "size":None,"mime_type":"image/png","meta":{"_type":"gradio.FileData"}}
    params=[data,None,PROMPT,4,NEG,3.0,1,1,20261027,False,6,
            "UniPCMultistep",3.0,16,False,True]
    resp=requests.post(HOST+"/gradio_api/call/generate_video",json={"data":params},timeout=70)
    resp.raise_for_status()
    event=resp.json().get("event_id")
    if not event:raise RuntimeError("no event id")
    print("WAN_SECOND_BEAT_QUEUED",event,flush=True)
    event_type=""
    with requests.get(HOST+"/gradio_api/call/generate_video/"+event,
                     headers={"Accept":"text/event-stream"},stream=True,timeout=(20,180)) as r:
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if time.monotonic()-START>185:raise TimeoutError("free GPU exceeded trial wait")
            if not line:continue
            if line.startswith("event:"):event_type=line[6:].strip()
            if line.startswith("data:") and event_type in ("complete","error"):
                reply=json.loads(line[5:].strip())
                if event_type=="error":raise RuntimeError("HF free GPU error: "+str(reply)[:500])
                v=reply[0] if isinstance(reply,list) and reply else None
                url=v if isinstance(v,str) else v.get("url") if isinstance(v,dict) else None
                if not url and isinstance(v,dict) and v.get("path"):
                    url=HOST+"/gradio_api/file="+v["path"]
                if not url or not url.startswith("http"):raise RuntimeError("no valid movie URL")
                rr=requests.get(url,timeout=90);rr.raise_for_status()
                fn=OUT/"PUPIS_WAN_SECOND_BEAT_3S.mp4";fn.write_bytes(rr.content)
                if fn.stat().st_size<20000:raise RuntimeError("MP4 suspiciously small")
                STATUS.update({"model_proved":True,"bytes":fn.stat().st_size,"file":str(fn)})
                print("WAN_SECOND_BEAT_OK",fn.stat().st_size,flush=True)
                return
    raise RuntimeError("video stream ended without result")

try:run()
except Exception as e:
    STATUS["error"]=str(e)[:950]
    print("SECOND_BEAT_NOT_PROVEN",STATUS["error"],flush=True)
finally:
    STATUS["seconds"]=round(time.monotonic()-START,2)
    (OUT/"SECOND_BEAT_STATUS.json").write_text(json.dumps(STATUS,indent=2),encoding="utf-8")
if not STATUS["model_proved"]:raise SystemExit(2)
