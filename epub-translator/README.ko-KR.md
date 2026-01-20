# EPUB 번역기

[English](README.md)

EPUB 파일을 번역하는 Claude Code 스킬.

## 특징

- 다국어 지원 (ja, en, zh, ko, ar, he 등)
- 병렬 번역 (동시 처리 수 설정 가능)
- 대용량 파일 분할 및 병합
- 레이아웃 변환 (세로/가로, LTR/RTL)
- LLM 기반 품질 검증

## 설치

**요구사항**: Python 3.8+, `zip`, `unzip`

```json
// ~/.claude/settings.json
{
  "skills": ["/path/to/epub-translator"]
}
```

## 사용법

```bash
# 일본어 → 한국어 (기본값)
/epub-translator "novel.epub"

# 영어 → 한국어
/epub-translator "book.epub" --source-lang en

# 일본어 → 중국어 (세로쓰기)
/epub-translator "novel.epub" --target-lang zh --vertical

# 10개 에이전트로 일괄 번역
/epub-translator "/books/" --parallel 10

# Opus 모델로 고품질 번역
/epub-translator "novel.epub" --high-quality
```

## 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--source-lang` | 원본 언어 | `ja` |
| `--target-lang` | 대상 언어 | `ko` |
| `--parallel` | 동시 에이전트 수 | `5` |
| `--split-threshold` | 분할 임계값 (KB) | `30` |
| `--split-parts` | 분할 개수 | `4` |
| `--high-quality` | Opus 모델 사용 | `false` |
| `--vertical` | 세로쓰기 (ja/zh만) | `false` |
| `--dict` | 커스텀 사전 (JSON) | 없음 |
| `--output-dir` | 출력 디렉토리 | `./translated` |

## 레이아웃 변환

대상 언어에 따라 출력 레이아웃 결정:

| 대상 | 방향 | 쓰기 모드 | 비고 |
|------|------|----------|------|
| ko, en | ltr | horizontal-tb | |
| ja, zh | ltr | horizontal-tb | 기본값 |
| ja, zh + `--vertical` | rtl | vertical-rl | 우종서 |
| ar, he | rtl | horizontal-tb | |

## 품질 검증

2단계 검증:
1. **원문 잔존 검사**: 번역 안 된 문자 탐지
2. **LLM 검증**: 자연스러움, 번역투 평가

품질 점수: 90-100 (우수), 75-89 (양호), 60-74 (보통), <60 (재번역)

## 커스텀 사전

고유명사와 문서 특유 용어에만 사용.

```json
{
  "proper_nouns": {
    "names": { "田中太郎": "다나카 타로" }
  },
  "domain_terms": {
    "独自技術": "고유 기술"
  }
}
```

## 워크플로우

1. **분석**: EPUB 추출, 대용량 파일 분할
2. **번역**: 서브에이전트로 병렬 번역
3. **메타데이터**: 목차, 제목, 저자 번역
4. **레이아웃**: 쓰기 방향 변환
5. **검증**: 품질 검사
6. **패키징**: 병합 후 EPUB 생성

## 문제 해결

| 문제 | 해결 |
|------|------|
| 원문 잔존 | `verify.py` 실행 |
| 대용량 파일 타임아웃 | `--split-threshold` 낮추기 |
| XML 오류 | 꺾쇠괄호 확인 (`<텍스트>` → `〈텍스트〉`) |
