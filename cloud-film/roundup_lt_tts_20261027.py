"""PUPIS SHORTS 2026-10-27 original 6-section Lithuanian combat-sports roundup.
Cloud-only TTS on free GitHub runner. Model RobertasTa/lt_LT-reginute1-medium.
CC BY 4.0 voice model; author attribution at publication.
No private data / no paid APIs. Sources listed in script manifest.
"""
import json, wave, hashlib, sys
from pathlib import Path
from huggingface_hub import snapshot_download
HERE=Path(__file__).resolve().parent
OUT=HERE/"output"/"roundup_20261027"
OUT.mkdir(parents=True,exist_ok=True)
VOICE_DIR=HERE/"reginute_voice"
SOURCES=[
 "https://www.lrt.lt/naujienos/sportas/10/3092130/gocmenas-sustabde-banski-po-nokdaunu-pasibaigusios-kovos-finale-susitiks-su-jemeljanovu",
 "https://www.tv3.lt/naujiena/sportas/gocmenas-pries-utma-finala-reze-tiesiai-sviesiai-jemeljanovo-laukia-nokautas-n1563389"
]
SECTIONS=[
{"id":"intro","text":"Keturi nokdaunai, atsisveikinimo pergalė ir penkiasdešimties tūkstančių eurų finalas! Tai Lietuvos kovinio sporto savaitės apžvalga."},
{"id":"pauliukevicius","text":"Vilniuje, UTMA dvidešimt turnyre, Ignas Pauliukevičius trečiajame raunde techniniu nokautu įveikė Naglį Kanišauską. Varžovas net keturis kartus atsidūrė nokdaune. Po kovos Pauliukevičius pasakojo rungtyniavęs nepaisydamas krūtinkaulio ir kelio traumų."},
{"id":"pakutinskas","text":"Veteranas Tomas Pakutinskas karjerą užbaigė pergale prieš Ioną Grigore. Pirmajame raunde pats patyrė nokdauną, tačiau atsitiesė, perėmė iniciatyvą ir po trijų raundų iškovojo pergalę. Įspūdingas atsisveikinimas!"},
{"id":"gedminas","text":"Mindaugas Gedminas teisėjų sprendimu nugalėjo Arnoldą Misiūną, o po kovos metė iššūkį Eimantui Stanioniui šešių raundų bokso susitikimui. Dominyką Dirkstį taip pat pakvietė į ringą. Kol kas tai tik kvietimai, ne pasirašytos sutartys."},
{"id":"finalas","text":"Deividas Jemeljanovas įveikė Rodrigo Mineiro, o Isa Gočmenas nugalėjo aštuoniolikmetį Tomą Banskį. Šie du finalininkai UTMA dvidešimt vienas turnyre kovos dėl čempiono diržo ir penkiasdešimties tūkstančių eurų prizo. Gočmenas jau viešai žada nokautą."},
{"id":"outro","text":"Kuri istorija labiausiai nustebino? Parašyk komentaruose. PUPIS SHORTS — Lietuvos kovinis sportas. Visos kovos scenos čia yra komiksinės rekonstrukcijos."}
]
print("VOICE_MODEL_DOWNLOAD",flush=True)
snapshot_download("RobertasTa/lt_LT-reginute1-medium",local_dir=str(VOICE_DIR))
sys.path.insert(0,str(VOICE_DIR))
from piper import PiperVoice
from phonemize_lithuanian import LithuanianPhonemizer
from skaiciu_pletiklis import isplesk
from synth_reginute import ReginuteSynth,i_int16
voice=PiperVoice.load(str(VOICE_DIR/"lt_LT-reginute1-medium.onnx"),config_path=str(VOICE_DIR/"lt_LT-reginute1-medium.onnx.json"))
synth=ReginuteSynth(voice,LithuanianPhonemizer(),length_scale=1.12,expand_text=isplesk)
for sec in SECTIONS:
    audio=synth.synthesize(sec["text"])
    fname=OUT/(sec["id"]+".wav")
    with wave.open(str(fname),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(synth.sr);f.writeframes(i_int16(audio))
    with wave.open(str(fname),"rb") as f:
        sec["duration_s"]=f.getnframes()/f.getframerate()
        sec["sample_rate"]=f.getframerate()
    sec["sha256"]=hashlib.sha256(fname.read_bytes()).hexdigest()
    sec["words"]=len(sec["text"].split())
    print("ROUNDUP_VOICE_SECTION",sec["id"],round(sec["duration_s"],2),flush=True)
DURATION=sum(x["duration_s"] for x in SECTIONS)
meta={"title":"Lietuvos kovinio sporto apžvalga 2026-10-27",
    "sections":SECTIONS,"total_narration_seconds":DURATION,
    "sources":SOURCES,
    "model":"RobertasTa/lt_LT-reginute1-medium",
    "voice_license":"CC BY 4.0","youtube_publishing_approved":False}
(OUT/"manifest.json").write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding="utf8")
print("ROUNDUP_VOICE_TOTAL",DURATION,flush=True)
if DURATION<59:
    raise RuntimeError("Narration shorter than 59s; no false one-minute PASS")
