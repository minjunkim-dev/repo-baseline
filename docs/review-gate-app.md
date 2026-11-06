# review/gate 전용 GitHub App

이 문서는 `POLICY.md` §5의 승인 경계를 Mac에서 만드는 절차다. 이 저장소의 PR은 설계와 도구와 기대값만 둔다. 앱을 만들지 않고, branch protection을 쓰지 않고, status를 올리지 않고, 병합하지 않는다.

## 무엇을 고정하나

승인 경계는 commit status `review/gate`다. 체크 run이 아니다.

카나리 E(2026-11-06, PR #39)는 필수 체크 `Review status`가 `app_id` 15368일 때, `checks: write`인 workflow의 `GITHUB_TOKEN`이 같은 이름의 체크 run을 success로 올리면 그 run도 앱 15368이고 최신 conclusion이 필수 조건을 통과시킨다는 것을 보였다. Actions 잡과 위조 run이 같은 종류의 객체이고 같은 앱이다.

전용 앱은 Commit statuses 쓰기와 Metadata 읽기만 가진다. Checks 권한이 없으므로 체크 run을 만들지 못한다. 브랜치 보호는 `{"context": "review/gate", "app_id": <그 앱의 정수 ID>}`로 고정한다. workflow 토큰이 같은 context로 commit status나 체크 run을 올려도 그 객체의 앱은 15368이다. 게시는 201일 수 있다. 그 객체는 필수 조건이 아니다.

`Review status` workflow는 증거 검사로 남긴다. `review/independent`, `review/security`, 승인 댓글, 근거 표를 읽고 없으면 실패한다. `review/gate`를 쓰지 않는다. 필수 목록에는 `app_id` 15368으로 남는다. 그 초록색은 승인 경계가 아니다. 15368은 같은 이름의 체크 run을 위조할 수 있다. 스크립트는 그 체크의 conclusion을 읽지 않는다.

`strict`는 true다. 새 head에는 `review/gate`가 없다. 인자 SHA가 열린 PR의 현재 head와 다르면 스크립트는 올리지 않는다. 조회 실패, 키가 0600 일반 파일이 아님, `GITHUB_ACTIONS`가 설정됨은 아무것도 올리지 않는다. 근거가 실패하면 그 SHA에 `failure`를 올려 이 앱이 이전에 올린 success를 지운다. 닫힌 PR, head 불일치, 기본 브랜치가 아닌 base에는 올리지 않는다.

Dependabot 버전 전용 예외는 `scripts/check_review_status.py`와 같다. 브랜치 보호는 작성자별로 빼지 못하므로 `review/gate`는 그 PR에도 필요하다. 버전·해시·Action SHA만 바꾼 Dependabot PR이면 스크립트는 두 리뷰 status 없이 success를 올린다. 다른 줄이 있으면 올리지 않고 failure다. 면제를 켜는 별도 플래그는 없다. 신뢰 경계 파일은 `uses:`의 40자 SHA 또는 `v` 태그 pin만 버전 전용이다. 짧은 해시, `\r`, 그 밖의 제어 문자, U+2028, U+2029가 있으면 버전 전용이 아니다. `previous_filename`이 있거나 `status`가 `modified`가 아니면 버전 전용이 아니다. 워크플로 밖으로 이름을 바꾸는 pin-only diff도 면제가 아니다. 작성자 쪽(REST나 web-flow로 Dependabot처럼 만든 커밋)은 아직 증명되지 않았다. 그 면제를 쓰기 전에 카나리로 확인한다.

근거 status의 이어받기는 이 게이트에 쓰지 않는다. `review/independent`와 `review/security`는 이 head에 success여야 한다. 1인 프로필에서 작성자는 저장소 소유자 또는 `STATUS_ACTORS`다. `STATUS_ACTORS`는 비어 있다. 이 앱의 로그인을 거기에 넣지 않는다. 앱은 `review/gate`만 올린다. 로그인이 `[bot]`으로 끝나면 1인·팀 모두 그 status를 받지 않는다. `github-actions[bot]`이 올린 리뷰 status는 실패다. 승인 댓글의 작성자가 `[bot]`이면 그 댓글도 승인이 아니다.

## 승인 때 Mac에서 하는 일

오늘 `/tmp/approve.sh`는 `review/independent`와 `review/security`를 올리고, 되돌리기 어려움이면 댓글 `되돌리기 어려움 승인: <SHA>`를 단다. 그 다음에 봉인 사본으로 게이트를 올린다. 체크아웃의 `python3 tools/post_review_gate.py`는 실행 경로가 아니다. 에이전트는 세 가지 모두를 실행하지 않는다.

증거 status와 승인 댓글은 개발 계정의 `gh` 키링으로 올린다. 그 셸에 `GH_TOKEN`을 두지 않는다. 게이트 프로세스만 다른 UID로 돈다. 그 UID의 `GH_TOKEN`은 읽기 전용 토큰 파일이고, 개발 계정의 `gh auth token`이 아니다. 앱 토큰은 status POST 한 번에만 쓴다.

스크립트는 Keychain 항목을 읽지 않는다. `REVIEW_GATE_APP_KEY`는 일반 파일이고, 모드가 `0600`이며, symlink가 아니고, 봉인 트리 안이 아니어야 한다. 아래 첫 번째 배치가 그 조건이다. 두 번째 배치는 Keychain을 그 파일로 꺼내는 약한 방법이다. 둘을 섞지 않는다.

```bash
set -euo pipefail
unset GH_TOKEN
SHA="<현재 head의 전체 SHA>"
REPO="minjunkim-dev/repo-baseline"
PR="<번호>"
# 개발 계정의 $HOME이 아니다. reviewgate 사용자의 홈이다.
GATE_USER=reviewgate
GATE_HOME=/Users/reviewgate
SEAL="$GATE_HOME/.config/repo-baseline/review-gate-seal"

gh api "repos/${REPO}/statuses/${SHA}" -f state=success -f context=review/independent \
  -f description="<도구> <모델> 지적 <수>"
# Security를 실행했을 때만.
gh api "repos/${REPO}/statuses/${SHA}" -f state=success -f context=review/security \
  -f description="<도구> <모델> 지적 <수>"
# 되돌리기 어려움만. 댓글을 고치지 말고 새로 단다.
gh pr comment "$PR" --repo "$REPO" --body "되돌리기 어려움 승인: ${SHA}"

# 키와 읽기 토큰은 이 셸에 들어오지 않는다. 래퍼가 reviewgate의 홈에서만 읽는다.
# 에이전트 셸에서 이 sudo를 실행하지 않는다. bash -s는 허용하지 않는다.
# NOPASSWD가 없으므로 암호를 묻는다. timestamp_timeout=0이라 캐시되지 않는다.
sudo -u "$GATE_USER" -H env HOME="$GATE_HOME" \
  "$GATE_HOME/.config/repo-baseline/review-gate-run" "$SHA" "$REPO" "$PR"
```

이 `sudo`는 소유자가 직접 실행한다. 개발 계정에 `NOPASSWD`가 있거나 sudo 암호가 캐시되어 있으면, 같은 UID의 에이전트가 `reviewgate` 홈의 pem을 `cat`한다. `bash -s`는 임의의 코드라 sudoers로 한 명령으로 좁힐 수 없다. 허용 명령은 그 래퍼 파일 하나다. 조건은 「첫 키를 넣기 전에」다.

같은 UID의 Keychain만 쓸 때(두 번째 계정 전)는 위 `sudo` 대신 아래 서브셸을 쓴다. Keychain은 원본이고, 스크립트에 넘기는 값은 그 실행의 일반 파일이다. 서브셸이 끝나면 `GH_TOKEN`은 개발 셸에 남지 않는다. 앞뒤의 `gh`는 개발 계정의 키링으로 남는다. `trap`은 서브셸이 끝날 때 임시 파일을 지운다. `rm -P`는 APFS에서 덮어쓰기를 보장하지 않는다. 보호는 파일을 지우는 것과, 그 파일이 살아있는 시간이 짧은 것이다. 서 있는 pem을 개발 홈에 두지 않는다. 그 파일이 있는 동안 같은 UID의 에이전트는 Keychain과 임시 파일을 읽는다. 봉인 트리를 그 UID가 소유하면 스크립트와 해시를 같이 고쳐 `shasum -c`가 의미가 없다. 첫 번째 배치와 같지 않다.

```bash
(
  set -euo pipefail
  SEAL="/var/review-gate/review-gate-seal"
  KEY=$(mktemp -t review-gate-key)
  chmod 0600 "$KEY"
  trap 'rm -P "$KEY"' EXIT
  security find-generic-password -a "$USER" -s review-gate-app-key -w > "$KEY"
  TOKEN=$(security find-generic-password -a "$USER" -s review-gate-read-token -w)
  cd "$SEAL"
  /usr/bin/shasum -a 256 -c /var/review-gate/seal.sha256
  export REVIEW_GATE_APP_KEY="$KEY"
  export REVIEW_GATE_APP_ID="<앱 ID>"
  set +e
  dry=$(GH_TOKEN="$TOKEN" python3 -I "$SEAL/tools/post_review_gate.py" --repo "$REPO" --pr "$PR" --sha "$SHA" --dry-run)
  set -e
  printf '%s\n' "$dry"
  kind=$(printf '%s\n' "$dry" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read().splitlines()[-1])["kind"])')
  if [ "$kind" = success ] || [ "$kind" = failure ]; then
    GH_TOKEN="$TOKEN" python3 -I "$SEAL/tools/post_review_gate.py" --repo "$REPO" --pr "$PR" --sha "$SHA"
  else
    echo "review gate not posted: $kind" >&2
    exit 1
  fi
)
```

`--dry-run`은 근거를 읽고 올릴 state를 출력한다. 토큰을 만들지 않고 POST하지 않는다. 표준 출력의 마지막 줄은 JSON이다. `kind`가 `success` 또는 `failure`이면 같은 인자로 dry-run 없이 실행한다. `failure`는 그 SHA에 failure를 올려 이 앱의 이전 success를 지운다. `set -e`만 두면 dry-run의 종료 코드 1이 그 갱신을 건너뛴다. `skip`과 `unverified`는 POST하지 않는다. 실실행이 끝나기 전에는 병합하지 않는다.

스크립트는 저장소 밖 0600 파일만 키로 받는다. symlink, 저장소 안의 경로, 다른 모드는 거부한다. `GITHUB_ACTIONS`가 있으면 거부한다.

## 앱 만들기

소유자가 브라우저에서 한다. 이 절차를 Actions나 클라우드 에이전트에 맡기지 않는다.

1. GitHub 개인 계정에서 GitHub App을 등록한다. [앱 등록](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app). 이름 예: `repo-baseline-review-gate`. Homepage URL은 `https://github.com/minjunkim-dev/repo-baseline`이면 된다.
2. Webhook은 끈다. Active를 끄면 Webhook URL이 필요 없다.
3. 권한은 저장소의 Commit statuses: Read and write, Metadata: Read(앱의 기본값)만 켠다. Checks, Contents, Pull requests, Administration, Actions는 끄다. 계정 권한은 비운다.
4. 설치 위치는 Only on this account. 설치가 끝나면 App ID(정수의 앱 ID, 설치 ID가 아니다)를 앱 설정 페이지에서 적는다.
5. Private key를 하나 생성한다. 브라우저 세션은 `reviewgate`의 것이다. 개발 계정의 다운로드 폴더, 개발 홈, `/tmp`, iCloud로 받지 않는다.

## 설치하는 저장소

앱 하나에 저장소만 고른다. 다음 넷만 설치한다.

| 저장소 |
| --- |
| `minjunkim-dev/repo-baseline` |
| `minjunkim-dev/smallnext` |
| `minjunkim-dev/BGLike` |
| `minjunkim-dev/mobile-runtime` |

다른 저장소, 조직 전체, 계정의 모든 저장소에는 설치하지 않는다. 새 저장소를 더할 때는 이 표를 먼저 고친다.

## 첫 키를 넣기 전에

아래는 첫 비밀키를 설치하기 전의 조건이다.

스크립트가 받는 키는 항상 일반 파일이다. Keychain 항목이나 symlink는 받지 않는다. 첫 키 전에는 개발 UID와 다른 macOS 계정 `reviewgate`를 만든다. 키, 읽기 전용 토큰, 봉인 트리, 해시 기록은 그 계정 홈에만 둔다. 개발 계정의 `$HOME`에 두지 않는다. 같은 UID의 Keychain은 그 계정을 만들기 전의 약한 방법이고, 실행할 때마다 일반 파일로 꺼내 쓴 뒤 지운다.

계정과 홈은 소유자가 한 번 만든다. 에이전트 셸에서 하지 않는다. `-password -`는 암호를 묻는다. argv에 넣지 않는다.

```bash
sudo sysadminctl -addUser reviewgate -fullName "review gate" -password - -home /Users/reviewgate -shell /bin/zsh
sudo chmod 0700 /Users/reviewgate
```

홈은 `0700`이고 소유자는 `reviewgate`다. 개발 UID는 그 디렉터리를 열지 못한다. 그 말은 sudo가 없을 때다.

sudo 조건은 이렇다. 개발 계정에 `NOPASSWD`를 주지 않는다. `/etc/sudoers`의 `timestamp_timeout`은 0이다. 에이전트 셸에서 sudo하지 않는다. `sudo -u reviewgate bash -s`는 임의의 코드라 한 줄로 좁힐 수 없다. 허용하는 명령은 `reviewgate`가 소유한 래퍼 하나다. 같은 UID의 에이전트가 sudo를 쓸 수 있으면 pem을 읽는다.

```
Defaults timestamp_timeout=0
<개발 계정> ALL=(reviewgate) /Users/reviewgate/.config/repo-baseline/review-gate-run
```

`NOPASSWD:`를 붙이지 않는다. `ALL`이나 `bash`를 허용하지 않는다. 봉인을 풀 때의 `tar`는 설치할 때 소유자가 직접 실행한다. 그 줄도 `bash`가 아니다. 개발 계정이 `admin`이면 `%admin ALL=(ALL) ALL`이 따로 있다. 암호가 있으면 그 줄로 pem을 읽는다. 이 절차는 그 관리자 권한을 지우지 않는다. 막는 조건은 `NOPASSWD`가 없는 것, `timestamp_timeout=0`, 에이전트 셸에서 sudo하지 않는 것이다.

게이트는 체크아웃에서 실행하지 않는다. `post_review_gate.py`는 자기 파일의 상위 디렉터리 `scripts/`를 `sys.path` 앞에 넣는다. 파일 하나만 복사하면 그 경로에 `check_review_status.py`가 없어 실패하고, 체크아웃 안에서 `python3 -I tools/post_review_gate.py`를 실행하면 같은 이유로 체크아웃의 검사기를 읽는다. `python3 -I`는 `PYTHONPATH`와 스크립트 디렉터리를 `sys.path`에 넣지 않는다. 격리는 봉인 트리가 체크아웃 밖에 있고, 그 트리의 `tools/`와 `scripts/`만 있는 데서 온다.

봉인 집합은 이 세 파일이다. 경로는 저장소와 같게 둔다.

| 봉인 경로 | 하는 일 |
| --- | --- |
| `tools/post_review_gate.py` | 토큰을 만들고 `review/gate`를 올린다 |
| `scripts/check_review_status.py` | 근거 판정. 게이트가 이 파일만 가져온다 |
| `scripts/pr_author.py` | 검사기가 `from pr_author import parse_author`로 읽는다 |

`reviewgate`로 로그인한 셸에서 디렉터리와 래퍼를 만든다. 개발 셸의 `sudo bash`로 만들지 않는다. 기본 macOS에는 `sha256sum`이 없다. 해시는 `/usr/bin/shasum`이다.

```bash
install -d -m 0700 "$HOME/.config/repo-baseline"
install -d -m 0700 "$HOME/.config/repo-baseline/review-gate-seal"
cat > "$HOME/.config/repo-baseline/review-gate-run" <<'EOS'
#!/bin/bash
set -euo pipefail
if [ "$#" -ne 3 ]; then
  echo "usage: review-gate-run SHA REPO PR" >&2
  exit 2
fi
sha=$1 repo=$2 pr=$3
seal="$HOME/.config/repo-baseline/review-gate-seal"
cd "$seal"
/usr/bin/shasum -a 256 -c "$HOME/.config/repo-baseline/seal.sha256"
export GH_TOKEN="$(cat "$HOME/.config/repo-baseline/read-token")"
export REVIEW_GATE_APP_ID="$(cat "$HOME/.config/repo-baseline/app-id")"
export REVIEW_GATE_APP_KEY="$HOME/.config/repo-baseline/review-gate.pem"
set +e
dry=$(python3 -I "$seal/tools/post_review_gate.py" --repo "$repo" --pr "$pr" --sha "$sha" --dry-run)
set -e
printf '%s\n' "$dry"
kind=$(printf '%s\n' "$dry" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read().splitlines()[-1])["kind"])')
if [ "$kind" = success ] || [ "$kind" = failure ]; then
  python3 -I "$seal/tools/post_review_gate.py" --repo "$repo" --pr "$pr" --sha "$sha"
else
  echo "review gate not posted: $kind" >&2
  exit 1
fi
EOS
chmod 0500 "$HOME/.config/repo-baseline/review-gate-run"
```

`python3`은 `sudo`의 `secure_path`에서 보여야 한다. Homebrew면 래퍼 안의 `python3`을 그 절대 경로로 적는다. 래퍼는 `reviewgate` 소유이고 개발 UID가 쓰지 못한다.

archive는 개발 UID로 한다. `sudo git`은 쓰지 않는다. `.git/config`의 filter와 `.gitattributes`의 `export-subst`는 개발 계정이 넣을 수 있다. `sudo git`이면 그 명령이 root로 돈다. `core.hooksPath`를 비운다. 가능하면 방금 받은 깨끗한 clone에서 한다.

```bash
GATE_HOME=/Users/reviewgate
SEAL="$GATE_HOME/.config/repo-baseline/review-gate-seal"
git -C /path/to/clean-clone -c core.hooksPath=/dev/null archive <검토한 커밋> \
  tools/post_review_gate.py scripts/check_review_status.py scripts/pr_author.py \
  | sudo -u reviewgate tar -C "$SEAL" -x
```

해시는 다시 `reviewgate` 셸에서 적는다.

```bash
cd "$HOME/.config/repo-baseline/review-gate-seal"
/usr/bin/shasum -a 256 \
  tools/post_review_gate.py scripts/check_review_status.py scripts/pr_author.py \
  > "$HOME/.config/repo-baseline/seal.sha256"
chmod 0600 "$HOME/.config/repo-baseline/seal.sha256"
```

세 해시는 `reviewgate` 홈의 `seal.sha256`이다. 개발 홈에 복사하지 않는다. 실행 전에 그 계정으로 `/usr/bin/shasum -a 256 -c`가 맞아야 한다. 하나라도 다르면 키를 연결하지 않는다.

두 번째 배치의 봉인 트리는 `/var/review-gate/review-gate-seal`이고, 해시 파일은 `/var/review-gate/seal.sha256`이다. 임시 키는 그 디렉터리 밖이다. 둘 다 `root:wheel`이다. 개발 UID가 소유하면 스크립트와 해시를 같이 바꿀 수 있어 해시 검사는 의미가 없다. 만드는 것도 소유자가 직접 한다.

```bash
sudo install -d -m 0755 -o root -g wheel /var/review-gate
sudo install -d -m 0755 -o root -g wheel /var/review-gate/review-gate-seal
git -C /path/to/clean-clone -c core.hooksPath=/dev/null archive <검토한 커밋> \
  tools/post_review_gate.py scripts/check_review_status.py scripts/pr_author.py \
  | sudo tar -C /var/review-gate/review-gate-seal -x
sudo chown -R root:wheel /var/review-gate
sudo chmod -R u=rwX,go=rX /var/review-gate
( cd /var/review-gate/review-gate-seal && /usr/bin/shasum -a 256 \
  tools/post_review_gate.py scripts/check_review_status.py scripts/pr_author.py ) \
  | sudo tee /var/review-gate/seal.sha256 >/dev/null
sudo chown root:wheel /var/review-gate/seal.sha256
sudo chmod 0644 /var/review-gate/seal.sha256
```

## 키를 Mac에 두기

첫 번째 배치. pem은 `reviewgate`의 일반 파일이다. 봉인 디렉터리의 옆이지 안은 아니다. 스크립트는 봉인 트리 안을 거절한다.

`reviewgate`로 로그인한 브라우저가 pem을 그 계정의 다운로드 폴더에 받는다. 그 셸에서 복사하고, 그 원본을 지운다. 개발 홈에는 pem이 없다. 개발 셸의 히스토리에 pem이나 토큰을 남기지 않는다.

```bash
install -d -m 0700 "$HOME/.config/repo-baseline"
install -m 0600 "$HOME/Downloads/<downloaded>.pem" "$HOME/.config/repo-baseline/review-gate.pem"
rm -P "$HOME/Downloads/<downloaded>.pem"
umask 077
cat > "$HOME/.config/repo-baseline/read-token"
printf '%s\n' '<앱 설정의 App ID>' > "$HOME/.config/repo-baseline/app-id"
chmod 0600 "$HOME/.config/repo-baseline/read-token" "$HOME/.config/repo-baseline/app-id"
```

`cat`은 토큰을 붙여 넣고 Ctrl-D로 끝낸다. 소유자는 `reviewgate`다. sudo가 없으면 개발 UID는 이 홈을 읽지 못한다. `NOPASSWD`이거나 sudo 암호가 캐시되어 있으면 그 분리는 없다. 에이전트 셸의 sudo가 pem을 읽는다. iCloud, 동기화 폴더, 저장소, Grok Bot이 쓰는 컴퓨터, 클라우드 에이전트 환경에는 복사하지 않는다. 키 내용을 환경 변수나 argv에 넣지 않는다.

개발 홈을 경유하지 않는 것이 기본이다. `/Users/Shared`는 그 브라우저를 쓸 수 없을 때만 쓴다. `reviewgate`의 `rm`은 개발 계정의 `~/Downloads`를 지우지 못한다. 각 원본은 그 파일을 소유한 계정이 지운다. 복사가 끝난 뒤 둘 다 없어야 한다.

```bash
# 개발 셸. 소유자가 직접 한다. 에이전트 셸이 아니다.
sudo install -m 0600 -o reviewgate -g staff \
  "$HOME/Downloads/<downloaded>.pem" /Users/Shared/review-gate.pem
rm -P "$HOME/Downloads/<downloaded>.pem"
```

```bash
# reviewgate 셸
install -m 0600 /Users/Shared/review-gate.pem "$HOME/.config/repo-baseline/review-gate.pem"
rm -P /Users/Shared/review-gate.pem
```

두 번째 배치를 쓸 때만, 같은 내용을 Keychain 항목 `review-gate-app-key`와 `review-gate-read-token`에 둔다. 개발 홈의 `review-gate.pem`은 만들지 않는다. 승인 절차의 `mktemp`가 그 항목을 스크립트가 읽는 일반 파일로 만든다.

확인: 버린 브랜치에 열린 Draft PR을 만든다. 본문에 리뷰 근거를 채우지 않는다. 고른 배치의 승인 명령으로, `--dry-run` 없이 그 PR의 현재 head에 `failure`를 올린다. 앱 이름으로 보이는지 본 뒤 PR을 닫는다. 기본 브랜치와, 리뷰 근거가 있는 PR에는 이 확인을 하지 않는다. head가 아닌 SHA에는 스크립트가 올리지 않는다.

## 기준선에 App ID 넣기

`.github/repository-settings.json`의 `review/gate` `app_id`는 지금 문자열 `REPLACE:<APP_ID>`다. 이것은 자리표시자다. 앱을 만든 뒤 그 문자열 전체를 앱 설정의 App ID 정수로 바꾼다. 따옴표 없는 숫자다. 15368을 넣지 않는다. 0을 넣지 않는다.

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

교체: 앱 설정에서 새 private key를 만든다. 첫 번째 배치면 `reviewgate` 홈의 `review-gate.pem`만 바꾼다. 두 번째 배치면 Keychain 항목만 바꾸고, 시험은 그 실행의 임시 파일을 본다. 개발 홈에 옛 pem을 남기지 않는다. 위 확인과 같이, 근거가 없는 열린 Draft PR의 현재 head에 `failure`를 올려 새 키가 동작하는지 본다. 동작하면 그 경로를 남기고, 그 다음에 앱 설정에서 이전 키를 지우고 디스크의 이전 pem을 지운다. 이전 키로 만든 installation token은 만료된다. 이미 올라가 있는 status는 지워지지 않는다.

폐기: 게이트를 올리는 일을 멈춘다. pem을 지운다. GitHub에서 키를 지우고, 필요하면 앱 설치를 제거한다. 설치를 빼면 새 `review/gate`를 올리지 못한다. 필수 체크로 남아 있으면 병합은 막힌다. 그것이 실패 닫힘이다. 보호에서 `review/gate`를 빼려면 기준선의 정수를 유지한 채 그 항목을 삭제한 별도 PR을 병합하고, 소유자가 계획을 본 뒤 적용한다. 15368이 `review/gate`를 충족하게 바꾸지 않는다.

## Mac Studio와 팀

서버가 생기기 전에는 키를 Mac에만 둔다. 서버가 생기면 같은 앱과 같은 앱 ID를 유지한 채 pem만 옮긴다.

1. Mac Studio의 게이트 계정 홈에 `0700` 디렉터리와 `0600` pem을 둔다. 그 계정은 개발 UID가 아니다. 개발용 Mac, Grok Bot의 컴퓨터, 저장소에는 두지 않는다. 옮긴 뒤 Mac의 pem을 지운다.
2. 올리는 주체는 소유자다. 스크립트는 서버에서 돌린다. 팀원이 키를 받지 않는다.
3. 증거 status `review/independent`와 `review/security`는 계속 사람 계정의 `gh`로 올린다. 팀 프로필에서는 그 PR을 구현하지 않은 사람이 남긴다. 앱이 그 둘을 대신 올리지 않는다. `STATUS_ACTORS`에 앱 로그인을 넣지 않는다.
4. `AGENTS.md`의 `프로필: 팀`과 승인 수·CODEOWNERS 변경은 `POLICY.md` §9다. 그 설정 쓰기는 소유자 승인 뒤에 `tools/apply_github_settings.py`로 한다. 키 이전과 한 PR에 섞지 않는다.
5. 되돌리기: 서버에서 올리기를 멈추고 pem을 Mac의 0600 경로로 되돌린다. 앱 ID가 같으면 보호 규칙은 그대로다.

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
