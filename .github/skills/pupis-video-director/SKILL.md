---
name: pupis-video-director
description: Independent evidence-first editorial and visual-quality skill for PUPIS SHORTS. Reject cheap/stale videos, verify sources, licensing, real movement, Lithuanian narration and owner permission before delivery.
---

# PUPIS SHORTS — Video Director & QA Skill (0 EUR cloud)

This is a **reusable repository-scoped agent skill**, not a newly installed ChatGPT-wide plugin.
All work must use cloud apps or free GitHub-hosted runners; never require the owner's Windows computer.
No YouTube private/public upload, automated payments, Gmail sending, Apps Script/Make trigger without fresh explicit owner permission.

## Non-negotiable execution

1. Read the latest **single** SSOT Google Doc and latest NEXT: `https://docs.google.com/document/d/1s5xmFWYEXoMs-06QioCuJU9Oy6dFygaejZVbW1xKroo/edit`. Read current evolution methodology: `https://docs.google.com/document/d/1gpdvlre6ruV5gAkGwvRiWYA9Ts5BX_40bXKAFqU5oQg/edit`.
2. The target is a **watchable original 30–60 s** Lithuanian 9:16 sport report, not a collection of ZIPs or prompts.
3. Before generation, identify **one sourced news claim**, its original date, identities, exact clip/image rights, whether any shown action is a **symbolic reconstruction**. No AI imitation of actual UTMA fight footage without clear labeling. No unsourced direct quotes or pretend confirmed bouts.
4. Produce three **visually distinct character designs** with consistent faces, silhouettes, ring outfits and action across scenes. Recoloring one identical puppet doesn't count. Use professional storyboard with scene objective, visible action, 0–1 s hook and audio alignment; replace repeated titles/blank/static cards. Prefer real permitted AI image-to-video motion over pan-and-zoom of still drawings.
5. Use cloud renderer (connected HeyGen where truly free, public ZeroGPU where available, free GitHub Actions for CPU audio / mux). No paid GPU, no user PC, no new service or billing subscription without permission. Verify real outputs, never infer success from a generation job's green status.
6. Run `python tools/pupis_video_qa.py --video <real.mp4> --evidence <facts-and-owners.json> --output <qa.json>`. The quality gate requires 1080x1920, >=24 FPS, 30–60 s, real video+audio, independently checked provenance and rights, distinct characters, and human audition/review. These are **our internal quality thresholds**, not YouTube's minimum requirements.
7. If the owner says a video is boring or poor, record `owner_verdict=REJECTED`, **do not** relabel it as PASS or publish it. A successful ffprobe is only TECH QA; the skill never grants OWNER APPROVED.
8. An agent should make ONE measurable production improvement on a real artifact. Report the old/new file IDs and what's still UNKNOWN. Write one factual SSOT record and read it back; avoid new scheduled tasks and repeating notes.

## Mechanically reproducible proof

On the isolated GitHub branch `pupis-shorts-cloud-video-20261027`, the regression workflow `.github/workflows/pupis-video-quality-regression.yml` downloads the existing 42.7s rejected MP4 from GitHub Actions run `40574937090`. It runs seven QA unit tests and the real-film gate with `--expect REJECTED`, creates JSON evidence, and uploads the report. A regression is **successful only if this bad film remains rejected**; no video is made publicly YouTube-accessible.

Known bad source: `https://drive.google.com/file/d/19OEG8SwJ6Kpr2goQB19v7YB6gUeOdfJ3/view`.
Known problems: 720x1280 at 20 FPS, 3 faces sharing one visual puppet, owner rejection, original TTS audition missing. **Do not auto-fix by upscaling or interpolation alone**; artwork direction must be materially changed.

## Interpretation

- `REJECTED`: owner rejected — stop and redesign.
- `BLOCKED`: technical or evidence gate failed — enumerate exact reasons, no release.
- `TECH_QA_AND_CREATIVE_REVIEW_PASSED_AWAIT_OWNER_APPROVAL`: evidence gates can be checked, but publication remains false; owner must separately approve.

This skill intentionally fails closed and cannot guarantee subjective artistic quality: that still needs actual viewing by the owner.
