"""PUPIS: independent zero-euro test of OFFICIAL LTX-2.5 public ZeroGPU I2V.
Use only the already-public, original fictional-character FLUX first frame.
No user PC, API key, payment, personal files, secrets or automatic YouTube upload.
Fails closed; if ZeroGPU requires auth/quota, report BLOCKED, not success.
"""
import json, os, time, traceback, shutil
from pathlib import Path
from gradio_client import Client, handle_file
import av

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"
OUT.mkdir(exist_ok=True)
SRC=OUT/"first_frame.png"
DEST=OUT/"PUPIS_LTX25_NATIVE_24FPS.mp4"
STATUS=OUT/"LTX25_ZERO_GPU_STATUS.json"
START=time.monotonic()
report={"engine":"official Lightricks/LTX-2.5 ZeroGPU Space",
        "zero_eur":True,"source_image":"first_frame.png / fictional original character",
        "requires_owner_pc":False,"completed":False,"error":None}
PROMPT=("A premium 2D animated graphic-novel boxing action shot, detailed hand-painted "
        "cinematic frame. Preserve EXACTLY the identity of the pictured ORIGINAL fictional "
        "boxer: distinctive dark hair with white streak, angular face, turquoise top and "
        "gold and cobalt boxing gloves. Real anatomical action and movement: he shifts "
        "his rear heel, turns his hips and shoulder, throws one short LEFT jab sharply "
        "toward camera, retracts the glove and lifts his guard, breathes and blinks. "
        "Articulated arms and natural inertia, crowd depth and floating ring dust under "
        "amber arena spotlights. Continuous motion, no loop, no sliding still photograph, "
        "no extra fingers or hands, no captions, no logos, no real athletes. "
        "Sound of one glove rushing past and a gym-room reverberation, no spoken words.")
try:
    if not SRC.is_file() or SRC.stat().st_size<10000:
        raise RuntimeError("Missing real original FLUX source from earlier verified run")
    print("LTX25_INITIALIZING_CLIENT",flush=True)
    client=Client("Lightricks/LTX-2.5",httpx_kwargs={"timeout":180.0})
    # The official app.py uses go.click(run, _INPUTS, _OUTPUTS), and its API
    # values correspond to: prompt,image,height,width,duration,seed,decoder,auto,
    # randomize,enhance.
    available=[str(k) for k in client.endpoints.keys()]
    print("LTX25_ENDPOINTS",available,flush=True)
    candidates=("/run","/generate","/predict")
    endpoint=next((name for name in candidates if name in available),None)
    if endpoint is None:
        # No speculative API calls: on contract drift, fail clearly.
        raise RuntimeError("Endpoint changed: "+str(available))
    print("LTX25_GENERATE",endpoint,flush=True)
    results=client.predict(
        PROMPT, handle_file(str(SRC)), 1472, 832, 2.0, 20261027,
        "conv", False, False, False, api_name=endpoint
    )
    print("LTX25_RESULT",repr(results)[:1200],flush=True)
    candidate=results[0] if isinstance(results,(tuple,list)) else results
    if isinstance(candidate,dict):
        path=candidate.get("path") or candidate.get("name") or candidate.get("url")
    else:path=candidate
    if not isinstance(path,str):raise RuntimeError("Output is not a video filename")
    local=Path(path)
    if not local.is_file():raise RuntimeError("Server result missing downloaded media: "+path)
    shutil.copy2(local,DEST)
    if DEST.stat().st_size<50000:raise RuntimeError("Generated file suspiciously small")
    with av.open(str(DEST)) as f:
        streams=f.streams
        vs=next((s for s in streams if s.type=="video"),None)
        aud=next((s for s in streams if s.type=="audio"),None)
        if vs is None: raise RuntimeError("No video stream")
        fps=float(vs.average_rate or 0)
        dur=float(f.duration or 0)/av.time_base
        report.update({
          "width":vs.codec_context.width,
          "height":vs.codec_context.height,
          "fps":round(fps,3),
          "duration_s":round(dur,3),
          "audio_stream":aud is not None,
          "size_bytes":DEST.stat().st_size,
          "video_codec":vs.codec_context.name,
          "completed":True,
        })
        if fps<23.5 or vs.codec_context.width<800 or vs.codec_context.height<1400:
            raise RuntimeError("Insufficient NATIVE output resolution or fps")
    print("LTX25_NATIVE_VIDEO_PASS",json.dumps(report),flush=True)
except Exception as ex:
    report["error"]=str(ex)[:1600]
    report["completed"]=False
    print("LTX25_NO_PASS",report["error"],flush=True)
finally:
    report["elapsed_seconds"]=round(time.monotonic()-START,2)
    STATUS.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
if not report["completed"]:raise SystemExit(2)
