# repo-baseline

1인 개발과 소규모 팀(2~6명) 저장소의 GitHub 설정·CI 기준을 한 곳에서 관리하는 원본 저장소다. 두 프로필의 차이는 `POLICY.md` §9에 있고, 기본은 1인 프로필이다.
새 프로젝트를 셋업하거나 기존 프로젝트를 다시 맞출 때 같은 결과가 나오게 한다.

## 구조

| 경로 | 역할 | 프로젝트로 복사 |
| --- | --- | --- |
| `POLICY.md` | 공통값과 허용 예외 | 아니요. 참조만 한다 |
| `prompts/github-repository-settings.md` | GitHub 서버 설정 절차 | 아니요. 에이전트 채팅에 첨부한다 |
| `prompts/pr-ci-setup.md` | 문서·CI·리뷰·병합 절차 | 아니요. 에이전트 채팅에 첨부한다 |
| `prompts/weekly-check.md` | 적용 중인 프로젝트의 주간 읽기 전용 점검 | 아니요. 이 저장소에서 에이전트에게 준다 |
| `templates/dependabot.yml`, `templates/dependabot-ecosystem.yml` | Dependabot 설정 원본 | 예. manifest의 `ecosystems` 목록으로 `.github/dependabot.yml`을 생성한다 |
| `templates/repo-baseline.json` | 복사 목록(manifest) 시작점 | 예. `.github/repo-baseline.json`으로 둔다 |
| `templates/repository-settings.json` | GitHub 설정 기준선 시작점(1인 프로필 값) | 예. `.github/repository-settings.json`으로 두고 `REPLACE` 값과 저장소 정보를 채운다. 팀 프로필은 `POLICY.md` §9의 값으로 바꾼다 |
| `templates/review-status.yml` | 리뷰 status를 경로로 검사하는 workflow | 예. `.github/workflows/review-status.yml`로 둔다. 프로젝트 파일이라 해시로 검사하지 않고 Dependabot이 pin을 올린다 |
| `templates/review-status-policy.json` | 공개 저장소에서 `Review status` workflow의 `pull_request_target`과 `issue_comment`만 허용하는 Actions 이벤트 정책 | 아니요. GitHub API로 만든다(`POLICY.md` §9) |
| `templates/CODEOWNERS` | 팀 프로필의 신뢰 경계 경로 소유자 | 팀 프로필만. `.github/CODEOWNERS`로 두고 소유자를 채운다 |
| `templates/claude-settings.json` | Claude Code 프로젝트 설정(Matt Pocock 플러그인, `.env` 읽기 차단) | 예. `.claude/settings.json`으로 둔다 |
| `scripts/` | 프로젝트에 그대로 복사하는 검사기와 테스트 | 예. 수정하지 않는다 |
| `vendor/mattpocock-skills/matt-code-review/` | 리뷰 관문 스킬(Matt Pocock `code-review`, 이름만 바꿈, MIT) | 예. manifest대로 `.agents/skills/`와 `.claude/skills/`에 복사한다 |
| `tools/apply_baseline.py` | manifest대로 `scripts/`와 `vendor/`의 스킬을 프로젝트에 복사하고 해시를 기록 | 아니요 |
| `tools/apply_github_settings.py` | 설정 기준선과 다른 GitHub 서버 설정을 계획·적용 | 아니요 |

`scripts/`의 파일과 생성한 `.github/dependabot.yml`은 프로젝트에서 직접 고치지 않는다. 이 저장소에서 고친 뒤 다시 적용한다.
프로젝트의 `scripts/check_repo_baseline.py`가 복사본이 기록된 해시와 다르면 CI를 실패시킨다.

## 새 프로젝트에 적용

