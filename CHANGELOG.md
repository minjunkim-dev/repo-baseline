# 변경 기록

## 2026-10-18 — 첫 버전

- 세 프로젝트(smallnext, BGLike, mobile-runtime)의 공통 검사기를 모았다.
  - `check_github_settings.py`: CodeQL `init`·`analyze` commit 불일치 검사를 추가했다.
  - `check_bugbot_rules.py`: 필수 규칙 목록을 `.github/repo-baseline.json`의 `bugbot_rules`에서 읽는다.
  - `check_repo_baseline.py`: 복사본 해시 검사를 새로 추가했다.
- Dependabot 공통값을 `POLICY.md`와 `templates/dependabot.yml`에 고정했다. 상한은 GitHub 기본값 5를 쓴다.
- 프롬프트 v4를 v5로 고쳤다. 값은 이 저장소를 참조한다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.
