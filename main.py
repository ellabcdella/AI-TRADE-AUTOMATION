import os
import json
import oracledb
import pandas as pd
import io
import re
from fastapi import FastAPI, File, UploadFile, Body, Response
from fastapi.responses import HTMLResponse
import google.generativeai as genai
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 1. 오라클 클라이언트 초기화
try:
    oracledb.init_oracle_client()
except Exception as e:
    print(f"Oracle Client 초기화 참고: {e}")

# 2. 제미나이 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

app = FastAPI()

# 3. 오라클 DB 연결 정보 (환경변수 유지)
DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "dsn": os.getenv("DB_DSN")
}

# --- [페이지 라우팅 추가] ---

@app.get("/", response_class=HTMLResponse)
def index_page():
    if os.path.exists("index.html"):
        with open("index.html", encoding="utf-8") as f:
            return f.read()
    return "<h1>index.html 파일을 찾을 수 없습니다.</h1>"

@app.get("/converter", response_class=HTMLResponse)
def converter_page():
    if os.path.exists("converter.html"):
        with open("converter.html", encoding="utf-8") as f:
            return f.read()
    return "<h1>converter.html 파일을 찾을 수 없습니다.</h1>"

@app.get("/hs-check", response_class=HTMLResponse)
def hs_check_page():
    if os.path.exists("hs_check.html"):
        with open("hs_check.html", encoding="utf-8") as f:
            return f.read()
    return "<h1>hs_check.html 파일을 찾을 수 없습니다.</h1>"

# --- [전체 조회 (컬럼 추가)] ---
@app.get("/get-invoices")
def get_invoices():
    try:
        conn = oracledb.connect(user=DB_CONFIG["user"], password=DB_CONFIG["password"], dsn=DB_CONFIG["dsn"])
        cursor = conn.cursor()
        # item_name, description_of_goods 추가 조회
        cursor.execute("SELECT filename, invoice_no, total_amount, shipper, consignee, pol, pod, item_name, description_of_goods FROM INVOICE")
        columns = [col[0].lower() for col in cursor.description]
        rows = cursor.fetchall()
        result = [dict(zip(columns, row)) for row in rows]
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- [대시보드 화면 - 기존 유지] ---
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    if os.path.exists("index.html"):
        with open("index.html", encoding="utf-8") as f:
            return f.read()
    return "<h1>index.html 파일을 찾을 수 없습니다.</h1>"

# --- [AI 분석 및 저장 (프롬프트 및 SQL 수정)] ---
@app.post("/analyze-document")
async def analyze_document(file: UploadFile = File(...)):
    try:
        content = await file.read()
        document_part = {"mime_type": file.content_type, "data": content}
        
        prompt = """
        너는 무역 서류 전문 분석가야. 반드시 아래 JSON 형식으로만 응답해.
        정보를 찾을 수 없다면 빈 문자열("")을 넣어줘.
        {
          "invoice_number": "인보이스 번호",
          "total_amount": "통화 기호 포함 총 금액",
          "shipper": "송하인 전체 명칭",
          "consignee": "수하인 전체 명칭",
          "port_of_loading": "선적항",
          "port_of_discharge": "도착항",
          "item_name": "가장 대표적인 상품명 하나",
          "description_of_goods": "상세 물품 설명 전체"
        }
        """
        response = model.generate_content([prompt, document_part])
        clean_json_str = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json_str)
        
        conn = oracledb.connect(user=DB_CONFIG["user"], password=DB_CONFIG["password"], dsn=DB_CONFIG["dsn"])
        cursor = conn.cursor()
        # 9개 컬럼 바인딩으로 수정
        sql = """
        INSERT INTO INVOICE (filename, invoice_no, total_amount, shipper, consignee, pol, pod, item_name, description_of_goods)
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)
        """
        cursor.execute(sql, [
            file.filename,
            data.get('invoice_number', ''),
            data.get('total_amount', ''),
            data.get('shipper', ''),
            data.get('consignee', ''),
            data.get('port_of_loading', ''),
            data.get('port_of_discharge', ''),
            data.get('item_name', ''),
            data.get('description_of_goods', '')
        ])
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

# --- [데이터 수정 API (신규 컬럼 UPDATE 추가)] ---
@app.put("/update-invoice")
async def update_invoice(data: dict = Body(...)):
    try:
        conn = oracledb.connect(user=DB_CONFIG["user"], password=DB_CONFIG["password"], dsn=DB_CONFIG["dsn"])
        cursor = conn.cursor()
        # item_name, description_of_goods 업데이트 추가
        sql = """
        UPDATE INVOICE 
        SET total_amount = :1, 
            shipper = :2, 
            consignee = :3,  
            pol = :4, 
            pod = :5,
            item_name = :6,
            description_of_goods = :7
        WHERE invoice_no = :8
        """
        cursor.execute(sql, [
            data.get('total_amount'), 
            data.get('shipper'), 
            data.get('consignee'), 
            data.get('pol'), 
            data.get('pod'),
            data.get('item_name'),
            data.get('description_of_goods'),
            data.get('invoice_no')
        ])
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- [엑셀 다운로드 API - 기존 유지] ---
@app.get("/download-excel")
async def download_excel():
    try:
        conn = oracledb.connect(user=DB_CONFIG["user"], password=DB_CONFIG["password"], dsn=DB_CONFIG["dsn"])
        df = pd.read_sql("SELECT * FROM INVOICE", conn)
        conn.close()

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Invoice_List')
        
        return Response(
            content=output.getvalue(),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename="invoices.xlsx"'}
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- [데이터 삭제 API - 기존 유지] ---
@app.delete("/delete-invoice/{invoice_no}")
async def delete_invoice(invoice_no: str):
    try:
        conn = oracledb.connect(user=DB_CONFIG["user"], password=DB_CONFIG["password"], dsn=DB_CONFIG["dsn"])
        cursor = conn.cursor()
        sql = "DELETE FROM INVOICE WHERE invoice_no = :1"
        cursor.execute(sql, [invoice_no])
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "message": f"Invoice {invoice_no} deleted."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- [HS CODE 추론 API] ---
@app.post("/hs-check")
async def hs_check_api(data: dict = Body(...)):
    try:
        item_name = data.get("item_name", "")
        description = data.get("description", "")
        
        if not item_name and not description:
            return {"status": "error", "message": "상품 정보가 없습니다."}

        prompt = f"""
        너는 국제 무역 전문가야. 아래 정보를 바탕으로 HS CODE 6자리를 추천해.
        [상품명]: {item_name}
        [상세설명]: {description}
        
        반드시 아래 JSON 형식으로만 응답해. 다른 설명은 하지마.
        {{
          "hs_code": "숫자6자리",
          "reason": "근거 요약",
          "confidence": "0~100"
        }}
        """
        response = model.generate_content(prompt)
        text = response.text
        
        # ```json ... ``` 태그가 있어도, 없어도 JSON만 추출하는 로직
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            clean_json_str = match.group()
            return json.loads(clean_json_str)
        else:
            # 정규식 실패 시 기존 방식 시도
            clean_json_str = text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json_str)
            
    except Exception as e:
        print(f"Server Error: {str(e)}")
        return {"status": "error", "message": str(e)}