"""Single zero-cost, anonymous, public ZeroGPU image-to-video trial.
No API tokens, purchases, signup, secrets, user files, or paid hardware.
Source app: https://huggingface.co/spaces/cbensimon/wan2-2-fp8da-aoti-preview2
API contract independently checked from MIT project IgorCSIS/nifty-vid.
One submit only. On failure: report UNKNOWN/FAILED; never mislabel fallback as AI.
"""
import json
import os
import sys
import time
from pathlib import Path
import requests

BASE=Path(__file__).resolve().parent
OUT=BASE/"output"
BASE_URL="https://cbensimon-wan2-2-fp8da-aoti-preview2.hf.space"
START=time.monotonic()
report={"backend":"public HF ZeroGPU / Wan2.2","model_proved":False,
        "budget_usd":0,"error":None,"source":"original symbolic illustrated frame"}
def log(msg):
    print(msg,flush=True)
def generate():
    png=OUT/"first_frame.png"
    if not png.exists():raise RuntimeError("missing local original first_frame.png")
    with png.open("rb") as f:
        u=requests.post(BASE_URL+"/gradio_api/upload",
                        files={"files":("first_frame.png",f,"image/png")},
                        timeout=(20,65))
    u.raise_for_status()
    paths=u.json()
    if not paths or not isinstance(paths,list):raise RuntimeError("bad upload result")
    src=paths[0]
    inp={"path":src,"url":BASE_URL+"/gradio_api/file="+src,
         "orig_name":"first_frame.png","size":None,
         "mime_type":"image/png","meta":{"_type":"gradio.FileData"}}
    negative="still image, bad anatomy, extra fingers, blurred subjects, text artifacts"
    # Fixed input order observed in the public Space's Gradio contract; check failures.
    params=[inp,None,"A genuine two-dimensional cartoon fight animation, moving elbows and hands: the blue boxer extends a strong straight jab, the red boxer ducks and shifts his feet. Animated body and glove motion, clearly distinct from moving the camera. No real people, no logos.",4,negative,3.0,1,1,42,True,6,
            "UniPCMultistep",3.0,16,False,True]
    r=requests.post(BASE_URL+"/gradio_api/call/generate_video",
                    json={"data":params},timeout=(20,70))
    r.raise_for_status()
    ev=r.json().get("event_id")
    if not ev:raise RuntimeError("no event_id")
    log("WAN_JOB_QUEUED event_id="+str(ev))
    url=BASE_URL+"/gradio_api/call/generate_video/"+ev
    with requests.get(url,headers={"Accept":"text/event-stream"},stream=True,
                      timeout=(20,140)) as resp:
        resp.raise_for_status()
        label=""
        for line in resp.iter_lines(decode_unicode=True):
            if time.monotonic()-START>175:
                raise TimeoutError("free public GPU trial reached max wait")
            if not line:
                continue
            if line.startswith("event:"):
                label=line[6:].strip()
            if line.startswith("data:") and label in ("complete","error"):
                value=json.loads(line[5:].strip())
                if label=="error":raise RuntimeError("remote generation error: "+str(value)[:350])
                d=value[0] if isinstance(value,list) and value else None
                vid=d if isinstance(d,str) else d.get("url") if isinstance(d,dict) else None
                if not vid and isinstance(d,dict) and d.get("path"):
                    vid=BASE_URL+"/gradio_api/file="+d["path"]
                if not vid or not vid.startswith(("https://","http://")):
                    raise RuntimeError("remote response missing playable video URL")
                with requests.get(vid,stream=True,timeout=(20,65)) as f:
                    f.raise_for_status()
                    target=OUT/"PUPIS_WAN_ZERO_GPU_3S.mp4"
                    with target.open("wb") as dest:
                        for chunk in f.iter_content(chunk_size=1024*1024):
                            dest.write(chunk)
                if target.stat().st_size<8000:
                    raise RuntimeError("download appears too small")
                log("WAN_VIDEO_CREATED "+str(target.stat().st_size))
                return str(target)
    raise RuntimeError("free public stream ended without complete")

try:
    OUT.mkdir(exist_ok=True)
    video=generate()
    report["model_proved"]=True
    report["video_path"]=video
except Exception as e:
    report["error"]=str(e)[:1000]
    log("WAN_TRIAL_NOT_PROVEN "+report["error"])
finally:
    report["elapsed_seconds"]=round(time.monotonic()-START,2)
    (OUT/"WAN_TRIAL_STATUS.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
