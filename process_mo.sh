#!/bin/bash
# Обработка снимков МО: срез водяного знака (низ 80px) + сжатие
cd "/c/Users/Victor/Desktop/hermes_work/питер-одиночество"
mkdir -p scenes_mo_final
ok=0
for f in scenes_mo/*.jpg; do
  n=$(basename "$f" .jpg)
  w=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$f")
  h=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$f")
  ch=$((h - 80))
  ffmpeg -y -loglevel error -i "$f" -vf "crop=$w:$ch:0:0,scale=640:-2" -q:v 4 "scenes_mo_final/$n.jpg" && ok=$((ok+1))
done
echo "обработано: $ok"
du -sh scenes_mo_final/
