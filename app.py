from flask import Flask, render_template, send_from_directory, request
from werkzeug.utils import secure_filename
import json
import os
from drive_upload import upload_to_drive  # 📌 Google Drive 업로드 함수

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 🔹 썸네일 + 업로드 페이지
@app.route('/upload/<sample>')
def upload(sample):
    config_path = os.path.join('sample_config', f'{sample}.json')

    if not os.path.exists(config_path):
        return f'❌ 샘플 \"{sample}\" 구성 파일이 존재하지 않습니다.'

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    display_name = config.get("display_name", sample)
    photo_list = config.get("photos", [])

    return render_template("uploader.html", sample=sample, display_name=display_name, photo_list=photo_list)

# 🔹 썸네일 이미지 제공
@app.route('/thumbs/<filename>')
def thumbs(filename):
    return send_from_directory('static/thumbs', filename)

# 🔹 파일 업로드 처리 → Google Drive 업로드
@app.route('/upload_file/<sample>/<photo_id>', methods=['POST'])
def handle_file_upload(sample, photo_id):
    if 'file' not in request.files:
        return '❌ 파일이 없습니다.', 400

    file = request.files['file']
    if file.filename == '':
        return '❌ 파일 이름이 없습니다.', 400

    customer_name = request.form.get('customer_name')
    if not customer_name:
        return '❌ 주문자 이름이 없습니다.', 400

    filename = secure_filename(photo_id + '.jpg')
    local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(local_path)

    try:
        upload_to_drive(local_path, filename, customer_name)
        return f'✅ {filename} 업로드 성공!'
    except Exception as e:
        return f'❌ 업로드 실패: {e} 카톡으로 문의주세요', 500

if __name__ == '__main__':
    app.run(debug=True)
