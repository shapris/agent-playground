import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pupis_video_qa import analyze

GOOD={'streams':[{'codec_type':'video','codec_name':'h264','width':1080,'height':1920,'r_frame_rate':'30/1'},
                 {'codec_type':'audio','codec_name':'aac'}],
      'format':{'duration':'42.0'}}
EVID={'source_facts_verified':True,'media_rights_verified':True,'voice_audition':'pass',
      'distinct_character_designs':3,'original_motion':'verified',
      'owner_verdict':'UNKNOWN','creative_review':'pass'}

class TestQualityGate(unittest.TestCase):
    def test_clean_tech_still_never_approves_publication(self):
        r=analyze(GOOD,EVID)
        self.assertEqual(r['gate'],'TECH_QA_AND_CREATIVE_REVIEW_PASSED_AWAIT_OWNER_APPROVAL')
        self.assertFalse(r['publish_approved'])
    def test_owner_reject_overrides_good_technical_metrics(self):
        r=analyze(GOOD,dict(EVID,owner_verdict='REJECTED'))
        self.assertEqual(r['gate'],'REJECTED')
        self.assertIn('OWNER_REJECTED',r['findings'])
    def test_reused_puppet_does_not_count_as_three_characters(self):
        r=analyze(GOOD,dict(EVID,distinct_character_designs=1))
        self.assertIn('CHARACTER_DESIGNS_NOT_DISTINCT',r['findings'])
    def test_unheard_lithuanian_voice_cannot_pass(self):
        r=analyze(GOOD,dict(EVID,voice_audition='unknown'))
        self.assertIn('VOICE_NATURALNESS_NOT_AUDITIONED',r['findings'])
    def test_sub_1080p_and_sub_24fps_fail_quality_floor(self):
        low={'streams':[dict(GOOD['streams'][0],width=720,height=1280,r_frame_rate='20/1'),GOOD['streams'][1]],'format':GOOD['format']}
        r=analyze(low,EVID)
        self.assertIn('INSUFFICIENT_PORTRAIT_RESOLUTION',r['findings'])
        self.assertIn('FRAME_RATE_UNDER_24',r['findings'])
    def test_no_audio_blocks(self):
        r=analyze({'streams':[GOOD['streams'][0]],'format':GOOD['format']},EVID)
        self.assertIn('NO_AUDIO_STREAM',r['findings'])
    def test_unverified_facts_and_rights_block(self):
        r=analyze(GOOD,dict(EVID,source_facts_verified=False,media_rights_verified=False))
        self.assertIn('FACTS_NOT_PROVEN',r['findings'])
        self.assertIn('MEDIA_RIGHTS_NOT_PROVEN',r['findings'])

if __name__=='__main__':unittest.main()
