# review/gate 전용 GitHub App

이 문서는 `POLICY.md` §5의 승인 경계를 Mac에서 만드는 절차다. 이 저장소의 PR은 설계와 도구와 기대값만 둔다. 앱을 만들지 않고, branch protection을 쓰지 않고, status를 올리지 않고, 병합하지 않는다.

## 2026-11-06 합의와 이 문서의 역할

- 승인 경계는 항상 **commit status** `review/gate`이고, 브랜치 보호에 **전용 App의 정수 `app_id`로 고정**한다. (`github-actions` 15368으로는 그 필수 context를 충족하지 못하게 한다.)
- **1인·소규모 팀의 권장 일상 경로**는 아래 **Keychain(앱 PEM) + 개발자 `gh`(증거 status) + 게이트 전용 읽기 `GH_TOKEN` + 기본 브랜치 checkout에서의 `post_review_gate.py`**다. 예전의 별도 `reviewgate` OS 계정, 봉인 트리(seal), sudoers, `git archive` 배포 중심 방식은 **선택(레거시)**로 두었다.
- **코드 변경은 하지 않는다.** 이 PR은 문서만 고친다. 장기적으로는 `REPLACE` 자리표시자·필수 `Review status` 조정·carry 삭제 등이 후속 순서로 온다(합의 문서 순서).

## 무엇을 고정하나

승인 경계는 commit status `review/gate`다. 체크 run이 아니다.

