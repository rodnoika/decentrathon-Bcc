import os, tempfile, shutil
from pathlib import Path
import gradio as gr
from ocr import run_ocr
def _default_out_dir() -> str:
    try:
        p = (Path.cwd() / "ocr_out").resolve()
        p.mkdir(parents=True, exist_ok=True)
        return str(p)
    except Exception:
        return tempfile.gettempdir()

def _guess_rec_dir() -> str:
    env = os.getenv("PADDLE_REC_MODEL_DIR", "").strip()
    cands = []
    if env:
        cands.append(Path(env).expanduser())
    home = Path.home()
    cands += [
        home / ".paddlex" / "official_models" / "eslav_PP-OCRv5_server_rec",
        home / ".paddlex" / "official_models" / "eslav_PP-OCRv5_mobile_rec",
    ]
    for c in cands:
        if c and c.exists():
            return str(c.resolve())
    return "" 

DEFAULT_OUT = _default_out_dir()
DEFAULT_REC = "/home/user/app/eslav_PP-OCRv5_mobile_rec"

def run_and_stage(in_file, out_dir, lang,
                  use_doc_unwarping, use_doc_orientation, use_textline_orientation,
                  use_server_rec, server_rec_dir,
                  use_gpu, gpu_id):
    out_dir = (out_dir or "").strip()
    if not out_dir:
        out_dir = str(Path(tempfile.mkdtemp(prefix="ocr_out_")))
    server_rec_dir = (server_rec_dir or "").strip()

    log, text, files = run_ocr(
        in_file, out_dir, lang,
        use_doc_unwarping, use_doc_orientation, use_textline_orientation,
        use_server_rec, server_rec_dir,
        use_gpu, gpu_id
    )

    stage_dir = Path(tempfile.mkdtemp(prefix="gradio_stage_"))
    staged = []
    for fp in files or []:
        p = Path(fp)
        if p.exists():
            dst = stage_dir / p.name
            try:
                shutil.copy2(p, dst)
            except Exception:
                dst = stage_dir / f"{p.stem}_copy{p.suffix}"
                shutil.copy2(p, dst)
            staged.append(str(dst))
    return log, text, staged

with gr.Blocks(title="PaddleOCR (CLI) • Минимальный UI") as demo:
    gr.Markdown("### PaddleOCR (CLI) — минимальный интерфейс(В hugging face дают мало мощности CPU, поэтому это может занимать большое время)")

    with gr.Row():
        in_file = gr.File(label="Файл (PDF/изображение)", file_count="single", type="filepath")
        out_dir = gr.Textbox(label="Папка вывода (пусто = Temp)", value=DEFAULT_OUT)

    with gr.Row():
        lang = gr.Dropdown(choices=["ru","en"], value="ru", label="Язык")

    with gr.Row():
        use_doc_unwarping = gr.Checkbox(value=True, label="use_doc_unwarping")
        use_doc_orientation = gr.Checkbox(value=True, label="use_doc_orientation_classify")
        use_textline_orientation = gr.Checkbox(value=True, label="use_textline_orientation")

    with gr.Row():
        use_server_rec = gr.Checkbox(value=True, label="use_server_rec (если модель есть)")
        server_rec_dir = gr.Textbox(label="Путь к server rec модели", value=DEFAULT_REC)

    with gr.Row():
        use_gpu = gr.Checkbox(value=False, label="GPU")
        gpu_id = gr.Number(value=0, precision=0, label="GPU ID")

    run_btn = gr.Button("Запустить")

    log_box = gr.Textbox(label="Лог", lines=16)
    text_box = gr.Textbox(label="Сводный текст (ALL)", lines=16)
    files_out = gr.Files(label="Скачать (лог, ALL.txt)")

    run_btn.click(
        fn=run_and_stage,
        inputs=[in_file, out_dir, lang,
                use_doc_unwarping, use_doc_orientation, use_textline_orientation,
                use_server_rec, server_rec_dir,
                use_gpu, gpu_id],
        outputs=[log_box, text_box, files_out]
    )

if __name__ == "__main__":
    demo.launch(show_error=True, debug=True)
