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
- SHA로 고정한 Action에는 Dependabot alert가 생기지 않는다. 그래서 Action의 보안 수정은 정기 업데이트로만 들어온다. 봇 PR은 매주 PR 담당자가 처리한다(`docs/development-workflow.md`).
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

- 독립 리뷰는 작성자와 분리한 컨텍스트에서 Standards·Spec과 버그 찾기를 실행한다. 각각은 축이고, 모델을 축마다 다른 패밀리로 나누라는 뜻이 아니다. 되돌리기 쉬움(two-way door: 되돌리기 쉬운 결정)은 그 셋을 작성 패밀리와 다른 모델 하나로 해도 된다. 리뷰 모델, effort, 근거 표, P0·P1의 수정·기각·한계 수용은 `docs/development-workflow.md`의 "역할 분담"을 따른다. 신뢰 경계 변경(아래)에는 Security를 추가한다. 도구는 다음과 같다(공통값).

| 리뷰 | 도구 | 언제 |
| --- | --- | --- |
| Standards·Spec | `/matt-code-review`만(저장소에 커밋한 사본, §7). 모델 패밀리는 `docs/development-workflow.md` 역할 분담 | 모든 PR |
| 버그 찾기 | 작성 패밀리와 다른 모델(`docs/development-workflow.md` 역할 분담). 되돌리기 쉬움은 Standards·Spec과 같은 모델 하나로 된다. 되돌리기 어려움(one-way door: 되돌리기 어려운 결정)은 그 절의 강한 모델 순서에서 작성 패밀리를 뺀 뒤 지금 쓸 수 있는 첫 모델. Opus를 쓸 수 있으면 Sonnet은 그 첫 모델이 아니다 | 모든 PR. 되돌리기 어려움의 강도와 한도 대체는 역할 분담 |
| Security | 작성 패밀리와 다른 모델. 되돌리기 어려움은 버그 찾기와 같은 강도. Semgrep CLI가 있으면 함께 실행 | 신뢰 경계 변경. 열린 지적은 고치거나, 오탐으로 기각하거나, 소유자가 한계로 수용하기 전에는 병합하지 않는다 |
| 외부 | 공개 저장소는 CodeRabbit, 비공개 저장소는 다른 모델 | 아래 외부 리뷰 대상 |
| 정기 Security 감사 | Cloudflare `security-audit` | 릴리스 전, 인증·외부 입력·결제 같은 새 공격면이 생길 때, 분기마다 한 번 이상 |
| 회고 | Matt Pocock `retro` | 사용자가 요청할 때(§6) |