1. `templates/repo-baseline.json`을 프로젝트의 `.github/repo-baseline.json`으로 복사한다.
2. `templates/claude-settings.json`을 프로젝트의 `.claude/settings.json`으로 둔다. 이미 있으면 합친다.
   공개 저장소는 `review-status.yml`을 기본 브랜치에 병합하기 전에 Actions 이벤트 정책을 만든다. 비공개 저장소는 이 단락을 건너뛴다. 이 저장소 루트에서, 대상 프로젝트의 `OWNER/NAME`으로 실행한다. 쓰기는 저장소 관리자 승인을 받는다. 먼저 조회하고, 같은 workflow 경로에 `pull_request_target`과 `issue_comment`만 허용하는 정책이 있으면 다시 만들지 않는다. PUT은 `source_type`이 Repository이고 `workflow_path.include`가 `.github/workflows/review-status.yml`뿐인 정책만 한다. 더 넓은 대상은 PUT하지 않는다. 그 파일을 `pull_request_target`만 허용하는 상위 정책이나 더 넓은 정책이 있으면 명령이 실패한다.

   ```bash
   set -euo pipefail
   ids=$(gh api --paginate repos/OWNER/NAME/actions/policies --jq '.policies[].id')
   found=0
   narrow=
   parent_narrow=0
   for id in $ids; do
     kind=$(gh api "repos/OWNER/NAME/actions/policies/$id" --jq 'def inc: (.conditions.workflow_path.include // []); def exact: inc == [".github/workflows/review-status.yml"]; def applies: exact or (inc | length) == 0 or (inc | index(".github/workflows/review-status.yml")) or (inc | index("~ALL")); def only: any(.rules[]?; .type=="restrict_action_events" and ((.parameters.allowed_events // []) | sort) == ["pull_request_target"]); def both: any(.rules[]?; .type=="restrict_action_events" and ((.parameters.allowed_events // []) | sort) == ["issue_comment","pull_request_target"]); if .enforcement=="active" and applies then (if both and exact then "both" elif only and exact and ((.source_type // "Repository")=="Repository") then "narrow" elif only then "parent" else "other" end) else "other" end')
     if [ "$kind" = "both" ]; then found=1; fi
     if [ "$kind" = "narrow" ]; then narrow="$narrow $id"; fi
     if [ "$kind" = "parent" ]; then parent_narrow=1; fi
   done
   if [ "$parent_narrow" = "1" ]; then
     echo "a parent policy allows only pull_request_target" >&2
     exit 1
   fi
   for id in $narrow; do
     gh api "repos/OWNER/NAME/actions/policies/$id" --method PUT --input templates/review-status-policy.json
     found=1
   done
   if [ "$found" = "0" ]; then
     gh api repos/OWNER/NAME/actions/policies --method POST --input templates/review-status-policy.json
   fi
   gh api --paginate repos/OWNER/NAME/actions/policies
   ```

   목록이나 상세 조회가 실패하면 멈춘다. 실패를 정책이 없는 것으로 보고 POST하지 않는다.

   재조회에서 그 허용이 보이기 전에는 workflow를 병합하지 않는다. 그다음 `templates/review-status.yml`을 별도 파일 `.github/workflows/review-status.yml`로 둔다. 다른 workflow와 합치거나 이 두 이벤트 외의 이벤트를 더하지 않는다(`POLICY.md` §9).
3. `.github/dependabot.yml` 항목의 `ecosystems`에 GitHub Actions 외의 실제 생태계를 적는다. 예: `{"package-ecosystem": "cargo", "directory": "/services/api"}`.
4. 테스트를 다른 폴더에서 실행하면 `files`의 대상 경로를 바꾼다. 예: `"scripts/source-only/test_github_settings.py": {"source": "scripts/test_github_settings.py"}`.
5. 이 저장소에서 다음을 실행한다.

   ```bash
   python3 tools/apply_baseline.py /path/to/project
   ```

6. 두 프롬프트를 같은 채팅에 첨부하고 순서대로 적용한다. [프로젝트 초기 설정과 일상 개발](docs/development-workflow.md)을 프로젝트 작업 문서에 연결한다. 사용자가 "처음 한 번"을 마친 뒤 tracker·도메인 설정(`triage`가 설치돼 있으면 라벨도)이 연결됐는지 확인한다.
7. 복사 파일 해시 검사와 테스트가 기존 필수 CI job에서 실행되는지 확인한다. [GitHub 설정 기준선과 기능 지원](docs/github-settings-profile.md)의 예외·결과 구분을 따른다.
8. 필수 CI가 실제 PR에서 성공한 뒤 GitHub 서버 설정을 적용한다(GitHub 설정 프롬프트 §4·§10).
   1. `templates/repository-settings.json`을 프로젝트의 `.github/repository-settings.json`으로 복사한다.
   2. `REPLACE`로 시작하는 값과 저장소 정보를 채운다. 남아 있으면 도구가 아무것도 읽지 않고 멈춘다.
      - `repository`: `owner/name`. `repository_id`: `gh api repos/OWNER/NAME --jq .id`의 값.
      - `default_branch`와 `expected.repository.default_branch`: 실제 기본 브랜치. 둘이 같아야 한다.
      - `visibility`: `public` 또는 `private`.
      - `checks`: 실제 PR에서 성공한 필수 job 이름. GitHub Actions면 `app_id`는 15368이다. `POLICY.md` §9의 `Review status` job도 같다.
      - 팀 프로필이면 리뷰 설정 네 값을 `POLICY.md` §9의 표대로 바꾸고 `templates/CODEOWNERS`를 `.github/CODEOWNERS`로 둔다.
      - `patterns_allowed`: workflow의 `uses:` 중 GitHub 소유가 아닌 action(`owner/repo@*`). 없으면 빈 목록.
      - CodeQL을 workflow 파일(advanced setup)로 돌리면 `codeql.state`를 `not-configured`로 바꾸고 `codeql_workflow`·`codeql_main_source`를 넣는다(`POLICY.md` §3).
      - 비공개 저장소에서 요금제로 쓸 수 없는 기능은 [GitHub 설정 기준선과 기능 지원](docs/github-settings-profile.md)의 예외로 옮긴다.
   3. `gh auth status`가 저장소 관리자(admin) 권한 계정으로 로그인된 곳에서, 이 저장소를 기준으로 계획을 본다. 읽기만 한다.

      ```bash
      python3 tools/apply_github_settings.py /path/to/project
      ```

   4. `DIFF`(현재 값 → 기준값)와 `PLAN`(쓰기 요청)을 확인하고 승인한 뒤 적용한다. 적용 후 자동으로 다시 감사해 `PASS`나 `LIMITED`를 출력한다.

      ```bash
      python3 tools/apply_github_settings.py /path/to/project --apply
      ```

   Grouped security updates는 API가 없어 화면에서 켠다(`POLICY.md` §2).

