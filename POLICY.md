# 저장소 공통 정책

이 문서는 1인 개발과 소규모 팀(2~6명) 저장소에 공통으로 적용하는 값을 정한다. 두 프로필이 다른 값은 §9에 있다. 프로필을 정하지 않은 프로젝트는 1인 프로필이다.
프롬프트(`prompts/`)는 절차와 판단 기준을 정한다. 구체적인 값은 이 문서와 `templates/`를 따른다.
정책 버전은 이 저장소의 commit SHA다. 각 프로젝트는 `.github/repo-baseline.json`의 `source_commit`에 적용한 버전을 기록한다.

## 1. 값의 종류

| 종류 | 뜻 | 바꾸는 방법 |
| --- | --- | --- |
| GitHub 필수값 | GitHub가 요구하는 값 | 바꿀 수 없다 |
| 공통값 | 적용 중인 모든 저장소에 같게 적용하는 운영 선택 | 이 저장소에서 바꾸고 모든 프로젝트에 다시 적용한다 |
| 프로필 값 | 1인·팀 프로필에 따라 다른 공통값(§9) | 이 저장소에서 바꾸고 그 프로필의 프로젝트에 다시 적용한다 |
| 허용 예외 | 프로젝트 사정으로 공통값과 다르게 두는 값 | 프로젝트 `docs/REPOSITORY_SETUP.md`에 이유와 함께 한 줄로 적는다 |

## 2. Dependabot

`tools/apply_baseline.py`가 `templates/dependabot.yml`과 manifest의 `ecosystems` 목록으로 `.github/dependabot.yml`을 생성한다. 생성한 파일의 해시를 manifest에 기록하므로, 프로젝트에서 값을 바꾸면 `check_repo_baseline.py`가 CI에서 실패한다. 생태계를 추가하려면 manifest의 `ecosystems`를 고치고 다시 적용한다.

| 항목 | 값 | 종류·근거 |
| --- | --- | --- |
| `schedule` | `weekly`, `wednesday`, `"10:00"`, `Asia/Seoul` | 공통값. 사용자 운영 선호. PR 생성 시각을 보장하지 않는다. |
| `labels` | `[dependencies]` | 공통값. 기본 생태계 라벨(`github_actions` 등)을 대체한다. |
| `commit-message` | `prefix: chore`, `include: scope` | 공통값. 제목은 `chore(deps): …` 또는 `chore(deps-dev): …`가 된다. |
| `open-pull-requests-limit` | 설정하지 않는다 | 공통값. GitHub 기본값 5를 쓴다. 업데이트 항목마다 따로 센다. GitHub 권장값은 없다. |
| `groups.codeql-action` | `patterns: ["github/codeql-action/*"]` | CodeQL advanced setup에서 Action을 SHA로 고정하면 필수. `init`과 `analyze`가 다른 버전이면 분석이 실패한다. |

- 보안 업데이트에는 GitHub의 고정 상한 10이 따로 적용된다. `open-pull-requests-limit`과 관계없다.
- Grouped security updates를 켠다(공통값). 계정 설정(새 저장소 자동 켜기)과 각 저장소 Settings → Advanced Security에서 켠다. 같은 패키지 관리자·디렉터리의 보안 수정을 PR 하나로 묶어 봇 PR 수를 줄인다. 묶음 안의 수정 하나가 빌드를 깨면 나머지도 함께 기다린다. `dependabot.yml`의 `groups`가 있으면 그 규칙이 우선한다.
  - REST API가 이 값을 돌려주지 않는다. `check_github_settings.py`로 감사할 수 없으므로 셋업 때 화면에서 확인한다.
- SHA로 고정한 Action에는 Dependabot alert가 생기지 않는다. 그래서 Action의 보안 수정은 정기 업데이트로만 들어온다. 봇 PR은 매주 처리한다.
- `groups`는 기본적으로 정기 업데이트에만 적용된다. SHA 고정 Action에는 보안 업데이트가 생기지 않으므로 지금 구조에서는 추가 설정이 필요 없다. 태그 고정으로 바꾸면 `applies-to: security-updates` 그룹을 검토한다.
- 허용 예외: 저장소의 Git 규칙이 scope를 기능 폴더 이름으로 정하면, 그 문서에 Dependabot `deps`·`deps-dev` 예외를 한 줄 적는다.

