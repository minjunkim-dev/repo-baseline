# 새 프로젝트 시작

언어와 기술 스택이 달라도 같은 순서로 개발을 시작한다. 이 문서는 그 공통 경로다. 아래 기본 명령은 파일을 복사하고 대상의 검사를 실행한다. 그 명령은 Python이 아니다. 해시 복사, 정책 검사, 게이트 서명은 이 저장소의 Python 도구이고 이 기본 명령에 넣지 않는다. GitHub 보호, 리뷰 게이트 앱, 특정 모델, 배포 채널은 아래 선택 프로필이다. 이 저장소 자신의 필수 체크와 `review/gate`는 이 문서로 바뀌지 않는다.

코어만 적용한 상태는 GitHub 보호가 켜진 것이 아니다. 그 프로젝트의 Evidence에는 프로필을 `미적용`으로 적는다. 서버 설정과 앱 키는 쓰지 않는다.

## 세 층

공통 계약, 언어 어댑터, 제품 옵션을 한 설치로 섞지 않는다.

- 공통 계약에서 코어가 복사하는 파일은 `.github/pull_request_template.md` 하나다. `templates/repo-baseline.core.json`도 그 파일만 가리킨다. 그 양식은 GitHub pull request 본문이다. GitHub PR을 쓰지 않으면 그 파일을 필수로 두지 않고, 네 칸과 `POLICY.md` §10의 문 판정만 자기 문서에 적는다.
- 설치하지 않고 읽는 것: `POLICY.md`, `docs/development-workflow.md`, Matt `/ask-matt` 다음 `/grill-with-docs`, `/to-spec`, `/to-tickets`, `/implement`. `disable-model-invocation: true`인 스킬은 사용자가 실행한다. `eval.md`는 만들지 않는다.
- 언어 어댑터는 `setup`, `check`, `test`, `build`다. format, lint, type, test, build 도구는 그 스택이 이미 가진 것만 쓴다. 이 저장소는 포매터나 새 의존성을 스택 선택 없이 넣지 않는다. 없는 칸은 `N/A`와 이유다.
- 제품 옵션은 아래 선택 프로필이다. GitHub 전체 manifest, Dependabot, Claude 설정, 리뷰 게이트 앱, pstack, 병합 큐, 단계 배포는 코어 `cp`가 켜지 않는다.
- 이 저장소 자신을 고칠 때의 독립 패밀리 리뷰, 라운드 상한 3, `review/gate`, `POLICY.md` §10은 이 원본의 안전 정책이다. 새 프로젝트의 제품 옵션과 이름이 같아도 코어 복사가 그 정책을 설치하거나 약하게 하지 않는다. GitHub 프로필을 켜면 그 절차가 `POLICY.md`를 따른다. 외부 리뷰와 병합 전 스레드 규칙은 `POLICY.md` §5에 그대로 있다.

예제 명령은 POSIX `cp`와 `sh`다. Git이 있는 clone에서 이 저장소 파일을 복사한다. Git이 없는 환경과, POSIX 셸이 없는 Windows 설치는 확인하지 않았다. 그 환경을 지원한다고 적지 않는다.

## 항상 하는 일

