"""Retrieve original LTX Video Fast result from authorized public free ZeroGPU run.
No private media, accounts, tokens or payment. Independently verify real motion.
"""
from pathlib import Path
import urllib.request, hashlib, json
import av
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"
OUT.mkdir(parents=True,exist_ok=True)
URL="https://lightricks-ltx-video-distilled.hf.space/gradio_api/file=/tmp/gradio/35703e6ef39de6afc314b063db3c38b13a460e40f1f25a9fd112170ee7140cb7/output_30054.mp4"
DEST=OUT/"PUPIS_LTX_FAST_ORIGINAL_2S_20261027.mp4"
req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0 PUPIS-Editorial-QA/1.0"})
with urllib.request.urlopen(req,timeout=55) as r,open(DEST,"wb") as w:
    while True:
        block=r.read(1024*512)
        if not block:break
        w.write(block)
if DEST.stat().st_size<30000:raise RuntimeError("Provider output missing or suspiciously small")
with av.open(str(DEST)) as c:
    vids=[s for s in c.streams if s.type=="video"]
    auds=[s for s in c.streams if s.type=="audio"]
    if not vids:raise RuntimeError("Not a real MP4 with video")
    v=vids[0]
    duration=c.duration/av.time_base if c.duration is not None else 0
    fps=float(v.average_rate or 0)
    frame_count=0
    samples=[]
    for frame in c.decode(video=0):
        frame_count+=1
        if frame_count in (1,round(fps*.5),round(fps*1),round(fps*1.5),round(fps*1.9)):
            samples.append(frame.to_image().resize((216,384)))
    meta={"video":str(DEST),"size_bytes":DEST.stat().st_size,
          "duration_s":duration,"width":v.codec_context.width,"height":v.codec_context.height,
          "fps":fps,"frame_count_decoded":frame_count,
          "audio_stream":bool(auds),"sha256":hashlib.sha256(DEST.read_bytes()).hexdigest(),
          "confirmed_public_cloud_provider":"Lightricks/LTX Video Fast ZeroGPU",
          "owner_approved":False,"youtube_published":False,"paid_service_used":False}
    if frame_count<16 or duration<1.5:raise RuntimeError("Incomplete media decode")
    if samples:
        canvas=Image.new("RGB",(216*len(samples),384),"#222")
        for i,img in enumerate(samples):canvas.paste(img,(i*216,0))
        canvas.save(OUT/"LTX_FAST_REAL_FRAMES_QA.png")
    (OUT/"LTX_FAST_REAL_QA.json").write_text(json.dumps(meta,indent=2,ensure_ascii=False))
    print("ORIGINAL_LTX_FAST_CLOUD_VIDEO_PROVED",json.dumps(meta),flush=True)
