from flask import Flask, request
from train_model import check_photo, check_news
import time
import base64

app = Flask(__name__)

HOME_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAWCIT | Cyber Intelligence</title>
    <style>
        body { font-family: 'Times New Roman', serif; background-color: #f1f3f4; margin: 0; display: flex; flex-direction: column; align-items: center; min-height: 100vh; }
        .gov-header { background-color: #212121; width: 100%; padding: 20px 0; text-align: center; border-bottom: 3px solid #b57a3d; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
        .logo-text { font-size: 32px; font-weight: bold; color: white; letter-spacing: 2px; text-transform: uppercase; }
        .emblem { color: #f9a825; font-size: 16px; margin-bottom: -5px; }
        .main-container { background-color: #ffffff; padding: 40px 60px; border-radius: 4px; box-shadow: 0 8px 30px rgba(0,0,0,0.1); text-align: center; width: 500px; margin-top: 40px; margin-bottom: 40px; border: 1px solid #ddd; position: relative; }
        h1 { color: #1a237e; font-size: 22px; margin-bottom: 10px; font-weight: bold; border-bottom: 1px solid #ccc; padding-bottom: 10px; text-transform: uppercase; }
        input[type="file"], textarea { font-family: inherit; font-size: 14px; color: #555; background-color: #fcfcfc; border: 1px solid #bbb; padding: 12px; width: 90%; margin-bottom: 10px; }
        button { background-color: #1a237e; color: white; border: none; padding: 12px 30px; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; cursor: pointer; border-radius: 2px; font-weight: bold; width: 95%; }
        button.news-btn { background-color: #b57a3d; margin-top: 10px;}
        button:hover { opacity: 0.9; }
        .divider { margin: 30px 0; border-top: 2px dashed #ccc; position: relative; }
        .divider span { background: white; padding: 0 15px; color: #777; font-size: 12px; position: absolute; top: -8px; left: 40%; font-weight: bold; }
        .or-text { font-weight: bold; color: #888; margin: 10px 0; font-size: 14px; }
        #loading-overlay { display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255, 255, 255, 0.95); z-index: 10; flex-direction: column; justify-content: center; align-items: center; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #1a237e; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin-bottom: 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        #scanning-text { color: #d32f2f; font-weight: bold; font-family: monospace; letter-spacing: 1px; }
    </style>
</head>
<body>
    <div class="gov-header">
        <div class="emblem">भारत सरकार | GOVT. OF INDIA</div>
        <div class="logo-text">RAWCIT | D.F.D</div>
    </div>
    <div class="main-container">
        <div id="loading-overlay">
            <div class="spinner"></div>
            <div id="scanning-text">Initiating Deep Scan...</div>
        </div>
        
        <h1>1. Image Forensics</h1>
        <p style="font-size: 12px; color: #666; margin-bottom: 20px;">Upload image to detect AI generation or manipulation.</p>
        <form id="uploadForm" action="/predict_image" method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*" required>
            <button type="submit">Scan Image</button>
        </form>

        <div class="divider"><span>OR</span></div>

        <h1 style="color: #b57a3d;">2. Text / News Forensics</h1>
        <p style="font-size: 12px; color: #666; margin-bottom: 20px;">Paste text OR upload a news screenshot to check authenticity.</p>
        
        <form id="textForm" action="/predict_news" method="POST" enctype="multipart/form-data">
            <textarea name="news_text" rows="3" placeholder="Paste suspicious text message here..."></textarea>
            
            <div class="or-text">--- OR ---</div>
            
            <input type="file" name="news_image" accept="image/*" title="Upload Newspaper cutting or Screenshot">
            
            <button type="submit" class="news-btn">Analyze Text / Screenshot</button>
        </form>
    </div>
    <script>
        document.getElementById('uploadForm').onsubmit = showLoad;
        document.getElementById('textForm').onsubmit = function(e) {
            // Check if at least one input is provided
            var text = document.getElementsByName('news_text')[0].value;
            var file = document.getElementsByName('news_image')[0].value;
            if(!text && !file) {
                alert("Please paste text OR upload a screenshot!");
                e.preventDefault();
                return;
            }
            showLoad();
        };
        function showLoad() {
            document.getElementById('loading-overlay').style.display = 'flex';
            const texts = ["Initiating Connection...","Extracting Data...","Running AI Engine...","Generating Report..."];
            let i = 0; setInterval(() => { if (i<texts.length) { document.getElementById('scanning-text').innerText = texts[i]; i++; } }, 600);
        }
    </script>
</body>
</html>
"""

RESULT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Intelligence Report - RAWCIT</title>
    <style>
        body {{ font-family: 'Times New Roman', sans-serif; background-color: #f1f3f4; display: flex; flex-direction: column; align-items: center; min-height: 100vh; margin: 0; padding-top: 80px; }}
        .gov-header {{ background-color: #212121; width: 100%; padding: 15px 0; text-align: center; border-bottom: 3px solid #b57a3d; position: fixed; top: 0; z-index: 100; }}
        .logo-text {{ font-size: 24px; font-weight: bold; color: white; text-transform: uppercase; letter-spacing: 1px; }}
        .analysis-container {{ display: flex; flex-direction: row; background: white; padding: 30px; border-radius: 4px; box-shadow: 0 8px 30px rgba(0,0,0,0.1); width: 850px; border: 1px solid #ddd; margin-bottom: 40px; gap: 30px; }}
        
        .evidence-viewer {{ flex: 1; border: 1px solid #eee; padding: 15px; background: #fafafa; display: flex; align-items: center; justify-content: center; flex-direction: column; overflow: hidden; }}
        #analyzed-content {{ max-width: 100%; max-height: 400px; display: block; }}
        .text-evidence {{ font-family: monospace; font-size: 14px; color: #444; background: #e0e0e0; padding: 15px; border-radius: 4px; width: 90%; word-wrap: break-word; }}
        
        .img-zoom-container {{ position: relative; cursor: crosshair; display: inline-block; }}
        .img-zoom-lens {{ position: absolute; border: 2px solid #b57a3d; border-radius: 50%; width: 100px; height: 100px; box-shadow: 0 0 10px rgba(0,0,0,0.5); display: none; pointer-events: none; background-repeat: no-repeat; z-index: 10; }}

        .report-panel {{ flex: 1.2; display: flex; flex-direction: column; border-top: 5px solid #1a237e; padding-top: 20px; }}
        h2 {{ color: #1a237e; font-weight: normal; margin-top: 0; margin-bottom: 25px; border-bottom: 1px solid #ccc; padding-bottom: 15px; text-transform: uppercase; }}
        .verdict-box {{ font-size: 16px; color: #333; line-height: 1.6; border-left: 5px solid #f9a825; background-color: #f9f9f9; padding: 20px; text-align: left; font-style: italic; word-wrap: break-word; }}
        .btn {{ display: inline-block; margin-top: 20px; padding: 12px 30px; background: #1a237e; color: white; text-decoration: none; text-transform: uppercase; letter-spacing: 1px; font-size: 14px; border-radius: 2px; font-weight: bold; text-align: center; }}
    </style>
</head>
<body>
    <div class="gov-header"><div class="logo-text">Govt. of India - Intelligence Report</div></div>
    
    <div class="analysis-container">
        <div class="evidence-viewer">
            {evidence_html}
        </div>
        <div class="report-panel">
            <h2>Forensic Verdict</h2>
            <div class="verdict-box">{verdict_message}</div>
            <a href="/" class="btn">← Back to Portal</a>
        </div>
    </div>
    
    <script>
        function imageZoom(imgID, lensID) {{
          var img = document.getElementById(imgID);
          var lens = document.getElementById(lensID);
          if(!img || !lens) return; 
          
          var zoom = 3;
          lens.style.backgroundImage = "url('" + img.src + "')";
          lens.style.backgroundSize = (img.width * zoom) + "px " + (img.height * zoom) + "px";
          img.addEventListener("mousemove", moveLens);
          lens.addEventListener("mousemove", moveLens);
          img.addEventListener("mouseleave", () => {{ lens.style.display = 'none'; }});
          img.addEventListener("mouseenter", () => {{ lens.style.display = 'block'; }});

          function moveLens(e) {{
            e.preventDefault();
            var a = img.getBoundingClientRect();
            var x = e.pageX - a.left - window.pageXOffset;
            var y = e.pageY - a.top - window.pageYOffset;
            x = x - (lens.offsetWidth / 2);
            y = y - (lens.offsetHeight / 2);
            if (x > img.width - lens.offsetWidth) x = img.width - lens.offsetWidth;
            if (x < 0) x = 0;
            if (y > img.height - lens.offsetHeight) y = img.height - lens.offsetHeight;
            if (y < 0) y = 0;
            lens.style.left = x + "px";
            lens.style.top = y + "px";
            lens.style.backgroundPosition = "-" + (x * zoom) + "px -" + (y * zoom) + "px";
          }}
        }}
        window.onload = function() {{ setTimeout(() => {{ imageZoom("analyzed-image", "zoom-lens"); }}, 100); }};
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return HOME_HTML

@app.route('/predict_image', methods=['POST'])
def predict_image():
    if request.files:
        file = request.files['file']
        try:
            image_bytes = file.read()
            encoded_string = base64.b64encode(image_bytes).decode('utf-8')
            image_data_url = f"data:image/jpeg;base64,{encoded_string}"
            file.seek(0)
        except:
            image_data_url = ""

        time.sleep(2) 
        result_text = check_photo(file)
        evidence = f"""<div class="img-zoom-container" id="zoom-container"><div class="img-zoom-lens" id="zoom-lens"></div><img id="analyzed-image" src="{image_data_url}"></div><p style='font-size:12px; color:#777;'>🔍 Hover for forensic magnification</p>"""
        return RESULT_HTML.format(evidence_html=evidence, verdict_message=result_text)
    return "No file uploaded!"

@app.route('/predict_news', methods=['POST'])
def predict_news():
    # 1. चेक करें कि यूज़र ने टेक्स्ट डाला है या फोटो (OCR के लिए)
    text_data = request.form.get('news_text', '').strip()
    
    if 'news_image' in request.files and request.files['news_image'].filename != '':
        # अगर फोटो अपलोड की है (OCR चालू करें)
        file = request.files['news_image']
        time.sleep(2)
        
        # यहाँ हम OCR के लिए train_model.py को फोटो भेज रहे हैं
        result_text = check_news(file, data_type="image")
        
        # रिज़ल्ट पेज पर दिखाने के लिए फोटो को बेस64 में बदलना
        file.seek(0)
        encoded_string = base64.b64encode(file.read()).decode('utf-8')
        image_data_url = f"data:image/jpeg;base64,{encoded_string}"
        
        evidence = f"""<h3 style='color:#b57a3d; margin-top:0;'>OCR Image Analysis:</h3><img src="{image_data_url}" style="max-width:200px; border:1px solid #ccc;"><p style='font-size:11px; color:#555;'>Extracting text from screenshot...</p>"""
        return RESULT_HTML.format(evidence_html=evidence, verdict_message=result_text)
        
    elif text_data:
        # अगर सीधा टेक्स्ट टाइप किया है
        time.sleep(2)
        result_text = check_news(text_data, data_type="text")
        evidence = f"""<h3 style='color:#b57a3d; margin-top:0;'>Intercepted Text:</h3><div class='text-evidence'>"{text_data}"</div>"""
        return RESULT_HTML.format(evidence_html=evidence, verdict_message=result_text)
        
    return "Please provide text or an image!"

if __name__ == '__main__':
    app.run(debug=True)