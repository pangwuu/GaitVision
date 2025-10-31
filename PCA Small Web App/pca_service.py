

import os
import tempfile
from werkzeug.utils import secure_filename
from datetime import datetime
from pca_pipeline_module import PCAAnalysisPipeline

class PCAService:
    """Service layer for PCA analysis operations"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.results_dir = os.path.join(self.temp_dir, 'results')
        os.makedirs(self.results_dir, exist_ok=True)
    
    def process_file(self, file, rotation_method=''):
        """
        Process uploaded CSV file and run PCA analysis
        
        Args:
            file: FileStorage object from Flask request
            rotation_method: str - '', 'varimax', or 'promax'
            
        Returns:
            str: Path to generated PDF report
        """
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        upload_path = os.path.join(self.temp_dir, f"{timestamp}_{filename}")
        file.save(upload_path)
        
        try:
            # Run PCA analysis
            pipeline = PCAAnalysisPipeline(
                csv_file=upload_path,
                rotation_option=rotation_method,
                results_dir=self.results_dir
            )
            
            results = pipeline.run_full_pipeline()
            
            # Return path to generated PDF
            return pipeline.pdf_path
            
        finally:
            # Clean up uploaded CSV file
            if os.path.exists(upload_path):
                os.remove(upload_path)
    
    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
