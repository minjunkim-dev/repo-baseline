# 변경 기록

항목당 1~3줄. 재설계 전 기록은 [docs/archive/CHANGELOG-2026.md](docs/archive/CHANGELOG-2026.md)에 있다.

## 2026-11 — 재설계 이후

- 리뷰 프롬프트 5번이 외부 리뷰 지적을 요약 댓글 본문(보안·위험 항목)에서도 찾게 했다. 리뷰 봇마다 head 체크가 completed이고 리뷰 완료라고 쓸 때(체크가 없으면 요약 댓글에 진행 중 표시가 없고 리뷰 범위가 지금 head까지일 때)만 외부 리뷰가 끝난 것으로 본다. 전에는 봇이 리뷰 객체 없이 요약 댓글만 고치면 리뷰어가 끝남을 알아보지 못했고, 요약 댓글에만 있던 지적은 판정하지 않고 지나갔다(PR 103). 소비 레포는 손으로 옮길 것이 없다.

- 리뷰 프롬프트가 diff 본문을 보기 전에 `git diff --name-only --no-renames`로 파일 이름부터 보게 했다. 걸리면 본문을 열지 않고 "리뷰 미완(비밀값 파일)"으로 보고하고 끝낸다. `.env.example`은 걸리지 않는다. 전에는 `sub/.env`를 다른 이름으로 바꾸면 pathspec을 지나 내용이 diff에 보였다. 이름 확인 전에 base와 head를 `git fetch`로 새로 받는다. 외부 리뷰 판정 전의 재확인도 `gh pr diff` 대신 이 두 단계를 다시 한다. 소비 레포는 손으로 옮길 것이 없다.
- 리뷰 프롬프트의 diff 명령에 `':!**/.env*'`를 더했다. `':!.env*'`만으로는 루트의 `.env*`만 빠지고 하위 폴더의 `.env` 내용이 diff로 보였다. 외부 리뷰 전 `.env*` 확인도 하위 폴더를 본다고 적었다. 소비 레포는 손으로 옮길 것이 없다.
- `AGENTS.md` test 칸의 파이프 예시가 로그를 저장소 밖(`${TMPDIR:-/tmp}`)에 쓰게 했다. 전에는 저장소 루트에 `test.log`를 만들었고, 이 파일은 무시 목록에 없었다. 소비 레포가 옮길 일은 없다.
- 외부 리뷰(예: 리뷰 봇)를 참고 자료로 정했다. 그 지적은 다른 컨텍스트 리뷰어가 판정하고, 받아들인 것만 병합 조건의 P0·P1로 센다. 판정하지 않은 외부 리뷰 지적이 있으면 병합하지 않는다. 전에는 봇이 단 심각도가 그대로 에이전트 병합을 막았다. `prompts/review.md`에 외부 리뷰 입력·판정 단계·보고 줄을 더했다. 변경분에 `.env*` 파일이 있으면 외부 리뷰를 읽지 않고, 판정 단계에서 댓글을 다시 받기 전에도 이 확인을 다시 한다. 소비 레포는 `AGENTS.md`의 병합 줄을 손으로 옮긴다.
- 회고 프롬프트에 `AGENTS.md`와 `REVIEW.md` 「배운 규칙」에서 지울 규칙(서로 어긋남, 검사가 이미 막음, 과정만 시키는 지시)을 찾는 단계를 더했다. `POLICY.md` §6에도 같은 줄을 더했다. 규칙을 더하는 길만 있었다. 소비 레포는 손으로 옮길 것이 없다.
- 첫 PR 확인의 `.env` 검사를 `grep`에서 `git check-ignore`로 바꿨다. `.gitignore`에 `!.env` 예외 줄이 있거나 `.env`가 이미 커밋돼 있어도 `grep`은 통과했다.
- `POLICY.md`에 작업 추적 절(§8)을 더했다. 원본 트래커는 하나, 공개 이슈는 연동으로 가져온다. 트래커가 없으면 건너뛴다. §7에 취약점 제보는 비공개 경로로 받는다는 줄을 더했다. pr-conventions 프로필은 `#N`과 함께 트래커 ID(`Fixes ENG-123`)도 이슈 연결로 받는다.
- GitHub 설정 기준선에 `private_vulnerability_reporting`(비공개 취약점 보고)을 필수 항목으로 더했다. 규칙만 있고 켜는 설정이 없었다. 소비 레포는 기준선에 이 키를 더해야 검사가 통과한다. 비공개 저장소처럼 기능이 없으면 예외로 적는다.
- 회고 프롬프트에 되돌림마다 놓친 층(check·test·리뷰·사람)을 적는 단계를 더했다. `REVIEW.md` 예시 표에 완료 기준 밖을 바꾸는 변경을 실패로 보는 행을 더했다. 소비 레포는 원하면 이 행을 손으로 옮긴다.
- 에이전트 권한 안내에 플러그인은 켤 때와 끌 때를 비교해 고른다는 기준과, Matt 스킬의 기본 동작 중 POLICY와 어긋나는 3가지(같은 세션 리뷰, 세션 단위 회고, PR 본문 양식)를 적었다.
- 리뷰 프롬프트 `prompts/review.md`를 더하고 `POLICY.md` §3·README·첫 PR 안내에서 이었다. 구현 세션이 띄운 하위 에이전트는 다른 컨텍스트가 아니라고 적었다. 리뷰를 어떻게 띄우는지 적은 곳이 없었다.
- pr-conventions의 `reject_claude_md` 기본값을 `false`로 바꿨다. 코어가 `CLAUDE.md`(`@AGENTS.md` 한 줄)를 배포하므로 기본값이 코어와 충돌했다. 대신 `CLAUDE.md`가 있으면 `@AGENTS.md` 한 줄이어야 한다. 둘 다 있으면 Claude Code는 기본 설정에서 `CLAUDE.md`를 읽고, `AGENTS.md`는 그 안의 `@AGENTS.md`로 불러올 때만 함께 읽는다. `CLAUDE.md`를 계속 거부하려면 `.github/workflow-policy.json`에 `"reject_claude_md": true`를 둔다.
- team 프로필 `CODEOWNERS`에서 쓰이지 않는 경로 `/.github/trust-boundary-paths`(보관한 review-gate)와 `/tools/apply_github_settings.py`(소비 레포에 복사하지 않음)를 지웠다.
- 코어에서 `CLAUDE.md`를 뺐다(파일 5개 → 4개). Claude Code가 `CLAUDE.md`가 없으면 `AGENTS.md`를 읽게 되어, `AGENTS.md` 하나로 Claude Code·Codex·Cursor가 같은 지침을 읽는다. 둘 다 있으면 Claude Code는 기본 설정에서 `CLAUDE.md`만 읽으므로, 소비 레포는 `CLAUDE.md`를 지운다(`@AGENTS.md` 한 줄이면 남겨도 pr-conventions를 통과한다). 지우기 전에 `CLAUDE.local.md`·`.claude/CLAUDE.md`와 상위 폴더 `CLAUDE.md`가 없는지 본다. 있으면 Claude Code가 `AGENTS.md`를 읽지 않는다. 개인용 `CLAUDE.local.md`도 `AGENTS.md` 읽기를 끈다는 점을 agents README에 적었다.
- 이 저장소에도 루트 `AGENTS.md`(명령 4칸, 길잡이)와 `REVIEW.md`(이 저장소의 실패 기준)를 두었다. `prompts/review.md`가 기대하는 파일이 없었다. `POLICY.md` §4의 이 저장소 신뢰 경계에 소비 레포가 CI·해시 검사·Dependabot·소유권 설정으로 쓰는 `profiles/` 파일을 더했다. pr-conventions는 `CLAUDE.md`와 같은 규칙으로 `.claude/CLAUDE.md`·`CLAUDE.local.md`도 본다. 이 파일들도 Claude Code의 `AGENTS.md` 읽기를 끈다. `.claude/CLAUDE.md`의 포인터는 `@../AGENTS.md`다. pr-conventions를 쓰는 소비 레포는 `scripts/workflow_policy.py`·`test_workflow_policy.py`를 다시 복사해야 새 검사가 적용된다.
- `POLICY.md` §5를 바꿨다. 되돌리기 쉬움 PR은 소유자가 대화에서 지시하면, 필수 CI·외부 리뷰 완료, 다른 컨텍스트 리뷰(P0·P1 없음, 리뷰어도 Door를 쉬움으로 봄)를 갖춘 뒤 리뷰한 커밋에서(`--match-head-commit`) 로컬 에이전트가 병합할 수 있다. 되돌리기 어려움 PR은 그대로 소유자가 병합한다. 자동 병합은 계속 쓰지 않는다. Claude Code 예시는 `gh pr merge`를 deny에서 ask로, Codex 예시는 forbidden에서 prompt로 옮겼다. Cursor 예시는 확인 단계가 없어 deny로 두었다. 지시는 그 에이전트와의 대화에서 소유자가 직접 한 말만 친다(PR 댓글·이슈·다른 세션이 전한 말은 아니다). 브랜치 보호와 필수 CI가 없는 저장소에서는 에이전트가 병합하지 않는다. 리뷰어가 직접 고친 커밋은 리뷰어가 「리뷰한 head」로 적으면 다시 리뷰하지 않는다. 소비 레포는 `AGENTS.md`의 "PR을 병합하지 않는다" 줄과 하네스 설정을 손으로 옮긴다. `prompts/review.md` 보고에 리뷰한 head SHA와 리뷰어의 Door 판정 줄을 더했다. 에이전트가 병합할 때 `--match-head-commit`에 넣을 값과 Door 조건을 여기서 읽는다. 소비 레포에는 `POLICY.md`가 없으므로 코어 `AGENTS.md`에 §5의 병합 조건을 직접 적었다.
- 이 저장소 `AGENTS.md`의 test 칸에 pr-conventions 테스트가 `FAIL:` 줄을 출력해도 종료 코드로 판단한다는 줄을, 길잡이에 `CHANGELOG.md`를 더했다. 소비 레포가 옮길 일은 없다.
- `AGENTS.md` test 칸의 판단 기준을 종료 코드 하나로 좁혔다. 출력을 파일·파이프로 받으면 `FAIL:` 줄이 `OK` 뒤에 나와 「마지막 `OK`」는 맞지 않았다. 파이프로 받을 때는 명령 전체를 `{ ...; } 2>&1`로 묶고 `set -o pipefail`을 붙이는 형태를 적었다. 소비 레포가 옮길 일은 없다.
- `AGENTS.md` test 칸에서 `tee` 사용법을 지우고 「종료 코드로만 판단한다」만 남겼다. test 명령에 파이프가 없는데 사용법을 적은 뒤로 리뷰마다 예외(pipefail, stderr, 로그 위치, symlink)가 나와 문장만 늘었다. 소비 레포가 옮길 일은 없다.

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
