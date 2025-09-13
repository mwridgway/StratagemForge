#!/usr/bin/env python3
"""
HLTV Demo Downloader for StratagemForge
========================================

Downloads CS:GO/CS2 demo files from HLTV.org for analysis.

Usage:
    python scripts/hltv_demo_downloader.py --team "Falcons" --limit 5
    python scripts/hltv_demo_downloader.py --match-url "https://www.hltv.org/matches/2345/..."
    python scripts/hltv_demo_downloader.py --event "BLAST Premier" --limit 10

Requirements:
    pip install requests beautifulsoup4 lxml
"""

import requests
import re
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HLTVDemoDownloader:
    """Download demos from HLTV.org with rate limiting and error handling."""
    
    def __init__(self, output_dir: str = "demos", delay: float = 2.0):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.delay = delay  # Rate limiting
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def search_matches(self, team: Optional[str] = None, event: Optional[str] = None, 
                      days: int = 30, limit: int = 10) -> List[Dict]:
        """Search for recent matches on HLTV."""
        matches = []
        
        try:
            # HLTV results page with filters
            url = "https://www.hltv.org/results"
            params = {}
            
            if team:
                # You'd need to get team ID from HLTV - this is simplified
                logger.info(f"Searching for matches with team: {team}")
                
            if event:
                logger.info(f"Searching for matches in event: {event}")
            
            # For demo purposes, we'll scrape the results page
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find match links (this selector may need adjustment based on HLTV's current structure)
            match_links = soup.find_all('a', class_='a-reset', href=re.compile(r'/matches/\d+/'))
            
            for link in match_links[:limit]:
                match_url = urljoin("https://www.hltv.org", link['href'])
                match_info = self._extract_match_info(link)
                
                if match_info:
                    match_info['url'] = match_url
                    matches.append(match_info)
                    
            logger.info(f"Found {len(matches)} matches")
            
        except Exception as e:
            logger.error(f"Error searching matches: {e}")
            
        return matches
    
    def _extract_match_info(self, link_element) -> Optional[Dict]:
        """Extract match information from HLTV link element."""
        try:
            # Extract team names and match details
            # This is a simplified version - you'd need to adapt to HLTV's actual structure
            text = link_element.get_text(strip=True)
            
            # Try to parse team names and score
            # Format usually like "Team1 2 - 1 Team2"
            match = re.search(r'(.+?)\s+(\d+)\s*-\s*(\d+)\s+(.+)', text)
            
            if match:
                team1, score1, score2, team2 = match.groups()
                return {
                    'team1': team1.strip(),
                    'team2': team2.strip(), 
                    'score1': int(score1),
                    'score2': int(score2),
                    'text': text
                }
        except Exception as e:
            logger.debug(f"Could not parse match info: {e}")
            
        return None
    
    def get_demo_links(self, match_url: str) -> List[Dict]:
        """Get demo download links from a specific match page."""
        demo_links = []
        
        try:
            logger.info(f"Getting demo links from: {match_url}")
            
            response = self.session.get(match_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for GOTV demo links
            # HLTV usually has links like "/download/demo/xxxxx"
            demo_elements = soup.find_all('a', href=re.compile(r'/download/demo/\d+'))
            
            for element in demo_elements:
                demo_url = urljoin("https://www.hltv.org", element['href'])
                
                # Try to extract map name from context
                map_name = self._extract_map_name(element)
                
                demo_info = {
                    'url': demo_url,
                    'map': map_name,
                    'match_url': match_url
                }
                
                demo_links.append(demo_info)
                
            logger.info(f"Found {len(demo_links)} demo links")
            
        except Exception as e:
            logger.error(f"Error getting demo links: {e}")
            
        return demo_links
    
    def _extract_map_name(self, element) -> str:
        """Try to extract map name from demo link context."""
        try:
            # Look for map name in surrounding text or data attributes
            parent = element.parent
            if parent:
                text = parent.get_text(strip=True)
                
                # Common CS map names
                maps = ['inferno', 'dust2', 'mirage', 'cache', 'overpass', 'train', 'nuke', 'vertigo', 'ancient']
                
                for map_name in maps:
                    if map_name.lower() in text.lower():
                        return map_name
                        
            return "unknown"
            
        except Exception:
            return "unknown"
    
    def download_demo(self, demo_info: Dict) -> Optional[Path]:
        """Download a single demo file."""
        try:
            demo_url = demo_info['url']
            map_name = demo_info.get('map', 'unknown')
            
            logger.info(f"Downloading demo for map: {map_name}")
            
            # Rate limiting
            time.sleep(self.delay)
            
            response = self.session.get(demo_url, stream=True)
            response.raise_for_status()
            
            # Extract filename from response headers or URL
            filename = self._get_filename_from_response(response, demo_info)
            file_path = self.output_dir / filename
            
            # Download with progress
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) == 0:  # Log every MB
                                logger.info(f"  Progress: {progress:.1f}% ({downloaded}/{total_size})")
            
            logger.info(f"✅ Downloaded: {file_path.name} ({downloaded:,} bytes)")
            return file_path
            
        except Exception as e:
            logger.error(f"❌ Failed to download demo: {e}")
            return None
    
    def _get_filename_from_response(self, response, demo_info: Dict) -> str:
        """Generate appropriate filename for downloaded demo."""
        try:
            # Try to get filename from Content-Disposition header
            content_disp = response.headers.get('Content-Disposition', '')
            filename_match = re.search(r'filename="?([^"]+)"?', content_disp)
            
            if filename_match:
                return filename_match.group(1)
                
            # Generate filename from demo info
            map_name = demo_info.get('map', 'unknown')
            timestamp = int(time.time())
            
            return f"hltv-demo-{map_name}-{timestamp}.dem"
            
        except Exception:
            return f"hltv-demo-{int(time.time())}.dem"
    
    def download_match_demos(self, match_url: str) -> List[Path]:
        """Download all demos for a specific match."""
        demo_links = self.get_demo_links(match_url)
        downloaded_files = []
        
        for demo_info in demo_links:
            file_path = self.download_demo(demo_info)
            if file_path:
                downloaded_files.append(file_path)
                
        return downloaded_files
    
    def download_team_recent_demos(self, team_name: str, limit: int = 5) -> List[Path]:
        """Download recent demos for a specific team."""
        matches = self.search_matches(team=team_name, limit=limit)
        all_downloaded = []
        
        for match in matches:
            logger.info(f"Processing match: {match.get('text', 'Unknown')}")
            demos = self.download_match_demos(match['url'])
            all_downloaded.extend(demos)
            
        return all_downloaded

def main():
    """CLI interface for HLTV demo downloader."""
    parser = argparse.ArgumentParser(description="Download CS:GO/CS2 demos from HLTV.org")
    
    parser.add_argument("--team", help="Team name to search for")
    parser.add_argument("--event", help="Event name to search for")
    parser.add_argument("--match-url", help="Direct match URL to download")
    parser.add_argument("--limit", type=int, default=5, help="Number of matches to process")
    parser.add_argument("--output", default="demos", help="Output directory for demos")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between requests (seconds)")
    
    args = parser.parse_args()
    
    if not any([args.team, args.event, args.match_url]):
        print("❌ Please specify --team, --event, or --match-url")
        return
    
    downloader = HLTVDemoDownloader(output_dir=args.output, delay=args.delay)
    
    try:
        if args.match_url:
            logger.info(f"Downloading demos from specific match: {args.match_url}")
            demos = downloader.download_match_demos(args.match_url)
            
        elif args.team:
            logger.info(f"Downloading recent demos for team: {args.team}")
            demos = downloader.download_team_recent_demos(args.team, limit=args.limit)
            
        elif args.event:
            logger.info(f"Downloading demos from event: {args.event}")
            matches = downloader.search_matches(event=args.event, limit=args.limit)
            demos = []
            for match in matches:
                demos.extend(downloader.download_match_demos(match['url']))
        
        logger.info(f"🎯 Downloaded {len(demos)} demo files successfully!")
        
        if demos:
            logger.info("📁 Downloaded files:")
            for demo_path in demos:
                logger.info(f"  • {demo_path.name}")
            
            logger.info(f"\n💡 Next step: Run your analysis pipeline:")
            logger.info(f"   python run_complete_pipeline_new.py --mode fast")
            
    except KeyboardInterrupt:
        logger.info("❌ Download cancelled by user")
    except Exception as e:
        logger.error(f"❌ Download failed: {e}")

if __name__ == "__main__":
    main()