## 3. CodeQL

- 기본은 GitHub default setup이다. 빌드 명령이나 toolchain 지정이 필요할 때만 advanced setup을 쓴다.
  - default setup이면 `.github/repository-settings.json`에 `codeql.state: "configured"`를 두고 `codeql_workflow`·`codeql_main_source`는 넣지 않는다. 감사 도구가 두 경우를 구분한다.
- advanced setup에서 `.github/repository-settings.json`이 `codeql_main_source.sha`로 workflow blob을 고정하면, `codeql.yml`을 바꾸는 PR은 이 값도 함께 갱신한다.
  - `scripts/check_github_settings.py`의 `codeql_source_drift()`가 PR CI에서 두 가지를 검사한다: blob SHA 일치, 모든 `github/codeql-action/*` 단계의 commit 일치.
  - 갱신 값: `git hash-object .github/workflows/codeql.yml`.
  - 검사는 YAML 구조를 해석하지 않는다. 주석과 `run:` 같은 블록 본문을 뺀 모든 `github/codeql-action/` 참조를 모아 비교한다. 읽지 못하는 참조나 블록으로 쓴 `uses:`는 고정되지 않은 것으로 보고 실패한다.
  - 이 검사는 정직한 편집(Dependabot, 사람, 에이전트)의 실수를 막는다. 보안 경계가 아니다. 따옴표 안의 이스케이프(`\u0061`)나 줄 연결로 이름을 숨기는 표기는 해석하지 않는다. 그런 작성자는 검사기 파일도 고칠 수 있기 때문이다.
- 집계 `CodeQL` check는 분석이 실패해도 `neutral`일 수 있다. GitHub는 필수 check의 `neutral`을 통과로 본다. 분석 실패로 병합을 막으려면 분석 job 결과를 필수 게이트에 연결한다.

## 4. GitHub 서버 설정

- 목표값은 `prompts/github-repository-settings.md` §3·§5의 표를 따른다.
- 각 프로젝트는 기대값을 `.github/repository-settings.json`에 두고 `scripts/check_github_settings.py`로 읽기 전용 감사를 한다.
- 공통값은 `templates/repository-settings.json`에 있다. 서버 적용은 `tools/apply_github_settings.py`가 같은 기준선으로 계획을 먼저 보이고, 승인 후 `--apply`로 다른 항목만 쓴다.
- 기능 미지원·비해당은 근거를 기록한 명시적 예외만 허용한다. 형식과 LIMITED·DRIFT·UNVERIFIED 구분은 `docs/github-settings-profile.md`를 따른다. 조회 실패를 자동 예외로 바꾸지 않는다.
- 서버 설정은 저장소마다 적용하고 감사로 확인한다. 조직 단위 ruleset은 쓰지 않는다. 조직 소유 저장소에서 달라지는 점은 §9를 따른다.

## 5. 리뷰와 병합

- 독립 리뷰는 작성자와 분리한 컨텍스트에서 Standards·Spec과, 아래 표의 "언제"에 해당하면 버그 찾기를 각각 실행한다. 신뢰 경계 변경(아래)에는 Security를 추가한다. 도구는 다음과 같다(공통값).

| 리뷰 | 도구 | 언제 |
| --- | --- | --- |
| Standards·Spec | 저장소에 커밋한 `matt-code-review`(Matt Pocock `code-review`, §7) | 모든 PR |
| 버그 찾기 | Claude Code 내장 `/code-review` | 코드가 바뀐 PR. 깊이는 양쪽 문 `low`, 한쪽 문·위험 변경 `high` |
| Security | Claude Code 내장 `/security-review`. Semgrep CLI가 있으면 함께 실행 | 신뢰 경계 변경. 열린 지적은 고치거나 오탐 이유를 남기기 전에는 병합하지 않는다 |
| 외부 | 공개 저장소는 CodeRabbit, 비공개 저장소는 다른 모델 | 아래 외부 리뷰 대상 |
| 정기 Security 감사 | Cloudflare `security-audit` | 릴리스 전, 인증·외부 입력·결제 같은 새 공격면이 생길 때, 분기마다 한 번 이상 |
| 회고 | Matt Pocock `retro` | 사용자가 요청할 때(§6) |

