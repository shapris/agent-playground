#!/usr/bin/env python3
"""PUPIS release gate: measurable tech QA + explicit rights/owner evidence.
Does NOT certify subjective art, does NOT publish, never enables billing.
"""
import argparse
import json
import subprocess
from pathlib import Path
from fractions import Fraction

MIN_WIDTH=1080
MIN_HEIGHT=1920
MIN_FPS=24.0
MIN_DURATION=30.0
MAX_DURATION=60.0

def ffprobe(path):
    cmd=['ffprobe','-v','error','-show_entries',
         'format=duration,size:stream=codec_name,codec_type,width,height,r_frame_rate',
         '-of','json',str(path)]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=30,check=True)
    return json.loads(p.stdout)

def analyze(probe,evidence):
    streams=probe.get('streams') or []
    video=next((s for s in streams if s.get('codec_type')=='video'),{})
    audio=next((s for s in streams if s.get('codec_type')=='audio'),{})
    d=float((probe.get('format') or {}).get('duration',0))
    w=int(video.get('width',0));h=int(video.get('height',0))
    try: fps=float(Fraction(video.get('r_frame_rate','0/1')))
    except (ZeroDivisionError,ValueError): fps=0.0
    reasons=[]
    if not video:reasons.append('NO_VIDEO_STREAM')
    if not audio:reasons.append('NO_AUDIO_STREAM')
    if not h or w<MIN_WIDTH or h<MIN_HEIGHT or abs(w/h-9/16)>.015:
        reasons.append('INSUFFICIENT_PORTRAIT_RESOLUTION')
    if fps<MIN_FPS:reasons.append('FRAME_RATE_UNDER_24')
    if d<MIN_DURATION or d>MAX_DURATION:reasons.append('INVALID_SHORTS_DURATION')
    if video.get('codec_name') not in ('h264','hevc','av1'):reasons.append('NONSTANDARD_VIDEO_CODEC')
    if audio.get('codec_name') not in ('aac','opus'):reasons.append('NONSTANDARD_AUDIO_CODEC')
    # Independent editorial and art evidence. Neither ffprobe nor job SUCCESS is approval.
    if evidence.get('source_facts_verified') is not True:reasons.append('FACTS_NOT_PROVEN')
    if evidence.get('media_rights_verified') is not True:reasons.append('MEDIA_RIGHTS_NOT_PROVEN')
    if evidence.get('voice_audition')!='pass':reasons.append('VOICE_NATURALNESS_NOT_AUDITIONED')
    if evidence.get('distinct_character_designs',0)<3:reasons.append('CHARACTER_DESIGNS_NOT_DISTINCT')
    if evidence.get('original_motion')!='verified':reasons.append('ARTICULATED_MOTION_NOT_PROVEN')
    owner=evidence.get('owner_verdict','UNKNOWN').upper()
    if owner=='REJECTED':reasons.append('OWNER_REJECTED')
    if evidence.get('creative_review')!='pass':reasons.append('CREATIVE_REVIEW_NOT_PASSED')
    return {'gate':'REJECTED' if 'OWNER_REJECTED' in reasons
            else 'BLOCKED' if reasons else 'TECH_QA_AND_CREATIVE_REVIEW_PASSED_AWAIT_OWNER_APPROVAL',
            'publish_approved':False,'owner_verdict':owner,
            'media':{'width':w,'height':h,'fps':round(fps,3),'duration_s':round(d,3),
                     'video_codec':video.get('codec_name'),'audio_codec':audio.get('codec_name')},
            'findings':reasons,'number_of_failures':len(reasons),
            'warning':'Frame count or ffprobe SUCCESS is NOT professional quality. NEVER publish.'}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--video',required=True)
    p.add_argument('--evidence',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--expect',choices=['REJECTED','BLOCKED',
                   'TECH_QA_AND_CREATIVE_REVIEW_PASSED_AWAIT_OWNER_APPROVAL'])
    args=p.parse_args()
    evidence=json.loads(Path(args.evidence).read_text(encoding='utf-8'))
    try:result=analyze(ffprobe(Path(args.video)),evidence)
    except Exception as ex:result={'gate':'BLOCKED','publish_approved':False,
                                  'findings':['MEDIA_PROBE_FAILED'],'error':str(ex)}
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if args.expect:
        if result['gate']!=args.expect:
            raise SystemExit('REGRESSION FAILED expected '+args.expect+', got '+result['gate'])
        print('EXPECTED_QUALITY_GATE_'+args.expect)
    elif result['gate']!='TECH_QA_AND_CREATIVE_REVIEW_PASSED_AWAIT_OWNER_APPROVAL':
        raise SystemExit(2)
if __name__=='__main__':main()
