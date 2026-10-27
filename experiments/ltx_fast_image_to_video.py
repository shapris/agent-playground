"""Single professional source-guided LTX Video Fast public ZeroGPU animation.
No paid API, login, subscription, local PC or private user material. Free public
original FLUX artwork, generated previously by PUPIS.
"""
import json, time, hashlib, requests
from pathlib import Path
import av
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"cloud-film"/"output"
OUT.mkdir(parents=True,exist_ok=True)
HOST="https://lightricks-ltx-video-distilled.hf.space"
SOURCE=OUT/"first_frame.png"
TARGET=OUT/"PUPIS_LTX_FAST_IMAGE_GUIDED_3S.mp4"
STATUS=OUT/"LTX_FAST_I2V_STATUS.json"
REPORT={"producer":"Lightricks LTX Video Fast official free ZeroGPU",
        "input":"Original FLUX comic boxer, no real persons",
        "cost_eur":0,"pc_used":False,"generation_proven":False,"error":None}
START=time.monotonic()
PROMPT=(
 "A beautiful frame-by-frame animation of the SAME illustrated boxer in the provided "
 "image. Preserve exactly his distinctive angular face, black hair with white streak, "
 "teal boxing kit and shiny yellow boxing gloves and the cinematic ring. A clear "
 "physical movement: he crouches with his weight on the rear leg, blinks, shifts "
 "his front foot, then fires one sharp LEFT JAB at the camera, rotating his "
 "shoulder and extending his elbow anatomically, then swiftly retracts into a "
 "tight guard. His other fist protects his face, torso weight shifts and his "
 "shorts and hair sway naturally. Cinematic high-detail 2D sports anime hand-inked "
 "graphic novel, real animated limbs, beautiful amber spotlights and crowd depth. "
 "No scene cut, no style change, no text, no subtitles, no camera-only zoom, no "
 "extra limbs, no other characters, no likeness of real people."
)
NEG=("blurry, deformed hands, extra arms, changing face, cartoon stick figures,"
     " frozen pose, slideshow, camera movement only, text, logo, watermark")

def run():
    if not SOURCE.exists() or SOURCE.stat().st_size<30000:
        raise RuntimeError("original FLUX artwork not available")
    REPORT["source_sha256"]=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    with SOURCE.open("rb") as f:
        rsp=requests.post(HOST+"/gradio_api/upload",
             files={"files":("source_boxer.png",f,"image/png")},timeout=(15,70))
    rsp.raise_for_status()
    remote_paths=rsp.json()
    if not isinstance(remote_paths,list) or not remote_paths:
        raise RuntimeError("Gradio did not provide uploaded source image")
    p=remote_paths[0]
    image={"path":p,"url":HOST+"/gradio_api/file="+p,
           "orig_name":"source_boxer.png","mime_type":"image/png",
           "meta":{"_type":"gradio.FileData"}}
    params=[PROMPT,NEG,image,None,896,512,"image-to-video",3,9,
            20261027,False,1,True]
    x=requests.post(HOST+"/gradio_api/call/image_to_video",
        json={"data":params},timeout=(15,60))
    x.raise_for_status()
    event=x.json().get("event_id")
    if not event:raise RuntimeError("no generation event ID")
    REPORT["job_submitted"]=True
    print("LTX_FREE_I2V_JOB_ACCEPTED",event,flush=True)
    event_kind=None
    video=None
    with requests.get(HOST+"/gradio_api/call/image_to_video/"+event,
                      headers={"Accept":"text/event-stream"},
                      stream=True,timeout=(15,250)) as r:
        r.raise_for_status()
        for raw_line in r.iter_lines(decode_unicode=True):
            if time.monotonic()-START>240:
                raise TimeoutError("Free ZeroGPU job exceeded safe 4 minute limit")
            if not raw_line:continue
            if raw_line.startswith("event:"):
                event_kind=raw_line[6:].strip()
            if raw_line.startswith("data:") and event_kind in ("complete","error"):
                result=json.loads(raw_line[5:].strip())
                if event_kind=="error":raise RuntimeError("Public Space error: "+str(result)[:450])
                first=result[0] if isinstance(result,list) and result else result
                if isinstance(first,dict) and "video" in first:first=first["video"]
                if isinstance(first,dict):
                    video=first.get("url")
                    if not video and first.get("path"):
                        video=HOST+"/gradio_api/file="+first["path"]
                elif isinstance(first,str):video=first
                break
    if not video or not str(video).startswith("http"):
        raise RuntimeError("No verified output video URL in provider completion")
    with requests.get(video,stream=True,timeout=(15,70)) as src:
        src.raise_for_status()
        with TARGET.open("wb") as dest:
            for chunk in src.iter_content(chunk_size=1024*512):
                dest.write(chunk)
    if TARGET.stat().st_size<30000:raise RuntimeError("Output MP4 is too small")
    frame_samples=[]
    frame_count=0
    with av.open(str(TARGET)) as container:
        v=next((s for s in container.streams if s.type=="video"),None)
        audio=any(s.type=="audio" for s in container.streams)
        if v is None:raise RuntimeError("no decoded video")
        dur=(container.duration or 0)/av.time_base
        fps=float(v.average_rate or 0)
        for fr in container.decode(video=0):
            frame_count+=1
            if frame_count in (1,10,25,40,60,80):
                frame_samples.append(fr.to_image().resize((205,360)))
        REPORT.update({"duration_s":round(dur,3),
            "fps":round(fps,3),
            "resolution":[v.codec_context.width,v.codec_context.height],
            "audio":audio,"frames_decoded":frame_count,"bytes":TARGET.stat().st_size,
            "output_sha256":hashlib.sha256(TARGET.read_bytes()).hexdigest()})
        if frame_count<32 or fps<20 or dur<1.5:
            raise RuntimeError("Output invalid, below minimum decode / frame requirements")
    if frame_samples:
        contact=Image.new("RGB",(205*len(frame_samples),360),"#181d2e")
        for i,img in enumerate(frame_samples):contact.paste(img,(i*205,0))
        contact.save(OUT/"LTX_FAST_IMAGE_GUIDED_REAL_FRAMES.png")
    REPORT["generation_proven"]=True
    print("LTX_FAST_I2V_REAL_MP4_PASS",json.dumps(REPORT),flush=True)

try:run()
except Exception as e:
    REPORT["error"]=str(e)
    print("LTX_FAST_I2V_UNPROVEN",str(e),flush=True)
finally:
    REPORT["elapsed_s"]=round(time.monotonic()-START,2)
    STATUS.write_text(json.dumps(REPORT,indent=2,ensure_ascii=False),encoding="utf8")
if not REPORT["generation_proven"]:raise SystemExit(2)
