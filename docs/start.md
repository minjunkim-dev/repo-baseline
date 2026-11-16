# 새 프로젝트 시작

빈 프로젝트(또는 기존 프로젝트)에 코어를 적용한다. `cp` 몇 번이면 끝난다. Python은 필요 없다.

## 1. 코어 복사

프로젝트 루트에서 실행한다.

```bash
git rev-parse --git-dir >/dev/null 2>&1 || git init   # 빈 프로젝트면 저장소부터 만든다
git clone --depth 1 https://github.com/minjunkim-dev/repo-baseline /tmp/repo-baseline
B=/tmp/repo-baseline/templates/core
cp -n "$B/AGENTS.md" "$B/REVIEW.md" .
mkdir -p .github && cp -n "$B/pull_request_template.md" .github/
{ echo; cat "$B/gitignore"; } >> .gitignore   # 앞의 echo는 기존 마지막 줄과 붙지 않게 한다
```

- `cp -n`은 있는 파일을 덮어쓰지 않는다. `AGENTS.md`·`REVIEW.md`가 이미 있으면 템플릿 내용을 손으로 합친다. macOS의 `cp -n`은 파일을 건너뛸 때도 종료 코드 1을 낸다. 진짜 복사 실패도 같은 코드이므로, 종료 코드로 판단하지 말고 오류 메시지와 4단계 확인 결과를 본다.
- `.gitignore`는 덮어쓰지 않고 뒤에 붙인다.
- `CLAUDE.md`는 만들지 않는다. Claude Code는 `CLAUDE.md`·`.claude/CLAUDE.md`·`CLAUDE.local.md`가 없으면 `AGENTS.md`를 읽는다([Memory](https://code.claude.com/docs/en/memory), 확인일 2026-11-09). 둘 다 있으면 기본 설정에서 `CLAUDE.md`만 읽으므로, 이미 있으면 내용을 `AGENTS.md`로 옮기고 `CLAUDE.md`를 지운다(또는 `@AGENTS.md` 한 줄만 남긴다). `CLAUDE.local.md`·`.claude/CLAUDE.md`나 상위 폴더의 `CLAUDE.md`가 있어도 `AGENTS.md`를 읽지 않으니, 4단계에서 함께 확인한다.

## 2. AGENTS.md 채우기

- 첫 줄 제목과 한두 문장 설명.
- 명령 4칸: setup, check(포맷·린트·타입 등 결정적 검사), test, build. 없는 칸은 `N/A: <이유>`다. 각 명령을 한 번씩 실제로 돌려 본다.
- 길잡이 표: 주요 경로와 설명.

60줄을 넘기지 않는다. 에이전트가 매 세션 읽는 파일이다.

## 3. REVIEW.md 채우기

- 실패로 보는 것: 프로젝트 영역별 행.
- 심각도의 P2 상한 `<N>`.
- 건너뛸 것: 생성 파일, vendor 경로.
- 민감한 파일: 인증·결제·권한·migration 경로([POLICY.md](../POLICY.md) §4).

## 4. 확인

```bash
grep -nE '<[^>]+>' AGENTS.md REVIEW.md   # N/A: <이유>와 배운 규칙 형식 예시만 남아야 한다
git check-ignore -q .env && git check-ignore -q .env.local && echo ignored
ls CLAUDE.md CLAUDE.local.md .claude/CLAUDE.md 2>/dev/null   # 나온 파일은 내용을 AGENTS.md로 옮긴 뒤 지우거나 @AGENTS.md(.claude/ 안은 @../AGENTS.md) 한 줄로 바꾼다. 출력이 없거나 포인터 한 줄뿐이면 통과다   # 예외 줄(`!.env`)이 있거나 이미 커밋돼 있으면 출력이 없다
```

## 5. 첫 PR

브랜치를 만들고 커밋한 뒤 PR을 연다. 본문은 `.github/pull_request_template.md`의 슬림 양식이다.

- Author: 쓴 도구와 모델. 사람이면 `사람 / 없음`.
- Summary: 코어 적용. 완료 기준: `AGENTS.md`·`REVIEW.md`에 템플릿 빈칸이 없고 Git이 `.env`·`.env.*`를 무시한다. 전에 통과하던 프로젝트 명령은 그대로 통과한다.
- Evidence: 4칸 명령을 돌린 결과. 돌리지 않은 칸과 이유.
- Merge Danger: 문서만 더했으면 되돌리기 쉬움. 민감한 파일: 없음.
- Review: [prompts/review.md](../prompts/review.md)로 리뷰한 결과. 되돌리기 쉬움이고 민감한 파일을 건드리지 않으면 구현 세션의 하위 에이전트가 리뷰해도 되고, 어려움이거나 민감한 파일을 건드리면 새 세션이 리뷰한다. 리뷰하는 기기에 repo-baseline 클론과 Python 3.9 이상이 필요하다.

이 PR은 문서만 더하면 되돌리기 쉬움이다. 병합은 소유자가 하거나, `POLICY.md` §5의 조건을 갖춘 뒤 에이전트에게 지시한다.

## 판 올리기

이 저장소가 바뀐 뒤 이미 적용한 저장소를 맞추는 법이다. 무엇이 바뀌었는지는 [CHANGELOG.md](../CHANGELOG.md)에서 지난번에 맞춘 뒤의 항목을 본다. 소비 레포가 손으로 옮길 일은 거기에 적혀 있다.

- hash-copy 프로필을 켰으면: 이 저장소의 깨끗한 `origin/main` checkout에서 `python3 profiles/hash-copy/apply_baseline.py <소비 레포 경로>`를 돌리고, 바뀐 파일로 소비 레포에 PR을 연다. 이 도구는 manifest의 대상 파일을 그대로 덮어쓰고, 소비 레포에서 고친 내용이 있어도 멈추지 않는다. 그래서 적용하기 전에 다음을 한다.
  1. 같은 명령에 `--check`를 붙여 돌린다. 파일을 쓰지 않고, 지금 원본과 다른 파일을 `DIFFERS`로 보고한다(그때 종료 코드는 1이다). 원본이 바뀌어도 `DIFFERS`가 되므로, 이것만으로는 누가 바꿨는지 모른다.
  2. 다른 파일마다 소비 레포의 sha256을 manifest(`.github/repo-baseline.json`)에 기록된 `sha256`과 비교한다. 같으면 원본이 바뀐 것이다. 다르면 소비 레포의 수정이다. manifest에 `scripts/check_repo_baseline.py`가 있으면 소비 레포에서 그것을 돌린다. `DRIFT`로 나온 파일이 소비 레포의 수정이다. 없으면 `shasum -a 256 <파일>`로 비교한다.
  3. 소비 레포의 수정이 있으면 덮어쓰기 전에 그 내용(원본 clone의 `git show <source_commit>:<source 경로>`와의 diff. `ecosystems` 항목은 생성한 파일이라 manifest의 `sha256`만 비교한다)을 보고하고, 그 수정을 이 저장소에 반영할지 소유자에게 묻는다. 답을 받은 뒤에 적용한다.
- 손으로 `cp`했으면: 바뀐 코어 파일을 다시 복사한다. `AGENTS.md`·`REVIEW.md`는 덮어쓰지 말고 바뀐 줄만 손으로 합친다.
- 판을 올리는 PR 자체는 소비 레포의 기존 검사기(base 브랜치의 것)로 검사된다. 검사기가 바뀌는 판이면 그 PR 본문은 옛 형식으로 쓴다. 예: 2026-11-14 판의 `되돌리기:` 줄은 옛 검사기가 모르므로, 그 PR 본문에는 `Door: 되돌리기 쉬움`처럼 옛 줄을 쓴다.

## 다음

- GitHub에 올리면 [github 프로필](../templates/github/)을 켠다.
- 다른 프로필은 [README](../README.md)의 표를 보고 필요할 때만 켠다.
- 에이전트에게 맡기려면 [prompts/setup.md](../prompts/setup.md)를 첨부한다.
