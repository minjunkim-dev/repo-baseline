# repo-baseline

1인·소규모 팀이 언어·스택·하네스(어떤 코딩 에이전트든)와 관계없이 바로 안전하게 개발을 시작하게 하는 최소 기준이다.
코어는 복사만 하는 작은 파일 4개와 한 쪽짜리 규칙([POLICY.md](POLICY.md))이다. 나머지는 이유가 있을 때만 켜는 프로필이다.

## 코어 적용 3단계

1. 이 저장소를 받는다(공개, 인증 불필요): `git clone https://github.com/minjunkim-dev/repo-baseline`
2. [templates/core/](templates/core/)를 프로젝트에 복사한다. `AGENTS.md`, `REVIEW.md`, `.github/pull_request_template.md`, `.gitignore` 추가분. Claude Code·Codex·Cursor 모두 `AGENTS.md`를 읽으므로 `CLAUDE.md`는 두지 않는다.
3. `AGENTS.md`의 명령 4칸(setup/check/test/build)과 `REVIEW.md`의 빈칸을 채우고, 첫 PR을 슬림 양식으로 연다.

명령은 [docs/start.md](docs/start.md)에 있다. 에이전트에게 맡기려면 [prompts/setup.md](prompts/setup.md) 하나를 첨부한다.

## 프로필

| 프로필 | 언제 켜는가 |
| --- | --- |
| [github](templates/github/) | GitHub에 올릴 때(권장). 브랜치 보호, 필수 CI, push protection, Dependabot, CI 골격, 에이전트 권한 예시 |
| [pr-conventions](profiles/pr-conventions/) | PR 제목·본문 형식을 CI로 검사하고 싶을 때 |
| [hash-copy](profiles/hash-copy/) | 공통 검사기를 해시로 고정해 여러 저장소에 똑같이 두고 싶을 때(Python 필요) |
| [team](profiles/team/) | 2명 이상. CODEOWNERS와 사람 승인 |
| [matt-skills](profiles/matt-skills/) | 리뷰의 두 축 판단·회고·PR 본문을 Matt Pocock 스킬에 맡기고 싶을 때. 켜면 스킬 설치가 규칙이다(설치 확인 스크립트) |
| [pstack](profiles/pstack/) | pstack 스킬을 쓸 때. 기본 동작 중 이 기준과 어긋나는 것(병합, 바로 반영, 규칙 위치)을 `AGENTS.md`에 적는다 |

PR을 열면 [prompts/review.md](prompts/review.md)로 리뷰한다. 되돌리기 쉬움이고 신뢰 경계를 건드리지 않으면 구현 세션의 하위 에이전트가 리뷰해도 되고, 어려움이거나 신뢰 경계를 건드리면 새 세션이 리뷰한다. 리뷰하는 기기에는 이 저장소의 클론과 Python 3.9 이상이 있어야 한다(리뷰 전 확인 스크립트).
회고는 정기 실행하지 않는다. 같은 지적이 반복될 때 [prompts/retro.md](prompts/retro.md)를 실행한다.

## 적용 중인 프로젝트

세 곳 모두 코어(`AGENTS.md`·`REVIEW.md`)와 github 프로필로 옮겼다(#71).

| 프로젝트 | 저장소 |
| --- | --- |
| Smallnext | `minjunkim-dev/smallnext` |
| BGLike | `minjunkim-dev/BGLike` |
| Runstir | `minjunkim-dev/mobile-runtime` |

## 그 밖에

- 비밀값은 이 저장소에 두지 않는다. 보안 문제 보고는 [SECURITY.md](SECURITY.md).
- 변경 기록: [CHANGELOG.md](CHANGELOG.md). 재설계 전 기록은 [CHANGELOG-2026.md](https://github.com/minjunkim-dev/repo-baseline/blob/c3f6d569871f51b83c1405dee34db6850a0b30e3/docs/archive/CHANGELOG-2026.md)(지운 보관 문서의 마지막 판).