- 역할마다 결정적 검사와 LLM 리뷰를 각각 하나까지만 둔다. 다른 모델의 두 번째 의견은 외부 리뷰 대상에만 둔다. 순서는 결정적 검사 → LLM 리뷰 → 사람이다. 선택 도구와 설치·확인 방법은 `docs/development-workflow.md`에 둔다.
- 가벼운 경로: 문서나 신뢰 경계가 아닌 설정만 바꾸는 양쪽 문 PR은 Standards·Spec 리뷰 하나만 받는다.
- 내장 명령이 없는 런타임은 같은 역할의 리뷰를 쓰고 무엇을 썼는지 리뷰 기록에 남긴다. CodeQL을 쓰더라도 Security 리뷰를 대신하지 않는다.
- 리뷰 기록: 필수 리뷰를 마친 에이전트는 리뷰한 head SHA에 commit status를 남긴다. context는 `review/independent`(Standards·Spec·버그 찾기)와 `review/security`다. 신뢰 경계 변경이 아니면 `review/security`는 `success`로 두고 비해당이라고 적는다. description에 도구·모델·지적 수를 적는다. PR 댓글은 사람이 읽는 기록으로 함께 남길 수 있다. 새 push의 SHA에는 status가 없으므로, 필수 체크로 등록하면(§9) 리뷰 뒤에 더한 커밋과 기준 브랜치 갱신은 다시 리뷰할 때까지 병합되지 않는다. 같은 GitHub 계정이 남긴 status는 사람과 에이전트를 구분하지 못한다. 절차가 실행됐다는 기록이지 보안 경계가 아니다.
- 신뢰 경계 변경은 누가 무엇을 할 수 있는지, 또는 신뢰하지 않는 입력이 더 높은 권한에 닿는지를 바꾸는 변경이다. 작성자의 판단이 아니라 diff로 정한다. 아래 중 하나라도 걸리면 신뢰 경계 변경이다. 애매하면 신뢰 경계 변경으로 본다.

| 종류 | 기준 | 정하는 사람 |
| --- | --- | --- |
| 공통 경로 | `.github/workflows/**`, `.github/repository-settings.json`, `.github/dependabot.yml`, `.github/CODEOWNERS`, `.claude/settings.json`, `.agents/skills/**`, `.claude/skills/**`, `.mcp.json`, 의존성 manifest·lockfile, `Dockerfile`, `.env*` | 이 저장소(공통값) |
| 프로젝트 경로 | 인증·결제·권한 검사·migration 등 프로젝트가 정한 경로 | 프로젝트 소유자(팀 프로필은 CODEOWNERS의 소유자). 프로젝트 리뷰 문서에 적는다 |
| 내용 | workflow `permissions`·`pull_request_target`, Secret·token 참조, 셸 실행·`eval`, 데이터·파일·브랜치 삭제, 외부 입력을 처음 받는 코드 | diff를 읽는 에이전트 |

