
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import os
import logging
import traceback
from werkzeug.utils import secure_filename
from config import Config
from pca_service import PCAService
# Import custom exceptions from the module where they are defined
from pca_pipeline_module import DataProcessingError, PCACalculationError

app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
logging.basicConfig(level=logging.INFO)

pca_service = PCAService()

@app.route('/')
def index():
    """Render the main upload page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handle file upload and PCA analysis"""
    if 'file' not in request.files:
        return {'success': False, 'error': 'No file uploaded'}, 400
    
    file = request.files['file']
    rotation = request.form.get('rotation', '')
    
    if file.filename == '':
        return {'success': False, 'error': 'No file selected'}, 400
    
    if not file.filename.endswith('.csv'):
        return {'success': False, 'error': 'Please upload a CSV file'}, 400
    
    try:
        pdf_path = pca_service.process_file(file, rotation)
        filename = os.path.basename(pdf_path)
        download_id = os.urandom(16).hex()

        app.config['TEMP_FILES'] = app.config.get('TEMP_FILES', {})
        app.config['TEMP_FILES'][download_id] = pdf_path

        return {
            'success': True, 
            'download_id': download_id,
            'filename': filename
        }
    
    except DataProcessingError as e:
        app.logger.warning(f"Data processing error for {file.filename}: {e}")
        return {'success': False, 'error': str(e)}, 422  # 422 Unprocessable Entity

    except PCACalculationError as e:
        app.logger.error(f"PCA calculation error for {file.filename}: {e}")
        return {'success': False, 'error': str(e)}, 500
    
    except Exception as e:
        tb = traceback.format_exc()
        app.logger.error(f"An unexpected error occurred for {file.filename}: {e}\n{tb}")
        return {'success': False, 'error': 'An unexpected internal error occurred. The administrator has been notified.'}, 500

@app.route('/download/<download_id>')
def download(download_id):
    """Download the generated PDF file"""
    temp_files = app.config.get('TEMP_FILES', {})
    pdf_path = temp_files.get(download_id)

    if not pdf_path:
        flash('Download link expired or invalid. Please try generating the report again.', 'error')
        return redirect(url_for('index'))
    
    if not os.path.exists(pdf_path):
        flash('The report file was not found. It may have been cleaned up. Please generate it again.', 'error')
        return redirect(url_for('index'))
    
    if download_id in app.config.get('TEMP_FILES', {}):
        del app.config['TEMP_FILES'][download_id]
    
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=os.path.basename(pdf_path),
        mimetype='application/pdf'
    )

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
