# 변경 기록

항목당 1~3줄. 재설계 전 기록은 [docs/archive/CHANGELOG-2026.md](docs/archive/CHANGELOG-2026.md)에 있다.

## 2026-11 — 재설계 (#73)

- 코어를 복사만 하는 5개 파일(`templates/core/`)과 한 쪽 규칙(`POLICY.md`)으로 줄였다. Python·manifest 없이 `cp`로 적용한다.
- GitHub 설정은 `templates/github/`, 게이트·PR 형식 검사·해시 복사·팀은 `profiles/` 아래 선택 프로필로 옮겼다. 리뷰 모델 패밀리는 권장으로 내렸다.
- 프롬프트는 `prompts/setup.md`와 `prompts/retro.md` 둘이다. 옛 셋업 프롬프트 2개, 주간 점검, `docs/development-workflow.md`는 지웠다.
- 소비 레포 3곳(smallnext, BGLike, mobile-runtime)을 새 기준으로 옮긴 뒤 `vendor/mattpocock-skills/`를 지웠다. 기본 리뷰 기준은 `REVIEW.md`다(#71).
