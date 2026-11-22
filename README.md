# stock-skill

Code của skill `stock-research-analyzer` (bản tin sáng và phân tích sâu chứng khoán). Đây là nguồn duy nhất: mỗi lần chạy, skill trên claude.ai `git clone` kho này về `research/skill`.

- `references/` – hướng dẫn từng chế độ (bản tin sáng, phân tích sâu, thu thập, chuỗi truyền dẫn, kiểm tra chéo, kỹ thuật).
- `scripts/` – script Python (giá từ VND MCP qua gia_vnd.py, chu kỳ, kiểm định, dự báo 6 phiên, biểu đồ, khối ngoại, chuỗi truyền dẫn vĩ mô, nén dữ liệu).
- Dữ liệu (giá, nhật ký, báo cáo) KHÔNG nằm ở đây: nằm trong Project "Economy and trading" và vault Obsidian.

## Khi một lần chạy bị lỗi

Mỗi lần chạy ghi `research/nhat-ky-chay.txt` (script `scripts/nhat_ky.py`): mỗi bước một dòng `giờ | trạng thái | bước | chi tiết | Gợi ý: cách sửa`. Trạng thái: OK · CẢNH BÁO · LỖI · BỎ QUA · DỪNG. Nhật ký nằm ở cuối phụ lục bản tin / cuối báo cáo sâu (ghi chú Obsidian), và trong thông báo khi lần chạy DỪNG. Muốn sửa: gửi dòng không OK cho Claude. Gặp lỗi mới thì thêm mẫu vào bảng `GOI_Y` trong `nhat_ky.py`.

Mỗi thay đổi là một commit có ghi lý do. Muốn quay lại bản trước: `git revert`.
