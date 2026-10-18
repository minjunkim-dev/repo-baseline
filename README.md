# repo-baseline

1인 개발 저장소의 GitHub 설정·CI 기준을 한 곳에서 관리하는 원본 저장소다.
새 프로젝트를 셋업하거나 기존 프로젝트를 다시 맞출 때 같은 결과가 나오게 한다.

## 구조

| 경로 | 역할 | 프로젝트로 복사 |
| --- | --- | --- |
| `POLICY.md` | 공통값과 허용 예외 | 아니요. 참조만 한다 |
| `prompts/github-repository-settings.md` | GitHub 서버 설정 절차 | 아니요. 에이전트 채팅에 첨부한다 |
| `prompts/pr-ci-setup.md` | 문서·CI·리뷰·병합 절차 | 아니요. 에이전트 채팅에 첨부한다 |
| `templates/dependabot.yml` | Dependabot 설정 시작점 | 예. 생태계만 프로젝트에 맞게 바꾼다 |
| `templates/repo-baseline.json` | 복사 목록(manifest) 시작점 | 예. `.github/repo-baseline.json`으로 둔다 |
| `scripts/` | 프로젝트에 그대로 복사하는 검사기와 테스트 | 예. 수정하지 않는다 |
| `tools/apply_baseline.py` | `scripts/`를 프로젝트에 복사하고 해시를 기록 | 아니요 |

`scripts/`의 파일은 프로젝트에서 직접 고치지 않는다. 이 저장소에서 고친 뒤 다시 적용한다.
프로젝트의 `scripts/check_repo_baseline.py`가 복사본이 기록된 해시와 다르면 CI를 실패시킨다.

## 새 프로젝트에 적용

1. `templates/repo-baseline.json`을 프로젝트의 `.github/repo-baseline.json`으로 복사한다.
2. `bugbot_rules`에 프로젝트의 `.cursor/BUGBOT.md` 경로를 모두 적는다.
3. 테스트를 다른 폴더에서 실행하면 `files`의 대상 경로를 바꾼다. 예: `"scripts/source-only/test_github_settings.py": {"source": "scripts/test_github_settings.py"}`.
4. 이 저장소에서 다음을 실행한다.

   ```bash
   python3 tools/apply_baseline.py /path/to/project
   ```

5. `templates/dependabot.yml`을 `.github/dependabot.yml`로 복사하고 실제 생태계만 추가한다.
6. 두 프롬프트를 같은 채팅에 첨부하고 순서대로 적용한다.
7. 복사한 테스트가 기존 필수 CI job에서 실행되는지 확인한다.

## 기존 프로젝트를 다시 맞춤

1. 먼저 차이를 본다. 아무것도 쓰지 않는다.

   ```bash
   python3 tools/apply_baseline.py /path/to/project --check
   ```

2. 다른 파일이 프로젝트의 의도된 변경이면 이 저장소로 옮긴다. 의도하지 않은 drift면 다시 적용한다.
3. 적용한 결과를 PR로 올리고 프로젝트의 리뷰·CI·병합 기준을 따른다.

## 이 저장소를 바꿀 때

1. `scripts/`를 바꾸면 테스트를 실행한다.

   ```bash
   python3 -m unittest discover -s tools -p 'test_*.py'
   python3 -m unittest discover -s scripts -p 'test_bugbot_rules.py'
   ```

   `test_github_settings.py`와 `test_repo_baseline.py`는 프로젝트 파일이 필요하다. 프로젝트에 적용한 뒤 그 프로젝트의 CI에서 검증한다.

2. commit한 뒤 각 프로젝트에 다시 적용하고 프로젝트별 PR을 올린다. `apply_baseline.py`는 commit하지 않은 변경이 있으면 멈춘다.
3. `CHANGELOG.md`에 바뀐 점과 다시 적용할 프로젝트를 적는다.

## 적용 중인 프로젝트

| 프로젝트 | 저장소 |
| --- | --- |
| Smallnext | `minjunkim-dev/smallnext` |
| BGLike | `minjunkim-dev/BGLike` |
| Runstir | `minjunkim-dev/mobile-runtime` |

## 제약

- 이 저장소는 private이다. 파일을 복사해서 쓰므로 프로젝트의 공개 여부와 관계없이 쓸 수 있다.
- 프로젝트 CI는 이 저장소에 접근하지 않는다. 처음 적용하거나 갱신할 때만 이 저장소를 읽을 권한이 필요하다. 다른 기기나 에이전트는 먼저 이 저장소를 clone한다.
- `apply_baseline.py`는 이 저장소에서 추적하는 일반 파일만 복사한다. 프로젝트 밖을 가리키는 경로와 symlink는 거부한다.
- 다른 저장소의 workflow가 이 저장소를 `uses:`로 참조하지 않는다. public 저장소는 private 원본을 호출할 수 없기 때문이다.
- Secret 값은 이 저장소에 두지 않는다.
