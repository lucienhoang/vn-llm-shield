| Vòng | Thay đổi                          | Block rate    | FPR          | Benign warned | Latency  |
| ---- | --------------------------------- | ------------- | ------------ | ------------- | -------- |
| 1    | Luật ban đầu (46 mẫu)             | 18/19 = 94.7% | 0/27 = 0%    | 0             | 0.080 ms |
| 1b   | Cùng luật, thêm 4 ca khó (50 mẫu) | 18/19 = 94.7% | 4/31 = 12.9% | 0             | 0.079 ms |
| 2    | Siết 4 luật (cần thêm ngữ cảnh)   | 18/19 = 94.7% | 0/31 = 0%    | 1 (P050)      | 0.111 ms |

Ghi chú: vòng 2 được chỉnh đúng theo các ca lỗi đã thấy nên số liệu lạc quan; cần đo lại trên mẫu chưa thấy.
