| Vòng | Dataset                         | Thay đổi                        | Block rate    | FPR          | Benign warned | Latency  |
| ---- | ------------------------------- | ------------------------------- | ------------- | ------------ | ------------- | -------- |
| 1    | 46 mẫu                          | Luật ban đầu                    | 18/19 = 94.7% | 0/27 = 0%    | 0             | 0.080 ms |
| 1b   | 50 mẫu                          | Cùng luật, thêm 4 ca khó        | 18/19 = 94.7% | 4/31 = 12.9% | 0             | 0.079 ms |
| 2    | 50 mẫu                          | Siết 4 luật (cần thêm ngữ cảnh) | 18/19 = 94.7% | 0/31 = 0%    | 1 (P050)      | 0.111 ms |
| 3    | 125 mẫu (75 mẫu mới, chưa thấy) | Luật không đổi                  | 25/52 = 48.1% | 1/73 = 1.4%  | 1             | 0.113 ms |
| 4    | 125 mẫu                         | Sửa luật developer mode (P081)  | 25/52 = 48.1% | 0/73 = 0%    | 1             | 0.097 ms |

Ghi chú:

- Vòng 2 chỉnh theo đúng các ca lỗi đã thấy nên lạc quan.
- Vòng 3 là phép đo công bằng nhất của lớp luật vì mẫu mới chưa dùng để chỉnh luật. Tuy vậy đợt 2 được soạn cố ý khó với luật từ khóa (leetspeak, base64, giả quyền...), nên 48.1% không đại diện cho lưu lượng thật.
- Vòng 4 đã chỉnh theo lỗi (P081) nên lạc quan.