- 사람은 어느 PR에든 Security 리뷰를 더 요청할 수 있다. 경로 기준에 걸린 PR은 에이전트가 Security 리뷰를 빼지 않는다. 예외는 아래 Dependabot 버전 갱신 하나다. PR 본문 Merge Danger에 걸린 기준을 적고, 걸린 것이 없으면 없다고 적는다.
- 예외: Dependabot이 연 PR이고 diff가 의존성 manifest·lockfile의 버전·해시와 workflow `uses:`의 Action 버전·SHA만 바꾸면 신뢰 경계 변경으로 보지 않는다. 다른 줄이 하나라도 바뀌거나 다른 사람이 커밋을 더하면 예외가 아니다. 예외인 PR은 필수 CI와 §2의 매주 처리를 따른다.
- 신뢰 경계 변경은 Security 리뷰 대상일 뿐이다. 사람 승인이 필요한 위험 변경인지는 `prompts/pr-ci-setup.md` §10으로 따로 판정한다.
- 리뷰는 수렴해야 한다. 리뷰·수정 라운드 상한은 3이다(공통값). 재리뷰 범위와 지적 표시는 `prompts/pr-ci-setup.md` §5를 따른다.
- 외부 리뷰: 권한·Secret·workflow·저장소 설정·dependency 정책을 바꾸는 PR과 `prompts/pr-ci-setup.md` §10의 위험 변경에는 작성자 세션 밖의 리뷰를 하나 더한다. 공개 저장소는 CodeRabbit 무료 플랜의 리뷰로 충족한다. CodeRabbit 리뷰를 받을 수 없는 비공개 저장소는 다른 모델의 리뷰를 받거나, 받지 못한 사실을 기록하고 사람 승인 여부를 위험 기준으로 판단한다. 같은 모델을 별도 컨텍스트로 돌린 리뷰는 외부 리뷰로 세지 않는다. 그 외 PR에 CodeRabbit이 남긴 지적은 참고용이다.
- CodeRabbit은 참고용 리뷰다. 필수 체크로 두지 않는다. 리뷰가 끝난 뒤에도 check가 `pending`으로 남아 병합을 막을 수 있기 때문이다. CodeRabbit이 외부 리뷰인 PR만 리뷰가 끝날 때까지 병합을 기다린다. 그 밖의 PR은 기다리지 않고, 병합 뒤 달린 지적은 후속 PR로 처리한다. 지적은 확인해 맞는 것만 고치고, 스레드마다 반영 여부를 답한 뒤 해결한다. Autofix·수정안 바로 커밋·docstring·테스트 생성은 쓰지 않는다. 다시 리뷰가 필요하면 `@coderabbitai full review`를 쓴다.
- 병합 전에 PR 본문이 저장소 PR 양식을 따르는지 확인한다(관련 Issue 또는 생략 이유, 플래그 상태 등). Dependabot PR에는 사람용 양식을 강제하지 않는다.
- 다른 사람이나 봇의 PR 브랜치에 커밋을 추가하면 PR 댓글로 알린다. 추가 커밋은 최종 head 리뷰와 필수 CI를 다시 거친다.
- 병합 위험 기준은 `prompts/pr-ci-setup.md` §10을 따른다. 사람 승인과 병합 실행자는 §9의 프로필을 따른다.
- 정기 Security 감사는 날짜·`source_ref`·감사 도구의 설치 commit·지적 수를 `security-audit` 라벨의 Issue로 남긴다. 공개 저장소에는 지적 내용을 쓰지 않고 비공개 security advisory에 둔다. 실행 방법은 `docs/development-workflow.md`를 따른다.

## 6. 회고

- 에이전트 환경 개선에는 Matt Pocock의 `retro`를 사용한다. 동명의 다른 회고 스킬로 대체하지 않는다.
- 회고는 사용자가 요청한 세션·PR을 대상으로 한다. 매 PR이나 일정에 따라 자동 실행하지 않는다. 제안을 먼저 보고하고 사용자가 선택한 개선만 반영한다.
- 개선은 같은 실수를 다음에 자동으로 막는 가장 앞 단계에 반영한다. 순서는 코드 구조·타입 → 결정적 검사(lint·CI·스크립트) → `AGENTS.md`·리뷰 문서 규칙 → 사람 리뷰다. 앞 단계로 막을 수 있으면 문서 규칙만 더하지 않는다.
- revert·hotfix PR의 본문에는 원래 PR과, 어느 단계(검증·CI·리뷰·승인·병합 후 복구)에서 잡았어야 했는지 적는다. 이 PR은 회고 후보다.
- 실행 절차와 완료 조건은 `prompts/pr-ci-setup.md` §7을 따른다.

## 7. 프로젝트 스킬과 작업 진입

