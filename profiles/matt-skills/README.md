# matt-skills 프로필

리뷰의 두 축 판단, 회고, PR 본문 내용을 [Matt Pocock 스킬](https://github.com/mattpocock/skills)에 맡기고 싶을 때 켠다. 안전장치는 그대로 repo-baseline 프롬프트가 맡는다. 리뷰 전 확인, 직접 고치기, 라운드, 외부 리뷰 판정, Review 칸이 그것이다. 이 프로필을 켠 저장소에서는 스킬 설치가 규칙이다.

## 켜기

1. 스킬을 설치한다. Claude Code 플러그인이면 [에이전트 안내](../../templates/github/agents/README.md)의 설정을 쓴다. 다른 하네스는 `~/.agents/skills/`나 저장소의 `.agents/skills/`에 둔다.
2. 소비 레포 `REVIEW.md` 끝에 아래 절을 붙인다. 리뷰어는 `REVIEW.md`를 늘 읽으므로 이 절이 프로필을 켰다는 표시다.

   ```markdown
   ## 스킬 위임

   이 저장소는 repo-baseline matt-skills 프로필을 쓴다. 리뷰어는 repo-baseline 클론의 `profiles/matt-skills/README.md` 「리뷰」 절차를 따른다.
   ```

3. 리뷰하는 기기에서 `python3 -I <repo-baseline 클론>/profiles/matt-skills/check_skills.py`가 종료 코드 0인지 본다. 스킬마다 찾은 경로와 sha256 앞 12자리를 출력한다. 같은 이름이라도 다른 스킬이면 찾은 것으로 보지 않는다. 리뷰할 저장소 안(`.claude/skills/`, `.agents/skills/`)에 같은 이름의 스킬이 있으면 실패한다. 하네스가 그 사본을 먼저 읽는데, 리뷰 대상 PR이 그 사본을 바꿀 수 있기 때문이다. 그래서 이 프로필의 스킬은 저장소에 커밋하지 않고 홈 폴더나 플러그인으로 설치한다.

## 리뷰

[prompts/review.md](../../prompts/review.md) 할 일 1번(두 축)을 아래처럼 한다. 나머지 순서는 그대로다.

1. `check_skills.py`를 돌린다. 종료 코드가 1이면 리뷰를 멈추고 「남은 지적」에 "리뷰 미완(스킬 없음)"과 출력을 적는다.
2. 하위 에이전트 리뷰어이거나 fork PR이면 스킬에 맡기지 않고 review.md 1번을 직접 한다. `code-review` 스킬은 축마다 하위 에이전트를 띄우고, `git diff <기준점>...HEAD`로 작업 트리의 HEAD를 보기 때문이다. 하위 에이전트 안에서는 하위 에이전트를 못 띄울 수 있고, fork PR은 checkout하지 않는다. 「확인한 것」에 그 이유를 적는다.
3. PR 본문의 `완료 기준:` 줄을 저장소 밖 임시 파일(예: `$TMPDIR/spec-<번호>.md`)에 쓴다.
4. `code-review` 스킬을 부른다. 넘기는 것은 셋이다.
   - 기준점: 리뷰 전 확인이 출력한 base ref. 2라운드부터는 직전 리뷰의 마지막 커밋.
   - spec: 3번 파일 경로. 트래커 설정이 없다는 안내는 무시한다.
   - 기준 문서: `REVIEW.md`의 「실패로 보는 것」·「코딩 기준」. 이 기준이 스킬의 스멜 목록보다 먼저라고 덧붙인다.
5. 스킬 보고의 Spec 지적은 `[Spec]`으로, Standards 지적은 `[Standards]`로 옮긴다. 심각도는 리뷰어가 `REVIEW.md`로 정한다. 스멜 목록에서 나온 지적은 「코딩 기준」에 근거가 없으면 P2 상한 안에서만 남긴다. 스킬은 고치지 않으므로 고치기는 review.md 3번대로 리뷰어가 한다.
6. 「확인한 것」에 `check_skills.py`가 출력한 `code-review` 경로와 sha256을 적는다.

## 회고

`/retro`를 써도 된다. 입력은 [prompts/retro.md](../../prompts/retro.md)의 입력이다. 반영할 곳은 retro.md 2번 순서(린트·검사, `REVIEW.md` 「코딩 기준」·「배운 규칙」, `AGENTS.md` 길잡이)다. `CODING_STANDARDS.md`는 만들지 않는다. 이 저장소의 리뷰는 그 파일을 읽지 않는다. 제안 중 사람이 고른 것만 반영한다(POLICY §6).

## PR 본문

`/pr`로 Summary와 「그림」을 써도 된다. 칸은 `.github/pull_request_template.md`를 지킨다. `완료 기준:`, 되돌리는 법, 신뢰 경계, Review 칸을 빼지 않는다.

## 맞춘 판

2026-11-10에 mattpocock/skills 설치본(커밋 `4ae2317`)의 `code-review`·`retro`·`pr`로 이 절차를 맞췄다. 스킬을 올리면 위 절차가 스킬 동작과 맞는지 다시 보고, `check_skills.py`의 표지 문구도 확인한다.
