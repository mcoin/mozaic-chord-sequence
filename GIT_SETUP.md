# Git Repository Setup

## Current Status

✅ Git repository initialized
✅ Initial commit created on `main` branch
✅ Core files committed
✅ `.gitignore` configured to exclude test files

## Connecting to GitHub

### Option 1: Create a new repository on GitHub

1. Go to https://github.com/new
2. Create a new repository (e.g., "mozaic-chord-sequence")
3. **Do NOT initialize with README, .gitignore, or license** (we already have these)
4. Copy the repository URL

Then connect your local repository:

```bash
# Add GitHub as remote
git remote add origin https://github.com/YOUR_USERNAME/mozaic-chord-sequence.git

# Push initial commit
git push -u origin main
```

### Option 2: Use GitHub CLI

```bash
# Install GitHub CLI if needed: brew install gh

# Create repo and push in one command
gh repo create mozaic-chord-sequence --public --source=. --remote=origin --push
```

## Daily Workflow

### Checking status
```bash
git status
```

### Adding changes
```bash
# Add specific files
git add chordSequenceGenerator.py

# Add all changes
git add .

# Check what's staged
git status
```

### Committing changes
```bash
git commit -m "Description of changes"
```

### Pushing to GitHub
```bash
git push
```

### Pulling latest changes
```bash
git pull
```

## Useful Commands

### View commit history
```bash
git log --oneline
```

### Create a new branch
```bash
git checkout -b feature-name
```

### Switch branches
```bash
git checkout main
git checkout feature-name
```

### View differences
```bash
# See what changed (unstaged)
git diff

# See what will be committed (staged)
git diff --cached
```

### Undo changes
```bash
# Undo changes to a file (before staging)
git checkout -- filename

# Unstage a file (keep changes)
git reset HEAD filename

# Undo last commit (keep changes)
git reset --soft HEAD~1
```

## .gitignore Patterns

The `.gitignore` file is configured to exclude:
- Test files (`test_*.mozaic`, `*_TEST.mozaic`)
- Generated files (`chordSequence10_*.mozaic`)
- Backup directories (`bckp/`)
- Python cache (`__pycache__/`, `*.pyc`)
- macOS files (`.DS_Store`)
- IDE files (`.vscode/`, `*.swp`)

## Repository Structure

```
chordSequence/
├── .gitignore              # Git ignore patterns
├── .songs.index            # Persistent song ordering
├── README.md               # Project overview
├── CLAUDE.md              # Architecture documentation
├── PURE_PYTHON_ENCODER.md # Pure Python implementation details
├── chordSequenceGenerator.py  # Main generator
├── mozaic_encoder.py       # General-purpose encoder
├── mozaic_pure_encoder.py  # Pure Python encoder
├── mozaic_reader.py        # .mozaic file reader
├── mozaic_edit.py          # Binary editing tool
└── songs/                  # Song chord files
    ├── all_of_me.txt
    ├── blues.txt
    └── ...
```

## Current Commit

```
commit 0f57d67
Author: [Your Name]
Date:   [Date]

    Initial commit: Mozaic Chord Sequence Generator

    Core features:
    - Pure Python NSKeyedArchiver encoder (iPad-compatible)
    - Multi-song chord sequence generator
    - Native Foundation encoder (macOS)
    - Mozaic file reader and editor tools
```

## Next Steps

1. Create a GitHub repository
2. Add the remote and push
3. Consider adding:
   - LICENSE file (MIT, Apache, etc.)
   - CONTRIBUTING.md (if accepting contributions)
   - GitHub Actions for automated testing
   - Example output files in a dedicated directory

## Tips

- Commit frequently with descriptive messages
- Create feature branches for major changes
- Keep commits focused (one logical change per commit)
- Write commit messages in present tense ("Add feature" not "Added feature")
- Pull before you push to avoid conflicts