- 도구는 세 층에 둔다. 저장소 층(`AGENTS.md`, `@AGENTS.md` 한 줄만 있는 `CLAUDE.md`, `.agents/skills`, `.claude/skills`, 비밀값 없는 `.mcp.json`)만 팀원과 클라우드 세션에 닿는다. 계정 층(클라우드 환경·Secret·커넥터)은 사람마다 등록하고, 로컬 층(`~/.agents`, `~/.claude`의 스킬·플러그인·MCP)은 그 컴퓨터에만 있다. 층별 목록은 `docs/development-workflow.md`를 따른다.
- 리뷰 관문 스킬은 저장소 층에 커밋한다. `vendor/mattpocock-skills/matt-code-review`(`mattpocock/skills` v1.3.2, commit `d1478fc`, MIT)를 `tools/apply_baseline.py`가 `.agents/skills/`와 `.claude/skills/`에 복사하고 해시를 기록한다. 내장 `/code-review`와 겹치지 않게 frontmatter `name`만 `matt-code-review`로 바꿨다. 올릴 때는 이 저장소에서 원본을 갱신하고 다시 적용한다.
- Claude Code 프로젝트 설정은 `templates/claude-settings.json`이다(두 프로필 공통). `.env` 파일 읽기를 막고, 로컬 편의로 Matt Pocock 마켓플레이스를 태그로 고정해 플러그인을 켠다. 이 플러그인은 클라우드 세션에서 읽히지 않는다. 이 파일은 지침 파일이 아니라 설정 파일이다.
- 개발 절차는 Matt Pocock 스킬을 설치된 원문대로 쓴다. 이 저장소는 스킬의 단계를 다시 정하지 않는다. 초기 설정에서 이 기준이 고르는 것(지침은 `AGENTS.md`만 사용, `@AGENTS.md` 한 줄만 있는 `CLAUDE.md`는 허용, 검증 스킬 하나만 예외, 이 저장소가 복사하는 스킬은 대상 아님)과 `main`에 들어가는 경계는 `docs/development-workflow.md`를 따른다.
- pstack 스킬은 Matt Pocock 스킬이 다루지 않는 단계에만 사람이 불러 쓴다. 단계별 배치는 `docs/development-workflow.md`를 따른다. 설치되지 않았으면 건너뛴다.

## 8. 주간 점검

- 주 1회 점검은 선택이다. 대상은 README의 적용 중인 프로젝트와 이 저장소다. 요청문은 `prompts/weekly-check.md`다. 공통값은 다음과 같다.

| 항목 | 값 |
| --- | --- |
| 점검 기간 | 지난 7일 |
| hotfix로 보는 범위 | 14일 안에 병합된 PR을 고친 PR |
| CI 시간 비교 | 이전 4주 중앙값보다 20% 넘게 늘면 표시 |
| 멈춘 PR | 7일 넘게 갱신이 없는 열린 PR, 열린 지 7일이 넘은 Dependabot PR |
| 리뷰 기록 누락 | 병합된 PR의 최종 head에 §5의 리뷰 status가 없거나 `success`가 아님 |
| 정기 감사 지연 | 마지막 `security-audit` Issue가 3개월보다 오래됨. 없으면 없다고 표시 |

- 점검은 회고 후보를 모을 뿐이다. 회고는 §6대로 사용자가 지정할 때만 한다.
- 점검 결과로 고칠 것이 생기면 PR로만 반영하고 같은 리뷰·필수 CI·위험별 병합을 거친다. 일정 실행 설정은 이 저장소에 두지 않는다.

## 9. 프로필

두 프로필은 GitHub 승인 설정·CODEOWNERS·병합 실행자만 다르다. 리뷰·CI·위험 판정은 같다. 프로젝트는 `AGENTS.md`에 프로필을 한 줄로 적는다. 적지 않으면 1인 프로필이다.

