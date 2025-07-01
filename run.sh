#!/bin/bash

# Simulasikan CTRL+C dengan membunuh proses Python sebelumnya (jika ada)
echo "🔄 Menghentikan proses Python sebelumnya..."
pkill -f "python3 main.py"

# Menarik update terbaru dari GitHub
echo "📥 Menjalankan git pull..."
git pull

# Menjalankan bot
echo "🚀 Menjalankan bot..."
python3 main.py
