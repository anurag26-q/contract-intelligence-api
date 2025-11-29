#!/usr/bin/env python
"""
Script to download sample contracts from public sources.
"""

import os
import requests
from pathlib import Path

# Sample contract URLs (publicly available)
SAMPLE_CONTRACTS = [
    {
        "name": "sample_nda.pdf",
        "url": "https://www.sec.gov/Archives/edgar/data/... (example URL)",
        "description": "Non-Disclosure Agreement"
    },
    # Add more public contract URLs here
]

def download_file(url: str, output_path: str):
    """Download file from URL."""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✓ Downloaded: {output_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to download {url}: {e}")
        return False


def main():
    """Download all sample contracts."""
    output_dir = Path(__file__).parent.parent / "sample_contracts"
    output_dir.mkdir(exist_ok=True)
    
    print("Downloading sample contracts...")
    print("=" * 60)
    
    for contract in SAMPLE_CONTRACTS:
        output_path = output_dir / contract["name"]
        
        if output_path.exists():
            print(f"⊘ Skipping (exists): {contract['name']}")
            continue
        
        print(f"Downloading: {contract['description']}")
        download_file(contract["url"], str(output_path))
    
    print("=" * 60)
    print("Done! Sample contracts are in sample_contracts/")
    print("\nNote: This script currently contains placeholder URLs.")
    print("For the assignment, manually add 3-5 public PDFs to sample_contracts/")


if __name__ == "__main__":
    main()