1. 기준 브랜치는 `main` 하나다. 작업 브랜치는 짧다. 병합은 squash다. 절차는 `docs/development-workflow.md`의 트렁크다.
2. 기능을 구현하기 전에 완료 기준을 적는다. 위치는 사용자가 승인한 Matt spec·ticket이다. `eval.md`나 그와 병렬인 검증 루프 파일을 만들지 않는다. 시작은 사용자가 `/ask-matt`를 실행하는 것이다. 이어서 `/grill-with-docs`, `/to-spec`, `/to-tickets`, `/implement`다. `disable-model-invocation: true`인 스킬은 사용자가 실행한다.
3. 프로젝트 문서에 명령 네 칸을 적는다. `setup`, `check`, `test`, `build`. 명령은 그 저장소의 스택이 정한다. 이 저장소는 패키지 매니저나 언어를 지정하지 않는다. Python을 쓰지 않는 프로젝트는 Python setup, `python3 -m unittest`, Python 3.11·3.13 matrix를 이 칸에 넣지 않는다. 없는 칸은 `N/A`와 이유다. `미실행`으로 적지 않는다.
4. 완료 주장은 그 명령의 출력이다. 구현자와 다른 컨텍스트의 검증자는 그 기준의 통과와 실패만 본다. 리뷰어는 그 기준이 놓친 결함을 본다. 두 역할의 결과를 한 기록으로 합치지 않는다. 구현 세션의 자체 점검은 독립 리뷰가 아니다. 리뷰 패밀리는 작성 패밀리와 다르다. 모델 이름은 `docs/development-workflow.md` 역할 분담을 따른다. 그 제품에서 고를 수 없으면 `미실행`이고, 실행한 것으로 적지 않는다.
5. 결정적 검사(복사 해시, 형식, CI)를 에이전트 규칙과 사람 리뷰보다 앞에 둔다. 반복 실수는 `POLICY.md` §6 순서로 구조와 정적 검사에 먼저 반영한다. 새 규칙은 사용자가 고른 것만 넣는다.
6. 문 유형은 `POLICY.md` §10만 정한다. 애매하면 되돌리기 어려움이다. 게이트·설정·앱은 사람이 최종 head를 승인한다. 리뷰·수정 라운드 상한은 3이다(`POLICY.md` §5). 다른 사례의 5라운드나, 같은 문제가 두 번 남은 뒤의 조기 종료 횟수를 이 숫자와 섞지 않는다.
7. 비밀값은 커밋하지 않는다. 장기 비밀은 소유자 Mac에만 둔다. 매니저는 코드를 쓰지 않는다. 구현은 클라우드 코더가 한다.

일회용 작업과 오래 두는 작업은 실패 비용, 의존하는 사람·시스템 수, 교체 비용, 유지 비용으로 구분한다. 엄밀함을 빼지 않는다. 위 표준 경로로 적용 비용을 낮춘다. 개인 실험은 해당 없는 칸을 `N/A`로 둔다. 다른 사람이 의존하기 시작하면 그 프로젝트의 검사 깊이를 올린다.

## 절차

이 저장소를 받아 둔 디렉터리에서 한다. 대상은 빈 프로젝트다. 아래 명령은 Python을 호출하지 않는다.

```bash
mkdir -p /path/to/project/.github /path/to/project/docs
cp .github/pull_request_template.md /path/to/project/.github/pull_request_template.md
```

대상 프로젝트에서 그 스택의 검사만 실행한다. 언어 도구가 없는 최소 예는 다음이다.

```bash
cd /path/to/project
printf '%s\n' '#!/bin/sh' 'echo ok' > check.sh
chmod +x check.sh
sh check.sh
```

작업 문서의 네 칸은 그 명령이거나 `N/A`와 이유다. 제품 기능은 사용자가 `/ask-matt`를 실행한 뒤에 시작한다. 첫 PR 본문은 복사된 `.github/pull_request_template.md`를 따른다. Evidence에 명령, 출력, head SHA, `N/A`를 적는다.

`Baseline checks (Python 3.11)`와 `Baseline checks (Python 3.13)`는 이 저장소 workflow가 그 minor로 unittest를 실제로 돌리는 체크다. 2026-11-07에 `main` 보호가 그 두 context(`app_id` 15368)와 `review/gate`(`app_id` 5641238)를 요구했다. 그 이름을 선언에서 빼거나 workflow에서 지우면, 보호를 바꾸기 전에는 머지가 그 context를 기다리며 멈춘다. 이 변경은 그 두 job을 유지한다. 필수가 아닌 job `Baseline checks`만 더한다. 그 job은 Python 3.15의 최신 patch만 고르고, minor를 `3.x`로 옮기지 않는다. 필수 목록에 넣지 않았고 서버 보호도 적용하지 않는다. 새 프로젝트의 언어 요구가 아니다.

