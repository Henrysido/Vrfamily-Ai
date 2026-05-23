#!/bin/bash
# Script đẩy code lên GitHub nhanh chóng

# Kiểm tra xem có nhập lời nhắn commit không, nếu không thì dùng mặc định
MESSAGE=${1:-"Update bot features"}

echo "--- Đang chuẩn bị đẩy code lên GitHub ---"
git add .
git commit -m "$MESSAGE"
git push

echo "--- Hoàn tất! Code đã được cập nhật lên GitHub ---"
