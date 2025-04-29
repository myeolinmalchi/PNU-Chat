# Retrieval Strategy Evaluation

## Description

- 다양한 Retrieval 전략(Dense-only, Hybrid 등)에 대해 Recall 성능을 비교 평가합니다.
- 특히 저사양 CPU 환경(Q8 모델)에서 품질 저하를 최소화하는 전략 탐색을 목표로 합니다.

## Environment

- Text Embedding: `BAAI/bge-m3`
- Reranker: `BAAI/bge-reranker-v2-m3`
- Quantization:
  - FP32 (Full Precision, ONNX)
  - Q8 (8-bit Quantized, GGUF)
- Augmentation: `solar-pro`

## Dataset Augmentation

### 증강 및 검증 파이프라인
1. Query 생성 (Augmentor)
  - LLM을 기반으로 각 문서 본문과 관련된 질문(Query) 5개를 생성합니다.
  - 질문과 표현은 다르지만 동일한 의미를 갖는 Paraphrase를 1개씩 추가 생성합니다.
  - 각 문서마다 총 10개의 질의(5 Queries + 5 Paraphrases)가 생성됩니다.
2. Query 검증 (Validator)
  - 생성된 각 Query가 아래 조건을 만족하는지 LLM을 통해 검증합니다.
  - 조건을 만족하지 못할 경우, 사유(`reasons`)를 기록하고 질의를 재생성합니다.
3. 최종 데이터 저장
  - 모든 질의가 성공적으로 생성되면, 각 문서의 URL과 관련 질의 목록을 JSONL 포맷으로 저장합니다.

### 출력 예시
```json
{
  "url": "https://onestop.pusan.ac.kr/page?menuCD=000000000000282",
  "queries": [
    "졸업 유예는 몇번까지 할 수 있나요?",
    "학사학위취득유예는 최대 몇 회 가능한가요?",
    "일반휴학 중 입대하는 경우 휴학을 병역휴학으로 전환하는 방법은 무엇인가요?",
    "학생지원시스템에서 일반휴학과 병역휴학을 신청하는 방법은 무엇인가요?"
  ]
}
```

## Evaluation Results

### 학생지원시스템

- Total Documents: 120
- Total Queries: 870 (10/doc)

#### Strategies

| ver | Strategy | Description |
|---:|:---|:---|
| V1 | Dense-only | 본문 Semantic Search |
| V2 | Hybrid (Dense + Sparse) | 본문 Lexical + Semantic Score 가중합 |
| V3 | Hybrid + RRF | 본문 및 요약 Hybrid Score + RRF |
| V4 | 🚧 V3 + Reranker | Top-10 Retrieval 결과 Rerank |

#### Results

![output (5)](https://github.com/user-attachments/assets/03be36ac-cb66-4945-be9d-bed233232d2a)

  
| ver | rrf k | $w_{lex}$ | Recall@3<br>(FP32) | Recall@3<br>(Q8) |
|:---:|---:|---:|---:|---:|
| V1 | - | - | 76.90 | 62.30 |
| V2 | - | 0.3 | 🥇78.74 | 69.54 |
| V2 | - | 0.5 | 77.36 | 70.57 |
| V2 | - | 0.7 | 74.25 | 68.05 |
| V3 | 40 | 0.3 | 77.36 | 68.85 |
| V3 | 40 | 0.5 | 🥈78.51 | 74.02 |
| V3 | 40 | 0.7 | 77.01 | 76.09 |
| V3 | 20 | 0.7 | 77.36 | 🥈77.13 |
| V3 | 10 | 0.7 | 77.82 | 🥇77.82 |
| V4 | 40 | 0.5 | 🚧37.93 | - |
