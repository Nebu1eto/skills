# Effective Writing

[English](README.md)

명확한 주장, 출처 기준, 매체에 맞는 형식을 지키며 글을 작성하고 다듬는 스킬입니다. 언어와 분야에 따라 계층화된 참조 가이드를 적재합니다.

## 목적

사용자에게 보이는 글, 저장소 문서, 리뷰 코멘트, 티켓, 보고서, 이메일, 슬라이드 문구, 요약문을 작성하거나 수정할 때 사용합니다. 모든 언어를 지원합니다.

일반적인 AI식 표현, 근거 없는 주장, 과장된 어조, 잘못된 인용, 초안 흔적, 매체에 맞지 않는 마크업을 줄이는 데 도움을 줍니다.

## 사용법

```bash
/effective-writing 이 README 섹션을 다시 작성해 주세요.
/effective-writing 이 보고서에서 근거 없는 주장을 검토해 주세요.
/effective-writing 이 결과를 간결한 PR 코멘트로 작성해 주세요.
/effective-writing この章を推敲してください。
```

## 적합한 작업

- README 및 문서 문장
- 기술 설명과 보고서
- 리뷰 코멘트와 이슈 티켓
- 이메일과 짧은 메시지
- 요약문과 슬라이드 문구
- 출처 기반 문장 수정
- 다국어 문서

## 계층화된 참조 가이드

스킬은 출력 언어와 문서 유형에 따라 참조 가이드를 적재합니다:

| 상황 | 적재되는 참조 |
|---|---|
| 영어 | `base-writing.md` + `en-writing.md` |
| 일본어 일반 | `base-writing.md` + `ja-writing.md` |
| 일본어 기술 문서 | `base-writing.md` + `ja-writing.md` + `ja-tech-writing.md` |
| 기타 언어 | `base-writing.md` |

### 명명 규칙

- `base-writing.md` — 모든 언어에 적용되는 규칙
- `<언어코드>-writing.md` — 특정 언어의 규칙
- `base-<분야>-writing.md` — 모든 언어의 특정 분야 규칙
- `<언어코드>-<분야>-writing.md` — 특정 언어의 특정 분야 규칙

## 참고한 스킬

일본어 작문 참조 문서(`ja-writing.md`, `ja-tech-writing.md`)는 [@k16shikano](https://github.com/k16shikano)의 다음 스킬을 기반으로 작성되었습니다 ([Unlicense](https://gist.github.com/k16shikano/67625f2a7d96e3bbdfae8d571a936063)):

- [japanese-tech-writing](https://gist.github.com/k16shikano/fd287c3133457c4fd8f5601d34aa817d)
- [cognitive-rhythm-writing](https://gist.github.com/k16shikano/eb2929f13ed19c97188393d297be8432)

## 구조

```text
effective-writing/
├── SKILL.md
├── agents/openai.yaml
└── references/
    ├── base-writing.md
    ├── en-writing.md
    ├── ja-writing.md
    └── ja-tech-writing.md
```
