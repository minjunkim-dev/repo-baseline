# linear 프로필

선택 프로필이다. 사이클·프로젝트 같은 계획 화면이나 여러 저장소를 한눈에 볼 곳이 필요할 때 켠다. GitHub Issue가 원본이고(POLICY §8, [github 프로필](../../templates/github/README.md#작업-추적)), Linear는 Linear의 GitHub Issues 동기화로 붙인다. 이 프로필이 없으면 계획은 Issue와 `docs/`에 적는다.

## 언제 켜는가

- 사이클(스프린트)을 정하고 돌아본다.
- 저장소 여러 개의 일을 한 화면에서 본다.
- 개발자가 아닌 사람이 GitHub보다 Linear에서 일하는 게 편하다.
- 공개하지 않을 판단을 둘 곳이 필요하다.

위에 해당하지 않으면 켜지 않는다. 같은 정보를 두 곳에서 보게 될 뿐이다.

## 동기화되는 것

[Linear GitHub 문서](https://linear.app/docs/github)(확인일 2026-11-20) 기준이다.

- 양쪽으로: 제목, 설명, 상태, 라벨, 담당자, 동기화 스레드의 댓글, 우선순위, 하위 Issue.
- 동기화하지 않음: 동기화 스레드 밖의 댓글(비공개 논의), 사이클, 프로젝트. 차단 관계(blocked by)는 문서의 동기화 목록에 없다.
- 양방향 동기화는 Linear 팀 하나에 저장소 하나다. 켠 뒤에 생긴 Issue만 동기화한다. 그 전 Issue는 Linear의 가져오기로 옮긴다.

## 규칙

| 정보 | 원본 |
| --- | --- |
| 목표·완료 조건·결정 기록, 열림·닫힘, 하위 Issue, 차단 관계 | GitHub Issue |
| 시작 준비 상태 | GitHub Issue의 상태 라벨([matt-skills](../matt-skills/README.md#issue-절차와-상태-라벨)) |
| 진행 상태(작업 중·리뷰 중·끝) | Linear 상태. PR이 열리고 병합될 때 Linear가 옮긴다 |
| 사이클, 프로젝트, 공개하지 않을 판단 | Linear |

- 저장소 작업은 Issue와 Linear가 동기화된 한 쌍이다. Linear에만 있는 저장소 작업은 만들지 않는다.
- 라벨은 시작 준비만, Linear 상태는 진행만 뜻한다. 같은 것을 두 번 적지 않는다.
- 동기화하는 Linear 팀에는 상태 라벨 다섯 개만 둔다. Linear 팀의 기본 라벨(Bug, Feature 등)은 지운다. 라벨은 양쪽으로 동기화되므로 남기면 GitHub에 분류 라벨이 생긴다. Linear 라벨이 GitHub에 새로 만들어지는지와 라벨 그룹이 어떻게 대응되는지는 문서에 없다. 켤 때 한 번 시험하고 결과를 이 절에 적는다.
- 브랜치 이름과 PR 본문에는 GitHub 번호만 쓴다(`Closes #12`). Linear의 「브랜치 이름 복사」(`user/lin-123-…`)는 pr-conventions의 브랜치 검사와 다르다. GitHub Issue가 닫히면 동기화로 Linear도 닫힌다.
- 차단 관계는 GitHub에서만 맞춘다.
- 우선순위는 동기화되어 공개 Issue에 보인다. 공개하지 않을 판단은 동기화 스레드 밖의 댓글에만 둔다(POLICY §8).
- matt-skills의 트래커는 GitHub으로 둔다. Linear MCP 같은 연결이 있어도 스킬이 Linear에 바로 쓰지 않게 한다.

## 켜기

1. Linear 조직에 GitHub 연동을 설치하고, 저장소 하나를 Linear 팀 하나와 양방향 동기화한다(Linear 설정 > Integrations > GitHub).
2. 그 팀의 라벨을 상태 라벨 다섯 개로 맞춘다.
3. 소비 레포 `AGENTS.md` 「작업 방식」 끝에 한 줄을 붙인다: `- 계획은 Linear로 본다. 원본은 GitHub Issue다. repo-baseline linear 프로필의 규칙을 따른다.`
