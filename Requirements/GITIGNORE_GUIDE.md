# .gitignore Guide for StratagemForge

This document explains the .gitignore patterns used in StratagemForge and what files are excluded from version control.

## Categories of Ignored Files

### 🏗️ Build Artifacts
- **Go binaries**: `*.exe`, `main`, `*-service`
- **Node.js builds**: `dist/`, `.next/`, `out/`, `build/`
- **TypeScript**: `*.tsbuildinfo`, `next-env.d.ts`

### 📦 Dependencies
- **Node.js**: `node_modules/`, `package-lock.json`
- **Go**: `vendor/` (if used), module cache in `go/pkg/mod/`
- **Python**: `__pycache__/`, `*.pyc`, virtual environments

### 🔧 Development Tools
- **Build tools**: `.task/`, `earthly.exe`, `task.exe`
- **IDE files**: `.vscode/settings.json`, `.idea/`, editor temp files
- **OS files**: `.DS_Store`, `Thumbs.db`

### 📊 Data and Logs
- **Project data**: `data/*` (except `.gitkeep`)
- **Demo files**: `demos/*` (except `.gitkeep`)
- **Logs**: `*.log`, `logs/`

### 🔐 Sensitive Files
- **Environment**: `.env*` files
- **Secrets**: Configuration files with credentials

### 🧪 Testing
- **Test outputs**: `test-results/`, `playwright-report/`, `coverage/`
- **Cache files**: `.pytest_cache/`, `.eslintcache`

## What IS Tracked

✅ **Source code**: `.go`, `.ts`, `.tsx`, `.py`, `.js`  
✅ **Configuration**: `package.json`, `go.mod`, `Dockerfile`, `compose.yml`  
✅ **Documentation**: `README.md`, `.md` files  
✅ **Build scripts**: `Taskfile.yml`, `Earthfile`  
✅ **IDE settings**: Shared `.vscode/tasks.json`, `.editorconfig`  
✅ **Directory structure**: `.gitkeep` files  

## Special Files

### .earthlyignore
Controls what gets sent to Earthly build context - similar to .dockerignore but for Earthly builds.

### .gitkeep Files
- `data/.gitkeep` - Preserves data directory structure
- `demos/.gitkeep` - Preserves demos directory structure

## Verification Commands

```bash
# Check ignored files aren't tracked
git ls-files | grep -E "\.(exe|tsbuildinfo)$|dist/|\.next/|node_modules/"

# See what's currently ignored
git status --ignored

# Check specific patterns
git check-ignore services/bff/dist/
git check-ignore web-app/.next/
git check-ignore services/user-service/main.exe
```

## Adding New Ignore Patterns

When adding new build tools or services:

1. **Global patterns** → Add to root `.gitignore`
2. **Build context** → Add to `.earthlyignore` 
3. **Service-specific** → Add to root `.gitignore` with path prefix

**Example**: New Rust service
```gitignore
# Add to .gitignore
**/target/
**/*.pdb
**/Cargo.lock
```
