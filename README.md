# repo-baseline

1인·소규모 팀이 언어·스택·에이전트 도구(어떤 코딩 에이전트든)와 관계없이 바로 안전하게 개발을 시작하게 하는 최소 기준이다.
코어는 복사만 하는 작은 파일 4개와 한 쪽짜리 규칙([POLICY.md](POLICY.md))이다. GitHub에 올리면 github 프로필도 켠다. 배포하는 앱이면 ops 프로필도 켠다. 나머지는 이유가 있을 때만 켜는 프로필이다.

## 코어 적용 3단계

1. 이 저장소를 받는다(공개, 인증 불필요): `git clone https://github.com/minjunkim-labs/repo-baseline`
2. [templates/core/](templates/core/)를 프로젝트에 복사한다. `AGENTS.md`, `REVIEW.md`, `.github/pull_request_template.md`, `.gitignore` 추가분. Claude Code·Codex·Cursor 모두 `AGENTS.md`를 읽으므로 `CLAUDE.md`는 두지 않는다.
3. `AGENTS.md`의 명령 4칸(setup/check/test/build)과 `REVIEW.md`의 빈칸을 채우고, 첫 PR을 슬림 양식으로 연다.

명령은 [docs/start.md](docs/start.md)에 있다. 에이전트에게 맡기려면 [prompts/setup.md](prompts/setup.md) 하나를 첨부한다.

## 프로필

| 프로필 | 언제 켜는가 |
| --- | --- |
| [github](templates/github/) | GitHub에 올리면 켠다(POLICY §5가 브랜치 보호·필수 CI·머지 큐를 요구한다). 브랜치 보호, 필수 CI, push protection, Dependabot, CI 골격, SECURITY.md, CodeRabbit 한국어 리뷰 설정, 에이전트 권한 예시 |
| [pr-conventions](profiles/pr-conventions/) | PR 제목·본문 형식을 CI로 검사하고 싶을 때 |
| [team](profiles/team/) | 2명 이상. CODEOWNERS와 사람 승인 |
| [matt-skills](profiles/matt-skills/) | 리뷰의 두 축 판단·회고·PR 본문을 Matt Pocock 스킬에 맡기고 싶을 때. 켜면 스킬 설치가 규칙이다(설치 확인 스크립트) |
| [ops](profiles/ops/) | 배포해서 사람이 쓰는 앱이면 켠다. 보안·에러 추적·제품 분석·감시 도구를 모두 쓰고, 빼는 도구만 이유와 함께 적는다. 조직에서 한 번 켤 것과 소비 레포마다 할 것, 비밀값 이름 |
| [pstack](profiles/pstack/) | pstack 스킬을 쓸 때. 기본 동작 중 이 기준과 어긋나는 것(병합, 바로 반영, 규칙 위치)을 `AGENTS.md`에 적는다 |

위 프로필은 규칙을 더한다. [hash-copy](profiles/hash-copy/)는 규칙이 아니라 이 저장소의 파일을 소비 레포에 복사하는 도구다. 공통 검사기를 해시로 고정해 여러 저장소에 똑같이 두고 싶을 때 쓴다(Python 필요).

PR을 열면 [prompts/review.md](prompts/review.md)로 리뷰한다. 되돌리기 쉬움이고 민감한 파일을 건드리지 않으면 구현 세션의 하위 에이전트가 리뷰해도 되고, 어려움이거나 민감한 파일을 건드리면 새 세션이 리뷰한다. 리뷰하는 기기에는 이 저장소의 클론과 Python 3.9 이상이 있어야 한다(리뷰 전 확인 스크립트).
회고는 정기 실행하지 않는다. 같은 지적이 반복될 때 [prompts/retro.md](prompts/retro.md)를 실행한다.

## 적용 중인 프로젝트

동기화 PR을 받는 저장소 목록은 [tools/consumers.json](tools/consumers.json)이다. 이 표는 적용 현황이고, 동기화 대상 목록이 아니다. 2026-11-18 기준으로 아래 여섯 곳 모두 코어(`AGENTS.md`·`REVIEW.md`·PR 템플릿)와 github 프로필(`.github/repository-settings.json`)이 있다. 이 저장소도 같은 구성을 쓴다. 서버 설정이 파일과 맞는지는 소유자가 `tools/apply_github_settings.py` 계획 모드로 확인한다. repo-office 연결은 `docs/agents/office.md`가 있는 곳이다.

| 프로젝트 | 저장소 | repo-office |
| --- | --- | --- |
| Smallnext | `minjunkim-labs/smallnext` | 연결 |
| BGLike | `minjunkim-labs/BGLike` | 연결 |
| Runstir | `minjunkim-labs/mobile-runtime` | 연결 |
| answer-desk | `minjunkim-labs/answer-desk` | 없음 |
| portfolio | `minjunkim-labs/portfolio` | 없음 |
| repo-office | `minjunkim-labs/repo-office` | 해당 없음 |

## 그 밖에

- 비밀값은 이 저장소에 두지 않는다. 보안 문제 보고는 [SECURITY.md](SECURITY.md).
- 변경 기록: [changelog.d/](changelog.d/)(2026-11-17부터, PR마다 파일 하나)와 [CHANGELOG.md](CHANGELOG.md)(그 전). 재설계 전 기록은 [CHANGELOG-2026.md](https://github.com/minjunkim-labs/repo-baseline/blob/c3f6d569871f51b83c1405dee34db6850a0b30e3/docs/archive/CHANGELOG-2026.md)(지운 보관 문서의 마지막 판).
