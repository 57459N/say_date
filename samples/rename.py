import os
from pathlib import Path

if __name__ == "__main__":
    root = Path('.')
    for d in os.listdir(root):
        if not Path(root / d).is_dir():
            continue
        
        for f in os.listdir(root / d):
            if not Path(root / d / f).is_file():
                continue
            if not f.endswith('.wav'):
                continue
            s = f.split("-")
            nf = s[1] if len(s) > 1 else s[0]
            os.rename(root / d / f, root / d / nf)
