# repo-baseline

1인·소규모 팀이 언어·스택·하네스(어떤 코딩 에이전트든)와 관계없이 바로 안전하게 개발을 시작하게 하는 최소 기준이다.
코어는 복사만 하는 작은 파일 5개와 한 쪽짜리 규칙([POLICY.md](POLICY.md))이다. 나머지는 이유가 있을 때만 켜는 프로필이다.

> 재설계 중(2026-11). 정본은 [docs/redesign-2026-11.md](docs/redesign-2026-11.md), 진행 상태는 [추적 이슈 #73](https://github.com/minjunkim-dev/repo-baseline/issues/73)이다.

## 코어 적용 3단계

1. 이 저장소를 받는다(공개, 인증 불필요): `git clone https://github.com/minjunkim-dev/repo-baseline`
2. [templates/core/](templates/core/)를 프로젝트에 복사한다. `AGENTS.md`, `CLAUDE.md`, `REVIEW.md`, `.github/pull_request_template.md`, `.gitignore` 추가분.
3. `AGENTS.md`의 명령 4칸(setup/check/test/build)과 `REVIEW.md`의 빈칸을 채우고, 첫 PR을 슬림 양식으로 연다.

명령은 [docs/start.md](docs/start.md)에 있다. 에이전트에게 맡기려면 [prompts/setup.md](prompts/setup.md) 하나를 첨부한다.

## 프로필

| 프로필 | 언제 켜는가 |
| --- | --- |
| [github](templates/github/) | GitHub에 올릴 때(권장). 브랜치 보호, 필수 CI, push protection, Dependabot, CI 골격, 에이전트 권한 예시 |
| [review-gate](profiles/review-gate/) | 에이전트의 무단 병합이나 승인 위조를 기계적으로 막아야 할 때. 전용 앱이 필수 status를 올린다 |
| [pr-conventions](profiles/pr-conventions/) | PR 제목·본문 형식을 CI로 검사하고 싶을 때 |
| [hash-copy](profiles/hash-copy/) | 공통 검사기를 해시로 고정해 여러 저장소에 똑같이 두고 싶을 때(Python 필요) |
| [team](profiles/team/) | 2명 이상. CODEOWNERS와 사람 승인 |

회고는 정기 실행하지 않는다. 같은 지적이 반복될 때 [prompts/retro.md](prompts/retro.md)를 실행한다.

## 적용 중인 프로젝트

옛 구조(전체 manifest·해시 검사)를 쓴다. 새 코어로의 이전은 W9에서 레포마다 한다.

| 프로젝트 | 저장소 |
| --- | --- |
| Smallnext | `minjunkim-dev/smallnext` |
| BGLike | `minjunkim-dev/BGLike` |
| Runstir | `minjunkim-dev/mobile-runtime` |

## 그 밖에

- 비밀값은 이 저장소에 두지 않는다. 보안 문제 보고는 [SECURITY.md](SECURITY.md).
- 변경 기록: [CHANGELOG.md](CHANGELOG.md). 재설계 전 기록은 [docs/archive/CHANGELOG-2026.md](docs/archive/CHANGELOG-2026.md).
