<!--
PR 본문 양식. 헤더 이름(## Summary, ## Evidence, ## Merge Danger)과 Door, Author는 그대로 둔다.
작성 기록은 아래 Author 줄이거나, 같은 내용의 두 줄이다.
  작성 도구: Claude Code | Cursor | Cursor 클라우드 에이전트 | 사람
  작성 모델: 도구가 보여주는 모델 이름. 사람은 `없음`.
tool과 모델이 둘 다 있어야 한다. 이전 도구가 있으면 이전 작성 모델: 에 이름을 쉼표로 적는다.
축 이름은 Standards, Spec, 버그 찾기, Security다. 버그 찾기와 Security를 돌리지 않으면 모델은 `해당 없음: <이유>`이고 P0·P1·P2는 0이다.
리뷰를 시작하지 못한 축은 모델·effort·P0·P1·P2에 미실행이라고 적는다. 미실행은 0이 아니다.
head SHA는 이 표를 쓸 때의 PR head 전체 40자다. 리뷰 모델의 토큰이 작성 모델과 같으면 안 된다.
-->

Author: <tool> / <model>

## Summary

왜 바꾸는지, 바꾸기 전과 후.

## Evidence

실행한 명령, 결과, head SHA, 확인하지 않은 범위.

## Merge Danger

<!-- Door 값은 `양쪽 문` 또는 `한쪽 문`만. POLICY.md §10으로 판정한다. -->

Door: <양쪽 문 또는 한쪽 문>

영향 범위:

복구:

신뢰 경계 기준: 없음

## Review evidence

| axis | model | effort | head SHA | P0 | P1 | P2 | result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Standards |  |  |  |  |  |  |  |
| Spec |  |  |  |  |  |  |  |
| 버그 찾기 |  |  |  |  |  |  |  |
| Security |  |  |  |  |  |  |  |
