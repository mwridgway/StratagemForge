import subprocess
import sys
from pathlib import Path

def build_rust_extension():
    """Build the Rust extension module"""
    rust_dir = Path(__file__).parent / "rust_processor"
    
    if not rust_dir.exists():
        print("❌ Rust processor directory not found")
        return False
        
    print("🦀 Building Rust extension...")
    
    try:
        # Build the Rust extension
        result = subprocess.run(
            ["cargo", "build", "--release"],
            cwd=rust_dir,
            capture_output=True,
            text=True,
            check=True
        )
        
        print("✅ Rust extension built successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build Rust extension: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ Cargo not found. Install Rust from https://rustup.rs/")
        return False

def install_rust_extension():
    """Install the built Rust extension using maturin"""
    rust_dir = Path(__file__).parent / "rust_processor"
    
    try:
        # Install maturin if not present
        subprocess.run([sys.executable, "-m", "pip", "install", "maturin"], check=True)
        
        # Build and install the extension
        subprocess.run([
            sys.executable, "-m", "maturin", "develop", "--release"
        ], cwd=rust_dir, check=True)
        
        print("✅ Rust extension installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Rust extension: {e}")
        return False

if __name__ == "__main__":
    if install_rust_extension():
        print("🚀 Ready to use high-performance Rust processor!")
    else:
        print("⚠️  Falling back to Python implementation")
