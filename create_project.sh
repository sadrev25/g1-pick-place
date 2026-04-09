#!/bin/bash
cd ~/waveye_demo/demo

# Create folder structure
mkdir -p policy/saved
mkdir -p vision
mkdir -p logs
mkdir -p assets

# Create __init__.py files
touch policy/__init__.py
touch vision/__init__.py

# Move existing files to right places
cp ik_controller.py assets/ik_controller_backup.py
cp body.py assets/body_backup.py

# Create VS Code workspace file
cat > waveye_demo.code-workspace << 'EOF'
{
  "folders": [
    {"path": "."}
  ],
  "settings": {
    "python.defaultInterpreterPath": "~/waveye_demo/bin/python3",
    "editor.fontSize": 14,
    "files.exclude": {
      "**/__pycache__": true,
      "**/*.pyc": true
    }
  }
}
EOF

echo "✅ Project structure created!"
echo "Open VS Code with: code waveye_demo.code-workspace"
