# PDF 번역 스킬

PDF 문서를 Markdown 및 PDF로 번역합니다.

[English](README.md)

## 설정

```bash
bash scripts/setup_env.sh
```

## 사용법

```bash
/pdf-translator document.pdf --target-lang ko
/pdf-translator paper.pdf --source-lang ja --academic
/pdf-translator paper.pdf --high-quality
```

## 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--source-lang` | 소스 언어 (자동 감지) | `auto` |
| `--target-lang` | 대상 언어 | `ko` |
| `--output-format` | markdown / pdf / both | `both` |
| `--academic` | 원문 용어 병기 | `false` |
| `--high-quality` | Opus 모델 사용 | `false` |
| `--dict` | 사용자 정의 사전 JSON | - |

## 아키텍처

```
PDF → extract_to_markdown.py → source.md → 분할 (대용량) → 번역 → generate_pdf.py → 출력
```

## 라이선스

MIT