## 에이전트에게 보낼 요청문

두 프롬프트(`prompts/github-repository-settings.md`, `prompts/pr-ci-setup.md`)를 첨부하고 아래 글을 함께 보낸다.

```text
첨부한 두 프롬프트(repo-baseline 버전)를 기준으로 이 프로젝트에 실제 적용하고 검증해줘.

같은 채팅에서 GitHub 초기 점검 → PR·CI/CD 셋업 → GitHub 최종 적용·검증 순서로 진행해. 중복 작업은 피하고 보류 항목까지 마무리해.
공통값은 repo-baseline의 POLICY.md와 templates를 따르고, 공통 검사기는 tools/apply_baseline.py로 복사해. 값을 새로 고르지 마.

프로필은 1인이다(팀이면 "팀"으로 바꿔 보낸다. POLICY.md §9). 별도 컨텍스트의 자체 리뷰를 기준으로 해. 공개 배포와 production 변경은 하지 마.

최종 독립 리뷰·필수 CI 후 위험별 병합 기준을 적용해. 문 판정은 `POLICY.md` §10만 따라. `POLICY.md` §5의 외부 리뷰 대상은 외부 리뷰(공개 저장소는 CodeRabbit)도 받고, 그 PR은 auto-merge하지 마. 한쪽 문은 사람이 최종 head를 승인하게 하고, 1인 프로필은 §10의 승인 댓글을 남겨. 팀 프로필이면 POLICY.md §9의 승인 규칙을 따라. `disable-model-invocation: true`인 스킬은 사용자가 실행한다. 완료 항목과 미확인 항목을 구분해 보고해.
```

## 기존 프로젝트를 다시 맞춤

1. `templates/repo-baseline.json`에 프로젝트 manifest에 없는 항목이 생겼으면(CHANGELOG에 적는다) 프로젝트의 `.github/repo-baseline.json`에 더한다. `--check`는 manifest에 이미 있는 항목만 비교한다.
2. 먼저 차이를 본다. 아무것도 쓰지 않는다.

   ```bash
   python3 tools/apply_baseline.py /path/to/project --check
   ```

3. 다른 파일이 프로젝트의 의도된 변경이면 이 저장소로 옮긴다. 의도하지 않은 drift면 다시 적용한다.
4. 적용한 결과를 PR로 올리고 프로젝트의 리뷰·CI·병합 기준을 따른다. `review-status.yml`을 처음 두는 공개 저장소는 그 파일을 기본 브랜치에 병합하기 전에 위 "새 프로젝트에 적용" 2단계의 이벤트 정책을 만든다.

## 일상 개발 시작

개발 절차는 Matt Pocock 스킬을 그대로 쓴다. 어떤 스킬로 시작할지는 사용자가 `/ask-matt`를 실행한다. `disable-model-invocation: true`인 스킬은 사용자가 실행한다. 처음 셋업과 이 기준이 더하는 `main` 경계는 [프로젝트 초기 설정과 일상 개발](docs/development-workflow.md)을 따른다.

## 자체 리뷰와 회고

기본 흐름은 구현 → 자동 검사 → 별도 Standards·Spec·버그 찾기 리뷰(버그 찾기는 코드 변경만, 신뢰 경계 변경은 Security 추가) → 확실한 결함 수정·커밋 → 최종 변경의 리뷰·검사 → 위험별 병합이다. 상세 기준은 `prompts/pr-ci-setup.md` §5·§6을 따른다.

같은 실수나 탐색·도구 사용 문제가 있었던 작업은 Matt Pocock의 `retro`에 대상 세션·PR을 지정해 돌아본다. 사용자가 고른 개선만 반영하며, 회고 자체는 정기 실행하지 않는다. 같은 프롬프트 §7을 따른다.

