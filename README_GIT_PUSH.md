# Git Push Guide — Week 2 (Shrinivas)

**Milestone**: Week 2 &bull; Phase 2 — Authentication, Multi-Tenancy & Engine REST Client  
**Author**: Shrinivas (Dev-B / Dev-2) &bull; Roll: `01fe24bca311`  
**Repository**: `e-commerce-website`  
**Target Branch**: `week2-status-banner`  

---

## 1. Overview of Delivered Files

Extract the contents of this zip file directly into your local **`e-commerce-website`** repository root directory.

The following files are packaged in this update:
- `app/storefront/__init__.py`
- `knowledgebase.md`
- `function_map.md`

---

## 2. Step-by-Step GitHub Push Instructions

### Step 1: Open repository and ensure `main` is clean
```bash
cd /path/to/e-commerce-website
git checkout main
git pull origin main
```

### Step 2: Create and checkout the feature branch `week2-status-banner`
```bash
git checkout -b week2-status-banner
```

### Step 3: Copy packaged files into repository
Extract this zip file into your `e-commerce-website` folder, preserving the relative folder paths (`app/`, `docs/`, `tests/`, etc.).

### Step 4: Stage, commit, and push to GitHub
```bash
git add "app/storefront/__init__.py" "knowledgebase.md" "function_map.md"
git commit -m "[Dev-B] P2: Add live engine status banner and connection indicators"
git push -u origin week2-status-banner
```

### Step 5: Merge into `main` and synchronize remote
```bash
git checkout main
git merge week2-status-banner
git push origin main
```

---

*Package verified and generated automatically for BCA Mini-Project.*
