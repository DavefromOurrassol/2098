#!/bin/bash
cd "$(git rev-parse --show-toplevel)"
echo "Message de commit :"
read MSG
git add .
git commit -m "$MSG"
git push
