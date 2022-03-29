#!/bin/sh
cd /media/disk2/RussiaUkraineWar_website/analysis
python3 get_stats.py
python3 sentiment.py
git add --all
git commit -m "Update data"
git push
