# 🚢 AI-TRADE-AUTOMATION

**LLM(Gemini) 기반 무역 서류 분석 및 HS CODE 자동 추천 시스템**

## 🔍 핵심 기능
1. **INVOICE 데이터화**
- 인보이스 서류 데이터를 Oracle DB와 연동하여 디지털화
- 품명, 상세 설명 등 핵심 무역 정보 실시간 조회

2. **AI HS CODE 추천**
- Google Gemini API를 활용하여 품목별 최적의 HS CODE(6자리) 추론
- 관세 분류 근거 및 추론 신뢰도(0~100%) 함께 제시

## 🛠 기술 스택
- **언어**: Python 3.10+
- **프레임워크**: FastAPI, Bootstrap 5
- **인공지능**: Google Generative AI (Gemini)
- **데이터베이스**: Oracle Database

## 📸 실행 화면
<img width="1897" height="680" alt="image" src="https://github.com/user-attachments/assets/cfa810c1-de7c-459e-95b0-652c73dd63f5" />
<img width="1882" height="614" alt="image" src="https://github.com/user-attachments/assets/67ad4aea-b770-42dc-9e26-4a07f6eafd1b" />
<img width="1901" height="394" alt="image" src="https://github.com/user-attachments/assets/8cb63d3e-60a3-4964-a38e-72e7023357a5" />

## ⚙️ 실행 방법
1. `.env` 파일에 API 키와 DB 정보 설정
2. `pip install fastapi uvicorn google-generativeai python-dotenv python-oracledb`
3. `uvicorn main:app --reload`

## 🛠 향후 보완 예정 사항
본 프로젝트는 데이터 보안을 위해 다음과 같은 보안 원칙을 준수 예정
- [ ] **OCR 고도화**: PDF 및 이미지 형태의 인보이스에서 텍스트 자동 추출 기능 추가
- [ ] **비식별화 로직 강화**: 정규표현식을 활용한 민감 정보(금액, 업체명) 자동 필터링 엔진 구축
- [ ] **판정 결과 히스토리 관리**: AI가 추천한 코드와 실제 확정된 코드 간의 차이를 분석하여 정확도 개선
