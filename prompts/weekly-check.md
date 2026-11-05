# 주간 점검 프롬프트

`repo-baseline`의 `POLICY.md` §8을 따라 적용 중인 프로젝트를 점검하고 보고해줘. 기간과 기준값은 §8의 표를 따른다.
대상은 `README.md`의 "적용 중인 프로젝트" 표에 있는 저장소와 `minjunkim-dev/repo-baseline`이다.

읽기만 한다. 파일 수정·PR 생성·댓글·병합·CI 재실행·설정 변경을 하지 마. `gh pr`·`gh issue`·`gh run` 조회에 `--repo <owner/name>`을 붙여. `gh api`에는 이 옵션이 없으니 경로에 저장소를 적어. `gh` 조회가 실패하면 그 항목을 미확인으로 적고 계속해.

## 1. 점검 항목

1. 병합: 점검 기간에 기본 브랜치로 병합된 PR의 번호·제목·작성자가 사람 계정인지 봇 계정인지·문 유형(되돌리기 쉬움(two-way door: 되돌리기 쉬운 결정)·되돌리기 어려움(one-way door: 되돌리기 어려운 결정)). 사람 계정의 PR을 사람과 에이전트로 나누지 마. GitHub는 이를 구분하지 않는다. 문 유형은 본문만 믿지 마. `gh pr diff <번호> --repo <owner>/<name> --name-only`로 바뀐 경로를 보고 `POLICY.md` §10으로 다시 판정해. 게이트 경로가 있으면 되돌리기 어려움이다. §5와 같은 버전 전용 Dependabot PR은 그 승인에서 빼고, 주 버전 변경과 `scripts/check_review_status.py` 변경은 빼지 마. 프로필은 프로젝트 `AGENTS.md`의 한 줄이고, 없으면 1인이다. 1인 되돌리기 어려움은 `gh api --paginate repos/<owner>/<name>/issues/<번호>/comments`의 모든 페이지에서 `되돌리기 어려움 승인:` 또는 deprecated인 `한쪽 문 승인:`으로 시작하는 댓글을 봐. 다른 접두사는 승인이 아니다. 작성자의 login이 `gh api repos/<owner>/<name> --jq .owner.login`과 같고, 그 뒤 SHA가 최종 head 전체와 같아야 한다. 팀 되돌리기 어려움은 그 댓글 대신 `POLICY.md` §9를 따른다. `gh api --paginate repos/<owner>/<name>/pulls/<번호>/reviews`의 모든 페이지에서 최종 head에 대한 사람 승인만 인정하고, PR 책임자와 에이전트·봇 승인은 세지 마. 댓글 `created_at`이나 리뷰 `submitted_at`이 `gh pr view <번호> --repo <owner>/<name> --json mergedAt`보다 늦으면 승인으로 세지 마. 승인 댓글은 `updated_at`이 그 `mergedAt`보다 늦으면 병합 뒤에 고친 것이므로 승인으로 세지 마. 조건에 맞는 승인이 없으면 표시해.
2. revert·hotfix: 제목이 `Revert`로 시작하거나 본문에 `This reverts commit`이 있는 PR, 그리고 §8의 hotfix 범위에 드는 PR. 각각 원래 PR과 본문에 적힌 놓친 단계(`POLICY.md` §6)를 옮겨 적어. 본문에 없으면 추정하고 추정이라고 표시해.
3. 필수 CI 시간: 프로젝트 `.github/repository-settings.json`의 `checks`는 job 이름이다. `Review status`는 리뷰를 기다려 다시 돌리는 job이라 뺀다. 그 job을 정의한 workflow를 `.github/workflows/`에서 찾고 트리거를 확인해. 기본 브랜치 `push`로 도는 workflow는 `gh run list --repo <owner/name> --workflow <파일> --branch <기본 브랜치> --status success --json createdAt,updatedAt`로, `pull_request`로만 도는 workflow는 `--branch` 대신 `--event pull_request`로 받아. 비교 기간을 다 덮도록 `--limit`을 충분히 줘. 실행 시간은 `createdAt`과 `updatedAt`의 차이(workflow 전체, 대기 포함)다. 이번 기간과 비교 기간의 중앙값을 구하고, §8의 기준을 넘게 늘었으면 표시해. 어느 기간에 성공 실행이 없으면 그 칸은 미확인으로 적고 중앙값·증가 표시·PASS를 적지 마.
4. 멈춘 PR: §8의 기준에 드는 열린 PR. 열린 PR에 미해결 대화 스레드가 있으면 그 PR도 같이 표시해.
5. 리뷰 기록 누락: 점검 항목 1의 PR마다 `gh pr view <번호> --repo <owner/name> --json headRefOid`로 최종 head를 받고, `gh run list --repo <owner/name> --workflow review-status.yml --commit <headRefOid> --event pull_request_target --limit 1 --json conclusion,headSha`로 결과를 읽어. `headSha`가 그 head와 같아야 한다. 이 이벤트의 실행은 그 커밋에 달리고, 목록의 `pull_requests`는 비어 있을 수 있다. `success`가 아니면 누락으로, job이 없으면 미적용으로 표시해.
6. 정기 감사: `gh issue list --repo <owner/name> --label security-audit --state all --limit 1 --json createdAt,title`로 마지막 기록 날짜를 봐. §8 기준보다 오래됐거나 없으면 표시해.
7. 마켓플레이스 태그: `gh api repos/mattpocock/skills/commits/<POLICY.md §7의 태그> --jq .sha`가 §7의 commit으로 시작하는지 봐. 다르면 사용자 결정에 적어.
8. 이벤트 정책: `gh api repos/<owner>/<name> --jq .visibility`와 기본 브랜치의 `.github/workflows/review-status.yml` 존재를 봐. 비공개이거나 workflow가 없으면 비해당으로 적어. 공개이고 workflow가 있으면 `gh api --paginate repos/<owner>/<name>/actions/policies`로 정책을 받아. `has_parents` 기본값이 true라 상위 정책도 들어 있다. 항목에 `conditions.workflow_path`나 `rules`가 없으면 `GET /repos/<owner>/<name>/actions/policies/<id>`로 상세를 봐. `enforcement`가 `active`이고 `restrict_action_events`의 `allowed_events`가 `issue_comment`와 `pull_request_target`뿐인 정책을 봐. 순서는 상관없다. `.github/workflows/review-status.yml`이 대상이어야 한다. `workflow_path`가 없거나, `include`가 `~ALL`이거나 비어 있거나, 그 경로 또는 그에 맞는 glob이 `include`에 있으면 대상이다. `exclude`가 그 파일에 맞으면 대상이 아니다. `*`는 `/`를 넘지 않고 `**`는 넘는다. 패턴을 판별할 수 없으면 대상으로 보고 표시해. 그런 정책이 없거나, 둘 중 하나가 빠지거나, 다른 이벤트까지 허용하면 표시해.

## 2. 보고

1. 프로젝트별 표: 병합 수, revert·hotfix 수, CI 시간 중앙값(이번 기간·비교 기간·증가 표시), 멈춘 PR 수, 리뷰 기록 누락 수, hotfix 비율(참고용), 마지막 정기 감사 날짜, 이벤트 정책(있음·없음·비해당).
2. 병합 PR 목록: 점검 항목 1의 필드와 리뷰 기록 누락 여부를 PR마다 적어.
3. 회고 후보: revert·hotfix PR 목록. 회고는 실행하지 마(`POLICY.md` §6).
4. 사용자 결정: 결정이 필요한 항목만 적어. 없으면 없다고 써. 위 1~3은 결정 항목이 없어도 빼지 마. 근거가 없는 항목을 PASS로 적지 마.

한국어로 간단명료하게 보고해.
