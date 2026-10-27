# 변경 기록

## 2026-10-27 — Matt Pocock 스킬 사용법을 다시 적지 않음

- 개발 절차 문서·PR/CI 셋업 프롬프트·POLICY·README에서 스킬의 단계(셋업 세부, 작업 크기별 진입 표, 명세→티켓→구현, 스킬 선택, retro 단계)를 옮겨 적던 부분을 뺐다. 옮겨 적은 내용이 원문과 어긋나 있었다(원문은 변경마다 grilling을 권하지만 문서는 불확실할 때만으로 바꿔 적음). 스킬은 설치된 원문대로 쓰고, 시작점은 `/ask-matt`에 묻는다.
- 남긴 것은 스킬이 정하지 않는 이 기준의 선택이다. `AGENTS.md`만 쓰기(셋업 스킬 전에 `CLAUDE.md`를 옮김), 모든 변경은 PR·필수 CI·위험별 병합(셋업 프롬프트 §10), 리뷰 정책(§5), 회고 정책(§6).
- README의 재적용 순서를 고쳤다. squash 병합과 병합 후 브랜치 삭제를 쓰므로 PR을 병합한 뒤 최신 `main`에서 적용한다.
- 공통 검사기·템플릿은 바뀌지 않아 소비 프로젝트 재적용은 필요 없다.
- 권한·Secret·workflow·저장소 설정·dependency 정책 PR의 추가 리뷰를 "다른 모델"에서 "작성자 세션 밖의 외부 리뷰"로 바꾸고, 공개 저장소는 CodeRabbit 무료 플랜으로 충족한다고 적었다. CodeRabbit은 참고용이며 필수 체크·자동 수정은 쓰지 않는다. GitHub 설정 프롬프트 §7도 CodeRabbit을 정리 대상에서 뺐다.
- CodeRabbit 리뷰 반영: 라벨 문서는 `triage`가 설치됐을 때만 완료 조건에 넣는다(셋업 스킬이 그때만 라벨 단계를 진행). Claude Code 플러그인에서는 `/mattpocock-skills:<이름>`처럼 플러그인 이름을 붙여 부른다.

## 2026-10-27 — 이 저장소에도 Dependabot 버전 업데이트 적용

- `.github/dependabot.yml`을 두었다. 생태계가 GitHub Actions뿐이라 `templates/dependabot.yml`을 그대로 쓴다. SHA로 고정한 `check.yml`의 action은 보안 알림이 생기지 않으므로 이 정기 업데이트로만 갱신된다(`POLICY.md` §2).
- 이 저장소에는 manifest가 없어 `apply_baseline.py`로 생성하지 않는다. 첫 줄을 사본이라는 설명으로 바꾸고, 나머지가 템플릿과 어긋나면 `tools` 테스트가 실패하게 했다.

## 2026-10-27 — 지침 파일을 AGENTS.md로 통일

- 초기 설정 6단계가 `## Agent skills` 블록을 `AGENTS.md`에만 둔다. 파일이 없으면 만든다. PR/CI 셋업 프롬프트 §3도 canonical 파일 선택 대신 `AGENTS.md`로 정리하게 맞췄다.
- 공통 검사기·템플릿은 바뀌지 않아 소비 프로젝트 재적용은 필요 없다. 기존 프로젝트의 `CLAUDE.md`는 다시 맞출 때 고유 규칙을 `AGENTS.md`로 옮기고 지운다.

## 2026-10-26 — 공개 저장소 전환

- 현재 파일·Git refs의 전체 이력·GitHub PR/댓글/실행 자료를 민감정보 점검한 뒤 public으로 전환했다. 기존 clone과 복사 기반 배포 방식은 유지한다.
- README에서 원본이 비공개라는 제약을 갱신했다. 공통 검사기·템플릿은 바뀌지 않아 소비 프로젝트 재적용은 필요 없다.

## 2026-10-26 — 초기 설정·작업 진입·원본 검증 보완

- 공식 Matt Pocock 초기 설정과 tracker·라벨·도메인 문서 연결을 추가했다. 작은 수정과 명세 → 의존성 티켓 → 준비된 작업 → 통합 검증 경로를 구분한다.
- 설정 검사기에 근거 있는 기능 미지원·비해당 예외와 LIMITED 결과를 추가했다. 기존 schema version 1은 유지하며, 예외가 없는 403·404·누락은 계속 검증 실패다.
- 원본 단위 테스트의 소비 프로젝트 의존성을 없앴다. 임시 Git 원본에서 실제 복사·프로젝트 테스트·출처·drift·복구·CodeQL pin 실패를 검사하고 읽기 전용 자체 CI에 연결했다.
- 복사본 해시 검사는 프로젝트 CI에서 별도 명령으로 실행한다. 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. 기존 프로젝트·서버 설정은 이 변경으로 갱신되지 않는다.

## 2026-10-26 — 자체 리뷰와 선택적 회고

- 두 셋업 프롬프트·정책·README에서 Bugbot 전용 셋업·규칙 예산·서버 시험 요구를 제거했다. 자체 Standards·Spec 리뷰와 확실한 결함의 직접 수정·커밋을 기본으로 한다.
- 공통 manifest에서 Bugbot 검사기·테스트·규칙 목록을 제거하고 해당 원본 파일을 삭제했다. 기존 프로젝트의 CI 호출·manifest·복사본 정리 순서는 README의 전환 절차를 따른다. 고유 코딩 규칙은 보존한다.
- Matt Pocock `mattpocock-skills:retro`의 출처·사용자 요청·기록 기반 제안·선택한 개선의 반영·검증 절차를 추가했다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. 서버 비활성화·계정 연결 해제와 기존 프로젝트 반영은 이 원본 변경으로 실행되지 않는다.

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
