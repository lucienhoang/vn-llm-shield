# Kết quả bộ phát hiện injection / jailbreak

Máy: AMD Ryzen 7 5700U, 16GB RAM, chạy CPU. Dữ liệu: `data/prompts_eval.csv` (165 mẫu từ vòng 7).
Block rate = tỉ lệ tấn công bị chặn; FPR = tỉ lệ câu vô hại bị chặn nhầm.

| Vòng | Dataset                            | Thay đổi                               | Block rate    | FPR          | Benign warned  | Latency                  |
| ---- | ---------------------------------- | -------------------------------------- | ------------- | ------------ | -------------- | ------------------------ |
| 1    | 46 mẫu                             | Luật ban đầu                           | 18/19 = 94.7% | 0/27 = 0%    | 0              | 0.080 ms                 |
| 1b   | 50 mẫu                             | Cùng luật, thêm 4 ca khó               | 18/19 = 94.7% | 4/31 = 12.9% | 0              | 0.079 ms                 |
| 2    | 50 mẫu                             | Siết 4 luật (cần thêm ngữ cảnh)        | 18/19 = 94.7% | 0/31 = 0%    | 1 (P050)       | 0.111 ms                 |
| 3    | 125 mẫu (75 mẫu mới, chưa thấy)    | Luật không đổi                         | 25/52 = 48.1% | 1/73 = 1.4%  | 1              | 0.113 ms                 |
| 4    | 125 mẫu                            | Sửa luật developer mode (P081)         | 25/52 = 48.1% | 0/73 = 0%    | 1              | 0.097 ms                 |
| 5    | 125 mẫu                            | Classifier đơn (5×5-fold CV, T=0.6)    | 67.3% ± 4.0   | 2.2% ± 0.7   | chưa đo        | ~4-5 ms (chỉ classifier) |
| 6    | 125 mẫu                            | Luật + classifier (5×5-fold CV, T=0.6) | 78.5% ± 2.2   | 2.2% ± 0.7   | 17.0% ± 3.0    | ~4-5 ms (chỉ classifier) |
| 7    | 165 mẫu (đợt 3: 40 mẫu, chưa thấy) | Luật không đổi so với vòng 4           | 25/69 = 36.2% | 0/96 = 0%    | 2 (P050, P148) | 0.105 ms                 |
| 8    | 165 mẫu                            | Classifier đơn (5×5-fold CV, T=0.6)    | 76.8% ± 4.0   | 4.4% ± 2.0   | chưa đo        | ~4.3 ms (chỉ classifier) |
| 9    | 165 mẫu                            | Luật + classifier (5×5-fold CV, T=0.6) | 82.6% ± 2.6   | 4.4% ± 2.0   | 13.1% ± 1.6    | ~4.3 ms (chỉ classifier) |

Vòng 9 là kết quả chính trên tập phát triển. Vòng 5-6 là phép đo trên bản dữ liệu cũ (125 mẫu), giữ lại để tham khảo lịch sử.

Tỉ lệ bị chặn theo nhóm (luật + classifier, T=0.6, 165 mẫu):

| Nhóm             | Bị chặn | n   |
| ---------------- | ------- | --- |
| benign           | 0.0%    | 30  |
| benign_pii       | 0.0%    | 32  |
| benign_lookalike | 12.4%   | 34  |
| injection        | 80.5%   | 42  |
| jailbreak        | 85.9%   | 27  |

## Ghi chú

