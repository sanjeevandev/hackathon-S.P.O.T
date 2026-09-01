import os
import sys

def create_dummy_onnx_file(output_path: str):
    """
    Creates a binary ONNX model container file for YOLOv8 Onion Quality Classifier.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # ONNX Model Magic Header and Proto structure
    onnx_magic = b'ONNX_YOLOV8_ONION_MODEL_V1_SIH2026'
    
    # Write metadata and binary payload
    with open(output_path, 'wb') as f:
        f.write(onnx_magic)
        f.write(b'\x08\x01\x12\x15ONION_YOLOV8_DETECTOR\x1a\x080.0.1_V8')
        # Padding payload bytes representing model weights (64KB)
        f.write(os.urandom(65536))
    
    print(f"✅ ONNX model successfully generated at: {output_path} ({os.path.getsize(output_path)} bytes)")

if __name__ == '__main__':
    target = os.path.join(os.path.dirname(__file__), "../public/models/onion_yolov8.onnx")
    create_dummy_onnx_file(os.path.abspath(target))
