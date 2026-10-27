"""CC BY 4.0 Lithuanian voice proof for PUPIS SHORTS.
Source: RobertasTa/lt_LT-reginute1-medium (voice CC BY 4.0);
helper source GPL-3.0, used as an external program (not copied into this repo).
Generated script is editorial prose, not a quote.
"""
import json
import os
from pathlib import Path
import sys
import wave
from huggingface_hub import snapshot_download

HERE=Path(__file__).resolve().parent
OUT=HERE/"output"
OUT.mkdir(exist_ok=True)
VOICE_DIR=HERE/"reginute_voice"
MODEL_REPO="RobertasTa/lt_LT-reginute1-medium"

TEXT=(
    "Viena pergalė. Du garsūs iššūkiai. Ir reakcijos, kurios užkūrė "
    "Lietuvos kovinio sporto diskusijas. "
    "Spalio dvidešimt ketvirtąją, UTMA turnyre, Mindaugas Gedminas "
    "po trijų raundų teisėjų sprendimu nugalėjo Arnoldą Misiūną. "
    "Tačiau tikrasis triukšmas prasidėjo po kovos. "
    "Gedminas pasiūlė Eimantui Stanioniui šešių raundų bokso susitikimą. "
    "Taip pat iškvietė Dominyką Dirkstį. "
    "Stanionis sureagavo iškalbingais jaustukais, o Dirkstys atsikirto ironiškai. "
    "Gedminas vėliau patikslino, kad Stanionį gerbia, bet nori su juo "
    "išbandyti jėgas ringe. "
    "Kol kas tai tik iššūkiai. Kovų sutartys nepatvirtintos. "
    "O kurį susitikimą labiausiai norėtum pamatyti tu?"
)
(OUT/"editorial_script_lt.txt").write_text(TEXT,encoding="utf-8")
print("Downloading voice model to ephemeral GitHub worker...",flush=True)
snapshot_download(MODEL_REPO,local_dir=str(VOICE_DIR))
sys.path.insert(0,str(VOICE_DIR))
from piper import PiperVoice
from phonemize_lithuanian import LithuanianPhonemizer
from skaiciu_pletiklis import isplesk
from synth_reginute import ReginuteSynth,i_int16

model=VOICE_DIR/"lt_LT-reginute1-medium.onnx"
config=VOICE_DIR/"lt_LT-reginute1-medium.onnx.json"
if not model.exists() or not config.exists():
    raise RuntimeError("Lithuanian licensed voice files missing")
voice=PiperVoice.load(str(model),config_path=str(config))
synth=ReginuteSynth(voice,LithuanianPhonemizer(),length_scale=1.16,expand_text=isplesk)
audio=synth.synthesize(TEXT)
out=OUT/"original_lt_narration.wav"
with wave.open(str(out),"wb") as f:
    f.setnchannels(1);f.setsampwidth(2);f.setframerate(synth.sr);f.writeframes(i_int16(audio))
with wave.open(str(out),"rb") as f:
    duration=f.getnframes()/f.getframerate()
(OUT/"narration_status.json").write_text(json.dumps({
    "voice_source":MODEL_REPO,"license":"CC-BY-4.0","duration_seconds":duration,
    "sample_rate":synth.sr,"characters":len(TEXT),"words":len(TEXT.split())
},ensure_ascii=False,indent=2),encoding="utf-8")
print("LT_TTS_OK duration=%.2f, words=%s"%(duration,len(TEXT.split())),flush=True)
