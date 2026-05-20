"""Catalog and processor for ASCII art samples"""
import os
import json
from pathlib import Path

SAMPLES_DIR = Path(__file__).parent / "data" / "art_samples"

def build_catalog():
    """Build a catalog of all art samples with metadata"""
    catalog = {
        "total": 0,
        "by_format": {},
        "by_theme": {},
        "files": []
    }
    
    if not SAMPLES_DIR.exists():
        return catalog
    
    # Analyze each file
    for file in sorted(SAMPLES_DIR.iterdir()):
        if file.is_file():
            suffix = file.suffix.lower()
            stat = file.stat()
            
            catalog["total"] += 1
            catalog["by_format"][suffix] = catalog["by_format"].get(suffix, 0) + 1
            
            file_info = {
                "name": file.name,
                "format": suffix,
                "size_kb": stat.st_size // 1024,
                "path": str(file.relative_to(SAMPLES_DIR.parent))
            }
            catalog["files"].append(file_info)
    
    return catalog

def print_catalog_summary():
    """Print a human-readable catalog"""
    catalog = build_catalog()
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║          ASCII ART SAMPLES CATALOG                        ║")
    print(f"║  Total: {catalog['total']} files, {sum(f['size_kb'] for f in catalog['files'])} KB")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    print("Format Distribution:")
    for fmt, count in sorted(catalog["by_format"].items(), key=lambda x: x[1], reverse=True):
        print(f"  {fmt:6s}: {count:3d} files")
    
    print()
    print("Files by size:")
    for f in sorted(catalog["files"], key=lambda x: x["size_kb"], reverse=True)[:10]:
        print(f"  {f['name']:50s} {f['size_kb']:6d} KB")

def get_sample(index=0):
    """Get a random or indexed sample"""
    catalog = build_catalog()
    if not catalog["files"]:
        return None
    return catalog["files"][index % len(catalog["files"])]

if __name__ == "__main__":
    print_catalog_summary()