카나리 E(2026-11-06, PR #39)는 필수 체크 `Review status`가 `app_id` 15368일 때, `checks: write`인 workflow의 `GITHUB_TOKEN`이 같은 이름의 체크 run을 success로 올리면 그 run도 앱 15368이고 최신 conclusion이 필수 조건을 통과시킨다는 것을 보였다. Actions 잡과 위조 run이 같은 종류의 객체이고 같은 앱이다.

전용 앱은 Commit statuses 쓰기와 Metadata 읽기만 가진다. Checks 권한이 없으므로 체크 run을 만들지 못한다. 브랜치 보호는 `{"context": "review/gate", "app_id": <그 앱의 정수 ID>}`로 고정한다. workflow 토큰이 같은 context로 commit status나 체크 run을 올려도 그 객체의 앱은 15368이다. 게시는 201일 수 있다. 그 객체는 필수 조건이 아니다.

`Review status` workflow는 증거 검사로 남긴다. `review/independent`, `review/security`, 승인 댓글, 근거 표를 읽고 없으면 실패한다. `review/gate`를 쓰지 않는다. 필수 목록에는 `app_id` 15368으로 남는다. 그 초록색은 승인 경계가 아니다. 15368은 같은 이름의 체크 run을 위조할 수 있다. 스크립트는 그 체크의 conclusion을 읽지 않는다.

`strict`는 true다. 새 head에는 `review/gate`가 없다. 인자 SHA가 열린 PR의 현재 head와 다르면 스크립트는 올리지 않는다. 조회 실패, 키가 0600 일반 파일이 아님, `GITHUB_ACTIONS`가 설정됨은 아무것도 올리지 않는다. 근거가 실패하면 그 SHA에 `failure`를 올려 이 앱이 이전에 올린 success를 지운다. 닫힌 PR, head 불일치, 기본 브랜치가 아닌 base에는 올리지 않는다.

Dependabot 버전 전용 예외는 `scripts/check_review_status.py`와 같다. 브랜치 보호는 작성자별로 빼지 못하므로 `review/gate`는 그 PR에도 필요하다. 버전·해시·Action SHA만 바꾼 Dependabot PR이면 스크립트는 두 리뷰 status 없이 success를 올린다. 다른 줄이 있으면 올리지 않고 failure다. 면제를 켜는 별도 플래그는 없다. 신뢰 경계 파일은 `uses:`의 40자 SHA 또는 `v` 태그 pin만 버전 전용이다. 짧은 해시, `\r`, 그 밖의 제어 문자, U+2028, U+2029가 있으면 버전 전용이 아니다. `previous_filename`이 있거나 `status`가 `modified`가 아니면 버전 전용이 아니다. 워크플로 밖으로 이름을 바꾸는 pin-only diff도 면제가 아니다. 작성자 쪽(REST나 web-flow로 Dependabot처럼 만든 커밋)은 아직 증명되지 않았다. 그 면제를 쓰기 전에 카나리로 확인한다.

근거 status의 이어받기는 이 게이트에 쓰지 않는다. `review/independent`와 `review/security`는 이 head에 success여야 한다. 1인 프로필에서 작성자는 저장소 소유자 또는 `STATUS_ACTORS`다. `STATUS_ACTORS`는 비어 있다. 이 앱의 로그인을 거기에 넣지 않는다. 앱은 `review/gate`만 올린다. 로그인이 `[bot]`으로 끝나면 1인·팀 모두 그 status를 받지 않는다. `github-actions[bot]`이 올린 리뷰 status는 실패다. 승인 댓글의 작성자가 `[bot]`이면 그 댓글도 승인이 아니다.

합의(증거-in-gate 방향): 장기적으로는 **별도 필수 `review/independent`·`review/security` status에 의존하지 않고**, PR 본문 근거·하드도어 승인 댓글만으로 게이트가 판정한 뒤 `review/gate`만 올리는 쪽으로 정리할 수 있다. **현재 구현**은 위 문단과 `tools/post_review_gate.py`가 읽는 검사기 그대로다.

## 권장: Keychain(PEM) + 개발자 gh + 게이트 읽기 GH_TOKEN + 기본 브랜치 checkout

1인·소규모 팀에서는 **에이전트가 읽을 수 있는 홈에 0600 PEM을 두지 않는다.** 앱 private key는 **개발자 macOS Keychain**에 넣고, 게이트를 올릴 때만 짧은 생명의 임시 파일로 꺼낸다. Keychain은 PEM을 **디스크에 남기지 않게** 하려는 저장소일 뿐이며, 기본 설정만으로 Touch ID나 하드웨어 보안 모듈 수준을 보장하지 않는다. `security`로 항목을 꺼낼 때(특히 `-w`) 자격·프롬프트 정책은 환경·항목 종류에 따라 다르다.

**같은 macOS 사용자(같은 UID)에서 돌아가는 에이전트는 개발자 세션과 격리되지 않는다.** 예전 레거시 경로의 별도 `reviewgate` OS 계정·sudoers 분리와 달리, 이 권장 경로는 **프로세스·권한 분리가 없다**. 에이전트가 해당 사용자로 실행 중이면 Keychain 항목을 읽거나 임시 PEM을 스캔할 수 있는지(항목 ACL·파일 타이밍)를 별도로 가정하지 않는다.

### 무엇을 쓰나 (현재 코드와 맞춤)

`tools/post_review_gate.py`는 **항상** 환경 변수 `GH_TOKEN`에 **게이트 전용 읽기 토큰**(설치 스코프: 저장소 메타데이터·상태 등 읽기에 필요한 최소 권한)이 있어야 한다. 비어 있으면 `review gate refused: GH_TOKEN must be the gate account read-only token`로 끝난다. **개발자 `gh auth token`을 그대로 쓰지 않는다**(권한이 넓고, 게이트 읽기 주체와 섞인다).

- **리뷰 증거 status·(하드도어일 때) 승인 댓글**: 개발 계정의 `gh`(OAuth/PAT, Keychain에 연결된 자격 증명). 증거용 `gh api`는 이 토큰으로 한다.
- **`post_review_gate.py`의 읽기**: 위와 **별도**인 **읽기 전용** 토큰을 `GH_TOKEN`으로 **서브셸에만** 내보낸다. PEM 경로·내용은 `GH_TOKEN`에 넣지 않는다.
- **쓰기(`review/gate` POST)**: Keychain에서 꺼낸 PEM 경로를 `REVIEW_GATE_APP_KEY`에 두고, `REVIEW_GATE_APP_ID`는 전용 앱의 정수 ID. `post_review_gate.py`는 이 저장소의 `tools/post_review_gate.py`를 **기본 브랜치(또는 검증한 릴리스)의 깨끗한 트리**에서 실행한다. **검토 중인 PR head의 워크스페이스에서는 실행하지 않는다.**

게이트 읽기 토큰 발급 예(한 번만): GitHub에서 **Fine-grained PAT** 또는 별도 **기계용 GitHub 사용자 + PAT**를 두고, 위 넷 저장소만 읽기로 제한한다. 값은 Keychain 항목 `review-gate-read-token` 등에만 두고, 셸 프로파일에 넣지 않는다.

**후속 코드 변경 아이디어:** 개발자 `gh` 자격 증명 하나로 읽기까지 하게 바꾸는 것은 가능하지만, **지금 릴리스의 스크립트는 그렇게 동작하지 않는다.**

### 체크아웃

게이트 스크립트는 `scripts/check_review_status.py`를 가져온다. **파일 한두 개만 복사하면 실패**한다. 고정 디렉터리의 clone(예: `$HOME/src/repo-baseline-gate`)에서 **`main`의 깨끗한 트리**로 맞춘 뒤 실행한다.

```bash
GATE_TREE="$HOME/src/repo-baseline-gate"   # PR head 워크스페이스가 아님
cd "$GATE_TREE" || exit 1
git fetch origin main
# 작업 트리가 깨끗한지 확인 — 로컬 커밋·수정이 있으면 게이트 스크립트가 읽는 검사기와 어긋날 수 있다
if [ -n "$(git status --porcelain)" ]; then
  echo "GATE_TREE has local changes; fix or use a fresh tree" >&2
  exit 1
fi
git reset --hard "origin/main"
```

대안: 검증한 **`main`의 전체 SHA**를 알고 있다면 `git fetch origin <SHA>` 후 `git reset --hard <SHA>`로 고정하거나, 깨끗한 디렉터리에 `git archive <SHA> ... | tar -x`로 풀어 쓴다.

### 승인 시 Mac에서 하는 일 (권장 흐름)

소유자가 직접 한다. 에이전트 셸이 아니다.

1. **검토한 head SHA를 변수에 고정**한다(아래 `SHA`). PR이 갱신되면 다시 읽어 바꾼다.
2. 증거 status(`review/independent`, 필요 시 `review/security`)는 **개발 계정 `gh api`**로 그 `SHA`에 올린다.
3. **1인 프로필이고 되돌리기 어려움(PR)일 때만**: PR 댓글 `되돌리기 어려움 승인: <SHA>` (한 줄, 위와 **동일한** 전체 SHA). 편집하지 말고 새 댓글을 단다(`POLICY.md` §5). 되돌리기 쉬움이면 이 댓글은 필요 없다.
4. 위 **체크아웃**으로 `GATE_TREE`를 깨끗이 맞춘다.
5. Keychain에서 PEM을 임시 파일로 꺼내 **`GH_TOKEN`(게이트 읽기 전용)** 과 함께 `--dry-run` 후 실제 실행한다.

```bash
set -euo pipefail
REPO="minjunkim-dev/repo-baseline"
PR="<번호>"
# 리뷰를 마친 head — PR이 바뀌었는지 확인할 때까지 이 값을 고정해 쓴다
SHA="<검토를 마친 head의 전체 40자 SHA>"
GATE_TREE="$HOME/src/repo-baseline-gate"

cd "$GATE_TREE"
git fetch origin main
if [ -n "$(git status --porcelain)" ]; then
  echo "GATE_TREE has local changes" >&2
  exit 1
fi
git reset --hard origin/main

# 2: 증거 (개발자 gh — description은 실제에 맞게)
gh api "repos/${REPO}/statuses/${SHA}" -f state=success -f context=review/independent \
  -f description="<도구> <모델> 지적 <수>"
# Security를 실행했을 때만
# gh api "repos/${REPO}/statuses/${SHA}" -f state=success -f context=review/security ...

# 3: 1인 프로필 + 되돌리기 어려움(PR)일 때만
# gh pr comment "$PR" --repo "$REPO" --body "되돌리기 어려움 승인: ${SHA}"

# 5: 게이트 — 읽기 토큰 + 설치 토큰 발급용 PEM (PEM은 GH_TOKEN에 넣지 않는다)
(
  set -euo pipefail
  KEY=$(mktemp -t review-gate-key)
  chmod 0600 "$KEY"
  trap 'rm -f "$KEY"' EXIT
  security find-generic-password -a "$USER" -s review-gate-app-key -w > "$KEY"
  export REVIEW_GATE_APP_KEY="$KEY"
  export REVIEW_GATE_APP_ID="<전용 앱 정수 ID>"
  # 게이트 전용 읽기 토큰 (예: Keychain에 저장해 둔 PAT)
  export GH_TOKEN="$(security find-generic-password -a "$USER" -s review-gate-read-token -w)"
  cd "$GATE_TREE"
  set +e
  dry=$(python3 -I tools/post_review_gate.py --repo "$REPO" --pr "$PR" --sha "$SHA" --dry-run)
  set -e
  printf '%s\n' "$dry"
  kind=$(printf '%s\n' "$dry" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read().splitlines()[-1])["kind"])')
  if [ "$kind" = success ] || [ "$kind" = failure ]; then
    python3 -I tools/post_review_gate.py --repo "$REPO" --pr "$PR" --sha "$SHA"
  else
    echo "review gate not posted: $kind" >&2
    exit 1
  fi
)
# 서브셸이 끝나면 GH_TOKEN·임시 PEM이 이 셸에 남지 않는다
```

`--dry-run`은 근거를 읽고 올릴 state를 출력한다. **설치 토큰(POST용 JWT)은 만들지 않고**, commit status POST도 하지 않는다. 표준 출력의 마지막 줄은 JSON이다. `kind`가 `success` 또는 `failure`이면 같은 인자로 dry-run 없이 실행한다. `failure`는 그 SHA에 failure를 올려 이 앱의 이전 success를 지운다. `set -e`만 두면 dry-run의 종료 코드 1이 그 갱신을 건너뛴다. `skip`과 `unverified`는 POST하지 않는다. 실실행이 끝나기 전에는 병합하지 않는다.

스크립트는 저장소 밖 0600 파일만 키로 받는다. symlink, 저장소 안의 경로, 다른 모드는 거부한다. `GITHUB_ACTIONS`가 있으면 거부한다.

### Keychain에 넣기

**PEM 내용을 명령 줄 argv로 넣지 않는다** (`-w "$(cat file.pem)"`는 프로세스 목록에 노출될 수 있다). 아래 중 하나를 쓴다.

- **대화형:** `security add-generic-password -a "$USER" -s review-gate-app-key -w` 만 실행하고, 프롬프트가 뜨면 PEM **전체**를 붙여 넣는다(끝에 개행 포함 여부는 GitHub PEM 형식에 맞출 것).
- **GUI:** **Keychain Access**에서 generic password 항목을 추가하고, 값 필드에 PEM 전체를 붙여 넣는다.

`cat`·`$(< file)`로 PEM을 **명령 줄에 펼쳐 넣지 않는다**. 잠시 파일에 둔 뒤 GUI로 옮기는 방식이면, 옮긴 뒤 그 파일을 바로 지운다.

`review-gate-read-token` 항목에는 **게이트 읽기 전용 PAT 문자열만** 넣는다. 넣은 뒤 디스크에 남긴 원본을 지운다.

다운로드한 원본 PEM은 Keychain에 넣은 뒤 **디스크에서 지운다.** 개발 홈에 서 있는 `review-gate.pem`을 두지 않는다.

## 앱 만들기

소유자가 브라우저에서 한다. 이 절차를 Actions나 클라우드 에이전트에 맡기지 않는다.

1. GitHub 개인 계정에서 GitHub App을 등록한다. [앱 등록](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app). 이름 예: `repo-baseline-review-gate`. Homepage URL은 `https://github.com/minjunkim-dev/repo-baseline`이면 된다.
2. Webhook은 끈다. Active를 끄면 Webhook URL이 필요 없다.
3. 권한은 저장소의 **Commit statuses: Read and write**, **Metadata: Read**(앱의 기본값)만 켠다. Checks, Contents, Pull requests, Administration, Actions는 끄다. 계정 권한은 비운다.
4. 설치 위치는 Only on this account. 설치가 끝나면 App ID(정수의 앱 ID, 설치 ID가 아니다)를 앱 설정 페이지에서 적는다.
5. Private key는 브라우저에서 생성한다. **PEM 내용은 Keychain으로만 옮기고**, 에이전트가 읽는 홈·저장소·클라우드 경로에 남기지 않는다.

## 설치하는 저장소

앱 하나에 저장소만 고른다. 다음 넷만 설치한다.

| 저장소 |
| --- |
| `minjunkim-dev/repo-baseline` |
| `minjunkim-dev/smallnext` |
| `minjunkim-dev/BGLike` |
| `minjunkim-dev/mobile-runtime` |

다른 저장소, 조직 전체, 계정의 모든 저장소에는 설치하지 않는다. 새 저장소를 더할 때는 이 표를 먼저 고친다.

확인: 버린 브랜치에 열린 Draft PR을 만든다. 본문에 리뷰 근거를 채우지 않는다. 위 Keychain 흐름으로, `--dry-run` 없이 그 PR의 현재 head에 `failure`를 올린다. 앱 이름으로 보이는지 본 뒤 PR을 닫는다. 기본 브랜치와, 리뷰 근거가 있는 PR에는 이 확인을 하지 않는다. head가 아닌 SHA에는 스크립트가 올리지 않는다.

## 기준선에 App ID 넣기

소비 프로젝트의 `.github/repository-settings.json`에는 `review/gate`의 `app_id`를 **전용 앱의 정수**로 둔다. 이 저장소(repo-baseline)의 기록은 **`5641238`**이다. `templates/repository-settings.json`을 채울 때는 아직 앱이 없으면 자리표시자를 쓰고, **정수로 바꾸기 전에는** `tools/apply_github_settings.py`가 조회 전에 멈춘다.

`tools/apply_github_settings.py`는 값이 `REPLACE`로 시작하면 조회 전에 멈춘다. `scripts/check_github_settings.py`도 그 문자열인 동안 `validate_profile`이 실패해 UNVERIFIED로 끝난다. 0, -1, 15368은 `review/gate`의 `app_id`로 통과하지 않는다. 적용 도구와 `validate_profile`이 둘 다 거절한다. 정수가 된 뒤에만 계획을 본다.

```bash
python3 tools/apply_github_settings.py .
```

`DIFF`에 `review/gate`의 `app_id`가 그 정수로 가는지만 확인한 뒤, 소유자가 승인하고 `--apply`한다. 이 설계 PR은 그 명령을 실행하지 않는다. smallnext, BGLike, mobile-runtime은 각자 기준선 PR에서 같은 context를 더한다. 그 PR도 보호를 적용하지 않는다. 적용은 각 저장소에서 소유자가 Mac으로 한다. repo-baseline의 E 재시험 기록을 Issue #32에 남기기 전에는 그 셋을 적용하지 않는다.

### 적용 전후

2026-11-06에 각 저장소 `main`의 `.github/repository-settings.json`을 읽었다. 서버의 branch protection은 이 환경의 토큰으로 조회하지 못했다(403). 카나리 E는 repo-baseline의 서버 보호가 `Review status`를 15368에 고정하고 있었음을 보였다. 아래 오른쪽 열은 기준선 파일의 계획이다. 아직 서버에 쓰지 않았다. `strict`는 네 저장소 모두 true이고 유지한다. 기존 체크는 빼지 않는다.

| 저장소 | 적용 전 필수 context (`app_id`) | 적용 후 |
| --- | --- | --- |
| repo-baseline | `Baseline checks (Python 3.11)` 15368, `Baseline checks (Python 3.13)` 15368, `Review status` 15368 | 왼쪽을 유지하고 `review/gate`를 전용 앱 ID에 추가 |
| smallnext | `PR conventions` 15368, `Repository hygiene` 15368, `Project checks` 15368, `Review status` 15368 | 왼쪽을 유지하고 `review/gate`를 전용 앱 ID에 추가 |
| BGLike | `policy / PR conventions and scope` 15368, `smoke` 15368, `CI` 15368, `Review status` 15368 | 왼쪽을 유지하고 `review/gate`를 전용 앱 ID에 추가 |
| mobile-runtime | `CI` 15368, `Review status` 15368 | 왼쪽을 유지하고 `review/gate`를 전용 앱 ID에 추가 |

## 키 교체와 폐기

앱 ID는 키를 바꿔도 그대로다. 보호의 `app_id`는 키 교체만으로 바꾸지 않는다.

교체: 앱 설정에서 새 private key를 만든다. Keychain의 `review-gate-app-key` 항목을 갱신한다. 위 확인과 같이, 근거가 없는 열린 Draft PR의 현재 head에 `failure`를 올려 새 키가 동작하는지 본다. 동작하면 그 경로를 남기고, 그 다음에 앱 설정에서 이전 키를 지운다. 이전 키로 만든 installation token은 만료된다. 이미 올라가 있는 status는 지워지지 않는다.

폐기: 게이트를 올리는 일을 멈춘다. Keychain 항목을 지운다. GitHub에서 키를 지우고, 필요하면 앱 설치를 제거한다. 설치를 빼면 새 `review/gate`를 올리지 못한다. 필수 체크로 남아 있으면 병합은 막힌다. 그것이 실패 닫힘이다. 보호에서 `review/gate`를 빼려면 기준선의 정수를 유지한 채 그 항목을 삭제한 별도 PR을 병합하고, 소유자가 계획을 본 뒤 적용한다. 15368이 `review/gate`를 충족하게 바꾸지 않는다.

## Mac Studio와 팀

서버가 생기기 전에는 키를 Mac에만 둔다. 서버가 생기면 같은 앱과 같은 앱 ID를 유지한 채 pem만 옮긴다.

1. Mac Studio의 게이트 계정 홈에 `0700` 디렉터리와 **또는** 동등한 HSM·Keychain 정책을 둔다. 개발용 Mac, Grok Bot의 컴퓨터, 저장소에는 두지 않는다. 옮긴 뒤 이전 위치의 재사용 가능한 PEM을 지운다.
2. 올리는 주체는 소유자다. 스크립트는 서버에서 돌릴 수 있으나, **키 재사용 자격 증명은 에이전트와 공유하지 않는다.**
3. 증거 status `review/independent`와 `review/security`는 계속 사람 계정의 `gh`로 올린다. 팀 프로필에서는 그 PR을 구현하지 않은 사람이 남긴다. 앱이 그 둘을 대신 올리지 않는다. `STATUS_ACTORS`에 앱 로그인을 넣지 않는다.
4. `AGENTS.md`의 `프로필: 팀`과 승인 수·CODEOWNERS 변경은 `POLICY.md` §9다. 그 설정 쓰기는 소유자 승인 뒤에 `tools/apply_github_settings.py`로 한다. 키 이전과 한 PR에 섞지 않는다.
5. 되돌리기: 서버에서 올리기를 멈추고 키를 Mac의 안전한 저장소로 되돌린다. 앱 ID가 같으면 보호 규칙은 그대로다.

## 카나리 E 재시험

자리표시자를 정수로 바꾸고 repo-baseline에 보호를 적용한 뒤에만 한다. 이 설계 PR에서는 하지 않는다. 시험 workflow를 `main`에 병합하지 않는다. 시험 PR은 닫는다.

1. 버린 브랜치에 다음 workflow만 둔 PR을 연다. 이름은 시험용이다. `pull_request`에서만 돈다.

```yaml
name: canary-e-retest
on:
  pull_request:
permissions:
  checks: write
  statuses: write
jobs:
  forge:
    runs-on: ubuntu-24.04
    steps:
      - name: Post the gate name with the workflow token
        env:
          GH_TOKEN: ${{ github.token }}
          SHA: ${{ github.event.pull_request.head.sha }}
          REPO: ${{ github.repository }}
        run: |
          set -euo pipefail
          gh api "repos/${REPO}/statuses/${SHA}" -f state=success -f context=review/gate -f description=canary-e-retest
          gh api "repos/${REPO}/check-runs" -f name=review/gate -f head_sha="${SHA}" -f status=completed -f conclusion=success -f started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)" -f completed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

2. 통과 조건. 두 API가 201이어도 된다. 체크 run의 앱은 15368이다. status의 작성자는 `github-actions[bot]`이다. 그 PR의 필수 체크 `review/gate`는 충족되지 않는다. GraphQL에서 그 15368 객체의 `isRequired`는 거짓이거나, 필수 context `review/gate`는 전용 앱의 success가 생기기 전까지 대기다. 병합 가능이 아니다.
3. 대조. 소유자가 증거 조건을 만족하는 그 head에 Mac 스크립트로 `review/gate` success를 올린 뒤에만 그 필수 context가 충족된다. 그 다음 workflow를 다시 돌려 같은 이름으로 success를 올려도, 15368 객체가 전용 앱의 필수 조건을 지우지 않는다. 전용 앱이 그 SHA에 failure를 올리면 필수 조건은 다시 실패다.
4. workflow 파일을 지우는 커밋을 넣지 않고 PR을 닫는다. `main`에 `checks: write`로 `review/gate`를 올리는 workflow를 두지 않는다.
5. 결과를 Issue #32 댓글 하나에 적는다. 시각, PR 번호, 위조 run의 앱 ID, 필수 체크가 충족되지 않았다는 문장, 전용 앱 success 뒤의 대조를 적는다. 그 댓글이 없으면 smallnext, BGLike, mobile-runtime의 적용은 멈춘다.

---

## 레거시(선택): reviewgate UID·봉인·sudoers·git archive

다음은 **이전에 문서화했던 강한 분리**다. 별도 macOS 사용자 `reviewgate`, 홈의 0600 PEM, 봉인 디렉터리(`review-gate-seal`), `sudoers`로 허용한 래퍼만 실행, `git archive`로 봉인 트리 갱신, 별도 읽기 전용 토큰 파일 등이다. **1인·소규모 팀의 기본 권장 경로는 아니다.** 운영상 필요할 때만 참고한다. 세부 셸 예시와 해시 절차는 이 문서의 이전 버전(git 기록)을 본다.

핵심 경고는 그대로다: 스크립트는 Keychain을 직접 읽지 않는다. `REVIEW_GATE_APP_KEY`는 일반 파일 경로다. **개발 UID와 같은 홈에서 에이전트가 돌면**, 임시 PEM이 있는 순간 키가 노출될 수 있다. 레거시 배치는 그 분리를 sudo·별도 홈으로 풀었다. Keychain 권장 경로는 **PEM을 에이전트가 읽는 홈에 두지 않는 것**이 첫 목표다.
