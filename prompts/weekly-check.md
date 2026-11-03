# 주간 점검 프롬프트

`repo-baseline`의 `POLICY.md` §8을 따라 적용 중인 프로젝트의 지난 7일을 점검하고 보고해줘.
대상은 `README.md`의 "적용 중인 프로젝트" 표에 있는 저장소와 `minjunkim-dev/repo-baseline`이다.

읽기만 한다. 파일 수정·PR 생성·댓글·병합·CI 재실행·설정 변경을 하지 마. `gh` 조회가 실패하면 그 항목을 미확인으로 적고 계속해.

## 점검 항목

1. 병합: 지난 7일 기본 브랜치에 병합된 PR의 번호·제목·작성자 종류(사람·Dependabot·에이전트)·PR 본문의 문 유형(양쪽 문·한쪽 문).
2. revert·hotfix: 제목이 `Revert`로 시작하거나 본문에 `This reverts commit`이 있는 PR, 그리고 14일 안에 병합된 PR을 고친 수정 PR. 각각 원래 PR과 어느 단계(검증·CI·리뷰·승인·병합 후 복구)에서 잡았어야 했는지 적어. 단계는 추정이라고 표시해.
3. 필수 CI 시간: 프로젝트 `.github/repository-settings.json`의 필수 check를 만드는 workflow에서 기본 브랜치의 성공 실행 시간 중앙값을 구해. 실행 시간은 `createdAt`과 `updatedAt`의 차이로 잰다(대기 시간 포함). 이전 4주 중앙값보다 20% 넘게 늘었으면 표시해.
4. 멈춘 PR: 7일 넘게 갱신이 없는 열린 PR과 처리하지 않은 Dependabot PR(`POLICY.md` §2는 매주 처리한다).

## 보고

1. 프로젝트별 표: 병합 수, revert·hotfix 수, CI 시간 중앙값(이번 주·이전 4주), 멈춘 PR 수.
2. 회고 후보: revert·hotfix와 같은 지적이 두 번 이상 나온 PR. 회고는 실행하지 마(`POLICY.md` §6).
3. 사용자 결정이 필요한 항목만 남겨. 근거가 없는 항목을 PASS로 적지 마.

한국어로 간단명료하게 보고해.