| 항목 | 1인(기본) | 팀(2~6명) |
| --- | --- | --- |
| `required_approving_review_count` | 0 | 1 |
| `dismiss_stale_reviews` | `true` | `true` |
| `require_code_owner_reviews` | `false` | `true` |
| `require_last_push_approval` | `false` | `true` |
| CODEOWNERS | 두지 않는다 | `templates/CODEOWNERS`로 §5 공통 경로와 프로젝트 경로의 소유자를 정한다 |
| 사람 승인 | 저장소 소유자 | 쓰기 권한이 있고 PR 책임자가 아닌 팀원 |
| 양쪽 문 병합 | 필수 CI·리뷰 뒤 맡은 에이전트 | 필수 승인·CI·리뷰 뒤 맡은 에이전트 |
| 한쪽 문 병합 | 소유자가 최종 head를 승인한 뒤 | 승인한 사람이나 PR 책임자 |

- `templates/repository-settings.json`은 1인 프로필 값이다. 팀 프로필은 복사한 뒤 위 표의 값으로 바꾼다.
- §5의 리뷰 status는 두 프로필 모두 필수 체크로 등록한다. 기존 프로젝트의 PR이 아무도 남기지 않는 status를 기다리지 않게 두 단계로 도입한다. ① 에이전트가 리뷰 status를 남기기 시작한다(필수 아님). ② 그 뒤 프로젝트마다 사람이 승인해 `tools/apply_github_settings.py`로 필수 체크에 등록한다. 등록한 저장소는 양쪽 문에 GitHub auto-merge를 쓸 수 있다. 등록할 때는 `checks`에 `{"context": "review/independent", "app_id": -1}`과 `review/security`를 더한다. `-1`은 모든 출처를 허용한다는 뜻이다(GitHub REST API). 검사기는 API가 `null`로 돌려줘도 같은 값으로 본다.
- 팀 프로필의 사람 승인:
  - PR 책임자는 PR을 연 사람이다. 에이전트가 연 PR은 그 에이전트를 시킨 사람이 책임자다. 책임자의 승인은 세지 않는다.
  - 에이전트와 봇의 승인은 사람 승인이 아니다. 에이전트는 PR을 승인하지 않는다. 에이전트가 사람 계정으로 승인하면 GitHub는 그 사람의 승인으로 기록하기 때문이다. Actions의 PR 승인은 §4 기준선에서 꺼져 있다.
  - 승인 뒤 새 push가 오면 마지막으로 push한 사람이 아닌 사람이 다시 승인해야 병합된다. 에이전트가 책임자 계정으로 push했으면 책임자는 그 head의 승인자가 될 수 없다.
  - 신뢰하는 작성자의 PR을 덜 읽고 승인하는 가벼운 승인 경로는 두지 않는다.
- CODEOWNERS 소유자는 저장소 쓰기 권한이 있어야 한다. 소유자가 한 명이면 그 사람의 PR을 승인할 소유자가 없으므로 두 명 이상이나 GitHub 팀을 적는다. GitHub 팀을 소유자로 쓰려면 조직 소유 저장소여야 한다.
- 조직 소유 저장소에서 달라지는 점([rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets), [protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) 문서, 2026-11-03 확인). 기준선 값에는 아래 기능이 없다. 쓰려면 이 저장소에서 공통값으로 정한다.
  - 브랜치 보호·저장소 ruleset: 공개 저장소는 Free, 비공개 저장소는 Pro·Team·Enterprise Cloud.
  - 조직 단위 ruleset: GitHub Team·Enterprise 요금제의 조직([GitHub changelog 2025-06-16](https://github.blog/changelog/2025-06-16-organization-rulesets-now-available-for-github-team-plans/)).
  - Merge queue: 조직 소유 공개 저장소, 또는 Enterprise Cloud 조직의 비공개 저장소. 개인 계정 저장소에는 없다.
  - 보호 우회 목록: 조직 소유 저장소에만 있다. 기준선은 우회를 두지 않는다.
- 비공개 팀 저장소의 외부 리뷰: CodeRabbit 무료 리뷰는 공개 저장소만 대상이고, 비공개 저장소는 PR을 여는 개발자마다 유료다(2026-11-03 확인). 기준선은 유료 서비스를 고르지 않는다. §5대로 다른 모델의 리뷰를 받는다.
