"""PUPIS SHORTS: free GitHub-hosted CPU puppet animation proof.
No personal data, paid APIs, subscriptions, account tokens, or public publishing.
This is a technical proof, NOT an approved news report.
"""
import math
import random
import subprocess
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE=Path(__file__).resolve().parent
OUT=BASE/"output"
OUT.mkdir(exist_ok=True)
W,H=540,960
FPS=24
DURATION=6
FRAMES=FPS*DURATION

def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"):
        try: return ImageFont.truetype(p,sz)
        except OSError: pass
    return ImageFont.load_default()

F_TITLE=font(28)
F_SMALL=font(16)
F_BRAND=font(23)
def pt(x,y):
    return (round(x),round(y))
def limb(d,a,b,color,w=26):
    a=pt(*a);b=pt(*b)
    d.line([a,b],fill="#080d1d",width=w+8,joint="curve")
    d.line([a,b],fill=color,width=w,joint="curve")
    for c in [a,b]:
        d.ellipse((c[0]-w//2,c[1]-w//2,c[0]+w//2,c[1]+w//2),fill=color,outline="#080d1d",width=3)
def glove(d,x,y,color,rot=0):
    d.ellipse((x-30,y-25,x+32,y+25),fill=color,outline="#061024",width=7)
    d.ellipse((x-11,y-23,x+14,y-11),fill="#ffffff",outline=None)
def boxer(d,x,y,color,skin,face=1,punch=0,duck=0,protect=0,sway=0):
    # face=1 looks right, face=-1 looks left; joints move independently of camera.
    headx=x+face*5+sway*9
    heady=y-163+duck*53
    chesty=y-65+duck*22
    hip=(x,y+66)
    lfoot=(x-52+duck*10,y+205)
    rfoot=(x+52+duck*15,y+198)
    limb(d,(x-20,y+58),(x-43+duck*7,y+142),color,31)
    limb(d,(x-43+duck*7,y+142),lfoot,color,26)
    limb(d,(x+21,y+53),(x+52+duck*15,y+129),color,31)
    limb(d,(x+52+duck*15,y+129),rfoot,color,28)
    d.rounded_rectangle((x-53,chesty-35,x+53,y+72),radius=24,fill=color,outline="#071021",width=7)
    d.line([(x,chesty-20),(x,y+40)],fill="#ffffff",width=3)
    d.rounded_rectangle((x-52,y+28,x+51,y+79),radius=8,fill="#13213a",outline="#071021",width=6)
    d.ellipse((headx-43,heady-49,headx+43,heady+43),fill=skin,outline="#080e1d",width=7)
    # brows and distinct facial expressions
    ex=headx+face*20
    d.line([pt(ex-face*8,heady-14),pt(ex+face*15,heady-19-duck*5)],fill="#0a1020",width=6)
    d.ellipse((ex-3,heady-12,ex+4,heady-4),fill="#0a1020")
    d.arc((min(headx-9,headx+face*31),heady-1,max(headx-9,headx+face*31),heady+22),20,150,fill="#0a1020",width=4)
    shoulder=(x+face*32,chesty-10)
    # rear defensive glove at near face, always alive with duck timing
    rear_elbow=(x-face*42,chesty+15+duck*13)
    rear_glove=(headx-face*45,heady+7+protect*8)
    limb(d,(x-face*28,chesty-12),rear_elbow,skin,21)
    limb(d,rear_elbow,rear_glove,skin,21)
    glove(d,*rear_glove,color)
    # attacking arm articulates: elbow flexes and wrist travels 120 px
    elbow=(x+face*(49+50*punch),chesty+3-15*punch)
    fist=(x+face*(67+149*punch),heady+39-48*punch)
    limb(d,shoulder,elbow,skin,24)
    limb(d,elbow,fist,skin,23)
    glove(d,*fist,color)
    if punch>0.30:
        gx,gy=fist
        for k in range(5):
            yy=gy+(-2+k)*13
            x1=gx-face*(65+20*punch+k*7)
            x2=gx-face*(30+13*punch)
            d.line([pt(x1,yy),pt(x2,yy-4)],fill="#fdf6ce",width=3)
    return fist

def pulse(t,at,width=0.32):
    z=(t-at)/width
    return math.exp(-z*z)
def frame(t):
    im=Image.new("RGB",(W,H),"#07152a")
    d=ImageDraw.Draw(im)
    # illustrated arena backdrop, spotlights and audience
    d.polygon([(0,0),(230,0),(88,630),(0,680)],fill="#15314f")
    d.polygon([(W,0),(318,0),(W,660)],fill="#331a42")
    d.ellipse((50,130,195,276),fill="#163f6c")
    d.ellipse((341,130,500,290),fill="#643443")
    for k in range(1,14):
        x=35+k*37
        d.line([(x,450),(x+math.sin(t*1.6+k)*8,530)],fill="#2a435a",width=8)
    # ring ropes: rear
    for y0 in [610,669,728]:
        d.line([(0,y0),(W,y0-38)],fill="#f4fafb",width=8)
        d.line([(0,y0+12),(W,y0-26)],fill="#213f5d",width=5)
    d.polygon([(0,775),(W,748),(W,930),(0,930)],fill="#19364a")
    for k in range(6):
        yy=785+k*26
        d.line([(0,yy),(W,yy-19)],fill="#254d64",width=2)
    pblue=max(pulse(t,1.58,.31),pulse(t,4.75,.28))
    pred=pulse(t,3.25,.32)
    redduck=pulse(t,1.70,.42)
    blueduck=pulse(t,3.35,.42)
    # blue boxer is in foreground after red boxer to ensure fists overlap
    boxer(d,372+12*math.sin(1.3*t),514+3*math.sin(3*t),
          "#ef4759","#dbb296",face=-1,punch=pred,duck=redduck,
          sway=math.sin(t*2.6))
    boxer(d,174+7*math.sin(1.7*t),520+5*math.sin(3.5*t),
          "#2388e9","#e4b997",face=1,punch=pblue,duck=blueduck,
          sway=math.sin(t*2.3))
    # impact flash and stars
    if pblue>.4:
        xx=355;yy=352
        rr=25+45*pblue
        for k in range(8):
            a=k*math.pi/4
            d.line([pt(xx+math.cos(a)*rr*.55,yy+math.sin(a)*rr*.55),
                    pt(xx+math.cos(a)*rr,yy+math.sin(a)*rr)],
                    fill="#fff4b1",width=5)
    if pred>.4:
        xx=192;yy=370;rr=20+43*pred
        for k in range(8):
            a=k*math.pi/4
            d.line([pt(xx+math.cos(a)*rr*.55,yy+math.sin(a)*rr*.55),
                    pt(xx+math.cos(a)*rr,yy+math.sin(a)*rr)],
                    fill="#ffe7cc",width=4)
    # headline overlays compact and readable
    d.rounded_rectangle((22,32,W-22,90),radius=14,fill="#07101d",outline="#ecb44f",width=3)
    d.text((39,43),"KOMIKSINĖ REKONSTRUKCIJA",font=F_TITLE,fill="#f2d58b")
    d.rounded_rectangle((20,866,W-20,925),radius=13,fill="#07101d",outline="#2d89e2",width=3)
    d.text((38,876),"PUPIS SHORTS  •  0 € CLOUD TEST",font=F_BRAND,fill="#f3f7fa")
    return im

def audio():
    sr=24000
    rng=random.Random(1902)
    with wave.open(str(OUT/"original_fx.wav"),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr)
        buf=bytearray()
        for k in range(DURATION*sr):
            t=k/sr
            s=0.0
            for at in (1.58,3.25,4.75):
                env=math.exp(-((t-at)/.09)**2)
                s+=env*(0.24*(rng.random()*2-1)+0.18*math.sin(2*math.pi*(90+110*abs(t-at))*t))
            s+=0.009*math.sin(2*math.pi*70*t)
            val=round(max(-0.80,min(0.80,s))*32767)
            buf.extend(val.to_bytes(2,"little",signed=True))
        w.writeframes(buf)

def main():
    audio()
    frame(0).save(OUT/"first_frame.png")
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
         "-r",str(FPS),"-i","pipe:0","-i",str(OUT/"original_fx.wav"),
         "-filter:v","scale=720:1280:flags=lanczos",
         "-c:v","libx264","-preset","veryfast","-crf","22",
         "-pix_fmt","yuv420p","-c:a","aac","-b:a","96k",
         "-shortest",str(OUT/"PUPIS_CLOUD_PUPPET_TEST.mp4")]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(FRAMES):
            proc.stdin.write(frame(i/FPS).tobytes())
        proc.stdin.close()
        code=proc.wait()
        if code: raise RuntimeError(f"ffmpeg failed: {code}")
    except Exception:
        proc.kill()
        raise
    print("CLOUD_PUPPET_MP4_OK")
if __name__=="__main__":main()
