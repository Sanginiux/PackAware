from flask import Flask, render_template, request, jsonify
import os
import cv2
import numpy as np
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure app
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Setup CSRF protection
csrf = CSRFProtect(app)
csrf.init_app(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configure app
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_product():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    image = request.files['image']
    if image.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    if image and allowed_file(image.filename):
        try:
            # Secure the filename
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)
            
            # Read and analyze the image
            img = cv2.imread(filepath)
            
            if img is None:
                return jsonify({'error': 'Could not process image'}), 400
            
            # Convert to multiple color spaces for better detection
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        except Exception as e:
            return jsonify({'error': f'An error occurred: {str(e)}'}), 500
        
        # Enhanced material detection using multiple features
        def get_material_mask(img_hsv, img_lab, img_gray, material_type):
            if material_type == 'plastic':
                # Plastic detection using transparency and reflection
                hsv_mask = cv2.inRange(img_hsv, np.array([0, 0, 200]), np.array([180, 30, 255]))
                lab_mask = cv2.inRange(img_lab, np.array([200, 115, 115]), np.array([255, 140, 140]))
                return cv2.bitwise_and(hsv_mask, lab_mask)
            
            elif material_type == 'glass':
                # Glass detection using reflection and transparency
                hsv_mask = cv2.inRange(img_hsv, np.array([90, 0, 200]), np.array([140, 30, 255]))
                gray_thresh = cv2.threshold(img_gray, 200, 255, cv2.THRESH_BINARY)[1]
                return cv2.bitwise_and(hsv_mask, gray_thresh)
            
            elif material_type == 'metal':
                # Metal detection using reflection and color
                hsv_mask = cv2.inRange(img_hsv, np.array([0, 0, 100]), np.array([180, 30, 190]))
                lab_mask = cv2.inRange(img_lab, np.array([150, 120, 120]), np.array([255, 135, 135]))
                return cv2.bitwise_and(hsv_mask, lab_mask)
            
            else:  # paper
                # Paper detection using texture and color
                hsv_mask = cv2.inRange(img_hsv, np.array([20, 30, 50]), np.array([30, 255, 255]))
                lab_mask = cv2.inRange(img_lab, np.array([130, 120, 120]), np.array([220, 140, 140]))
                return cv2.bitwise_and(hsv_mask, lab_mask)
        
        # Calculate material percentages with enhanced detection
        plastic_mask = get_material_mask(hsv, lab, gray, 'plastic')
        glass_mask = get_material_mask(hsv, lab, gray, 'glass')
        metal_mask = get_material_mask(hsv, lab, gray, 'metal')
        paper_mask = get_material_mask(hsv, lab, gray, 'paper')
        
        total_pixels = img.shape[0] * img.shape[1]
        plastic_percent = np.sum(plastic_mask > 0) / total_pixels
        glass_percent = np.sum(glass_mask > 0) / total_pixels
        metal_percent = np.sum(metal_mask > 0) / total_pixels
        paper_percent = np.sum(paper_mask > 0) / total_pixels
        
        # Determine primary material
        percentages = {
            'Plastic': plastic_percent,
            'Glass': glass_percent,
            'Metal': metal_percent,
            'Paper': paper_percent
        }
        
        primary_material = max(percentages.items(), key=lambda x: x[1])[0]
        
        # Define packaging types and their properties with detailed eco scores
        packaging_types = {
            'Plastic': {
                'type': 'Plastic Container',
                'material': 'PET/HDPE',
                'recyclability': 'Highly Recyclable',
                'pollution_score': 7.5,
                'eco_scores': {
                    'biodegradability': 2.0,  # 1-10 scale
                    'recycling_ease': 8.5,
                    'energy_footprint': 6.0,
                    'water_impact': 7.0,
                    'reusability': 7.5
                },
                'environmental_impact': {
                    'decomposition_time': '450 years',
                    'ocean_impact': 'High - Can break down into microplastics',
                    'landfill_impact': 'High - Non-biodegradable',
                    'carbon_footprint': 'Medium - 6kg CO2 per kg produced'
                },
                'recycling_tips': [
                    'Rinse thoroughly before recycling',
                    'Remove labels if possible',
                    'Check local recycling guidelines',
                    'Crush to save space'
                ],
                'alternatives': ['Glass Container', 'Metal Container', 'Biodegradable Container']
            },
            'Glass': {
                'type': 'Glass Container',
                'material': 'Glass',
                'recyclability': 'Infinitely Recyclable',
                'pollution_score': 8.5,
                'eco_scores': {
                    'biodegradability': 1.0,
                    'recycling_ease': 9.5,
                    'energy_footprint': 5.0,
                    'water_impact': 8.5,
                    'reusability': 9.5
                },
                'environmental_impact': {
                    'decomposition_time': '1 million years',
                    'ocean_impact': 'Low - Does not break down into harmful chemicals',
                    'landfill_impact': 'Low - Inert material',
                    'carbon_footprint': 'High - 8kg CO2 per kg produced'
                },
                'recycling_tips': [
                    'Rinse thoroughly',
                    'Remove metal caps and cork',
                    'Sort by color if required',
                    'Do not break before recycling'
                ],
                'alternatives': ['Metal Container', 'Biodegradable Container']
            },
            'Metal': {
                'type': 'Metal Container',
                'material': 'Aluminum/Steel',
                'recyclability': 'Highly Recyclable',
                'pollution_score': 8.0,
                'eco_scores': {
                    'biodegradability': 1.0,
                    'recycling_ease': 9.0,
                    'energy_footprint': 7.0,
                    'water_impact': 8.0,
                    'reusability': 8.5
                },
                'environmental_impact': {
                    'decomposition_time': '200-500 years',
                    'ocean_impact': 'Low - Does not break down into harmful chemicals',
                    'landfill_impact': 'Medium - Slowly oxidizes',
                    'carbon_footprint': 'Medium - 5kg CO2 per kg produced'
                },
                'recycling_tips': [
                    'Rinse clean',
                    'Crush if possible',
                    'Remove paper labels',
                    'Check for local metal recycling programs'
                ],
                'alternatives': ['Glass Container', 'Biodegradable Container']
            },
            'Paper': {
                'type': 'Paper Package',
                'material': 'Cardboard/Paper',
                'recyclability': 'Easily Recyclable',
                'pollution_score': 9.0,
                'eco_scores': {
                    'biodegradability': 9.0,
                    'recycling_ease': 9.5,
                    'energy_footprint': 8.0,
                    'water_impact': 6.5,
                    'reusability': 7.0
                },
                'environmental_impact': {
                    'decomposition_time': '2-6 months',
                    'ocean_impact': 'Low - Biodegrades naturally',
                    'landfill_impact': 'Low - Biodegradable',
                    'carbon_footprint': 'Low - 3kg CO2 per kg produced'
                },
                'recycling_tips': [
                    'Keep dry and clean',
                    'Remove tape and staples',
                    'Flatten boxes',
                    'Avoid contamination with food'
                ],
                'alternatives': ['Biodegradable Container', 'Reusable Container']
            },
            'Bioplastic': {
                'type': 'Biodegradable Container',
                'material': 'PLA/PHA',
                'recyclability': 'Industrially Compostable',
                'pollution_score': 8.5,
                'eco_scores': {
                    'biodegradability': 8.5,
                    'recycling_ease': 7.0,
                    'energy_footprint': 7.5,
                    'water_impact': 8.0,
                    'reusability': 6.5
                },
                'environmental_impact': {
                    'decomposition_time': '3-6 months in industrial composting',
                    'ocean_impact': 'Medium - Requires specific conditions to biodegrade',
                    'landfill_impact': 'Low - Biodegradable in proper conditions',
                    'carbon_footprint': 'Low - 4kg CO2 per kg produced'
                },
                'recycling_tips': [
                    'Check local industrial composting facilities',
                    'Do not mix with regular plastic recycling',
                    'Look for composting certification symbols',
                    'Verify acceptable in your area'
                ],
                'alternatives': ['Paper Package', 'Reusable Container']
            }
        }
        
        # Get analysis for detected material with detailed eco scores
        analysis_result = {
            'packaging_type': packaging_types[primary_material]['type'],
            'material': packaging_types[primary_material]['material'],
            'recyclability': packaging_types[primary_material]['recyclability'],
            'pollution_score': packaging_types[primary_material]['pollution_score'],
            'eco_scores': packaging_types[primary_material]['eco_scores'],
            'environmental_impact': packaging_types[primary_material]['environmental_impact'],
            'recycling_tips': packaging_types[primary_material]['recycling_tips'],
            'alternatives': packaging_types[primary_material]['alternatives'],
            'material_percentages': {
                'Plastic': f"{plastic_percent * 100:.1f}%",
                'Glass': f"{glass_percent * 100:.1f}%",
                'Metal': f"{metal_percent * 100:.1f}%",
                'Paper': f"{paper_percent * 100:.1f}%"
            }
        }
        
        return jsonify(analysis_result)

@app.route('/submit-data', methods=['POST'])
def submit_data():
    data = request.get_json()
    # TODO: Add data validation and storage logic
    return jsonify({'message': 'Data received successfully'})

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

if __name__ == '__main__':
    app.run(debug=True)
