"""PUPIS SHORTS cloud comic report V2: actual articulated animated characters + CC-BY LT narration.
Runs entirely on free CPU GitHub-hosted runner. No external photo or video assets.
This is an illustrative reconstruction, not real fight footage. NOT for auto-publication.
"""
import colorsys
import math
from pathlib import Path
import random
import subprocess
import sys
import wave
from PIL import Image, ImageDraw, ImageFont
import render as puppet

BASE=Path(__file__).resolve().parent
OUT=BASE/"output"
OUT.mkdir(exist_ok=True)
SR=22050
W,H=540,960
FPS=20
VOICE=OUT/"original_lt_narration.wav"
assert VOICE.exists(),"Create licensed Lithuanian narrator first!"
with wave.open(str(VOICE),"rb") as f:
    DURATION=f.getnframes()/f.getframerate()
if not (20<DURATION<85):
    raise RuntimeError("Unexpected TTS length: "+str(DURATION))
END=min(59.0,DURATION+0.35)
N=round(END*FPS)
print("REPORT_START duration %.3f frames %s"%(END,N),flush=True)

def font(size):
    opts=["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
          "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]
    for z in opts:
        try:return ImageFont.truetype(z,size)
        except OSError:pass
    return ImageFont.load_default()
FONTBIG=font(47);FONTMED=font(30);FONTSMALL=font(21);FONTXS=font(17);FONTHEAD=font(27)

def line(d,a,b,color,width=18):
    a=tuple(round(x) for x in a)
    b=tuple(round(x) for x in b)
    d.line([a,b],fill="#071528",width=width+8,joint="curve")
    d.line([a,b],fill=color,width=width,joint="curve")
    for pt in (a,b):
        r=width/2
        d.ellipse((pt[0]-r,pt[1]-r,pt[0]+r,pt[1]+r),
                  fill=color,outline="#071528",width=3)
def rr(d,rect,fill,r=22,outline="#071528",width=5):
    d.rounded_rectangle(rect,radius=r,fill=fill,outline=outline,width=width)

def bg(d,t,col1,col2,seed=0):
    d.rectangle((0,0,W,H),fill=col1)
    d.polygon([(0,0),(W*0.77,0),(0,H*.87)],fill=col2)
    d.polygon([(W,100),(W,800),(W*.57,520)],fill="#142342")
    for k in range(12):
        angle=k*math.pi/6+.05*math.sin(t*.7)
        l=780
        a=270+60*math.cos(angle)
        b=475+60*math.sin(angle)
        d.line([(a,b),(a+l*math.cos(angle),b+l*math.sin(angle))],
               fill="#2a4060",width=4)
    for i in range(50):
        xx=(i*101+seed*17)%W
        yy=(i*151+seed*71)%H
        r=2+(i%4)
        d.ellipse((xx-r,yy-r,xx+r,yy+r),fill="#324e6c")

def person(d,cx,cy,side,col,skin,hair,g,face=0.0,gesture=0.0,smirk=0.0):
    """Distinct stylized heads, breathing shoulders, articulated forearms."""
    bounce=math.sin(g*4+side*1.1)*4
    cx=cx+side*math.sin(g*1.5)*3
    cy=cy+bounce
    hip=(cx,cy+96)
    d.ellipse((cx-88,cy+32,cx+95,cy+220),fill="#0b1b2f",outline="#030b16",width=7)
    d.rounded_rectangle((cx-85,cy+35,cx+85,cy+203),radius=45,fill=col,outline="#030b16",width=9)
    d.line([(cx,cy+50),(cx,cy+186)],fill="#ffffff",width=4)
    # elbows and animated upper torso
    l_sh=(cx-59,cy+58);r_sh=(cx+59,cy+58)
    l_el=(cx-94-24*gesture,cy+130-50*gesture)
    l_hand=(cx-47-35*gesture,cy+20-95*gesture)
    r_el=(cx+92+15*gesture,cy+123-70*gesture)
    r_hand=(cx+35+53*gesture,cy+7-92*gesture)
    line(d,l_sh,l_el,skin,23);line(d,l_el,l_hand,skin,20)
    line(d,r_sh,r_el,skin,23);line(d,r_el,r_hand,skin,20)
    for hx,hy in (l_hand,r_hand):
        d.ellipse((hx-21,hy-20,hx+24,hy+23),fill="#f6ede4",outline="#081321",width=5)
    # Neck, actual moving head expression
    rr(d,(cx-18,cy-25,cx+19,cy+51),skin,r=12)
    d.ellipse((cx-61,cy-140,cx+65,cy-12),fill=skin,outline="#07101d",width=8)
    d.pieslice((cx-64,cy-151,cx+67,cy-37),180,359,fill=hair,outline="#07101d",width=6)
    # hairstyle shapes
    for i in range(4):
        offset=(-45+i*27)
        d.polygon([(cx+offset,cy-127),(cx+offset+13,cy-165-8*(i%2)),(cx+offset+30,cy-125)],
                  fill=hair)
    brow=-18-9*face
    d.line([(cx-45,cy-83),(cx-9,cy-86+brow*.15)],fill="#07101d",width=6)
    d.line([(cx+13,cy-87+brow*.15),(cx+49,cy-83)],fill="#07101d",width=6)
    for dx in (-28,29):
        d.ellipse((cx+dx-5,cy-81,cx+dx+5,cy-69),fill="#101321")
    # mouth shape reacts when gesture or smirk changes
    my=cy-45
    mw=17+8*smirk
    d.arc((cx-mw,my-6,cx+mw,my+20+10*smirk),5 if smirk>0 else 200,155 if smirk>0 else 335,fill="#081321",width=5)
    return (cx,cy)

def chip(d,x,y,text,fill="#ffdc6b",width=480):
    rr(d,(x,y,x+width,y+61),fill,r=14,outline="#07101d",width=5)
    d.text((x+16,y+10),text,font=FONTHEAD,fill="#09172a")

def intro(d,t,p):
    bg(d,t,"#091a38","#263466",1)
    # two active foils, speed streaks and changing glove positions
    g=math.sin(t*8)
    d.ellipse((160,350,395,586),fill="#192e4b",outline="#efaa59",width=12)
    for side,x,col in ((1,158,"#3c90fb"),(-1,385,"#e9535f")):
        yy=515+math.sin(t*4+x)*11
        d.ellipse((x-38,yy-45,x+38,yy+45),fill=col,outline="#ffffff",width=7)
        d.line([(x,yy),(x+side*(55+60*math.sin(t*6)**2),yy-28)],fill="#fef4cd",width=14)
    d.text((35,180),"VIENA PERGALĖ",font=FONTBIG,fill="#ffffff")
    d.text((35,252),"DU IŠŠŪKIAI",font=FONTBIG,fill="#ffd675")
    d.text((35,310),"IR REAKCIJOS!",font=FONTBIG,fill="#f7696c")
    d.text((54,615),"Spalio 24-oji, 2026",font=FONTMED,fill="#ffffff")

def bout(d,t,p):
    # reuse already physically tested articulated boxer animation, but crop to hide old branding
    frame=puppet.frame((t*2.1)%6)
    d.bitmap((0,0),Image.new("1",(W,H)),fill=None) if False else None
    # return frame to composite directly; animate own venue headline
    return frame

def podium(d,t,p):
    bg(d,t,"#06192c","#174b53",2)
    person(d,265,486,1,"#238bd0","#d6a584","#1f1820",t,
           gesture=.22+.48*(math.sin(t*4)+1)/2)
    chip(d,24,170,"GEDMINAS NUGALĖJO",fill="#ffd16a",width=492)
    for k in range(8):
        y=350+(k*73+t*30)%350
        x=(k*77+math.sin(t*3+k)*15)%W
        d.polygon([(x,y-15),(x+8,y),(x,y+18),(x-8,y)],fill="#fbe7aa")
    d.text((70,745),"3 RAUNDAI",font=FONTBIG,fill="#ffffff")
    d.text((88,815),"TEISĖJŲ SPRENDIMAS",font=FONTSMALL,fill="#ffd16a")

def challenge(d,t,p):
    bg(d,t,"#12203d","#263965",3)
    gest=(math.sin(t*3)+1)/2
    person(d,202,520,1,"#287fbe","#d6a884","#21141a",t,gesture=gest)
    d.rounded_rectangle((305,250,515,450),radius=25,fill="#f5e9d2",outline="#071021",width=7)
    d.polygon([(305,417),(273,456),(342,431)],fill="#f5e9d2")
    d.text((326,279),"IŠŠŪKIS!",font=FONTMED,fill="#0b203a")
    d.text((322,340),"6 RAUNDAI",font=FONTSMALL,fill="#be303d")
    d.text((72,762),"STANIONIUI",font=FONTBIG,fill="#ffd66f")
    d.text((72,825),"IR DIRKSČIUI",font=FONTMED,fill="#ffffff")

def reaction(d,t,p,name):
    stan=name=="STANIONIS"
    col=("#7f335e" if stan else "#1f6e68")
    bg(d,t,"#101b31",col,5 if stan else 6)
    shade=("#dc5c68" if stan else "#2eb0a5")
    person(d,274,520,1,shade,
           "#dfb99e" if stan else "#c58f68",
           "#1d1720" if stan else "#201c17",
           t,gesture=.1+.4*(math.sin(t*3.7)+1)/2,
           smirk=.1 if stan else .8)
    if stan:
        for k,(v,x,y) in enumerate([("?!",32,205),("!",435,265),("?!",375,720)]):
            sway=math.sin(t*4+k)*16
            d.ellipse((x,y+sway,x+100,y+100+sway),fill="#ffdc6c",outline="#08132b",width=6)
            d.text((x+16,y+15+sway),v,font=FONTBIG,fill="#0d1a30")
    else:
        rr(d,(24,205,510,310),"#f8e6cc",r=32)
        d.text((60,222),"IRONIŠKAS ATSAKAS",font=FONTMED,fill="#0a2035")
    d.text((60,756),name,font=FONTBIG,fill="#ffffff")
    d.text((55,828),"PAVIEŠINTA REAKCIJA",font=FONTSMALL,fill="#fee3a1")

def split(d,t,p):
    bg(d,t,"#091831","#25265e",7)
    d.polygon([(0,0),(W//2+35,0),(W//2-35,H),(0,H)],fill="#153d5e")
    d.polygon([(W//2+35,0),(W,0),(W,H),(W//2-35,H)],fill="#61334c")
    sway=math.sin(t*3.1)
    person(d,130,570,1,"#358fd1","#e1b89d","#1a121a",t,.28+.12*sway)
    person(d,415,570,-1,"#db5064","#cb927a","#281b1e",t,.25-.12*sway)
    for x,y in [(222,290),(292,355),(240,430)]:
        d.polygon([(x,y),(x+36,y+15),(x+9,y+60),(x+21,y+28)],fill="#ffe2a0")
    chip(d,30,180,"KOVOS NEPATVIRTINTOS",fill="#fbd98b",width=483)

def closer(d,t,p):
    bg(d,t,"#0b1831","#24456d",9)
    gl=(math.sin(t*4)+1)/2
    d.arc((74,180,470,675),45+gl*5,295-gl*5,fill="#f6cf71",width=20)
    d.rounded_rectangle((147,400,394,520),radius=37,fill="#df525e",outline="#ffe09d",width=14)
    d.text((184,426),"RINGAS?",font=FONTBIG,fill="#ffffff")
    d.text((45,677),"KĄ PAMATYTUM",font=FONTMED,fill="#ffffff")
    d.text((54,730),"RINGE TU?",font=FONTBIG,fill="#ffd36d")
    d.text((48,816),"ŠALTINIAI: UTMA / LRT / TV3",font=FONTSMALL,fill="#ffffff")

def draw_overlay(d,t,scene):
    # persistent exact disclosure and unobtrusive publisher brand
    rr(d,(17,15,523,85),"#081626",r=15,outline="#ffd46c",width=3)
    d.text((32,27),"KOMIKSINĖ REKONSTRUKCIJA",font=FONTHEAD,fill="#ffd46c")
    # not actual footage, explicit
    rr(d,(14,893,525,947),"#061225",r=12,outline="#2e90c8",width=3)
    d.text((37,902),"PUPIS SHORTS  •  NE REALI KOVA",font=FONTXS,fill="#ffffff")
    d.rectangle((0,955,round(W*min(1,t/END)),959),fill="#fbd17c")

BEATS=[
  (.00,.095,intro),
  (.095,.26,bout),
  (.26,.40,podium),
  (.40,.56,challenge),
  (.56,.69,lambda d,t,p:reaction(d,t,p,"STANIONIS")),
  (.69,.82,lambda d,t,p:reaction(d,t,p,"DIRKSTYS")),
  (.82,.93,split),
  (.93,1.01,closer)
]
def render_at(t):
    p=t/END
    lo,hi,fn=next((a,b,f) for a,b,f in BEATS if p>=a and p<b)
    q=(p-lo)/(hi-lo)
    if fn==bout:
        im=bout(None,t,q)
        d=ImageDraw.Draw(im)
        d.text((46,165),"KOVA RINGE",font=FONTBIG,fill="#ffffff",stroke_width=3,stroke_fill="#08203e")
        d.text((42,232),"SIMBOLINIS VAIZDAS",font=FONTSMALL,fill="#ffd67c")
    else:
        im=Image.new("RGB",(W,H),"#06111d")
        d=ImageDraw.Draw(im)
        fn(d,t,q)
    draw_overlay(d,t,fn)
    # subtle 3-frame white cut flash at the start of each new scene
    if q<.025 and lo>0:
        alpha=round((.025-q)*13/.025)
        if alpha>0:
            flash=Image.new("RGB",(W,H),"#ffffff")
            im=Image.blend(im,flash,min(.16,alpha/100))
    return im

out=OUT/"PUPIS_SHORTS_CLOUD_2D_NEWS_OWNER_REVIEW.mp4"
cmd=["ffmpeg","-y","-hide_banner","-loglevel","error",
     "-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
     "-r",str(FPS),"-i","pipe:0",
     "-i",str(VOICE),
     "-filter_complex","[0:v]scale=720:1280:flags=lanczos[v]",
     "-map","[v]","-map","1:a:0","-c:v","libx264",
     "-preset","veryfast","-crf","21","-pix_fmt","yuv420p",
     "-c:a","aac","-b:a","128k","-af","loudnorm=I=-17:TP=-1.5:LRA=8",
     "-shortest",str(out)]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
try:
    for i in range(N):
        p.stdin.write(render_at(i/FPS).tobytes())
        if i and i%180==0:print("render frames",i,"of",N,flush=True)
    p.stdin.close()
    code=p.wait(timeout=120)
    if code:raise RuntimeError("FFmpeg failed "+str(code))
except BaseException:
    p.kill()
    raise
render_at(END*.57).save(OUT/"scene_stanionis.png")
render_at(END*.75).save(OUT/"scene_dirkstys.png")
print("LT_NEWS_REPORT_COMPLETE",out,out.stat().st_size,flush=True)
