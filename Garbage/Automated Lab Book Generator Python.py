# modules/image_processor.py
import os
import cv2
import numpy as np
from PIL import Image
import shutil
from datetime import datetime

from config import IMAGE_DIR

class ImageProcessor:
    def __init__(self):
        """Initialize image processor for handling graphs and visual data"""
        # Create images directory if it doesn't exist
        os.makedirs(IMAGE_DIR, exist_ok=True)
    
    def import_image(self, source_path):
        """Import an image into the project's image directory"""
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Image file not found: {source_path}")
        
        # Generate a unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(source_path)
        base_name, ext = os.path.splitext(filename)
        new_filename = f"{base_name}_{timestamp}{ext}"
        destination = os.path.join(IMAGE_DIR, new_filename)
        
        # Copy the file
        shutil.copy2(source_path, destination)
        print(f"Image imported to {destination}")
        
        return destination
    
    def preprocess_image(self, image_path):
        """Preprocess an image for better analysis"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Load the image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image at {image_path}")
        
        # Basic preprocessing
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive thresholding for better feature extraction
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Save preprocessed image
        base_path = os.path.splitext(image_path)[0]
        processed_path = f"{base_path}_processed.png"
        cv2.imwrite(processed_path, thresh)
        
        print(f"Preprocessed image saved to {processed_path}")
        return processed_path
    
    def extract_graph_data(self, image_path):
        """
        Extract data points from a graph image
        Note: This is a simplified placeholder - real implementation would 
        require more sophisticated CV techniques
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        # Detect graph type (bar, line, scatter, etc.)
        # This would require sophisticated image recognition
        
        print("Graph data extraction would require custom implementation based on graph type")
        return {
            "status": "placeholder",
            "message": "Graph data extraction requires custom implementation based on graph type",
            "image_path": image_path
        }
    
    def is_graph(self, image_path):
        """
        Attempt to determine if an image is a graph/chart or a regular photo
        This is a simplified implementation
        """
        if not os.path.exists(image_path):
            return False
            
        try:
            # Load the image
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Look for characteristic features of graphs:
            # 1. Large number of straight lines (axes, grid lines)
            # 2. High contrast areas
            
            # Edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                                    minLineLength=100, maxLineGap=10)
            
            # Count significant lines
            line_count = 0 if lines is None else len(lines)
            
            # A high number of straight lines often indicates a graph
            if line_count > 15:
                return True
                
            # Check for areas of high contrast - often present in graphs
            std_dev = np.std(gray)
            if std_dev > 50:  # Arbitrary threshold, would need tuning
                return True
                
            return False
        except Exception as e:
            print(f"Error analyzing image: {e}")
            return False


# Simple command-line test
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Test image processing")
    parser.add_argument("--image", help="Path to image file")
    parser.add_argument("--action", choices=["import", "preprocess", "analyze"],
                        default="analyze", help="Action to perform")
    args = parser.parse_args()
    
    if not args.image or not os.path.exists(args.image):
        print("Please provide a valid image path")
        sys.exit(1)
    
    processor = ImageProcessor()
    
    if args.action == "import":
        imported = processor.import_image(args.image)
        print(f"Imported image: {imported}")
    elif args.action == "preprocess":
        processed = processor.preprocess_image(args.image)
        print(f"Preprocessed image: {processed}")
    else:  # analyze
        is_graph = processor.is_graph(args.image)
        print(f"Is this a graph? {is_graph}")
        if is_graph:
            data = processor.extract_graph_data(args.image)
            print(f"Extracted data: {data}")
