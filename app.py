import subprocess, sys, re, ast
from pathlib import Path

in_path = Path(r"C:\Users\Rodnoi\Downloads\хакатон\8A16.pdf")   # файл или папка
out_dir = Path(r"C:\Users\Rodnoi\Downloads\хакатон\ocr_out")
LANG = "ru"

USE_DOC_UNWARPING = True
USE_DOC_ORIENTATION = True
USE_TEXTLINE_ORIENTATION = True

USE_SERVER_REC = True
SERVER_REC_DIR = Path(r"C:\Users\Rodnoi\.paddlex\official_models\eslav_PP-OCRv5_server_rec")

USE_GPU = False
GPU_ID = 0


out_dir.mkdir(parents=True, exist_ok=True)

cmd = [sys.executable, "-m", "paddleocr", "ocr",
       "-i", str(in_path),
       "--lang", LANG,
       "--save_path", str(out_dir)]

if USE_DOC_UNWARPING:
    cmd += ["--use_doc_unwarping", "true"]
if USE_DOC_ORIENTATION:
    cmd += ["--use_doc_orientation_classify", "true"]
if USE_TEXTLINE_ORIENTATION:
    cmd += ["--use_textline_orientation", "true"]

if USE_SERVER_REC and SERVER_REC_DIR.exists():
    cmd += ["--rec_model_dir", str(SERVER_REC_DIR)]
elif USE_SERVER_REC and not SERVER_REC_DIR.exists():
    print(f"[WARN] Server rec model not found: {SERVER_REC_DIR}. Продолжу с mobile по умолчанию.")

if USE_GPU:
    cmd += ["--device", f"gpu:{GPU_ID}"]

print("[CMD]", " ".join(cmd))

log_file = out_dir / f"{in_path.stem}_paddleocr.log"
with log_file.open("w", encoding="utf-8") as lf:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        print(line, end="")
        lf.write(line)
    rc = proc.wait()

if rc != 0:
    print(f"\n[ERROR] CLI вернул код {rc}. Лог: {log_file}")
    sys.exit(rc)

candidates = sorted(out_dir.glob(f"{in_path.stem}_page*.txt"))
if not candidates:
    candidates = sorted(out_dir.glob(f"{in_path.stem}.txt"))

if candidates:
    merged = out_dir / f"{in_path.stem}_ALL.txt"
    with merged.open("w", encoding="utf-8") as w:
        for i, p in enumerate(candidates, 1):
            w.write(p.read_text(encoding="utf-8"))
            if i < len(candidates):
                w.write("\n\n")
    print(f"\n[OK] Сводный текст: {merged}")
else:
    log = log_file.read_text(encoding="utf-8", errors="ignore")
    texts = []
    for m in re.finditer(r"['\"]rec_texts['\"]:\s*(\[[^\]]*\])", log, flags=re.S):
        try:
            arr = ast.literal_eval(m.group(1))  
            texts.extend(arr)
        except Exception:
            continue
    if texts:
        merged = out_dir / f"{in_path.stem}_ALL.txt"
        merged.write_text("\n".join(texts), encoding="utf-8")
        print(f"\n[OK] Сводный текст (из лога): {merged}")
    else:
        print("\n[WARN] Не нашёл *.txt и не смог извлечь rec_texts из лога. Проверь лог:", log_file)
