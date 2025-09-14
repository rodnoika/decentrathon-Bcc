# -*- coding: utf-8 -*-
# Логика запуска PaddleOCR (CLI) + сбор текста

import subprocess, sys, re, ast, os
from pathlib import Path
from typing import List, Tuple
# в начале файла, рядом с import'ами
try:
    from gemini_post import clean_and_extract, post_check
    _HAS_GEMINI = True
except ImportError:
    _HAS_GEMINI = False


def run_ocr(in_file, out_dir_str, lang,
            use_doc_unwarping, use_doc_orientation, use_textline_orientation,
            use_server_rec, server_rec_dir_str,
            use_gpu, gpu_id) -> Tuple[str, str, List[str]]:
    """
    Возвращает (log_text, merged_text, files_out)
    """
    if not in_file:
        return "Файл не выбран.", "", []

    in_path = Path(in_file if isinstance(in_file, (str, os.PathLike)) else getattr(in_file, "name"))
    out_dir = Path(out_dir_str)
    out_dir.mkdir(parents=True, exist_ok=True)

    server_rec_dir = Path(server_rec_dir_str) if server_rec_dir_str else Path("")

    cmd = [sys.executable, "-m", "paddleocr", "ocr",
           "-i", str(in_path),
           "--lang", str(lang),
           "--save_path", str(out_dir)]

    if use_doc_unwarping:
        cmd += ["--use_doc_unwarping", "true"]
    if use_doc_orientation:
        cmd += ["--use_doc_orientation_classify", "true"]
    if use_textline_orientation:
        cmd += ["--use_textline_orientation", "true"]

    if use_server_rec and server_rec_dir.exists():
        cmd += ["--rec_model_dir", str(server_rec_dir)]

    if use_gpu:
        try:
            gid = int(gpu_id)
        except Exception:
            gid = 0
        cmd += ["--device", f"gpu:{gid}"]

    log_file = out_dir / f"{in_path.stem}_paddleocr.log"
    log_text = "[CMD] " + " ".join(cmd) + "\n"

    with log_file.open("w", encoding="utf-8") as lf:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            log_text += line
            lf.write(line)
        rc = proc.wait()

    if rc != 0:
        log_text += f"\n[ERROR] CLI вернул код {rc}. Лог: {log_file}\n"

    # Ищем TXT
    candidates = sorted(out_dir.glob(f"{in_path.stem}_page*.txt"))
    if not candidates:
        candidates = sorted(out_dir.glob(f"{in_path.stem}.txt"))

    merged_path = out_dir / f"{in_path.stem}_ALL.txt"
    merged_text = ""
    files_out = [str(log_file)]

    if candidates:
        with merged_path.open("w", encoding="utf-8") as w:
            for i, p in enumerate(candidates, 1):
                w.write(p.read_text(encoding="utf-8"))
                if i < len(candidates):
                    w.write("\n\n")
        merged_text = merged_path.read_text(encoding="utf-8")
        files_out.append(str(merged_path))
    else:
        # План Б: достать rec_texts из лога
        log = log_file.read_text(encoding="utf-8", errors="ignore")
        texts = []
        for m in re.finditer(r"['\"]rec_texts['\"]:\s*(\[[^\]]*\])", log, flags=re.S):
            try:
                arr = ast.literal_eval(m.group(1))
                if isinstance(arr, list):
                    texts.extend([str(x) for x in arr])
            except Exception:
                continue
        if texts:
            merged_path.write_text("\n".join(texts), encoding="utf-8")
            merged_text = merged_path.read_text(encoding="utf-8")
            files_out.append(str(merged_path))
        else:
            log_text += "\n[WARN] Не нашёл *.txt и не смог извлечь rec_texts из лога."
            

    return log_text, (merged_text if merged_text else "(пусто)"), files_out
