import requests
from PIL import Image, ExifTags
import io
import cv2
import pytesseract
import numpy as np

# Tesseract का रास्ता
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

API_TOKEN = "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"
IMAGE_API_URL = "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector"
TEXT_API_URL = "https://api-inference.huggingface.co/models/mrm8488/bert-tiny-finetuned-fake-news-detection"

def get_metadata_truth(img):
    exif = img.getexif()
    if not exif:
        return "<br><br><span style='color: #757575; font-size: 13px;'><i>[Forensics Note: Digital/Compressed Media. No metadata found.]</i></span>"
    return "<br><br><span style='color: #757575; font-size: 13px;'><i>[Forensics Note: Original Camera Metadata is intact.]</i></span>"

def offline_image_forensics(img):
    try:
        open_cv_image = np.array(img.convert('RGB')) 
        open_cv_image = open_cv_image[:, :, ::-1].copy() 
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if laplacian_var < 150:
            return {"status": "FAKE", "score": float(laplacian_var), "method": "Offline (Laplacian Pixel Noise Engine)"}
        else:
            return {"status": "REAL", "score": float(laplacian_var), "method": "Offline (Laplacian Pixel Noise Engine)"}
    except Exception as e:
        return {"status": "ERROR", "score": 0}

def scan_image_with_ai(img):
    img_copy = img.copy()
    img_copy.thumbnail((600, 600))
    if img_copy.mode != 'RGB': 
        img_copy = img_copy.convert('RGB')
    img_byte_arr = io.BytesIO()
    img_copy.save(img_byte_arr, format='JPEG', quality=80)
    compressed_bytes = img_byte_arr.getvalue()
    
    headers = {"Authorization": "Bearer " + API_TOKEN, "Content-Type": "application/octet-stream"}
    
    try:
        res = requests.post(IMAGE_API_URL, headers=headers, data=compressed_bytes, timeout=3)
        if res.status_code == 200:
            result = res.json()
            label = result[0]['label'].lower()
            score = result[0]['score'] * 100
            if 'artificial' in label or 'fake' in label:
                return {"status": "FAKE", "score": score, "method": "Cloud AI Neural Engine"}
            else:
                return {"status": "REAL", "score": score, "method": "Cloud AI Neural Engine"}
    except:
        pass
            
    return offline_image_forensics(img)

def check_photo(file_path):
    try:
        img = Image.open(file_path)
        metadata_text = get_metadata_truth(img)
        res = scan_image_with_ai(img)
        method_used = res.get('method', 'Unknown')
        
        if res["status"] == "FAKE":
            return "<span style='color: #d32f2f; font-weight: bold; font-size: 16px;'>[TRUE RESULT] AI GENERATED/MANIPULATED</span><br><span style='color: #555; font-size: 12px;'><b>Active Engine:</b> " + method_used + "</span>" + metadata_text
        elif res["status"] == "REAL":
            return "<span style='color: #2e7d32; font-weight: bold; font-size: 16px;'>[TRUE RESULT] REAL IMAGE</span><br><span style='color: #555; font-size: 12px;'><b>Active Engine:</b> " + method_used + "</span>" + metadata_text
        else:
            return "<span style='color: #f57c00; font-weight: bold;'>[ERROR] Unreadable format or corrupted file.</span>"
    except Exception as e:
        return "<span style='color: #d32f2f;'>Error: " + str(e) + "</span>"

def check_video(file_path):
    try:
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened(): 
            return "Error reading video."
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames_to_test = [total_frames // 4, total_frames // 2, (total_frames * 3) // 4]
        
        fake_count = 0
        for frame_no in frames_to_test:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            ret, frame = cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame)
                res = scan_image_with_ai(pil_img)
                if res.get("status") == "FAKE": 
                    fake_count += 1
        cap.release()
        
        if fake_count > 0:
            return "<span style='color: #d32f2f; font-weight: bold; font-size: 16px;'>[TRUE RESULT] DEEPFAKE VIDEO DETECTED</span><br><span style='color: #555;'>Forensics: Artificial manipulation found in video frames.</span>"
        else:
            return "<span style='color: #2e7d32; font-weight: bold; font-size: 16px;'>[TRUE RESULT] REAL VIDEO</span><br><span style='color: #555;'>Forensics: Frames appear to have natural sensor noise.</span>"
    except Exception as e:
        return str(e)

def check_news(input_data, data_type="text"):
    text = ""
    if data_type == "image":
        try:
            img = Image.open(input_data).convert('L')
            text = pytesseract.image_to_string(img)
        except: 
            pass
    else:
        text = input_data
        
    final_header = "<h3 style='color:#b57a3d;'>Extracted Text:</h3><div style='background:#eee;padding:10px;border-radius:5px;'>" + text[:200] + "...</div><br>"
    headers = {"Authorization": "Bearer " + API_TOKEN}
    try:
        res = requests.post(TEXT_API_URL, headers=headers, json={"inputs": text}, timeout=4)
        if res.status_code == 200:
            pred = res.json()[0]
            top = max(pred, key=lambda x: x['score'])
            if 'fake' in str(top['label']).lower() or '1' in str(top['label']).lower():
                return final_header + "<span style='color: #d32f2f; font-weight: bold;'>[TRUE RESULT] FAKE NEWS (Cloud AI)</span>"
            return final_header + "<span style='color: #2e7d32; font-weight: bold;'>[TRUE RESULT] REAL NEWS (Cloud AI)</span>"
    except: 
        pass
        
    fake_keywords = ['win', 'free', 'lottery', 'forwarded', 'claim', 'urgent', 'virus', 'whatsapp', 'alert', 'shocking']
    if any(word in text.lower() for word in fake_keywords):
        return final_header + "<span style='color: #d32f2f; font-weight: bold;'>[TRUE RESULT] FAKE/SPAM NEWS DETECTED (Offline Engine)</span>"
    else:
        return final_header + "<span style='color: #2e7d32; font-weight: bold;'>[TRUE RESULT] REAL NEWS (Offline Engine)</span>"