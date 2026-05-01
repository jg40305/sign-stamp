import tkinter as tk
from tkinter import messagebox
import fitz
from PIL import Image, ImageTk
import io

# ===== 請修改這裡 =====
PDF_INPUT   = "x.pdf"
STAMP_IMG   = "已去背.png"
PDF_OUTPUT  = "x_print.pdf"
PAGE_NUM    = 1       # 第幾頁（0起算，第2頁=1）
SCALE       = 1.5     # 預覽縮放比例
SPLIT_RATIO = 0.62    # 大章佔圖片寬度比例
LARGE_SIZE  = (98, 84)   # 大章在PDF裡的尺寸（點）
SMALL_SIZE  = (63, 77)   # 小章在PDF裡的尺寸（點）
# ======================

class StampPlacer:
    def __init__(self):
        # 切章
        combined = Image.open(STAMP_IMG).convert("RGBA")
        w, h = combined.size
        split = int(w * SPLIT_RATIO)
        self.large_orig = combined.crop((0, 0, split, h))
        self.small_orig = combined.crop((split, 0, w, h))

        # 讀PDF頁面
        self.doc = fitz.open(PDF_INPUT)
        page = self.doc[PAGE_NUM]
        pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE))
        self.bg = Image.open(io.BytesIO(pix.tobytes("png")))
        self.pdf_w = page.rect.width
        self.pdf_h = page.rect.height

        # 章的顯示圖
        lw, lh = int(LARGE_SIZE[0]*SCALE), int(LARGE_SIZE[1]*SCALE)
        sw, sh = int(SMALL_SIZE[0]*SCALE), int(SMALL_SIZE[1]*SCALE)
        self.large_disp = self.large_orig.resize((lw, lh), Image.LANCZOS)
        self.small_disp = self.small_orig.resize((sw, sh), Image.LANCZOS)

        # 初始位置（顯示像素）
        self.pos = {
            "large": [int(149*SCALE), int(476*SCALE)],
            "small": [int(404*SCALE), int(485*SCALE)]
        }
        self._drag = {"x": 0, "y": 0, "tag": None}
        self.setup()

    def setup(self):
        self.root = tk.Tk()
        self.root.title("拖動章到正確位置，再點儲存")

        # Canvas + scrollbar
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)
        cw = int(self.pdf_w * SCALE)
        ch = int(self.pdf_h * SCALE)
        self.canvas = tk.Canvas(frame, width=min(cw,900), height=min(ch,750),
                                scrollregion=(0,0,cw,ch))
        sb_y = tk.Scrollbar(frame, orient="vertical",   command=self.canvas.yview)
        sb_x = tk.Scrollbar(frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side=tk.RIGHT,  fill=tk.Y)
        sb_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 背景
        self.bg_photo = ImageTk.PhotoImage(self.bg)
        self.canvas.create_image(0, 0, anchor="nw", image=self.bg_photo)

        # 章
        self.large_photo = ImageTk.PhotoImage(self.large_disp)
        self.small_photo = ImageTk.PhotoImage(self.small_disp)
        self.ids = {
            "large": self.canvas.create_image(*self.pos["large"], anchor="nw",
                                              image=self.large_photo, tags="large"),
            "small": self.canvas.create_image(*self.pos["small"], anchor="nw",
                                              image=self.small_photo, tags="small")
        }
        for tag in ("large", "small"):
            self.canvas.tag_bind(tag, "<ButtonPress-1>",
                                 lambda e, t=tag: self.start_drag(e, t))
            self.canvas.tag_bind(tag, "<B1-Motion>",
                                 lambda e, t=tag: self.drag(e, t))

        # 按鈕
        bar = tk.Frame(self.root)
        bar.pack(fill=tk.X, padx=10, pady=6)
        tk.Label(bar, text="直接用滑鼠拖動章的位置", font=("Arial",11)).pack(side=tk.LEFT, padx=6)
        tk.Button(bar, text="💾 儲存 PDF", command=self.save,
                  bg="#4CAF50", fg="white", font=("Arial",11), padx=12).pack(side=tk.RIGHT)

        self.root.mainloop()

    def start_drag(self, e, tag):
        self._drag = {"x": e.x, "y": e.y, "tag": tag}

    def drag(self, e, tag):
        dx, dy = e.x - self._drag["x"], e.y - self._drag["y"]
        self.canvas.move(self.ids[tag], dx, dy)
        self.pos[tag][0] += dx
        self.pos[tag][1] += dy
        self._drag["x"], self._drag["y"] = e.x, e.y

    def save(self):
        # 轉回 PDF 座標
        lx, ly = self.pos["large"][0]/SCALE, self.pos["large"][1]/SCALE
        sx, sy = self.pos["small"][0]/SCALE, self.pos["small"][1]/SCALE

        self.large_orig.save("_tmp_large.png")
        self.small_orig.save("_tmp_small.png")

        doc  = fitz.open(PDF_INPUT)
        page = doc[PAGE_NUM]
        page.insert_image(fitz.Rect(lx, ly, lx+LARGE_SIZE[0], ly+LARGE_SIZE[1]),
                          filename="_tmp_large.png", overlay=True)
        page.insert_image(fitz.Rect(sx, sy, sx+SMALL_SIZE[0], sy+SMALL_SIZE[1]),
                          filename="_tmp_small.png", overlay=True)
        doc.save(PDF_OUTPUT)
        messagebox.showinfo("完成", f"已儲存：{PDF_OUTPUT}")
        self.root.destroy()

StampPlacer()