#!/usr/bin/env python3
"""
Simple HLTV Demo Downloader
============================

A lightweight demo downloader that works with HLTV.org structure.

Usage:
    python scripts/simple_hltv_downloader.py --match-id 2367890
    python scripts/simple_hltv_downloader.py --demo-url "https://www.hltv.org/download/demo/12345"

Requirements:
    pip install requests
"""

import requests
import re
import time
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleHLTVDownloader:
    """Simple, reliable HLTV demo downloader."""
    
    def __init__(self, output_dir: str = "demos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_demo_by_url(self, demo_url: str, custom_name: Optional[str] = None) -> Optional[Path]:
        """Download demo from direct HLTV demo URL."""
        try:
            logger.info(f"Downloading demo from: {demo_url}")
            
            response = self.session.get(demo_url, stream=True)
            response.raise_for_status()
            
            # Generate filename
            if custom_name:
                filename = f"{custom_name}.dem" if not custom_name.endswith('.dem') else custom_name
            else:
                # Extract from URL or use timestamp
                demo_id = re.search(r'/demo/(\d+)', demo_url)
                if demo_id:
                    filename = f"hltv-demo-{demo_id.group(1)}.dem"
                else:
                    filename = f"hltv-demo-{int(time.time())}.dem"
            
            file_path = self.output_dir / filename
            
            # Download with progress
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            
            logger.info(f"Downloading to: {file_path.name}")
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Show progress every 5MB
                        if downloaded % (5 * 1024 * 1024) == 0 and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            logger.info(f"  Progress: {progress:.1f}%")
            
            logger.info(f"✅ Downloaded: {file_path.name} ({downloaded:,} bytes)")
            return file_path
            
        except Exception as e:
            logger.error(f"❌ Failed to download demo: {e}")
            return None
    
    def download_match_demos(self, match_id: str) -> list:
        """Download demos from HLTV match ID."""
        try:
            match_url = f"https://www.hltv.org/matches/{match_id}/"
            logger.info(f"Getting demos from match: {match_url}")
            
            response = self.session.get(match_url)
            response.raise_for_status()
            
            # Look for demo download links in the page
            demo_pattern = r'href="(/download/demo/\d+)"'
            demo_matches = re.findall(demo_pattern, response.text)
            
            downloaded_demos = []
            
            for demo_path in demo_matches:
                demo_url = f"https://www.hltv.org{demo_path}"
                
                # Extract map info if possible
                map_name = self._extract_map_from_context(response.text, demo_path)
                custom_name = f"match-{match_id}-{map_name}" if map_name != "unknown" else None
                
                demo_file = self.download_demo_by_url(demo_url, custom_name)
                if demo_file:
                    downloaded_demos.append(demo_file)
                    
                # Rate limiting
                time.sleep(1)
            
            return downloaded_demos
            
        except Exception as e:
            logger.error(f"❌ Failed to get match demos: {e}")
            return []
    
    def _extract_map_from_context(self, page_content: str, demo_path: str) -> str:
        """Try to extract map name from page context."""
        try:
            # Look for map names around the demo link
            maps = ['inferno', 'dust2', 'mirage', 'cache', 'overpass', 'train', 'nuke', 'vertigo', 'ancient']
            
            # Find the section of text around the demo link
            demo_index = page_content.find(demo_path)
            if demo_index != -1:
                # Get surrounding text (500 chars before and after)
                start = max(0, demo_index - 500)
                end = min(len(page_content), demo_index + 500)
                context = page_content[start:end].lower()
                
                for map_name in maps:
                    if map_name in context:
                        return map_name
            
            return "unknown"
            
        except Exception:
            return "unknown"

def main():
    """CLI interface for simple HLTV downloader."""
    parser = argparse.ArgumentParser(description="Download CS:GO/CS2 demos from HLTV.org")
    
    parser.add_argument("--match-id", help="HLTV match ID (e.g., 2367890)")
    parser.add_argument("--demo-url", help="Direct HLTV demo URL")
    parser.add_argument("--output", default="demos", help="Output directory")
    parser.add_argument("--name", help="Custom filename for demo")
    
    args = parser.parse_args()
    
    if not any([args.match_id, args.demo_url]):
        print("❌ Please specify --match-id or --demo-url")
        print("\nExamples:")
        print("  python scripts/simple_hltv_downloader.py --match-id 2367890")
        print("  python scripts/simple_hltv_downloader.py --demo-url 'https://www.hltv.org/download/demo/12345'")
        return
    
    downloader = SimpleHLTVDownloader(output_dir=args.output)
    
    try:
        demos = []
        
        if args.demo_url:
            demo = downloader.download_demo_by_url(args.demo_url, args.name)
            demos = [demo] if demo else []
            
        elif args.match_id:
            demos = downloader.download_match_demos(args.match_id)
        
        if demos:
            logger.info(f"🎯 Successfully downloaded {len(demos)} demos!")
            logger.info("📁 Downloaded files:")
            for demo_path in demos:
                logger.info(f"  • {demo_path.name}")
            
            logger.info(f"\n💡 Next step: Run your analysis pipeline:")
            logger.info(f"   python run_complete_pipeline_new.py --mode fast")
        else:
            logger.warning("❌ No demos were downloaded")
            
    except KeyboardInterrupt:
        logger.info("❌ Download cancelled by user")

if __name__ == "__main__":
    main()