주간 점검은 `prompts/weekly-check.md`로 회고 후보를 모은다. 읽기만 하며 항목과 기준값은 `POLICY.md` §8을 따른다. 점검을 일정 실행하면 그 설정은 이 저장소 밖에 둔다.

## 기존 리뷰 서비스 구성에서 전환

기존 프로젝트에 이 버전을 적용하기 전에 다음을 확인한다. `apply_baseline.py`는 기존 manifest를 읽으므로, 아래 정리 없이 실행하면 삭제된 원본을 찾지 못한다. 파일 삭제와 문서 이동은 프로젝트별 PR로 검토한다.

1. 이전 `.cursor/BUGBOT.md`에만 있는 고유 기준을 코딩 규칙·도메인 원문으로 옮긴다. 자체 리뷰 문서의 자료 선택 표에 연결하고, 내용이 보존된 요약 파일만 제거한다. 개인·전역 규칙은 유지한다.
2. 기존 CI·검사 명령에서 `check_bugbot_rules.py`·`test_bugbot_rules.py` 호출을 제거한다. 다른 빌드·테스트·보안 검사와 보호는 유지한다. trusted base의 기존 검사가 전환을 막으면 기존 정책으로 통과할 수 있는 전환 PR을 먼저 준비한다.
3. `.github/repo-baseline.json`에서 `source`가 `scripts/check_bugbot_rules.py` 또는 `scripts/test_bugbot_rules.py`인 항목과 `bugbot_rules` 키를 제거한다. 해당 복사 파일도 내용과 실제 위치를 확인한 뒤 제거한다.
4. 남은 파일의 차이를 `tools/apply_baseline.py /path/to/project --check`로 확인하고 다시 적용한다. 실제 프로젝트 CI에서 남은 공통 검사·자체 리뷰를 검증한다.

서버 서비스 비활성화와 GitHub App·계정 연결 해제는 저장소 파일 갱신과 별개다. 관련 서버 기능의 사용 여부와 영향 범위를 확인하고 승인된 변경만 수행한다.

## 이 저장소를 바꿀 때

1. `scripts/`, `templates/`, `tools/`를 바꾸면 테스트를 실행한다.

   ```bash
   python3 -m unittest discover -s scripts -p 'test_*.py'
   python3 -m unittest discover -s tools -p 'test_*.py'
   ```

   원본 단위 테스트는 합성 fixture를 사용한다. 도구 테스트는 깨끗한 임시 Git 원본을 만들고 default·advanced·미지원 설정의 프로젝트에 실제 복사한 뒤 테스트·출처 SHA·해시 drift·재적용·CodeQL pin 실패를 검사한다. 개인 프로젝트·GitHub 인증·네트워크는 필요 없다. 자체 CI는 같은 명령을 Python 3.11·3.13에서 실행한다. 실제 서버 감사·지원 여부·스킬 실행은 이 테스트의 검증 범위 밖이다.

2. 변경을 PR로 올려 `main`에 병합한 뒤, 최신 `main`을 받아 각 프로젝트에 다시 적용하고 프로젝트별 PR을 올린다. `apply_baseline.py`는 commit하지 않은 변경이 있으면 멈춘다. 병합 전 브랜치에서 적용하면 squash 병합 뒤 `main`에 없는 커밋이 출처로 기록된다.
3. `CHANGELOG.md`에 바뀐 점과 다시 적용할 프로젝트를 적는다.

이 저장소 자신의 GitHub 설정 기준선은 `.github/repository-settings.json`이다. `python3 tools/apply_github_settings.py .`로 차이를 확인한다.

## 적용 중인 프로젝트

| 프로젝트 | 저장소 |
| --- | --- |
| Smallnext | `minjunkim-dev/smallnext` |
| BGLike | `minjunkim-dev/BGLike` |
| Runstir | `minjunkim-dev/mobile-runtime` |

## 제약

- 이 저장소는 public이다. 파일을 복사해서 쓰므로 적용 대상 프로젝트의 공개 여부와 관계없이 쓸 수 있다.
- 프로젝트 CI는 이 저장소에 접근하지 않는다. 처음 적용하거나 갱신할 때 이 저장소를 clone한다. 공개 원본이므로 읽기 인증은 필요 없다.
- `apply_baseline.py`는 이 저장소에서 추적하는 일반 파일만 복사한다. 프로젝트 밖을 가리키는 경로와 symlink는 거부한다.
- 다른 저장소의 workflow가 이 저장소를 `uses:`로 참조하지 않는다. 소비 프로젝트의 CI는 복사본과 기록한 해시만으로 검증하며 원본 접근에 의존하지 않는다.
- Secret 값은 이 저장소에 두지 않는다.