- Standards·Spec의 독립 리뷰는 `/matt-code-review`로만 부른다. 플러그인의 `code-review`와 내장 `/code-review`는 이 역할이 아니다. 내장 `/code-review`는 버그 찾기다. `/implement`가 끝에서 돌리는 `code-review`는 구현 중의 자체 점검이며 `review/independent`로 세지 않는다.
- 역할마다 결정적 검사와 LLM 리뷰를 각각 하나까지만 둔다. 다른 모델의 두 번째 의견은 외부 리뷰 대상에만 둔다. 되돌리기 어려움에서 한도로 다음 모델을 쓴 뒤 더 강한 모델로 다시 보는 일은 후속 Issue다. 병합을 막지 않고, 할지는 소유자가 정한다(`docs/development-workflow.md` 역할 분담). 순서는 결정적 검사 → LLM 리뷰 → 사람이다. 선택 도구와 설치·확인 방법은 `docs/development-workflow.md`에 둔다.
- 가벼운 경로: 문서나 신뢰 경계가 아닌 설정만 바꾸는 되돌리기 쉬움 PR은 Standards·Spec·버그 찾기를 작성 패밀리와 다른 모델 하나로 받는다. Security는 받지 않는다.
- 내장 명령이 없는 런타임은 같은 역할의 리뷰를 쓰고 무엇을 썼는지 리뷰 기록에 남긴다. CodeQL을 쓰더라도 Security 리뷰를 대신하지 않는다. 위 표의 버그 찾기가 이미 그 예외를 적는다. 작업 문서의 Cursor·Codex 칸이 미확인이어도 그 예외를 Claude Code 명령으로 되돌리지 않는다. 역할 분담의 패밀리 규칙도 이 문장으로 특정 패밀리 전용으로 되돌리지 않는다.
- 리뷰 기록: context는 `review/independent`(Standards·Spec·버그 찾기)와, Security 리뷰를 실행했으면 `review/security`다. description에 도구·모델·지적 수를 적는다. 사람이 읽는 근거 표(축, 모델, effort, head SHA, P0, P1, P2)는 PR 본문에 두고 `docs/development-workflow.md` 역할 분담을 따른다. PR 댓글은 사람이 읽는 기록으로 함께 남길 수 있다. 1인 프로필에서는 코드를 쓴 에이전트가 이 status를 남기지 않는다. Grok Bot이 리뷰 결과·리뷰한 모델·head SHA를 확인한 뒤, 소유자가 남긴다. 기록 수단은 Mac의 `gh`다. Mac Studio로 옮겨도 그 앱은 `review/gate`만 올리고, 이 두 status는 올리지 않는다(`docs/review-gate-app.md`). 팀 프로필에서는 그 PR을 구현하지 않은 사람이 남긴다. 구현한 에이전트는 어느 프로필에서든 자기 PR에 통과를 찍지 않는다. `Review status` workflow는 이 status를 쓰지 않고 읽기만 한다. 1인 프로필에서 그 읽기는 아래 문단대로 저장소 소유자와 `STATUS_ACTORS`만 success로 센다.
- `Review status` CI job(`scripts/check_review_status.py`, `templates/review-status.yml`)이 바뀐 파일 경로로 필요한 status를 정하고, 그 head에 없으면 실패한다. `review/independent`와 `review/security`가 필요한지는 그 head의 `compare(base, head)`로 정한다. 열린 PR의 현재 파일·커밋 목록으로 정하지 않는다. `review/independent`는 아래 Dependabot 예외가 아닌 모든 PR에 필요하다. 아래 표의 공통 경로나 프로젝트 경로에 걸리면 `review/security`도 필요하다. 예외는 둘 다 면제한다. 경로에 걸리지 않아도 그 head에 `review/security`나 `review/independent`가 있으면 `success`여야 한다. 내용 기준은 오탐이 많아 이 job이 보지 않고 리뷰어가 판단한다. 이 job은 `pull_request_target`으로 기본 브랜치의 workflow와 검사기를 실행하고 PR 코드를 실행하지 않는다. 트리거 `branches`는 `main`이라 그 브랜치가 아닌 base에서는 job이 돌지 않는다. 검사기는 이 PR의 `base.ref`가 저장소 `default_branch`와 같아야 하고, 이벤트 `BASE_SHA`가 그 기본 브랜치의 끝이거나 조상이어야 한다. `compare(BASE_SHA...default_branch)`의 status가 `ahead` 또는 `identical`이 아니면 실패한다. 다른 base의 PR은 통과 근거가 아니다. 그래서 PR은 이 검사 코드를 고칠 수 없고, 검사 변경은 기본 브랜치에 병합된 뒤에 적용된다. 다만 PR이 `pull_request` workflow로 같은 이름의 job을 더할 수는 있다. GitHub가 같은 이름의 체크를 어떻게 판정하는지는 확인하지 못했으므로, `.github/workflows/**`를 바꾸는 PR의 Security 리뷰에서 이를 본다. 새 push의 SHA에는 `review/gate`가 없으므로, 그 status가 생기기 전에는 병합되지 않는다. `Review status` job은 필수 체크가 아니다. 새 head에 그 context가 없고 diff identity가 이미 `success`인 status의 것과 같으면 이 job이 그 status를 이어받아 통과한다. 기준 브랜치 갱신만이 아니다. 같은 diff의 push나 force-push도 이어받는다. 현재 head의 `failure`·`pending`은 유지한다. 가장 최근 이전 status가 `success`가 아니거나 조회되지 않으면 이어받지 않는다. 이어받기 해시에는 diff와, 바뀐 파일의 변경 후 blob id 전체(40자)가 들어간다. `index` 줄의 축약 SHA는 쓰지 않는다. id는 바뀐 경로의 상위 디렉터리 git tree만 읽는다. 다른 디렉터리와 그 안의 gitlink는 열지 않는다. 바뀐 경로 자체가 gitlink이면 blob 대신 그 커밋 id를 넣는다. 응답이 잘리거나, id가 빠지거나, 40자가 아니면 이어받지 않는다. 양쪽 경로가 같은 `diff --git` 헤더는 가운데에서 자른다. `svc b/package.json`처럼 경로 안에 ` b/`가 있어도 그 파일의 id를 쓴다. 경로가 다르면 `rename to`나 `copy to`에서 새 경로를 읽고, 그것도 없으면 이어받지 않는다. 파일을 지운 경우는 그 경로가 없어진 것으로 넣는다. 이름을 바꾼 경우와 바이너리 파일은 바뀐 뒤 경로의 id를 넣는다. `@@` 헤더의 줄 번호는 빼되, 두 번째 `@@` 뒤의 함수 이름은 남긴다. 그 이름은 diff가 hunk를 어느 함수로 적었는지라서, 이름이 다른 함수로 옮기면 blob을 보기 전에도 해시가 달라진다. YAML `jobs:`나 JSON처럼 이름이 없거나 같고, `impl` 안의 메서드나 잘린 긴 시그니처는 그 헤더만으로 구분되지 않는다. 그 경우는 변경 후 blob id가 파일 전체를 가른다. 헤더를 빼면 그 구분이 diff 쪽에서 사라지므로 둘 다 둔다. 기준 브랜치가 다른 파일만 바꾸면 이 파일의 blob id가 그대로라 이어받는다. 같은 파일을 바꾸면 줄만 밀려도 blob id가 달라져 다시 리뷰받는다. 빈 줄만 주변에 있거나, 같은 함수 안에서 옮기거나, 줄에 CR을 넣어도 blob id가 달라져 이어받지 않는다. 공백이 다르거나 diff를 확인하지 못하면 이어받지 않는다. 1인 프로필에서 `review/independent`와 `review/security`는 `creator.login`이 저장소 `owner.login`이거나 `scripts/check_review_status.py`의 `STATUS_ACTORS`에 있을 때만 success로 센다. `STATUS_ACTORS`는 서버 앱 로그인을 두는 설정이고 지금은 비어 있다. 다른 작성자의 status는 실패로 본다. 없는 status로 보지 않는다. 목록은 `commits/{sha}/statuses`이고 최신순이다. context마다 첫 항목을 쓴다. combined status에는 `creator`가 없어 쓰지 않는다. 그 목록을 없는 status로 보면 이어받기가 최신 거부를 지울 수 있다. 실패로 보면 그 context는 이 head에 있고 success가 아니므로 이어받지 않는다. 이어받기의 이전 SHA도 같다. 팀 프로필은 사람 작성자를 보지 않는다. 로그인이 `[bot]`으로 끝나면 1인·팀 모두 실패다. 승인 댓글의 작성자도 같다. 같은 GitHub 계정의 사람과 에이전트는 여전히 구분하지 못한다. 그 계정의 status는 절차 기록이다.
- 이 저장소의 필수 체크 기록: `.github/repository-settings.json`의 `required_status_checks`는 `strict: true`다. `checks`는 `Baseline checks (Python 3.11)`(`app_id` 15368), `Baseline checks (Python 3.13)`(`app_id` 15368), `{"context": "review/gate", "app_id": 5641238}`이다. `{"context": "Review status", "app_id": 15368}`은 필수 목록에 없다. 카나리 E 재시험(Issue #32, PR #47)이 Actions 15368의 위조와 소유자 status가 병합을 BLOCKED로 남긴 뒤에 뺐다. 승인 경계는 `review/gate`를 **전용 GitHub App의 정수 `app_id`에 고정**하는 것이다. 이 저장소 기록의 전용 앱 ID는 5641238이다. 다른 저장소나 새 프로젝트는 앱을 만든 뒤 그 정수로 채우고, 채우기 전에는 `REPLACE:<APP_ID>` 자리표시자를 둘 수 있다. 그 문자열이 남아 있으면 `tools/apply_github_settings.py`는 조회 전에 멈추고, `scripts/check_github_settings.py`는 UNVERIFIED로 끝난다. 가짜 정수를 넣어 감사를 통과시키지 않는다. `Review status` job 이름은 `templates/review-status.yml`과 `.github/workflows/review-status.yml`과 같고, 필수 체크가 아니다. PR #31의 체크 이름도 `Review status`였다. 이 파일은 기대값이다. 기록을 담은 PR은 branch protection을 쓰지 않는다. 병합 뒤 소유자가 Mac에서 `tools/apply_github_settings.py`로 적용한다. 적용되면 Dependabot 버전 전용 PR을 뺀 모든 PR(되돌리기 쉬움 포함)에 `review/independent`가 필요하다. 1인 프로필에서 status는 소유자만 올린다는 규칙이다. 에이전트가 status를 올리는 것은 금지지만 GitHub가 기술적으로 막지는 않는다. 1인 프로필에서 검사기는 `creator.login`이 저장소 소유자이거나 `STATUS_ACTORS`(지금은 비어 있음)인 status만 success로 센다(#34). smallnext, BGLike, mobile-runtime은 repo-baseline에 보호 규칙을 적용하고, 카나리 시험(같은 이름 체크 위장, 이전 실패 run이 남은 head의 병합 가능 여부, Dependabot 예외)을 통과하고, status 작성자·편집된 승인 댓글 검사기 수정이 병합·재적용된 뒤에 카나리 결과는 Issue #32 댓글 하나에 적는다. 그 기록이 없으면 멈춘다. 이 PR은 그 세 저장소의 `.github/repository-settings.json`을 바꾸지 않는다. `Review status`를 필수로 넣지 않는다. 그 세 저장소의 `Review status` workflow는 그대로 둔다. 그 PR이 그 저장소의 branch protection을 적용하지 않는다. 적용은 각 저장소에서 소유자가 Mac으로 한다.
- 카나리 E(2026-11-06, PR #39, 닫힘): 그때의 필수 체크 `Review status`는 `app_id` 15368(github-actions)이었다. `permissions: checks: write`인 workflow가 `GITHUB_TOKEN`으로 같은 이름의 체크 run을 conclusion success로 올리면 GitHub는 201을 주고, 그 run의 앱은 15368이며, GraphQL은 `isRequired`를 참으로 둔다. 최신 conclusion이 이긴다. 마지막 진짜 run 뒤에 올린 위조 success가 필수 조건을 통과시킨다. workflow 토큰은 그 게이트를 위조할 수 있다.
- 승인 경계는 commit status `review/gate`다. 체크 run `Review gate`가 아니다. 카나리 E가 위조한 객체는 체크 run이고, Actions 잡도 같은 앱 15368의 체크 run이다. 전용 GitHub App의 권한은 Commit statuses 쓰기와 Metadata 읽기뿐이다. Checks 권한과 webhook은 없다. 그 앱은 체크 run을 만들지 못한다. 브랜치 보호의 `checks[]`는 context와 `app_id`로 체크 run과 commit status를 함께 고른다. `review/gate`를 그 앱의 `app_id`에 고정하면, workflow 토큰이 같은 이름으로 status나 체크 run을 올려도 앱은 15368이라 필수 조건이 아니다. 게시는 201일 수 있다. 키는 Mac에만 있고 Actions에 닿지 않는다. 절차와 저장소별 적용 전후와 E 재시험은 `docs/review-gate-app.md`다.
- `Review status` workflow는 증거 검사로 남긴다. 폐지하지 않고, `review/gate`를 쓰지 않으며, 앱 키를 갖지 않는다. 필수 목록에는 두지 않는다. 근거가 없으면 `review/gate`가 막는다. 그 job도 근거가 없으면 실패하지만, 그 실패는 필수 체크가 아니다. 그 success는 승인 경계가 아니다. 15368은 workflow 토큰이 같은 이름의 체크 run을 만들 수 있다. `tools/post_review_gate.py`는 그 체크의 conclusion을 읽지 않는다. 그 SHA의 `review/independent`·`review/security`, PR 본문의 리뷰 패밀리, 1인 프로필의 승인 댓글을 다시 읽는다. 검사기의 이어받기로 이전 SHA의 status를 이 게이트의 근거로 쓰지 않는다. 근거 status는 이 head에 있어야 한다.
- Dependabot 버전 전용 예외는 검사기와 같다. 브랜치 보호는 작성자별로 빼지 못하므로 `review/gate`도 모든 PR에 필요하다. 버전 전용 diff이면 스크립트는 두 리뷰 status 없이 그 SHA에 success를 올린다. 다른 줄이 있거나 판정이 안 되면 success를 올리지 않는다. `strict`는 true다. 브랜치를 갱신하면 head SHA가 바뀌고 이전 `review/gate`는 그 head를 덮지 않는다. 인자 SHA가 열린 PR의 현재 head와 다르거나, PR이 닫혔거나, base가 기본 브랜치가 아니면 아무것도 올리지 않는다. 조회가 실패하거나, 키가 0600 일반 파일이 아니거나, `GITHUB_ACTIONS`가 있으면 올리지 않는다. 근거가 이 head에서 실패하면 그 SHA에 failure를 올려 이 앱의 이전 success를 지운다. 적용 전에는 서버의 필수 체크가 이 파일과 다를 수 있다. 이 파일에서 `Review status`를 빼도, 소유자가 적용하기 전에는 서버 보호가 그 체크를 요구할 수 있다. 카나리 E 재시험은 `review/gate`를 5641238에 고정한 뒤의 음성 결과다(Issue #32, PR #47). 전용 앱 success로 병합이 열리는 대조는 그 댓글에서 미실행이다.
- 신뢰 경계 변경은 누가 무엇을 할 수 있는지, 또는 신뢰하지 않는 입력이 더 높은 권한에 닿는지를 바꾸는 변경이다. 작성자의 판단이 아니라 diff로 정한다. 아래 중 하나라도 걸리면 신뢰 경계 변경이다. 애매하면 신뢰 경계 변경으로 본다.

| 종류 | 기준 | 정하는 사람 |
| --- | --- | --- |
| 공통 경로 | `.github/workflows/**`, `.github/actions/**`, `.github/repository-settings.json`, `.github/dependabot.yml`, `.github/dependabot.yaml`, `.github/CODEOWNERS`, `.github/repo-baseline.json`, `.github/trust-boundary-paths`, `scripts/check_*.py`, `scripts/workflow_policy.py`, `scripts/pr_author.py`, `scripts/rerun_review_status.py`, `tools/post_review_gate.py`, `tools/apply_github_settings.py`, `docs/review-gate-app.md`, `.github/workflow-policy.json`, `.claude/settings.json`, `.claude/hooks/**`, `.claude/agents/**`, `.claude/commands/**`, `.agents/skills/**`, `.claude/skills/**`, `.mcp.json`, 의존성 manifest·lockfile, `Dockerfile`, `.env*` | 이 저장소(공통값) |
| 프로젝트 경로 | 인증·결제·권한 검사·migration 등 프로젝트가 정한 경로 | 프로젝트 소유자(팀 프로필은 CODEOWNERS의 소유자). `.github/trust-boundary-paths`에 한 줄에 하나씩 적고 프로젝트 리뷰 문서에서 연결한다. `/`가 있으면 저장소 루트 기준 경로이고(`src/auth`, `/src/auth/`, `src/auth/**`는 같다), `/`가 없으면 어느 깊이든 그 파일 이름이다. `*`는 `/`도 넘는다. CI는 기준 브랜치의 파일을 읽는다 |
| 내용 | workflow `permissions`·`pull_request_target`, Secret·token 참조, 셸 실행·`eval`, 데이터·파일·브랜치 삭제, 외부 입력을 처음 받는 코드 | diff를 읽는 에이전트 |

- 사람은 어느 PR에든 Security 리뷰를 더 요청할 수 있다. 경로 기준에 걸린 PR은 에이전트가 Security 리뷰를 빼지 않는다. 예외는 아래 Dependabot 버전 갱신 하나다. PR 본문 Merge Danger에 걸린 기준을 적고, 걸린 것이 없으면 없다고 적는다.
- 예외: Dependabot이 연 PR이고 diff가 의존성 manifest·lockfile의 버전·해시와 workflow `uses:`의 Action 버전·SHA만 바꾸면 신뢰 경계 변경으로 보지 않는다. 다른 줄이 하나라도 바뀌거나 다른 사람이 커밋을 더하면 예외가 아니다. 이름에 붙은 숫자(`pkg-2`, `x-1.2.3.tgz`)는 패키지·파일 이름의 일부로 보므로, `resolved` URL이 바뀌는 npm·yarn lockfile은 예외가 아니다. 예외인 PR은 필수 CI와 §2의 매주 처리를 따른다. 이 예외는 `review/security`와 `review/independent`를 모두 면제하고, 외부 리뷰 대상에서도 뺀다. 그 head에 리뷰 status가 있으면 `success`여야 한다. 이 면제는 리뷰 status와 외부 리뷰만 뺀다. 이 예외와 같은 버전 전용 diff가 §10의 게이트 경로를 바꾸면 사람 되돌리기 어려움 승인에서도 뺀다. 그 경로의 Action·의존성 주 버전이 바뀌거나 `scripts/check_review_status.py`가 바뀌면 빼지 않는다(§10). 이 검사기는 승인 댓글에서 게이트 경로의 Action 주 버전을 본다. 표 밖의 문 유형은 판정하지 않는다. §10 표의 게이트 경로는 아래 승인 댓글로 본다.
- 신뢰 경계 변경은 Security 리뷰 대상일 뿐이다. 사람 승인이 필요한 되돌리기 어려움인지는 §10으로 판정한다. CI workflow와 리뷰 게이트 파일은 Security 리뷰만으로 병합하지 않는다(§10).
- 1인 프로필의 승인 댓글: `Review status` job이 §10 표의 게이트 경로를 바꾼 PR에서 `review/owner-approval`을 실패로 넣는다. 이것은 commit status가 아니다. 같은 계정이 status를 올릴 수 있어, 그 이름의 status가 있어도 댓글을 대신하지 않는다. `Review status`는 그 댓글의 필수 체크가 아니다. 댓글이 없으면 `review/gate`가 failure다. 저장소 소유자의 이슈 댓글이 `되돌리기 어려움 승인: <현재 head의 전체 SHA>`로 시작하면 통과한다. deprecated인 `한쪽 문 승인: <현재 head의 전체 SHA>`도 같다. 둘 다 댓글 첫 줄의 그 접두사와 전체 SHA만 인정한다. 다른 철자나 다른 SHA는 통과하지 않는다. 댓글 재실행은 본문을 읽지 않고 이 검사기를 다시 돌린다. 옛 접두사 제거는 #30이다. 작성자는 저장소 `owner.login`과 같다. 댓글 재실행도 그 로그인만 본다. 둘은 같은 계정이다. 조직 소유 저장소의 `owner.login`은 조직 이름이라 사람 댓글과 같지 않다. 조직 저장소는 1인 프로필을 쓰지 않고 `프로필: 팀`을 쓴다. 1인으로 두면 멤버 댓글은 승인도 재실행도 아니다. 별도의 승인 계정 목록은 두지 않는다. SHA가 다르거나, 작성자가 그 로그인과 다르거나, 댓글이 없으면 실패다. 새 head는 이전 댓글을 잇지 않는다. diff가 같아도 같다. 편집한 댓글은 승인이 아니다. `updated_at`이 `created_at`과 같은 문자열이고 GraphQL `lastEditedAt`이 null이며 `includesCreatedEdit`가 아닐 때만 인정한다. 시각이 없거나 다르면 실패다. REST 시각은 초 단위라 같은 초 편집은 두 문자열이 같다. 그 경우 `lastEditedAt`이 생기면 실패다. 내용을 바꾸려면 그 댓글을 고치지 말고 새 댓글을 단다. `edited` 재실행은 본문을 읽지 않고 이 검사기를 다시 돌리므로, 편집된 댓글만 있던 이전 성공은 유지되지 않는다. 되돌리기 쉬움과 위 Dependabot 버전 전용 예외는 통과한다. 기준 브랜치 `AGENTS.md`에 한 줄 `프로필: 팀`이 있으면 팀 프로필이라 이 댓글을 요구하지 않는다. 그 줄이 없거나 파일이 없으면 1인이다. 그 줄을 더하거나 빼는 diff는, 기준 브랜치가 아직 1인이면 게이트 경로와 같이 댓글을 요구한다. diff를 읽지 못하면 그 파일이 바뀐 것으로 본다. 이름을 바꿔 `AGENTS.md`가 된 파일은 patch에 그 줄이 없어도, 그 head의 `AGENTS.md`에 줄이 있고 기준 브랜치에는 없으면 댓글을 요구한다. 이 판정의 파일 목록은 `compare(base, head)`다. 열린 PR의 최신 파일 목록이 아니다. 목록이 300개 이상이거나 diff가 너무 크면 댓글을 요구한다. 404가 아닌 읽기 오류면 확인 불가다. 게이트 경로의 Action 주 버전이 바뀌거나, `uses:`에 `# vN` 주석과 `@vN` 태그가 없어 주 번호를 모르면 승인 댓글 예외로 통과시키지 않는다. `review/security`와 `review/independent` 면제는 그대로다. 표 밖의 되돌리기 어려움(돈·계정·migration 등)도 이 job이 보지 않는다.
- 리뷰는 수렴해야 한다. 리뷰·수정 라운드 상한은 3이다(공통값). 한 라운드는 리뷰 뒤에 작성자가 수정 커밋을 한 번 push하는 것이다. 그 push에 커밋이 여러 개여도 한 라운드다. 그 push에 대한 CodeRabbit 증분 리뷰는 같은 라운드다. 재리뷰 범위와 지적 표시는 `prompts/pr-ci-setup.md` §5를 따른다. 상한에 닿았는데 아직 병합 전이면, 남은 CodeRabbit 지적에는 이유를 답하고 스레드를 해결한 뒤 후속 Issue에 적는다. 그 지적은 병합 뒤 후속 PR에서 고친다. 상한을 넘는 수정 라운드는 소유자만 승인한다.
- 외부 리뷰: 권한·Secret·workflow·저장소 설정·dependency 정책을 바꾸는 PR과 §10의 되돌리기 어려움에는 작성자 세션 밖의 리뷰를 하나 더한다. 공개 저장소는 CodeRabbit 무료 플랜의 리뷰로 충족한다. CodeRabbit 리뷰를 받을 수 없는 비공개 저장소는 다른 모델의 리뷰를 받거나, 받지 못한 사실을 기록하고 사람 승인 여부를 §10으로 판단한다. 같은 모델을 별도 컨텍스트로 돌린 리뷰는 외부 리뷰로 세지 않는다. `interrogate`를 포함한 추가 의견도 외부 리뷰로 세지 않는다. 그 외 PR에 CodeRabbit이 남긴 지적은 참고용이다.
- CodeRabbit은 참고용 리뷰다. 필수 체크로 두지 않는다. 리뷰가 끝난 뒤에도 check가 `pending`으로 남아 병합을 막을 수 있기 때문이다. 브랜치 보호는 대화 해결을 필수로 두므로, 병합 전에 달린 스레드는 그 자체로 병합 조건이다. 병합 전에 달린 CodeRabbit 스레드는 PR 종류와 관계없이 답하고 해결한다. 병합 뒤에 달린 지적은 후속 PR로 처리한다. 외부 리뷰 대상 PR은 auto-merge를 예약하지 않는다. 그 리뷰가 끝나고 위 스레드를 해결한 뒤에 병합한다. 지적은 확인해 맞는 것만 고치고, 스레드마다 반영 여부를 답한 뒤 해결한다. Autofix·수정안 바로 커밋·docstring·테스트 생성은 쓰지 않는다. 다시 리뷰가 필요하면 `@coderabbitai full review`를 쓴다. CodeRabbit check가 SKIPPED이거나 `Review paused`이면 외부 리뷰는 끝나지 않았고, `@coderabbitai full review`를 요청한다. 예외는, CodeRabbit 리뷰가 끝난 head와 견줘 바뀐 것이 이미 리뷰된 PR들 사이의 충돌을 푼 main 병합뿐인 head다. 소유자는 그 사실을 승인에 적고 외부 리뷰를 다시 받지 않고 승인할 수 있다.
- 병합 전에 PR 본문이 `.github/pull_request_template.md`를 따르는지 확인한다. CI가 보는 것과 보지 않는 것을 나눈다. `scripts/workflow_policy.py`(`templates/pr-policy.yml`)가 PR에서 검사한다(CI). 트리거 `branches`는 `main`이다. 이 필터가 있는 복사는 다른 base에서 돌지 않는다. `pull_request`는 PR에 있는 workflow를 쓰므로, PR이 필터를 지우면 그 복사는 다시 돌 수 있다. PR conventions만으로는 게이트가 아니다. workflow 변경은 필수 체크 `review/gate`(`app_id` 5641238)와 Baseline checks가 막는다. `Review status`는 그 필수 체크가 아니다. 제목은 Conventional Commits이고, 설명은 소문자 라틴 또는 한글로 시작하며, 72자 이하이고, 마침표로 끝나지 않는다. 브랜치는 `<type>/<이슈>-<slug>`다. `docs`/`build`/`ci`/`chore`는 이슈 번호를 생략할 수 있다. 기본 봇 접두사는 `claude`/`codex`/`dependabot`다. `feat`/`fix`/`refactor`/`perf`/`test`/`revert`는 본문에 `Refs`/`Closes`/`Fixes`/`Resolves #N`이 있어야 한다. 본문에 `## Summary`, `## Evidence`, `## Merge Danger`가 있어야 한다. `Door:`는 `되돌리기 쉬움` 또는 `되돌리기 어려움`이다. 필드 이름은 `Door:`다. deprecated인 `양쪽 문`과 `한쪽 문`도 같은 의미로 통과한다. 다른 철자와 다른 필드 이름은 통과하지 않는다. 옛 값 제거는 #30이다. 작성 기록은 `Author: <tool> / <model>`이거나 `작성 도구:`와 `작성 모델:`이다. 둘이 같이 있으면 같아야 한다. tool은 `Claude Code`, `Cursor`, `Cursor 클라우드 에이전트`, `사람`이다. 사람은 모델이 `없음`이다. Dependabot이 연 PR은 이 본문 절·Door·작성 기록을 검사하지 않는다. 제목·브랜치·이슈 링크는 검사한다. `AGENTS.md`와 feature flag 검사는 기본으로 켜 두고, `.github/workflow-policy.json`으로 끈다. 그 파일은 복사하지 않는다. 이 저장소는 그 둘을 끄고 `cursor` 브랜치 접두사를 더한다. 리뷰 근거 표는 이 검사가 보지 않는다. 표는 리뷰 뒤에 채워지므로 `Review status`가 본다(CI). 축은 Standards, Spec, 버그 찾기, Security다. `bug-finding`은 버그 찾기와 같다. 헤더는 `axis`/`축`, `model`/`모델`, `effort`, `head SHA`, `P0`, `P1`, `P2`다. `result`/`결과`는 있어도 된다. 모델은 비어 있으면 안 된다. 버그 찾기와 Security는 `해당 없음: <이유>`일 수 있고 그때 P0·P1·P2는 0이다. Standards와 Spec은 그렇게 비우지 않는다. `미실행`은 실패다. head SHA는 그 실행의 head 전체 40자와 같다. P0·P1은 0 이상의 정수다. 리뷰 모델과 작성 모델, `이전 작성 모델`의 패밀리가 같으면 실패다(CI). 패밀리는 `docs/development-workflow.md` 역할 분담이고, 플랫폼은 보지 않는다. CI 별칭 표에서 Opus와 Sonnet은 Claude다. `grok-4.7-high-fast`는 Grok, `Composer 2.5`는 Composer, Gemini는 Gemini, GPT는 GPT다. 표에 없는 이름, `chatgpt`, `codex`, 패밀리가 둘인 이름은 실패다. 되돌리기 어려움의 버그 찾기·Security는 그 역할 분담의 가장 강한 다른 패밀리고, 한도면 다음 패밀리를 쓰고 근거에 적는다. 본문은 파싱만 하고 실행하지 않는다. 실패 이름은 `review/evidence`다. commit status가 아니다. Dependabot 작성자는 이 표 검사에서 뺀다. 본문을 고치면 이미 있는 `pull_request_target` `edited`로 같은 job이 다시 돈다. 그 재실행은 #21과 같다. 댓글 본문은 읽지 않는다. 플래그 상태, 영향 범위 문장, 신뢰 경계의 내용 판단은 CI가 보지 않는다. 이 조기 검사는 `pull_request`로 돈다. base에 스크립트가 있으면 그 파일과 `.github/workflow-policy.json`을 쓰고, 없을 때만 PR 쪽을 실행한다. 그 예외는 검사기를 처음 넣는 PR뿐이다. base의 검사기가 `--root`를 모르면 job은 실패한다. 그 검사기는 PR 트리를 보지 못한다. base에 있는 뒤로는 PR이 `workflow_policy.py`나 `pr_author.py`를 바꿔도 그 실행에는 닿지 않는다. `AGENTS.md`, `CLAUDE.md`, feature flag는 `--root`로 PR 트리를 읽고 실행하지 않는다. `ready_for_review`는 draft가 ready가 될 때 본문을 고치지 않아도 이 검사와 `Review status`를 다시 돌린다. 공개 저장소의 `pull_request_target` 허용은 `review-status.yml`만 대상으로 하고, 이 검사가 그 정책을 바꾸지 않기 위해서다.
- 다른 사람이나 봇의 PR 브랜치에 커밋을 추가하면 PR 댓글로 알린다. 추가 커밋은 최종 head 리뷰와 필수 CI를 다시 거친다.
- 문 판정은 §10을 따른다. 병합 절차는 `prompts/pr-ci-setup.md` §10을 따른다. 사람 승인과 병합 실행자는 §9의 프로필과 §10의 기록을 따른다.
- 정기 Security 감사는 날짜·`source_ref`·감사 도구의 설치 commit·지적 수를 `security-audit` 라벨의 Issue로 남긴다. 공개 저장소에는 지적 내용을 쓰지 않고 비공개 security advisory에 둔다. 실행 방법은 `docs/development-workflow.md`를 따른다.

## 6. 회고

- 에이전트 환경 개선에는 Matt Pocock의 `retro`를 사용한다. 동명의 다른 회고 스킬로 대체하지 않는다.
- 회고는 사용자가 요청한 세션·PR을 대상으로 한다. 매 PR이나 일정에 따라 자동 실행하지 않는다. 제안을 먼저 보고하고 사용자가 선택한 개선만 반영한다.
- 개선은 같은 실수를 다음에 자동으로 막는 가장 앞 단계에 반영한다. 순서는 코드 구조·타입 → 결정적 검사(lint·CI·스크립트) → `AGENTS.md`·리뷰 문서 규칙 → 사람 리뷰다. 앞 단계로 막을 수 있으면 문서 규칙만 더하지 않는다.
- revert·hotfix PR의 본문에는 원래 PR과, 어느 단계(검증·CI·리뷰·승인·병합 후 복구)에서 잡았어야 했는지 적는다. 이 PR은 회고 후보다.
- 실행 절차와 완료 조건은 `prompts/pr-ci-setup.md` §7을 따른다.

## 7. 프로젝트 스킬과 작업 진입

- 도구는 세 층에 둔다. 저장소 층(`AGENTS.md`, `@AGENTS.md` 한 줄만 있는 `CLAUDE.md`, `.agents/skills`, `.claude/skills`, 비밀값 없는 `.mcp.json`)만 팀원과 클라우드 세션에 닿는다. 계정 층(클라우드 환경·Secret·커넥터)은 사람마다 등록하고, 로컬 층(`~/.agents`, `~/.claude`의 스킬·플러그인·MCP)은 그 컴퓨터에만 있다. 층별 목록은 `docs/development-workflow.md`를 따른다.
- 리뷰 관문 스킬은 저장소 층에 커밋한다. 저장소에 복사한 사본은 해시로 지키지만, 플러그인의 태그는 원본 쪽에서 옮겨질 수 있으므로 주간 점검이 §8대로 commit을 대조한다. `vendor/mattpocock-skills/matt-code-review`(`mattpocock/skills` v1.3.2, commit `d1478fc`, MIT)를 `tools/apply_baseline.py`가 `.agents/skills/`와 `.claude/skills/`에 복사하고 해시를 기록한다. 내장 `/code-review`와 겹치지 않게 frontmatter `name`만 `matt-code-review`로 바꿨다. 올릴 때는 이 저장소에서 원본을 갱신하고 다시 적용한다.
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
| 리뷰 기록 누락 | 병합된 PR의 최종 head에서 §5의 `Review status` job이 `success`가 아님 |
| hotfix 비율 | 병합 PR 중 위 hotfix 범위에 드는 PR의 비율. 참고용이고 병합·auto-merge의 조건이 아니다 |
| 정기 감사 지연 | 마지막 `security-audit` Issue가 3개월보다 오래됨. 없으면 없다고 표시 |
| 마켓플레이스 태그 | §7의 태그가 가리키는 commit이 §7의 commit과 다르면 표시 |
| 이벤트 정책 | 공개 저장소에 `.github/workflows/review-status.yml`이 있으면, Actions 이벤트 정책이 그 파일에 `pull_request_target`과 `issue_comment`만 허용함. 없거나 다른 이벤트까지 허용하거나 둘 중 하나가 빠지면 표시. 비공개 저장소와 workflow가 없는 저장소는 비해당 |

- 점검은 회고 후보를 모을 뿐이다. 회고는 §6대로 사용자가 지정할 때만 한다.
- 점검 결과로 고칠 것이 생기면 PR로만 반영하고 같은 리뷰·필수 CI·위험별 병합을 거친다. 일정 실행 설정은 이 저장소에 두지 않는다.

## 9. 프로필

두 프로필은 GitHub 승인 설정·CODEOWNERS·병합 실행자, 그리고 1인 프로필에서 리뷰 status를 남기는 사람(§5)만 다르다. 리뷰·CI·위험 판정은 같다. 프로젝트는 `AGENTS.md`에 프로필을 한 줄로 적는다. 팀이면 그 한 줄은 `프로필: 팀`이다. 적지 않으면 1인 프로필이다. `Review status`는 이 한 줄만 팀으로 본다.

| 항목 | 1인(기본) | 팀(2~6명) |
| --- | --- | --- |
| `required_approving_review_count` | 0 | 1 |
| `dismiss_stale_reviews` | `true` | `true` |
| `require_code_owner_reviews` | `false` | `true` |
| `require_last_push_approval` | `false` | `true` |
| CODEOWNERS | 두지 않는다 | `templates/CODEOWNERS`로 §5 공통 경로와 프로젝트 경로의 소유자를 정한다 |
| 사람 승인 | 저장소 소유자 | 쓰기 권한이 있고 PR 책임자가 아닌 팀원 |
| 되돌리기 쉬움 병합 | `review/gate`가 필수로 적용된 뒤에는 소유자의 `review/independent`가 있어야 병합된다. Dependabot 버전 전용 PR은 그 status가 없다. status는 소유자만 올린다는 규칙이다. 에이전트가 status를 올리는 것은 금지지만 GitHub가 기술적으로 막지는 않는다. 1인 프로필에서 검사기는 `creator.login`이 저장소 소유자이거나 `STATUS_ACTORS`(지금은 비어 있음)인 status만 success로 센다(#34). 적용 전인 프로젝트는 필수 CI·리뷰 뒤 맡은 에이전트 | 필수 승인·CI·리뷰 뒤. status는 그 PR을 구현하지 않은 사람이 남긴다 |
| 되돌리기 어려움 병합 | 소유자가 §10의 승인 댓글을 남긴 뒤 | 승인한 사람이나 PR 책임자 |

- `templates/repository-settings.json`은 1인 프로필 값이다. 팀 프로필은 복사한 뒤 위 표의 값으로 바꾼다.
- 이 저장소(`minjunkim-dev/repo-baseline`)도 소비 프로젝트와 같이 `Review status`를 둔다. 검사기 원본이 기본 브랜치에 먼저 있어야 job이 승인 댓글을 본다. 순서는 다음과 같다. ① 공개 저장소는 Actions 이벤트 정책을 먼저 만든다(아래). 허용 이벤트는 `pull_request_target`과 `issue_comment`뿐이다. ② `templates/review-status.yml`을 `.github/workflows/review-status.yml`로 두어 병합한다. 재조회에서 두 이벤트가 보이기 전에는 병합하지 않는다. ③ `checks`에 `Review status`를 넣지 않는다. 승인 경계의 필수 체크는 `{"context": "review/gate", "app_id": <전용 앱의 정수>}`다. 15368을 넣지 않는다. workflow가 기본 브랜치에 있고 job이 한 번 성공한 뒤에 그 기록을 병합하고, 소유자가 Mac에서 `tools/apply_github_settings.py`로 적용한다. 그 전에 없는 체크 이름을 서버에 올리면 검사가 영원히 대기할 수 있다. 이 저장소는 `Review status`를 필수로 적었다가, 카나리 E 재시험 뒤에 뺐다. `.github/repository-settings.json`은 `strict: true`이고 `Baseline checks (Python 3.11)`(`app_id` 15368), `Baseline checks (Python 3.13)`(`app_id` 15368), `review/gate`(`app_id` 5641238)를 둔다. `Review status`는 없다. 소비 프로젝트에서 아직 앱 ID를 넣지 않았으면 `review/gate`에 `REPLACE:<APP_ID>`가 남을 수 있고, 그동안 적용 도구는 조회 전에 멈춘다. 이 파일은 기대값이다. 기록을 담은 PR은 branch protection을 쓰지 않는다. 병합 뒤 소유자가 Mac에서 적용한다. 적용되면 Dependabot 버전 전용 PR을 뺀 모든 PR(되돌리기 쉬움 포함)에 `review/independent`가 필요하다. 1인 프로필에서 status는 소유자만 올린다는 규칙이다. 에이전트가 status를 올리는 것은 금지지만 GitHub가 기술적으로 막지는 않는다. 1인 프로필에서 검사기는 `creator.login`이 저장소 소유자이거나 `STATUS_ACTORS`(지금은 비어 있음)인 status만 success로 센다(#34). smallnext, BGLike, mobile-runtime은 repo-baseline에 보호 규칙을 적용하고, 카나리 시험(같은 이름 체크 위장, 이전 실패 run이 남은 head의 병합 가능 여부, Dependabot 예외)을 통과하고, status 작성자·편집된 승인 댓글 검사기 수정이 병합·재적용된 뒤에 카나리 결과는 Issue #32 댓글 하나에 적는다. 그 기록이 없으면 멈춘다. 이 PR은 그 세 저장소의 `.github/repository-settings.json`을 바꾸지 않는다. `Review status`를 필수로 넣지 않는다. 그 세 저장소의 `Review status` workflow는 그대로 둔다. 그 PR이 그 저장소의 branch protection을 적용하지 않는다. 적용은 각 저장소에서 소유자가 Mac으로 한다. ①의 서버 정책과 ③의 branch protection은 검사기를 바꾸는 PR이 적용하지 않는다. ②의 workflow 파일도 그 PR에 넣지 않는다. 기본 브랜치에 없는 동안 그 PR 자신을 막지 않기 위해서다.
- §5의 `Review status` job은 두 프로필 모두 둔다. 필수 체크로 등록하지 않는다. 필수 체크는 `review/gate`다. 도입은 위 ①②와 `review/gate` 기록이다. 이 저장소의 파일 기록은 위 항목이다. 아직 ③ 전인 프로젝트도, 위 문단의 카나리 통과와 status 작성자·편집된 승인 댓글 검사기 수정(S1·S3)의 병합·재적용이 먼저다. 그 다음에 기존 PR이 아무도 남기지 않는 status를 기다리지 않게 ①②로 job을 먼저 두고, 리뷰 status를 남기기 시작한 뒤 `review/gate`를 필수 체크로 기록한다. `Review status`는 필수로 기록하지 않는다. 새 프로젝트도 카나리 통과 기록이 있기 전에는 같은 조건이다. 병합 뒤 적용은 소유자가 Mac에서 한다. 1인 프로필에서 남기는 사람은 §5의 소유자다. 저장소 정책이 `pull_request_target`만 허용하면, 둘 다 허용하는 정책이 이미 있어도 그 좁은 정책은 `PUT /repos/<owner>/<name>/actions/policies/<id>`로 고친다. 상위 조직·기업 정책이 더 좁으면 이 저장소 명령으로 고치지 못하고 멈춘다. 더 좁은 정책이 남아 있으면 `issue_comment`가 막힌다.
- Actions 이벤트 정책: GitHub는 공개 저장소의 `pull_request_target`을 2026-12-02부터 기본으로 막는다(2026-11-09·16 16:00~18:00 UTC에 미리 막아 본다). 막히면 그 job이 돌지 않거나 실패로 끝난다. `Review status`는 필수 체크가 아니므로 그 실패만으로 병합이 막히지는 않는다. `templates/review-status-policy.json`은 이 workflow 파일 하나에 `pull_request_target`과 `issue_comment`만 허용한다. 다른 이벤트는 막히므로 이 workflow는 별도 파일로 두고 그 둘 외의 이벤트를 더하지 않는다. `issue_comment` 실행은 PR 체크가 아니다. 그 job은 기본 브랜치만 checkout하고 PR 코드와 댓글 본문은 실행하지 않으며, PR이 아닌 이슈 댓글은 돌리지 않는다. 재실행은 열린 PR에서, 댓글 작성자가 저장소 소유자일 때만 한다. 다른 사람의 댓글은 이 승인을 바꾸지 않으므로 다시 돌리지 않는다. 유지관리자 목록은 두지 않는다. 그 댓글을 지우면 페이로드의 작성자는 그대로 소유자이므로 다시 돈다. 그 댓글을 고쳐도 작성자는 그대로라 다시 돈다. 다른 계정이 고친 경우도 같다. 검사기는 `updated_at`이 `created_at`과 같고 `lastEditedAt`이 null인 댓글만 승인으로 본다. 같은 초 편집은 시각 문자열이 같아도 승인이 아니다. 편집한 댓글은 무효이고 새 댓글을 단다. 같은 PR의 이전 재실행은 취소한다. 그 head의 `pull_request_target` 실행을 `head_sha`로 찾아 다시 돌린다. 목록의 `pull_requests`는 비어 있다. 그 실행을 찾지 못하면 그 head에 실패하는 `Review status` 체크를 남긴다. `actions: write`는 재실행에만, `checks: write`는 그 실패 체크에만 쓴다. `review/independent`와 `review/security`는 쓰지 않는다. 개인 계정의 공개 저장소에서도 만들 수 있다(2026-11-04 `repo-baseline`에서 생성·삭제로 확인). 비공개 저장소는 대상이 아니다. [변경 공지](https://github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2/), [안전하게 쓰는 법](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target) (2026-11-04 확인).
- GitHub auto-merge 조건은 §10이다. revert 없는 기간 같은 조건은 두지 않는다. 실패가 revert가 아니라 후속 fix로 나타나 구분되지 않기 때문이다.
- 팀 프로필의 사람 승인:
  - PR 책임자는 PR을 연 사람이다. 에이전트가 연 PR은 그 에이전트를 시킨 사람이 책임자다. 책임자의 승인은 세지 않는다.
  - 에이전트와 봇의 승인은 사람 승인이 아니다. 에이전트는 PR을 승인하지 않는다. 에이전트가 사람 계정으로 승인하면 GitHub는 그 사람의 승인으로 기록하기 때문이다. Actions의 PR 승인은 §4 기준선에서 꺼져 있다.
  - 승인 뒤 새 push가 오면 마지막으로 push한 사람이 아닌 사람이 다시 승인해야 병합된다. 에이전트가 책임자 계정으로 push했으면 책임자는 그 head의 승인자가 될 수 없다.
  - 두 명 팀에서 승인자가 PR 브랜치에 push하면 승인할 사람이 없어 병합이 막힌다. 책임자가 마지막 push를 하거나, 승인할 다른 팀원을 정한다.
  - 신뢰하는 작성자의 PR을 덜 읽고 승인하는 가벼운 승인 경로는 두지 않는다.
- CODEOWNERS 소유자는 저장소 쓰기 권한이 있어야 한다. 소유자가 한 명이면 그 사람의 PR을 승인할 소유자가 없으므로 두 명 이상이나 GitHub 팀을 적는다. GitHub 팀을 소유자로 쓰려면 조직 소유 저장소여야 한다.
- 조직 소유 저장소에서 달라지는 점([rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets), [protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) 문서, 2026-11-03 확인). 기준선 값에는 아래 기능이 없다. 쓰려면 이 저장소에서 공통값으로 정한다.
  - 브랜치 보호·저장소 ruleset: 공개 저장소는 Free, 비공개 저장소는 Pro·Team·Enterprise Cloud.
  - 조직 단위 ruleset: GitHub Team·Enterprise 요금제의 조직([GitHub changelog 2025-06-16](https://github.blog/changelog/2025-06-16-organization-rulesets-now-available-for-github-team-plans/)).
  - Merge queue: 조직 소유 공개 저장소, 또는 Enterprise Cloud 조직의 비공개 저장소. 개인 계정 저장소에는 없다.
  - 보호 우회 목록: 조직 소유 저장소에만 있다. 기준선은 우회를 두지 않는다.
- 비공개 팀 저장소의 외부 리뷰: CodeRabbit 무료 리뷰는 공개 저장소만 대상이고, 비공개 저장소는 PR을 여는 개발자마다 유료다(2026-11-03 확인). 기준선은 유료 서비스를 고르지 않는다. §5대로 다른 모델의 리뷰를 받는다.

## 10. 문 판정

문 유형은 이 절만 정한다. 이름은 되돌리기 어려움(one-way door: 되돌리기 어려운 결정)과 되돌리기 쉬움(two-way door: 되돌리기 쉬운 결정)이다. 필드 이름은 `Door:`다. PR 본문 Merge Danger의 Door에는 이 판정만 적는다. 설치된 Matt `/pr` 스킬은 되돌리기 비용을 문으로 적는다. 그 스킬은 이 저장소 vendor에 없다(`vendor/`는 `matt-code-review`만 둔다). 스킬 원문은 고치지 않고, Door 값은 이 절의 판정으로 채운다.

판정 질문은 "망가지면 사용자가 무엇을 잃나"다. 작성자가 아니라 변경 내용으로 정한다. 애매하면 되돌리기 어려움이다.

| 문 | 기준 |
| --- | --- |
| 되돌리기 어려움 | 돈, 계정 접근, 다른 사람 데이터의 노출. 데이터 삭제나 복구가 어려운 migration. Secret·인증·권한을 넓히는 변경. 새 workflow 쓰기 권한. 대량 발송. 복구가 불확실하거나 영향 범위가 넓음. 아래 게이트 경로 |
| 되돌리기 쉬움 | 위 기준에 하나도 해당하지 않음 |

되돌리기 어려움은 위험 변경이다. 사람 승인 전에 §5의 외부 리뷰를 받는다. 버그 찾기·Security의 모델과 effort는 `docs/development-workflow.md` 역할 분담을 따른다. 리뷰 프롬프트에 이 절의 문 유형을 적는다. Cursor의 effort 설정이 제품에 있는지는 확인하지 않았다.

게이트 경로를 바꾸는 PR은 프로필과 관계없이 되돌리기 어려움이다. Security 리뷰만으로 병합하지 않는다. Dependabot이 연 PR이고 diff가 §5의 버전 전용 예외와 같으면(버전·해시·Action SHA만 바꾸고 다른 줄은 없음) 그 경로여도 사람 되돌리기 어려움 승인에서 뺀다. 아래 둘은 그 승인에서 빼지 않는다.

- 게이트 경로의 Action이나 의존성 주 버전이 바뀌는 경우. 주 번호는 `uses:` 줄의 버전 주석(`# v4.2.1`)이나 태그(`v4`)의 첫 숫자로 본다. `v4`에서 `v5`, `v4.2.1`에서 `v5.0.0`은 주 버전이다. `v4.2.1`에서 `v4.3.0`은 아니다. 주석과 태그가 없어 주 번호를 모르면 되돌리기 어려움으로 본다.
- `scripts/check_review_status.py`, `scripts/workflow_policy.py`, `scripts/pr_author.py`, `tools/post_review_gate.py`, `tools/apply_github_settings.py`, `docs/review-gate-app.md`가 바뀌는 경우. 작성자가 Dependabot이든 사람이든 같다.

| 경로 | 어디서 |
| --- | --- |
| `.github/workflows/**` | 소비 프로젝트와 이 저장소. `review-status.yml`을 포함한다 |
| `templates/review-status.yml` | 이 저장소의 workflow 템플릿 |
| `scripts/check_review_status.py` | 리뷰 게이트 검사기. 버전 전용 예외 없이 항상 되돌리기 어려움 |
| `scripts/workflow_policy.py`, `scripts/pr_author.py` | PR 본문 검사. base에 스크립트가 있으면 그 파일과 설정을 쓰고, 없을 때만 PR 쪽을 실행한다. 파일 검사는 PR 트리를 읽는다. 버전 전용 예외 없이 항상 되돌리기 어려움 |
| `.github/workflow-policy.json` | 그 검사의 저장소 설정. 버전 전용 예외 없이 항상 되돌리기 어려움 |
| `templates/pr-policy.yml` | PR conventions workflow 템플릿 |
| `scripts/rerun_review_status.py` | 승인 댓글 뒤 Review status를 다시 돌리는 스크립트. `checks: write`를 쓴다 |
| `tools/post_review_gate.py` | Mac에서만 실행하는 `review/gate` 게시. 앱 비밀키는 저장소에 없다. 버전 전용 예외 없이 항상 되돌리기 어려움 |
| `tools/apply_github_settings.py` | 설정 기준선을 서버에 쓰는 도구. 버전 전용 예외 없이 항상 되돌리기 어려움 |
| `docs/review-gate-app.md` | 전용 앱 런북. 버전 전용 예외 없이 항상 되돌리기 어려움 |
| `templates/review-status-policy.json` | 이벤트 정책 템플릿. 이 정책의 서버 값을 바꾸는 작업도 같다 |
| `.github/repository-settings.json`, `templates/repository-settings.json` | 저장소 설정 기준선 |

사람 승인:

- 승인 대상은 최종 head SHA 하나다. 그 뒤 push가 있으면 그 SHA로 다시 승인한다.
- 1인 프로필: 사용자 계정이 소유한 저장소에서, 그 소유자가 PR 댓글을 남긴다. 댓글은 `되돌리기 어려움 승인: <head sha>`로 시작한다. deprecated인 `한쪽 문 승인: <head sha>`도 같은 의미다. 둘 다 첫 줄의 정확한 접두사와 전체 SHA만 인정한다. 제거는 #30이다. `<head sha>`는 승인하는 head의 전체 SHA다. 작성자 login이 저장소 `owner.login`과 다르거나 SHA가 현재 head와 다르면 승인이 아니다. 편집한 댓글도 승인이 아니다. `updated_at`과 `created_at`이 같고 `lastEditedAt`이 null이어야 한다. 같은 초 편집은 시각 문자열이 같아도 승인이 아니다. 내용을 바꾸려면 댓글을 고치지 말고 새 댓글을 단다. 조직 소유 저장소는 이 댓글의 대상이 아니다(§5). 팀 프로필을 쓴다. 그 전에는 병합하지 않는다. `Review status` job이 이 댓글을 검사하고, 없으면 `review/owner-approval`로 실패한다(§5). 그 job은 필수 체크가 아니고, commit status로 따로 요구하지 않는다. 병합은 그 댓글과, 그 head에 전용 앱이 올린 `review/gate` success가 있어야 한다. 에이전트는 그 status를 올리지 않는다. 절차는 `docs/review-gate-app.md`다. 새 push는 이전 댓글을 무효로 한다. 병합은 `--match-head-commit`으로 그 SHA를 고정한다. auto-merge는 하지 않는다.
- 팀 프로필: §9의 사람 승인으로 최종 head를 승인한다. 에이전트와 봇의 승인은 세지 않는다. auto-merge는 하지 않는다.
- 1인 프로필의 GitHub 필수 승인 0명은 이 승인을 없애지 않는다. 에이전트는 PR을 승인하지 않는다.

auto-merge는 §9 ③의 branch protection까지 적용한 프로젝트에서, 이 절의 되돌리기 쉬움이고 §5의 외부 리뷰 대상이 아닌 PR에만 예약한다. `review/gate`가 필수인 저장소에서는 Dependabot 버전 전용 PR을 뺀 되돌리기 쉬움도 `review/independent`가 success이기 전에는 병합되지 않는다. 1인 프로필에서 status는 소유자만 올린다는 규칙이다. 에이전트가 status를 올리는 것은 금지지만 GitHub가 기술적으로 막지는 않는다. 1인 프로필에서 검사기는 `creator.login`이 저장소 소유자이거나 `STATUS_ACTORS`(지금은 비어 있음)인 status만 success로 센다(#34). auto-merge 예약은 그 status가 success인 뒤에만 한다. 되돌리기 어려움과 외부 리뷰 대상 PR은 예약하지 않는다. 외부 리뷰 대상은 그 리뷰가 끝난 뒤에 병합한다. CodeRabbit check가 SKIPPED이거나 `Review paused`이면 외부 리뷰는 끝나지 않았고, `@coderabbitai full review`를 요청한다. 예외는, CodeRabbit 리뷰가 끝난 head와 견줘 바뀐 것이 이미 리뷰된 PR들 사이의 충돌을 푼 main 병합뿐인 head다. 소유자는 그 사실을 승인에 적고 외부 리뷰를 다시 받지 않고 승인할 수 있다.

병합 전에 달린 CodeRabbit 스레드는 PR 종류와 관계없이 답하고 해결한다. 병합 뒤에 달린 지적은 후속 PR로 처리한다.
