# Writing Tropes

[English](README.md)

명확한 주장, 출처 기준, 매체에 맞는 형식을 지키며 글을 작성하고 다듬는 스킬입니다.

## 목적

사용자에게 보이는 글, 저장소 문서, 리뷰 코멘트, 티켓, 보고서, 이메일, 슬라이드 문구, 요약문을 작성하거나 수정할 때 사용합니다.

일반적인 AI식 표현, 근거 없는 주장, 과장된 어조, 잘못된 인용, 초안 흔적, 매체에 맞지 않는 마크업을 줄이는 데 도움을 줍니다.

## 사용법

```bash
/writing-tropes Rewrite this README section.
/writing-tropes Review this report for unsupported claims.
/writing-tropes Draft a concise PR comment from these findings.
```

## 적합한 작업

- README 및 문서 문장
- 기술 설명과 보고서
- 리뷰 코멘트와 이슈 티켓
- 이메일과 짧은 메시지
- 요약문과 슬라이드 문구
- 출처 기반 문장 수정

## 작성 규칙

- 작성 전에 목적, 독자, 근거 범위, 주장 유형, 출력 형식을 확인합니다.
- 주장은 구체적이고, 출처에 묶여 있으며, 근거에 비례해야 합니다.
- 직접적인 동사와 일관된 용어를 사용합니다.
- 홍보성 어조, 일반적인 연결어, 극적인 문장 구조, 장식적 서식을 피합니다.
- 최종 출력 전에 자리표시자, 초안 메모, 도구 흔적, 인용 잔여물을 제거합니다.

## 참고 문서

이 스킬은 다음 전체 가이드를 따릅니다.

```text
references/writing-quality.md
```

이 파일은 스타일, 출처 표기, 인용 무결성, 형식, 최종 자체 점검 규칙의 기준입니다.

## 구조

```text
writing-tropes/
├── SKILL.md
├── agents/openai.yaml
└── references/writing-quality.md
```
