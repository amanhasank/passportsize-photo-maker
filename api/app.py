from flask import Flask, request, render_template, send_file
from PIL import Image, ImageEnhance, ImageDraw
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__, template_folder="templates", static_folder="static")

A4_WIDTH_MM, A4_HEIGHT_MM = 210, 297
DPI = 300
WIDTH_PX = int(A4_WIDTH_MM / 25.4 * DPI)
HEIGHT_PX = int(A4_HEIGHT_MM / 25.4 * DPI)

PASSPORT_WIDTH_CM, PASSPORT_HEIGHT_CM = 3.5, 4.5
PASSPORT_WIDTH_PX = int(PASSPORT_WIDTH_CM / 2.54 * DPI)
PASSPORT_HEIGHT_PX = int(PASSPORT_HEIGHT_CM / 2.54 * DPI)

def enhance_image(img):
    img = ImageEnhance.Brightness(img).enhance(1.1)
    img = ImageEnhance.Contrast(img).enhance(1.2)
    return img

def compose_sheet(img, n):
    enhanced = enhance_image(img)
    passport_img = enhanced.resize((PASSPORT_WIDTH_PX, PASSPORT_HEIGHT_PX))
    cols = WIDTH_PX // PASSPORT_WIDTH_PX
    rows = HEIGHT_PX // PASSPORT_HEIGHT_PX
    max_fit = cols * rows
    n = min(n, max_fit)

    sheet = Image.new('RGB', (WIDTH_PX, HEIGHT_PX), 'white')
    count = 0
    for r in range(rows):
        for c in range(cols):
            if count >= n:
                break
            x = c * PASSPORT_WIDTH_PX
            y = r * PASSPORT_HEIGHT_PX
            sheet.paste(passport_img, (x, y))

            draw = ImageDraw.Draw(sheet)
            border_color = (160, 160, 160)
            border_width = int(DPI * 0.02)
            for i in range(border_width):
                draw.rectangle([x+i, y+i, x+PASSPORT_WIDTH_PX-i-1, y+PASSPORT_HEIGHT_PX-i-1], outline=border_color)
            count += 1
        if count >= n:
            break
    return sheet

def create_pdf_sheet(img_pil):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    img_pil.save("/tmp/temp.jpg", "JPEG")
    c.drawImage("/tmp/temp.jpg", 0, 0, A4[0], A4[1])
    c.showPage()
    c.save()
    buf.seek(0)
    os.remove("/tmp/temp.jpg")
    return buf

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        f = request.files['image']
        num = int(request.form['number'])
        img = Image.open(f.stream).convert("RGB")
        sheet = compose_sheet(img, num)
        buf = io.BytesIO()
        sheet.save(buf, format='JPEG')
        buf.seek(0)
        return send_file(buf, mimetype='image/jpeg', as_attachment=True, download_name='passport_sheet.jpg')
    return render_template('index.html')

@app.route('/pdf', methods=['POST'])
def pdf():
    f = request.files['image']
    num = int(request.form['number'])
    img = Image.open(f.stream).convert("RGB")
    sheet = compose_sheet(img, num)
    pdf_bytes = create_pdf_sheet(sheet)
    return send_file(pdf_bytes, mimetype='application/pdf', as_attachment=True, download_name='passport_sheet.pdf')