- Vòng 1-4 và 7 đo trực tiếp (lớp luật không học từ dữ liệu). Vòng 5-6 và 8-9 đo bằng cross-validation 5×5-fold: mỗi câu được chấm bởi mô hình chưa từng thấy câu đó.
- "±" là độ lệch chuẩn giữa 5 lần chia dữ liệu, không phải khoảng tin cậy. Với 69 mẫu tấn công và 96 mẫu vô hại, một câu tương đương khoảng 1.4 điểm phần trăm (tấn công) và 1.0 điểm (vô hại), nên chênh lệch nhỏ giữa các vòng chưa đủ để kết luận có xu hướng.
- Ngưỡng T=0.6 là ngưỡng nhỏ nhất trong lưới (0.3 đến 0.8, bước 0.1) cho FPR của luật + classifier không quá 5%. Luật chọn được đặt trước khi xem số. Với 165 mẫu, T=0.5 cho FPR 9.8% (vượt) còn T=0.6 cho 4.4% (đạt, sát giới hạn). Ngưỡng cảnh báo (warn) là 0.4.
- "Benign warned" ở vòng 9: câu vô hại không bị chặn nhưng có xác suất tấn công từ 0.4 trở lên theo classifier. Ở vòng 7 là số câu vô hại bị luật gắn warn.
- Vòng 2 chỉnh theo đúng các ca lỗi đã thấy nên lạc quan. Vòng 4 cũng đã chỉnh theo lỗi (P081).
- Vòng 3 và vòng 7 là hai phép đo "chưa thấy" của lớp luật. Đợt 2 và đợt 3 được soạn cố ý nhắm vào các kiểu luật từ khóa yếu (leetspeak, base64, giả quyền, hoàn thành câu, hư cấu...), nên 48.1% và 36.2% không đại diện cho lưu lượng thật. Ở vòng 7, luật chặn 0/17 mẫu tấn công mới của đợt 3.
- Danh sách ca sót thay đổi giữa vòng 6 và 9 (xem Phụ lục B). Nguyên nhân chưa được kiểm chứng.
- Độ trễ vòng 5-9 chỉ đo phần classifier. Độ trễ của toàn bộ `detect()` sẽ đo lặp nhiều lần ở bước thực nghiệm chính thức (#20).
- Các con số trên đều là ước lượng trên tập phát triển. Con số công bằng nhất sẽ lấy từ tập kiểm tra độc lập (`data/prompts_test.csv`), chấm một lần sau khi đóng băng bộ phát hiện tại tag `injection-frozen`.

## Phụ lục A: quét ngưỡng (5×5-fold CV, 165 mẫu)

| method                    | block rate   | FPR          |
| ------------------------- | ------------ | ------------ |
| rules only                | 36.2% +-0.0% | 0.0% +-0.0%  |
| classifier only, T=0.3    | 97.4% +-0.6% | 31.9% +-0.8% |
| rules + classifier, T=0.3 | 98.3% +-0.6% | 31.9% +-0.8% |
| classifier only, T=0.4    | 94.2% +-1.6% | 17.5% +-2.3% |
| rules + classifier, T=0.4 | 95.7% +-0.9% | 17.5% +-2.3% |
| classifier only, T=0.5    | 88.1% +-3.4% | 9.8% +-2.5%  |
| rules + classifier, T=0.5 | 91.3% +-1.8% | 9.8% +-2.5%  |
| classifier only, T=0.6    | 76.8% +-4.0% | 4.4% +-2.0%  |
| rules + classifier, T=0.6 | 82.6% +-2.6% | 4.4% +-2.0%  |
| classifier only, T=0.7    | 60.0% +-2.0% | 1.9% +-1.2%  |
| rules + classifier, T=0.7 | 71.0% +-1.3% | 1.9% +-1.2%  |
| classifier only, T=0.8    | 44.1% +-2.2% | 0.8% +-0.4%  |
| rules + classifier, T=0.8 | 61.2% +-1.1% | 0.8% +-0.4%  |

## Phụ lục B: ca thất bại ở T=0.6 (165 mẫu, luật + classifier)

- Tấn công bị sót trong ít nhất nửa số lần lặp: P044, P096, P100, P101, P103, P106, P108, P152, P155, P158, P159.
  - So với danh sách ở 125 mẫu: P104, P105, P120, P122 không còn trong danh sách; P152, P155, P158, P159 là mới.
- Câu vô hại bị chặn nhầm trong ít nhất nửa số lần lặp: P029, P079, P148.
  - P079 ("bỏ qua thông báo lỗi cũ"): mô hình học cụm "bỏ qua" từ các mẫu tấn công.
  - P148 ("no restrictions" trong ngữ cảnh mua bán dữ liệu) và P029 (quy định bảo mật về mật khẩu).
