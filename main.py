from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
from collections import Counter
import matplotlib.colors as mcolors

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

def get_color_name(rgb):
    # Convert RGB to hex
    hex_color = rgb_to_hex(rgb)
    
    # Calculate distance to known colors
    min_dist = float('inf')
    closest_color = "Unknown"
    
    for color_name, color_hex in mcolors.CSS4_COLORS.items():
        # Convert hex to RGB
        h = color_hex.lstrip('#')
        color_rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        
        # Calculate Euclidean distance
        dist = sum((c1 - c2) ** 2 for c1, c2 in zip(rgb, color_rgb)) ** 0.5
        
        if dist < min_dist:
            min_dist = dist
            closest_color = color_name
    
    return closest_color.replace('dark', 'dark ').replace('light', 'light ').title()

def extract_colors(image_path, num_colors=5):
    # Open image
    img = Image.open(image_path)
    
    # Resize for faster processing if the image is large
    if max(img.size) > 800:
        img.thumbnail((800, 800))
    
    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Get pixel data
    pixels = np.array(img)
    pixels = pixels.reshape(-1, 3)
    
    # Round the RGB values to reduce the number of distinct colors
    pixels = (pixels // 10) * 10
    
    # Count occurrences of each color
    color_counter = Counter(map(tuple, pixels))
    
    # Get the most common colors
    most_common_colors = color_counter.most_common(num_colors)
    
    # Format the results
    results = []
    for color, count in most_common_colors:
        percentage = count / len(pixels) * 100
        hex_color = rgb_to_hex(color)
        color_name = get_color_name(color)
        results.append({
            'rgb': color,
            'hex': hex_color,
            'name': color_name,
            'percentage': round(percentage, 2)
        })
    
    return results

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        
        # If the user does not select a file, the browser submits an empty file
        if file.filename == '':
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the image
            num_colors = int(request.form.get('num_colors', 5))
            colors = extract_colors(filepath, num_colors)
            
            return render_template('result.html', 
                                  image_file=url_for('static', filename=f'uploads/{filename}'),
                                  colors=colors,
                                  filename=filename)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)