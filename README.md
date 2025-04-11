<h1 align="center">PNU Chat</h1>
<img width="100%" alt="부산대학교" align="center" src="https://github.com/user-attachments/assets/ec4f2b4f-7f35-49d6-8919-596ca93424bc" />

<p align="center">
  <br/>
  <b>AI 어시스턴트가 부산대학교의 공지사항, 학사일정, 학적, 교육 과정 등에 대한 궁금증을 신속하게 해결해줍니다.</b>
</p>


## 프로젝트 소개
부산대학교의 학과별 공지사항, 학생지원시스템, 학사일정 등의 데이터를 주기적으로 수집하고, <br/> 이를 바탕으로 사용자의 질문에 답변하는 RAG 기반의 FAQ 챗봇 서비스입니다.

ChatGPT, Grok3 등과 유사한 대화형 인터페이스를 제공하며, 누구나 쉽고 편리하게 이용할 수 있습니다.

- 개발 기간: 2024.10 ~
- 접속 주소: [pnu.chat](https://pnu.chat)

## 팀원 소개
| **강민석** | **박준혁** | **박상훈** |
|:-:|:-:|:-:|
| <img src="https://github.com/myeolinmalchi.png" width="150" height="150" style="border-radius: 50%;"> | <img src="https://github.com/JakeFRCSE.png" width="150" height="150" style="border-radius: 50%;"> | <img src="https://github.com/sanghunii.png" width="150" height="150" style="border-radius: 50%;"> | 
| **개발 총괄** | **문서 파싱 서버** | **API 엔드포인트** |
| [myeolinmalchi](https://github.com/myeolinmalchi) | [JakeFRCSE](https://github.com/JakeFRCSE) | [sanghunii](https://github.com/sanghunii) |
## Stacks
  - Backend: `Python3` `FastAPI` `SQLAlchemy` `Dependency Injector`
  - Frontend: `React.js` `TypeScript` `Zustand`
  - Text Embedding: [`myeolinmalchi/bge-m3-fastapi`](https://github.com/myeolinmalchi/bge-m3-fastapi)
  - Reranker: [`BAAI/bge-reranker-v2-m3`](https://huggingface.co/BAAI/bge-reranker-v2-m3) [`huggingface/text-embeddings-inference`](https://github.com/huggingface/text-embeddings-inference)
  - Database: `PostgreSQL` `pgvector`
  - Chat Completion: `gpt-4o-mini`

## 화면 구성
| 메인 화면 | 채팅 페이지 | 사이드바 |
|:-:|:-:|:-:|
| <img src="https://github.com/user-attachments/assets/a61e48d3-3fd9-4148-bbc9-7e1907358010" width="300" /> | <img src="https://github.com/user-attachments/assets/c07aba53-bf1e-482a-80e3-dfc31ee72269" width="300"/> | <img width="300" src="https://github.com/user-attachments/assets/aa563c93-0d3b-4dd2-920d-92068c51c222"/> |

## RAG Diagram

- TODO

## Server Architecture Diagram

- TODO
