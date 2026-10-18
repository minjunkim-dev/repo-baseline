# 변경 기록

## 2026-10-18 — 공유 브랜치 이름 검사

- BGLike의 기존 브랜치 정규식을 `scripts/check_branch_name.py`로 추출했다. CI와 pre-push가 같은 검사기를 쓴다.
- pre-push는 실제 목적지 ref를 검사한다. 기본 브랜치·태그·삭제를 허용한다.
- 회귀 검사를 추가했다. 원본 도구·검사는 로컬에서 실행하고, 해시가 일치하는 복사본·테스트는 BGLike의 기존 필수 CI에서 실행한다.
- 비공개 원본에 시도한 새 CI는 계정 결제 제한으로 job을 시작하지 못했다. 새 workflow는 포함하지 않는다. 실패한 실행 기록은 PR #2에 남긴다.
- 적용 대상: BGLike. smallnext·mobile-runtime의 hook과 workflow는 이번 범위에 포함하지 않는다.

## 2026-10-18 — Grouped security updates

- `POLICY.md` §2: Grouped security updates를 공통값으로 켠다. 계정 기본값과 smallnext·BGLike·mobile-runtime에 적용했다. API로 감사할 수 없어 화면 확인 항목으로 남긴다.

## 2026-10-18 — Dependabot 설정 생성·추적

- `.github/dependabot.yml`을 `templates/dependabot.yml`과 `templates/dependabot-ecosystem.yml`로 생성한다. 프로젝트별 생태계는 manifest의 `ecosystems`에 적는다.
- 생성한 파일도 해시로 추적한다. 프로젝트에서 Dependabot 값을 바꾸면 CI가 실패한다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 6차 반영

- `check_github_settings.py`: `github/codeql-action` 이름을 대소문자 구분 없이 찾는다. GitHub는 owner/repo 이름의 대소문자를 구분하지 않는다.
- 이스케이프·줄 연결로 이름을 숨기는 표기는 보류했다. 후속 Issue로 추적한다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 5차 반영

- `check_github_settings.py`: 따옴표 밖의 `#`만 주석으로 지운다. 블록 경계를 블록을 가진 키의 열로 계산한다. 따옴표 안의 `: |`는 블록 헤더로 보지 않는다.
- 남은 한계(이스케이프·줄 연결로 이름 숨기기)는 위협 모델 밖으로 `POLICY.md` §3에 기록했다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 4차 반영

- `check_github_settings.py`: step 구조 해석을 없앴다. 주석과 블록 본문을 뺀 모든 `github/codeql-action/` 참조를 비교한다. 단독 `-`, 여러 줄 flow 표기로도 참조를 숨길 수 없다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 3차 반영

- `check_github_settings.py`: step 수준에서 읽지 못한 `github/codeql-action/` 표기는 실패로 처리한다(fail-closed). `-   name:`처럼 공백이 많은 목록 표기도 읽는다.
- `test_apply_baseline.py`: 테스트가 직접 만든 임시 폴더만 지운다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 2차 반영

- `apply_baseline.py`: `git --literal-pathspecs`로 추적 여부를 확인한다. `:(exclude)…` 같은 이름이 다른 파일과 매칭되지 않는다.
- `check_github_settings.py`: step 단위 `uses:` 키만 읽는다. `run:` 블록 본문과 `with:` 입력은 무시한다. 접힌 값은 고정으로 보지 않는다.
- `test_github_settings.py`: CodeQL 테스트가 프로젝트의 setup 종류와 무관한 fixture를 쓴다. default setup 프로젝트에서도 통과한다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 반영

- `apply_baseline.py`: 추적된 저장소 내부 파일만 원본으로 허용한다. manifest와 대상의 symlink·외부 경로를 거부한다.
- `check_github_settings.py`: CodeQL 참조를 실제 `uses:` 줄에서만 읽는다. 대소문자를 정규화하고 태그 참조도 불일치로 본다. default setup 기준선을 지원한다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 첫 버전

- 세 프로젝트(smallnext, BGLike, mobile-runtime)의 공통 검사기를 모았다.
  - `check_github_settings.py`: CodeQL `init`·`analyze` commit 불일치 검사를 추가했다.
  - `check_bugbot_rules.py`: 필수 규칙 목록을 `.github/repo-baseline.json`의 `bugbot_rules`에서 읽는다.
  - `check_repo_baseline.py`: 복사본 해시 검사를 새로 추가했다.
- Dependabot 공통값을 `POLICY.md`와 `templates/dependabot.yml`에 고정했다. 상한은 GitHub 기본값 5를 쓴다.
- 프롬프트 v4를 v5로 고쳤다. 값은 이 저장소를 참조한다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.
