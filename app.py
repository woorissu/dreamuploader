from flask import Flask, render_template, send_from_directory, request, jsonify
from werkzeug.utils import secure_filename
import json
import os
from drive_upload import upload_to_drive  # 📌 Google Drive 업로드 함수

app = Flask(__name__)

# 🔹 업로더 페이지
@app.route('/upload/<sample>')
def upload(sample):
    config_path = os.path.join('products', sample, 'config.json')

    if not os.path.exists(config_path):
        return f'❌ 샘플 \"{sample}\" 구성 파일이 존재하지 않습니다.'

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    display_name = config.get("display_name", sample)
    photo_list = config.get("photos", [])

    print(f"📂 로딩된 config for {sample}: {photo_list}")

    return render_template("uploader.html", sample=sample, display_name=display_name, photo_list=photo_list)

# 🔹 썸네일 이미지 제공
@app.route('/thumbs/<sample>/<filename>')
def thumbs(sample, filename):
    thumb_path = os.path.join('products', sample, 'thumbnails')
    return send_from_directory(thumb_path, filename)

# 🔹 파일 업로드 처리 → Google Drive 업로드 + 폴더 링크 반환
@app.route('/upload_file/<sample>/<photo_id>', methods=['POST'])
def handle_file_upload(sample, photo_id):
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '파일이 없습니다.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '파일 이름이 없습니다.'}), 400

    customer_name = request.form.get('customer_name')
    if not customer_name:
        return jsonify({'status': 'error', 'message': '주문자 이름이 없습니다.'}), 400

    filename = secure_filename(photo_id + '.jpg')

    try:
        # ✅ 드라이브 업로드 후 폴더 링크 반환
        folder_link = upload_to_drive(file.stream, filename, customer_name)
        return jsonify({
            'status': 'ok',
            'filename': filename,
            'folder_link': folder_link
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'업로드 실패: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