해시가 필요하면 `templates/repo-baseline.core.json`을 대상의 `.github/repo-baseline.json`으로 두고, 이 저장소에서 `python3 tools/apply_baseline.py /path/to/project`를 실행한다. 그 Python은 템플릿을 복사하는 쪽의 도구다. 대상의 setup·test가 아니다. 코어 목록은 PR 본문 양식만 복사하므로 대상에 `.py`를 만들지 않는다.

이미 `templates/repo-baseline.json` 전체를 쓰는 프로젝트는 코어 파일로 manifest를 바꾸지 않는다. 해시 대상이 줄어든다. GitHub 프로필을 나중에 켜려면 전체 템플릿에만 있는 항목을 그 manifest에 더한 뒤 다시 적용한다.

## 선택 프로필

기본으로 켜지 않는다. 그 저장소에 해당할 때만 켠다.

| 프로필 | 언제 | 어디 |
| --- | --- | --- |
| GitHub 검사·Dependabot·리뷰 근거·PR 형식 | 이 기준의 GitHub 저장소로 올릴 때 | `templates/repo-baseline.json` 전체. 절차는 README「새 프로젝트에 적용」. 공개 저장소의 `review-status.yml` 이벤트 정책도 그 절이다 |
| 복사한 Python 검사기 | 그 전체 목록을 해시로 지킬 때 | 적용 기계의 `python3 tools/apply_baseline.py`. 대상 CI는 복사된 검사기만, 그 프로젝트가 고른 `python3` 하나로 돌린다. 3.11·3.13 matrix와 이 저장소의 필수 체크 이름은 복사하지 않는다 |
| 저장소 설정과 `review/gate` | 보호를 서버에 쓸 때 | `templates/repository-settings.json`, `docs/review-gate-app.md`. 앱·보호·병합은 소유자 Mac이다. 이 문서는 적용하지 않는다 |
| Claude Code | 그 런타임을 쓸 때 | `templates/claude-settings.json`, `.claude/skills/` |
| Cursor 등 `.agents`를 읽는 런타임 | 그 런타임을 쓸 때 | `.agents/skills/`의 `matt-code-review`. 전체 manifest는 Claude와 이 경로를 둘 다 복사한다 |
| 모델 로스터 | 이 소유자의 작성과 리뷰 | `docs/development-workflow.md` 역할 분담. 선호를 지우지 않는다. 쓸 수 없는 모델은 `미실행` |
| pstack | 추가 검증·영향 | 같은 문서. Matt 절차를 대체하지 않는다 |
| 병합 큐, 단계 배포, 여러 봇, 상시 감시, 야간 정리 | 그 배포와 운영이 있을 때 | 라이브러리·문서 저장소의 필수 구성이 아니다. 자동 머지는 `POLICY.md` §10이 예약하지 않는다. 이 문서가 그 규칙을 완화하지 않는다 |
| CodeRabbit | 공개 저장소의 외부 리뷰 | 필수 체크가 아니다. 병합 전 스레드는 기존 정책대로 해결한다 |

이 저장소와 smallnext, BGLike, mobile-runtime은 GitHub 프로필을 이미 쓴다. 소비 프로젝트의 `.github/repository-settings.json`은 이 변경이 복사하지 않는다.

## 가져오지 않는 것

특정 조직의 승인 인원, 작성량, 자동 머지, 조직 ruleset, 다중 릴리스 채널을 모든 새 프로젝트의 필수로 두지 않는다. Capital One은 발표자의 배경이다. 특정 은행 시스템의 절차로 옮기지 않는다. 공개 보안 신고 안내 파일은 이 시작 경로가 만들지 않는다. 그 안내는 별도 변경으로 다룬다.

라운드 상한 3은 유지한다. 7겹 리뷰의 규모, 병합 큐, 단계 배포는 위 선택 프로필이다. 검증 루프 시연의 5라운드와 같은 문제 2회 뒤 조기 종료는 그 시연의 숫자이며 이 상한과 섞지 않는다.
