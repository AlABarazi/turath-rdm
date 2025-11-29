import os
import subprocess
import sys
import glob
import img2pdf
from pathlib import Path

def rasterize_pdf(input_pdf, output_pdf, dpi=150):
    print(f"🔥 Rasterizing {input_pdf} to {output_pdf} at {dpi} DPI...")
    
    # Create temp dir
    temp_dir = Path("temp_raster")
    temp_dir.mkdir(exist_ok=True)
    
    # 1. Convert PDF to JPGs
    print("   Step 1: Extracting pages to JPG...")
    cmd = [
        "pdftoppm",
        "-jpeg",
        "-r", str(dpi),
        str(input_pdf),
        str(temp_dir / "page")
    ]
    subprocess.check_call(cmd)
    
    # 2. Convert JPGs to PDF
    print("   Step 2: merging JPGs to PDF...")
    images = sorted(list(temp_dir.glob("page-*.jpg")))
    
    if not images:
        print("❌ No images extracted!")
        return False
        
    with open(output_pdf, "wb") as f:
        f.write(img2pdf.convert([str(i) for i in images]))
        
    # Cleanup
    print("   Step 3: Cleaning up...")
    for i in images:
        os.remove(i)
    temp_dir.rmdir()
    
    print(f"✅ Rasterization complete: {output_pdf}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python rasterize_book.py <input_pdf> <output_pdf>")
        sys.exit(1)
        
    rasterize_pdf(sys.argv[1], sys.argv[2])
