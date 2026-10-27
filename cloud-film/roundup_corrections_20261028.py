"""Repair edition of 83-second report:
new LT pronunciation-aware narration, original licensed real boxer portrait.
No falsified faces. The source portrait is Wikimedia Commons CC BY-SA 4.0.
Zero paid services or user PC. Keep original and attribution.
"""
import json, wave, sys, hashlib, urllib.request
from pathlib import Path
from huggingface_hub import snapshot_download
BASE=Path(__file__).resolve().parent
OUT=BASE/"output"/"roundup_corrected"
OUT.mkdir(exist_ok=True,parents=True)
MODEL_DIR=BASE/"reginute_voice"
SOURCE_PHOTO="https://upload.wikimedia.org/wikipedia/commons/f/ff/Mindaugas_Gedminas_in_2019.jpg"
PHOTO_PAGE="https://commons.wikimedia.org/wiki/File:Mindaugas_Gedminas_in_2019.jpg"
# Rephrased to shorten syntactically difficult sentences; names isolated by brief breaks.
TEXT={
"intro":"Keturi nokdaunai. Paskutinė veterano kova. Ir penkiasdešimt tūkstančių eurų kovinio sporto finale. Lietuvos kovinio sporto apžvalga.",
"pauliukevicius":"Vilniuje, turnyre UTMA dvidešimt, Ignas Pauliukevičius, trečiajame raunde techniniu nokautu, įveikė Naglį Kanišauską. Kanišauskas patyrė keturis nokdaunus. Po kovos Pauliukevičius prabilo apie krūtinkaulio ir kelio traumas.",
"pakutinskas":"Tomas Pakutinskas atsisveikino su profesionaliu ringu pergale prieš Ioną Grigore. Pirmąjį raundą Pakutinskas pats patyrė nokdauną. Tačiau atsitiesė, atgavo iniciatyvą ir nugalėjo po trijų raundų.",
"gedminas":"Mindaugas Gedminas, teisėjų sprendimu, nugalėjo Arnoldą Misiūną. Po kovos jis pakvietė Eimantą Stanionį į šešių raundų bokso susitikimą. Taip pat iškvietė Dominyką Dirkstį. Tačiau sutartos kovos dar nėra.",
"finalas":"Deividas Jemeljanovas nugalėjo Rodrigo Mineiro. Isa Gočmenas įveikė jaunąjį Tomą Banskį. Abu sportininkai pateko į UTMA finalą, kuriame laukia penkiasdešimties tūkstančių eurų prizas ir čempiono diržas. Gočmenas viešai pažadėjo nokautą. Tai pažadas, ne kovos baigtis.",
"outro":"Kuri istorija tave nustebino labiausiai? Parašyk komentaruose. PUPIS SHORTS. Lietuvos kovinis sportas. Rodomi komiksiniai kadrai yra iliustracijos, o ne tikros kovos filmuota medžiaga."
}
# Asset licensing note is always retained with the raw image; attribution on screen in final edit.
req=urllib.request.Request(SOURCE_PHOTO,headers={"User-Agent":"PUPIS-SHORTS-editorial/1.0 (Wikimedia CC BY-SA attribution)"})
with urllib.request.urlopen(req,timeout=55) as x: data=x.read()
if not data.startswith(b"\xff\xd8") or len(data)<20000:raise RuntimeError("Image bytes invalid")
(OUT/"Mindaugas_Gedminas_in_2019_CC_BY_SA_4_0.jpg").write_bytes(data)
print("LICENSED_FACE_DOWNLOADED",len(data),flush=True)
snapshot_download("RobertasTa/lt_LT-reginute1-medium",local_dir=str(MODEL_DIR))
sys.path.insert(0,str(MODEL_DIR))
from piper import PiperVoice
from phonemize_lithuanian import LithuanianPhonemizer
from skaiciu_pletiklis import isplesk
from synth_reginute import ReginuteSynth,i_int16
voice=PiperVoice.load(str(MODEL_DIR/"lt_LT-reginute1-medium.onnx"),config_path=str(MODEL_DIR/"lt_LT-reginute1-medium.onnx.json"))
synth=ReginuteSynth(voice,LithuanianPhonemizer(),length_scale=1.10,expand_text=isplesk)
meta=[]
for k,v in TEXT.items():
    audio=synth.synthesize(v)
    name=OUT/(k+".wav")
    with wave.open(str(name),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(synth.sr);f.writeframes(i_int16(audio))
    with wave.open(str(name),"rb") as f: seconds=f.getnframes()/f.getframerate()
    meta.append({"name":k,"text":v,"duration":seconds,"sha256":hashlib.sha256(name.read_bytes()).hexdigest()})
    print("VOICE",k,round(seconds,2),flush=True)
j={"segments":meta,"total_narration_s":sum(x["duration"] for x in meta),
   "real_photo":{"subject":"Mindaugas Gedminas","source":PHOTO_PAGE,
    "original_url":SOURCE_PHOTO,"license":"CC BY-SA 4.0",
    "author":"Mindaugas Gedminas (Wikimedia Commons file description)",
    "sha256":hashlib.sha256(data).hexdigest()},
   "voice_model":"RobertasTa/lt_LT-reginute1-medium","voice_license":"CC BY 4.0",
   "human_pronunciation_review":"UNKNOWN","youtube_publication":False}
(OUT/"license_and_narration_manifest.json").write_text(json.dumps(j,ensure_ascii=False,indent=2))
print("TOTAL_AUDIO_SECONDS",j["total_narration_s"],flush=True)
