# 주간 점검 프롬프트

`repo-baseline`의 `POLICY.md` §8을 따라 적용 중인 프로젝트를 점검하고 보고해줘. 기간과 기준값은 §8의 표를 따른다.
대상은 `README.md`의 "적용 중인 프로젝트" 표에 있는 저장소와 `minjunkim-dev/repo-baseline`이다.

읽기만 한다. 파일 수정·PR 생성·댓글·병합·CI 재실행·설정 변경을 하지 마. `gh` 조회가 실패하면 그 항목을 미확인으로 적고 계속해.

## 1. 점검 항목

1. 병합: 점검 기간에 기본 브랜치로 병합된 PR의 번호·제목·작성자가 사람 계정인지 봇 계정인지·PR 본문의 문 유형(양쪽 문·한쪽 문). 사람 계정의 PR을 사람과 에이전트로 나누지 마. GitHub는 이를 구분하지 않는다.
2. revert·hotfix: 제목이 `Revert`로 시작하거나 본문에 `This reverts commit`이 있는 PR, 그리고 §8의 hotfix 범위에 드는 PR. 각각 원래 PR과 본문에 적힌 놓친 단계(`POLICY.md` §6)를 옮겨 적어. 본문에 없으면 추정하고 추정이라고 표시해.
3. 필수 CI 시간: 프로젝트 `.github/repository-settings.json`의 `checks`는 job 이름이다. 그 job을 정의한 workflow를 `.github/workflows/`에서 찾아. 기본 브랜치의 성공 실행을 `gh run list --workflow <파일> --branch <기본 브랜치> --status success --json createdAt,updatedAt`로 받아. 비교 기간을 다 덮도록 `--limit`을 충분히 줘. 실행 시간은 `createdAt`과 `updatedAt`의 차이(workflow 전체, 대기 포함)다. 이번 기간과 비교 기간의 중앙값을 구해.
4. 멈춘 PR: §8의 기준에 드는 열린 PR.

## 2. 보고

1. 프로젝트별 표: 병합 수, revert·hotfix 수, CI 시간 중앙값(이번 기간·비교 기간), 멈춘 PR 수.
2. 회고 후보: revert·hotfix PR 목록. 회고는 실행하지 마(`POLICY.md` §6).
3. 사용자 결정이 필요한 항목만 남겨. 근거가 없는 항목을 PASS로 적지 마.

한국어로 간단명료하게 보고해.
