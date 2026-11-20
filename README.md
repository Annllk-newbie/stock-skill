# stock-skill

Code của skill `stock-research-analyzer` (bản tin sáng và phân tích sâu chứng khoán). Đây là nguồn duy nhất: mỗi lần chạy, skill trên claude.ai `git clone` kho này về `research/skill`.

- `references/` – hướng dẫn từng chế độ (bản tin sáng, phân tích sâu, thu thập, chuỗi truyền dẫn, kiểm tra chéo, kỹ thuật).
- `scripts/` – script Python (giá KBS + Vietcap, chu kỳ, kiểm định, dự báo 6 phiên, biểu đồ, khối ngoại, chuỗi truyền dẫn vĩ mô, nén dữ liệu, mô phỏng hành vi nhà đầu tư nhiều agent `mo_phong_hanh_vi.py` – cần numpy).
- Dữ liệu (giá, nhật ký, báo cáo) KHÔNG nằm ở đây: nằm trong Project "Economy and trading" và vault Obsidian.

Mỗi thay đổi là một commit có ghi lý do. Muốn quay lại bản trước: `git revert`.
