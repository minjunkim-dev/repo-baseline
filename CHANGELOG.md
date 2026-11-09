# 변경 기록

항목당 1~3줄. 재설계 전 기록은 [docs/archive/CHANGELOG-2026.md](docs/archive/CHANGELOG-2026.md)에 있다.

## 2026-11 — 재설계 이후

- 첫 PR 확인의 `.env` 검사를 `grep`에서 `git check-ignore`로 바꿨다. `.gitignore`에 `!.env` 예외 줄이 있거나 `.env`가 이미 커밋돼 있어도 `grep`은 통과했다.
- `POLICY.md`에 작업 추적 절(§8)을 더했다. 원본 트래커는 하나, 공개 이슈는 연동으로 가져온다. 트래커가 없으면 건너뛴다. §7에 취약점 제보는 비공개 경로로 받는다는 줄을 더했다. pr-conventions 프로필은 `#N`과 함께 트래커 ID(`Fixes ENG-123`)도 이슈 연결로 받는다.
- GitHub 설정 기준선에 `private_vulnerability_reporting`(비공개 취약점 보고)을 필수 항목으로 더했다. 규칙만 있고 켜는 설정이 없었다. 소비 레포는 기준선에 이 키를 더해야 검사가 통과한다. 비공개 저장소처럼 기능이 없으면 예외로 적는다.
- 회고 프롬프트에 되돌림마다 놓친 층(check·test·리뷰·사람)을 적는 단계를 더했다. `REVIEW.md` 예시 표에 완료 기준 밖을 바꾸는 변경을 실패로 보는 행을 더했다. 소비 레포는 원하면 이 행을 손으로 옮긴다.
- 에이전트 권한 안내에 플러그인은 켤 때와 끌 때를 비교해 고른다는 기준과, Matt 스킬의 기본 동작 중 POLICY와 어긋나는 3가지(같은 세션 리뷰, 세션 단위 회고, PR 본문 양식)를 적었다.
- 리뷰 프롬프트 `prompts/review.md`를 더하고 `POLICY.md` §3·README·첫 PR 안내에서 이었다. 구현 세션이 띄운 하위 에이전트는 다른 컨텍스트가 아니라고 적었다. 리뷰를 어떻게 띄우는지 적은 곳이 없었다.
- pr-conventions의 `reject_claude_md` 기본값을 `false`로 바꿨다. 코어가 `CLAUDE.md`(`@AGENTS.md` 한 줄)를 배포하므로 기본값이 코어와 충돌했다. 대신 `CLAUDE.md`가 있으면 `@AGENTS.md` 한 줄이어야 한다. 둘 다 있으면 Claude Code는 기본 설정에서 `CLAUDE.md`를 읽고, `AGENTS.md`는 그 안의 `@AGENTS.md`로 불러올 때만 함께 읽는다. `CLAUDE.md`를 계속 거부하려면 `.github/workflow-policy.json`에 `"reject_claude_md": true`를 둔다.
- team 프로필 `CODEOWNERS`에서 쓰이지 않는 경로 `/.github/trust-boundary-paths`(보관한 review-gate)와 `/tools/apply_github_settings.py`(소비 레포에 복사하지 않음)를 지웠다.

## 2026-11 — 재설계 (#73)

- 코어를 복사만 하는 5개 파일(`templates/core/`)과 한 쪽 규칙(`POLICY.md`)으로 줄였다. Python·manifest 없이 `cp`로 적용한다.
- GitHub 설정은 `templates/github/`, 게이트·PR 형식 검사·해시 복사·팀은 `profiles/` 아래 선택 프로필로 옮겼다. 리뷰 모델 패밀리는 권장으로 내렸다.
- 프롬프트는 `prompts/setup.md`와 `prompts/retro.md` 둘이다. 옛 셋업 프롬프트 2개, 주간 점검, `docs/development-workflow.md`는 지웠다.
- 소비 레포 3곳(smallnext, BGLike, mobile-runtime)을 새 기준으로 옮긴 뒤 `vendor/mattpocock-skills/`를 지웠다. 기본 리뷰 기준은 `REVIEW.md`다(#71).
- review-gate 프로필을 `docs/archive/review-gate/`로 보관했다. 기본 설정이 이미 막는 것만 막고 로컬 에이전트는 막지 못했다. `pr_author.py`는 `profiles/pr-conventions/`로 옮겼다.
- `REVIEW.md` 예시 표에 거짓말하는 테스트(구현 값 되풀이, 소스 모양 검사, 실패를 가리는 mock)를 실패로 보는 행을 더했다.
- `POLICY.md` 병합 절에서 기준이 없던 "근거가 쌓이면 저위험 경로부터 자동 병합" 문장을 지웠다. 자동 병합을 쓰지 않는 정책은 그대로다. 회고 절의 "근거가 쌓이면 완화한다"도 지웠다.
- GitHub 설정 도구에서 CodeQL workflow blob sha 고정(`codeql_main_source`)을 뺐다. codeql-action을 올릴 때마다 기준선을 고쳐야 했다. 남아 있으면 이름을 대고 멈춘다. workflow가 active인지는 계속 본다. smallnext·BGLike·mobile-runtime의 기준선에서 이 키를 지워야 다시 적용된다.
- 부르는 곳이 없던 오프라인 CodeQL 참조 검사와 보관한 review-gate의 App ID 검증을 지웠다. hash-copy 묶음은 설정 검사기를 더 복사하지 않는다. 검사기는 소유자가 이 저장소에서 돌린다.
- PR 양식 Summary에 `완료 기준:` 줄을 두고, `AGENTS.md`에 시작 전에 적는다는 규칙을 더했다. `REVIEW.md`가 받는다던 완료 기준을 적을 곳이 없었다.
- 자체 CI를 Python 3.11·3.13 두 벌에서 최신 안정 버전 한 벌(`Baseline checks`)로 줄였다. 스크립트는 표준 라이브러리만 쓰고 3.9~3.15에서 통과했다. 서버 보호는 아직 옛 두 context를 요구하므로, 병합 직전에 소유자가 `python3 tools/apply_github_settings.py . --apply`로 필수 체크를 `Baseline checks`로 바꾼 뒤 이 PR을 병합한다.
