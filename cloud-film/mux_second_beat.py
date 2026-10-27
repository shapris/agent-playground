"""Join two actually AI-generated moving scenes, with original short sound design.
No fake stretch, looping or still-image filler. Media is a private OWNER REVIEW
prototype only, not a real UTMA fight and never published automatically.
"""
import json,subprocess,wave,math,random
import av
import imageio_ffmpeg
from pathlib import Path
BASE=Path(__file__).resolve().parent
OUT=BASE/"output"
A=OUT/"PUPIS_WAN_ZERO_GPU_3S.mp4"
B=OUT/"PUPIS_WAN_SECOND_BEAT_3S.mp4"
assert A.stat().st_size>50000 and B.stat().st_size>50000

def metadata(f):
    with av.open(str(f)) as container:
        stream=next(s for s in container.streams if s.type=="video")
        return {"format":{"duration":round((container.duration or 0)/av.time_base,5)},
                "streams":[{"codec_type":"video","width":stream.codec_context.width,
                            "height":stream.codec_context.height}]} 
FFMPEG=imageio_ffmpeg.get_ffmpeg_exe()
m1,m2=metadata(A),metadata(B)
for m in (m1,m2):
    stream=next(s for s in m["streams"] if s["codec_type"]=="video")
    assert stream["width"]==480 and stream["height"]==832
D1=float(m1["format"]["duration"]);D2=float(m2["format"]["duration"])
duration=D1+D2
print("CLOUD_ORIGINAL_SCENE_DURATIONS",D1,D2,flush=True)
sr=24000
rng=random.Random(20261027)
target=OUT/"handmade_boxing_fx.wav"
with wave.open(str(target),"wb") as w:
    w.setframerate(sr);w.setnchannels(1);w.setsampwidth(2)
    buf=bytearray()
    for i in range(math.ceil(duration*sr)):
        t=i/sr
        val=0.0
        # subtle dark cinematic ambience
        val+=0.009*math.sin(2*math.pi*74*t)
        for moment in (0.66, 1.11, D1+0.9, D1+1.7):
            d=t-moment
            attack=math.exp(-(d/.11)**2)
            val+=attack*(0.12*(2*rng.random()-1)+0.17*math.sin(2*math.pi*100*d))
        val=max(-0.72,min(0.72,val))
        buf.extend(round(val*32767).to_bytes(2,"little",signed=True))
    w.writeframes(buf)
out=OUT/"PUPIS_CINEMATIC_2_ACTIONS_6S.mp4"
cmd=[FFMPEG,"-hide_banner","-loglevel","error","-y",
     "-i",str(A),"-i",str(B),"-i",str(target),
     "-filter_complex","[0:v]fps=16,format=yuv420p[v0];"
      "[1:v]fps=16,format=yuv420p[v1];"
      "[v0][v1]concat=n=2:v=1:a=0,"
      "scale=720:1280:flags=lanczos[v]",
     "-map","[v]","-map","2:a:0","-c:v","libx264","-crf","19","-preset","medium",
     "-r","16","-pix_fmt","yuv420p",
     "-c:a","aac","-b:a","128k","-shortest",str(out)]
subprocess.run(cmd,check=True,timeout=130)
subprocess.run([FFMPEG,"-v","error","-i",str(out),"-f","null","-"],check=True,timeout=60)
info=metadata(out)
assert float(info["format"]["duration"])>=5.8
(OUT/"TWO_BEAT_STATUS.json").write_text(json.dumps({
    "source_1_seconds":D1,"source_2_seconds":D2,
    "both_real_AI_generated_clips":True,
    "output_mp4":str(out),"duration":float(info["format"]["duration"]),
    "owner_approved":False,"budget_eur":0
},indent=2),encoding="utf8")
print("CINEMATIC_TWO_BEAT_VIDEO_OK",out.stat().st_size,flush=True)
