import os, json, re, textwrap
from typing import Tuple
from dotenv import load_dotenv

load_dotenv()

def _get_model(model_name: str):
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Не найден GEMINI_API_KEY (задай в .env).")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)

def _split_chunks(text: str, limit: int = 180_000):
    if not text:
        return ["(пусто)"]
    return [text[i:i+limit] for i in range(0, len(text), limit)]

def clean_and_extract(ocr_text: str, model_name: str = "gemini-1.5-pro") -> Tuple[str, str]:
    system = textwrap.dedent("""
        Ты помощник по пост-обработке результатов OCR (русский/английский деловой документ).
        Задачи:
        1) Исправить артефакты OCR, склеить переносы слов, восстановить абзацы и нумерацию.
        2) НЕ выдумывать данные: если не уверен — оставляй как есть/пиши null.
        Формат ответа:
        ---
        CLEAN_MARKDOWN:
        (аккуратно отформатированный документ в Markdown)
        ---
        EXTRACTED_JSON:
        {
          "doc_type": "contract | act | invoice | ...",
          "doc_number": "...",
          "doc_date": "YYYY-MM-DD|null",
          "parties": [{"name":"...", "role":"Seller|Buyer|Продавец|Покупатель|...", "address":null}],
          "currency": "RUB|BYN|KZT|USD|...",
          "total_amount": "строка как в документе или null",
          "incoterms": "например FCA Zhlobin 2010|null",
          "sections": [{"index":"I","title":"..."}],
          "emails": ["..."],
          "phones": ["..."]
        }
        Возвращай строго в указанном формате, без дополнительных комментариев.
    """).strip()

    model = _get_model(model_name)
    parts = _split_chunks(ocr_text)
    content = [{"role": "user", "parts": [system]}]
    for i, chunk in enumerate(parts, 1):
        content.append({"role": "user", "parts": [f"Фрагмент {i}/{len(parts)}:\n{chunk}"]})

    resp = model.generate_content(content)
    full = resp.text or ""

    clean_md = ""
    extracted_json = "{}"

    m1 = re.search(r"CLEAN_MARKDOWN:\s*(.*?)\n---", full, flags=re.S)
    if m1:
        clean_md = m1.group(1).strip()

    m2 = re.search(r"EXTRACTED_JSON:\s*(\{.*\})\s*$", full, flags=re.S)
    if m2:
        raw_json = m2.group(1).strip()
        try:
            obj = json.loads(raw_json)
            extracted_json = json.dumps(obj, ensure_ascii=False, indent=2)
        except Exception:
            extracted_json = raw_json

    return clean_md, extracted_json

def post_check(clean_markdown: str, extracted_json: str, model_name: str = "gemini-1.5-pro") -> str:
    spec = textwrap.dedent("""
        Ты валидатор пост-OCR результата. Дан очищенный Markdown документа и JSON с полями.
        Проверь согласованность и полноту. Не придумывай факты, если поле не вытекает из текста — оставь null.
        Верни ТОЛЬКО JSON следующей формы:

        {
          "ok": true|false,
          "issues": [
            {"type":"missing_field","field":"doc_number","where":"EXTRACTED_JSON","hint":"номер не найден"},
            {"type":"inconsistency","field":"currency","where":"CLEAN_MARKDOWN vs JSON","hint":"в тексте BYN, в JSON RUB"},
            {"type":"suspicious_value","field":"doc_date","where":"CLEAN_MARKDOWN","hint":"дата в будущем"},
            {"type":"format","field":"emails[0]","where":"JSON","hint":"некорректный email"}
          ],
          "normalizations": {
            "dates_detected": ["..."],
            "amounts_detected": ["..."],
            "incoterms_detected": ["..."]
          },
          "summary": "краткие выводы по качеству распознавания и извлечения"
        }
    """).strip()

    model = _get_model(model_name)
    content = [
        {"role": "user", "parts": [spec]},
        {"role": "user", "parts": [f"CLEAN_MARKDOWN:\n{clean_markdown or '(пусто)'}"]},
        {"role": "user", "parts": [f"EXTRACTED_JSON:\n{extracted_json or '{}'}"]},
    ]
    resp = model.generate_content(content)
    text = (resp.text or "").strip()

    try:
        obj = json.loads(text)
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        m = re.search(r"(\{.*\})", text, flags=re.S)
        if m:
            raw = m.group(1)
            try:
                obj = json.loads(raw)
                return json.dumps(obj, ensure_ascii=False, indent=2)
            except Exception:
                return raw 
        return text
