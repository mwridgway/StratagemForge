# 🎮 HLTV Demo Download Guide for StratagemForge

## 📖 Overview

There are several effective ways to download CS:GO/CS2 demo files from HLTV.org for analysis with your StratagemForge pipeline.

---

## 🚀 **Method 1: Simple Python Downloader (Recommended)**

### **Setup**
```powershell
# Install required dependency
pip install requests
```

### **Usage**

**Download by Match ID:**
```powershell
# Find match ID from HLTV URL (e.g., https://www.hltv.org/matches/2367890/...)
python scripts/simple_hltv_downloader.py --match-id 2367890

# Custom output directory
python scripts/simple_hltv_downloader.py --match-id 2367890 --output "new_demos"
```

**Download by Direct Demo URL:**
```powershell
# Direct demo download
python scripts/simple_hltv_downloader.py --demo-url "https://www.hltv.org/download/demo/12345"

# With custom filename
python scripts/simple_hltv_downloader.py --demo-url "https://www.hltv.org/download/demo/12345" --name "blast-final-inferno"
```

### **Integration with Pipeline**
```powershell
# Download demos and run analysis in one workflow
python scripts/simple_hltv_downloader.py --match-id 2367890
python run_complete_pipeline_new.py --mode fast
```

---

## 🔧 **Method 2: Manual Download**

### **Step-by-Step Process**

1. **Visit HLTV.org**
   - Go to https://www.hltv.org/matches
   - Find the match you want to analyze

2. **Navigate to Match Page**
   - Click on the specific match
   - Look for "GOTV Demo" or "Download Demo" links

3. **Download Demo Files**
   - Right-click demo links and "Save As..."
   - Save to your `demos/` folder in StratagemForge

4. **Rename Files (Optional)**
   ```powershell
   # Example naming convention
   # team1-vs-team2-map-event.dem
   Rename-Item "downloaded_demo.dem" "falcons-vs-vitality-inferno-blast.dem"
   ```

---

## 🌐 **Method 3: Browser Automation (Advanced)**

For bulk downloading, you could use browser automation:

```python
# Example with selenium (requires: pip install selenium)
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def download_recent_demos(team_name: str, count: int = 5):
    """Download recent demos for a team using browser automation."""
    driver = webdriver.Chrome()  # Requires chromedriver
    
    try:
        # Navigate to HLTV results
        driver.get(f"https://www.hltv.org/results?team={team_name}")
        
        # Find match links
        match_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/matches/']")
        
        for i, link in enumerate(match_links[:count]):
            match_url = link.get_attribute('href')
            
            # Open match page in new tab
            driver.execute_script(f"window.open('{match_url}', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
            
            # Find and click demo download links
            demo_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/download/demo/']")
            
            for demo_link in demo_links:
                demo_link.click()
                time.sleep(2)  # Wait for download
            
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            
    finally:
        driver.quit()
```

---

## 📊 **Method 4: HLTV API (If Available)**

HLTV doesn't have an official public API, but there are community projects:

```bash
# Example using unofficial HLTV API wrapper
pip install hltv-api

# Python usage
from hltv_api import HLTV

hltv = HLTV()
matches = hltv.get_recent_matches(team="Falcons", limit=5)

for match in matches:
    demos = hltv.get_match_demos(match.id)
    for demo in demos:
        # Download demo file
        demo.download("demos/")
```

---

## 🎯 **Finding the Right Demos**

### **Getting Match IDs from HLTV URLs**

HLTV match URLs follow this pattern:
```
https://www.hltv.org/matches/[MATCH_ID]/[team1-vs-team2-event]
```

Examples:
- `https://www.hltv.org/matches/2367890/falcons-vs-vitality-blast-premier-fall-final`
- Match ID: `2367890`

### **Best Practices for Demo Selection**

1. **Recent Matches** - Get the latest tactics and meta
2. **Specific Opponents** - Target teams you'll face
3. **Tournament Context** - Playoffs vs group stage differences
4. **Map Pool** - Focus on maps your team plays

### **Pro Team Demo Sources**

**Tier 1 Teams to Analyze:**
- Falcons, Vitality, NAVI, Astralis, G2, FaZe
- Recent tournament matches (BLAST, ESL, PGL)

**Useful Match Types:**
- **Finals/Playoffs** - Teams play their best strategies
- **Bo3/Bo5 Series** - See adaptation between maps
- **Recent Patches** - Current meta strategies

---

## ⚡ **Integration with StratagemForge Pipeline**

### **Complete Workflow**

```powershell
# 1. Download recent team demos
python scripts/simple_hltv_downloader.py --match-id 2367890
python scripts/simple_hltv_downloader.py --match-id 2367891
python scripts/simple_hltv_downloader.py --match-id 2367892

# 2. Run analysis pipeline
python run_complete_pipeline_new.py --mode fast

# 3. Review strategic insights
# Check console output for tactical analysis
```

### **Automated Demo Collection Script**

```powershell
# Create a batch download script
$matchIds = @("2367890", "2367891", "2367892", "2367893", "2367894")

foreach ($id in $matchIds) {
    Write-Host "Downloading match $id..."
    python scripts/simple_hltv_downloader.py --match-id $id
    Start-Sleep -Seconds 2
}

Write-Host "Running analysis pipeline..."
python run_complete_pipeline_new.py --mode fast
```

---

## 🚨 **Important Notes**

### **Rate Limiting**
- HLTV has rate limiting - don't spam requests
- Add delays between downloads (1-2 seconds)
- Respect their servers and terms of service

### **File Management**
```powershell
# Organize demos by date/team/event
New-Item -ItemType Directory -Path "demos/2024-09-13-blast-final"
Move-Item "*.dem" "demos/2024-09-13-blast-final/"

# Clean up old demos periodically
Get-ChildItem "demos/" -Name "*.dem" | Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-30) } | Remove-Item
```

### **Storage Considerations**
- Demo files are typically 50-200MB each
- Consider compression for archival
- Your optimized pipeline reduces storage needs significantly

---

## 🎯 **Recommended Workflow for Teams**

### **Weekly Demo Collection**
1. **Monday**: Download weekend tournament demos
2. **Wednesday**: Get demos from upcoming opponents
3. **Friday**: Collect demos from similar tactical teams

### **Pre-Match Preparation**
1. Download 3-5 recent demos from upcoming opponent
2. Run fast analysis to identify patterns
3. Use insights for tactical preparation

### **Post-Match Analysis**
1. Download your own team's demo (if available)
2. Compare with pre-match analysis
3. Identify successful counter-strategies

---

## 💡 **Pro Tips**

1. **Follow Tournament Streams** - Note interesting tactical rounds for later analysis
2. **Track Meta Changes** - Download demos after major updates
3. **Cross-Reference Results** - Compare demo analysis with actual match outcomes
4. **Build Demo Library** - Collect demos from various scenarios (comebacks, upsets, etc.)

---

*Your StratagemForge pipeline is optimized to handle large volumes of demo data efficiently!*
