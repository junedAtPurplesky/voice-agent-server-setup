#!/usr/bin/env python3
"""
Standalone script to download and verify CosyVoice models
Can be run independently or used by the service
"""

import os
import sys
import shutil
from typing import List, Tuple


def verify_model_files(model_path: str) -> Tuple[bool, List[str]]:
    """
    Verify that all required model files are present.
    Returns: (is_complete, missing_files)
    """
    # Required files for CosyVoice-300M-SFT model
    required_files = [
        'speech_tokenizer_v1.onnx',  # CRITICAL: Most commonly missing
        'campplus.onnx',
        'flow.decoder.estimator.fp32.onnx',
        'cosyvoice.yaml',
        'flow.pt',
        'hift.pt'
    ]
    
    missing_files = []
    for file in required_files:
        file_path = os.path.join(model_path, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    return len(missing_files) == 0, missing_files


def download_model(model_id: str, local_dir: str, force: bool = False) -> bool:
    """
    Download model from ModelScope with verification.
    
    Args:
        model_id: ModelScope model ID (e.g., 'iic/CosyVoice-300M-SFT')
        local_dir: Local directory to save model
        force: Force re-download even if directory exists
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from modelscope import snapshot_download
    except ImportError:
        print("❌ ERROR: modelscope package not installed")
        print("Install with: pip install modelscope")
        return False
    
    # Make path absolute
    local_dir = os.path.abspath(local_dir)
    
    print("=" * 70)
    print("CosyVoice Model Downloader")
    print("=" * 70)
    print(f"Model ID: {model_id}")
    print(f"Destination: {local_dir}")
    print()
    
    # Check if model exists
    if os.path.exists(local_dir):
        if not force:
            print("Checking existing model...")
            is_complete, missing = verify_model_files(local_dir)
            
            if is_complete:
                print("✅ Model already complete!")
                print()
                print("Model files:")
                for file in os.listdir(local_dir):
                    file_path = os.path.join(local_dir, file)
                    if os.path.isfile(file_path):
                        size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        print(f"  ✓ {file} ({size_mb:.1f} MB)")
                return True
            else:
                print(f"⚠️  Model INCOMPLETE! Missing: {missing}")
                print("Will re-download...")
        else:
            print("⚠️  Force mode: Will re-download...")
        
        print()
        print("Removing existing directory...")
        shutil.rmtree(local_dir)
        print("✓ Old directory removed")
    
    # Create parent directory
    os.makedirs(os.path.dirname(local_dir), exist_ok=True)
    
    # Download
    print()
    print("Downloading model from ModelScope...")
    print("This may take several minutes (~1GB download)...")
    print()
    
    try:
        downloaded_path = snapshot_download(
            model_id,
            local_dir=local_dir,
            local_files_only=False
        )
        
        print()
        print(f"✓ Download completed: {downloaded_path}")
        
    except Exception as e:
        print()
        print(f"❌ Download failed: {e}")
        return False
    
    # Verify
    print()
    print("Verifying downloaded files...")
    is_complete, missing = verify_model_files(local_dir)
    
    if is_complete:
        print("✅ Verification passed! All required files present")
        print()
        print("Model files:")
        
        total_size = 0
        for file in sorted(os.listdir(local_dir)):
            file_path = os.path.join(local_dir, file)
            if os.path.isfile(file_path):
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                total_size += size_mb
                print(f"  ✓ {file} ({size_mb:.1f} MB)")
        
        print()
        print(f"Total size: {total_size:.1f} MB")
        print()
        print("=" * 70)
        print("✅ MODEL READY TO USE!")
        print("=" * 70)
        return True
    else:
        print(f"❌ Verification FAILED! Missing: {missing}")
        print()
        print("The download may have been interrupted. Please try again.")
        return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download and verify CosyVoice models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download default model (CosyVoice-300M-SFT)
  python download_model.py
  
  # Force re-download
  python download_model.py --force
  
  # Download specific model
  python download_model.py --model-id iic/CosyVoice2-0.5B --output pretrained_models/CosyVoice2-0.5B
  
  # Only verify existing model
  python download_model.py --verify-only
        """
    )
    
    parser.add_argument(
        '--model-id',
        default='iic/CosyVoice-300M-SFT',
        help='ModelScope model ID (default: iic/CosyVoice-300M-SFT)'
    )
    
    parser.add_argument(
        '--output',
        default='pretrained_models/CosyVoice-300M-SFT',
        help='Output directory (default: pretrained_models/CosyVoice-300M-SFT)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-download even if model exists'
    )
    
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify existing model, do not download'
    )
    
    args = parser.parse_args()
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, args.output)
    
    if args.verify_only:
        print("=" * 70)
        print("Model Verification")
        print("=" * 70)
        print(f"Checking: {output_path}")
        print()
        
        if not os.path.exists(output_path):
            print(f"❌ Model directory does not exist: {output_path}")
            sys.exit(1)
        
        is_complete, missing = verify_model_files(output_path)
        
        if is_complete:
            print("✅ Model verification PASSED!")
            print()
            print("All required files present:")
            for file in sorted(os.listdir(output_path)):
                file_path = os.path.join(output_path, file)
                if os.path.isfile(file_path):
                    size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    print(f"  ✓ {file} ({size_mb:.1f} MB)")
            sys.exit(0)
        else:
            print(f"❌ Model verification FAILED!")
            print(f"Missing files: {missing}")
            print()
            print("Run without --verify-only to download missing files:")
            print(f"  python {os.path.basename(__file__)} --force")
            sys.exit(1)
    
    # Download
    success = download_model(args.model_id, output_path, force=args.force)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

