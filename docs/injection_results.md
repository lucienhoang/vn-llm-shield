# Kết quả bộ phát hiện injection / jailbreak

Máy: AMD Ryzen 7 5700U, 16GB RAM, chạy CPU. Dữ liệu: `data/prompts_eval.csv`.
Block rate = tỉ lệ tấn công bị chặn; FPR = tỉ lệ câu vô hại bị chặn nhầm.

| Vòng | Dataset                         | Thay đổi                               | Block rate    | FPR          | Benign warned | Latency                  |
| ---- | ------------------------------- | -------------------------------------- | ------------- | ------------ | ------------- | ------------------------ |
| 1    | 46 mẫu                          | Luật ban đầu                           | 18/19 = 94.7% | 0/27 = 0%    | 0             | 0.080 ms                 |
| 1b   | 50 mẫu                          | Cùng luật, thêm 4 ca khó               | 18/19 = 94.7% | 4/31 = 12.9% | 0             | 0.079 ms                 |
| 2    | 50 mẫu                          | Siết 4 luật (cần thêm ngữ cảnh)        | 18/19 = 94.7% | 0/31 = 0%    | 1 (P050)      | 0.111 ms                 |
| 3    | 125 mẫu (75 mẫu mới, chưa thấy) | Luật không đổi                         | 25/52 = 48.1% | 1/73 = 1.4%  | 1             | 0.113 ms                 |
| 4    | 125 mẫu                         | Sửa luật developer mode (P081)         | 25/52 = 48.1% | 0/73 = 0%    | 1             | 0.097 ms                 |
| 5    | 125 mẫu                         | Classifier đơn (5×5-fold CV, T=0.6)    | 67.3% ± 4.0   | 2.2% ± 0.7   | chưa đo       | ~4-5 ms (chỉ classifier) |
| 6    | 125 mẫu                         | Luật + classifier (5×5-fold CV, T=0.6) | 78.5% ± 2.2   | 2.2% ± 0.7   | 17.0% ± 3.0   | ~4-5 ms (chỉ classifier) |

Tỉ lệ bị chặn theo nhóm (luật + classifier, T=0.6):

| Nhóm             | Bị chặn | n   |
| ---------------- | ------- | --- |
| benign           | 0.0%    | 22  |
| benign_pii       | 0.0%    | 23  |
| benign_lookalike | 5.7%    | 28  |
| injection        | 73.9%   | 33  |
| jailbreak        | 86.3%   | 19  |

## Ghi chú

- Vòng 1-4 đo trực tiếp (lớp luật không học từ dữ liệu). Vòng 5-6 đo bằng cross-validation 5×5-fold: mỗi câu được chấm bởi mô hình chưa từng thấy câu đó.
- "±" là độ lệch chuẩn giữa 5 lần chia dữ liệu, không phải khoảng tin cậy. Với 52 mẫu tấn công, độ bất định thực tế lớn hơn.
- Ngưỡng T=0.6 là ngưỡng nhỏ nhất trong lưới (0.3 đến 0.8, bước 0.1) cho FPR của luật + classifier không quá 5%. Luật chọn được đặt trước khi xem số. Ngưỡng cảnh báo (warn) là 0.4.
- "Benign warned" ở vòng 6: câu vô hại có xác suất tấn công từ 0.4 đến dưới 0.6 và không bị luật chặn.
- Vòng 2 chỉnh theo đúng các ca lỗi đã thấy nên lạc quan.
- Vòng 3 là phép đo công bằng nhất của lớp luật vì mẫu mới chưa dùng để chỉnh luật. Đợt 2 được soạn cố ý khó với luật từ khóa (leetspeak, base64, giả quyền...), nên 48.1% không đại diện cho lưu lượng thật.
- Vòng 4 đã chỉnh theo lỗi (P081) nên lạc quan.
- Độ trễ vòng 5-6 chỉ đo phần classifier (dao động 4.0 đến 4.8 ms giữa các lần chạy). Độ trễ của toàn bộ `detect()` sẽ đo lặp nhiều lần ở bước thực nghiệm chính thức (#20).

## Phụ lục A: quét ngưỡng (5×5-fold CV)

method block rate FPR
rules only 48.1% +-0.0% 0.0% +-0.0%
classifier only, T=0.3 97.7% +-1.4% 33.2% +-1.0%
rules + classifier, T=0.3 98.5% +-0.8% 33.2% +-1.0%
classifier only, T=0.4 90.8% +-2.2% 19.2% +-2.6%
rules + classifier, T=0.4 93.5% +-2.9% 19.2% +-2.6%
classifier only, T=0.5 80.0% +-2.0% 9.0% +-1.4%
rules + classifier, T=0.5 85.0% +-2.2% 9.0% +-1.4%
classifier only, T=0.6 67.3% +-4.0% 2.2% +-0.7%
rules + classifier, T=0.6 78.5% +-2.2% 2.2% +-0.7%
classifier only, T=0.7 55.8% +-1.7% 1.4% +-0.0%
rules + classifier, T=0.7 73.1% +-1.2% 1.4% +-0.0%
classifier only, T=0.8 40.0% +-3.1% 0.5% +-0.7%
rules + classifier, T=0.8 63.8% +-2.2% 0.5% +-0.7%

## Phụ lục B: ca thất bại ở T=0.6

- Tấn công bị sót thường xuyên: P044, P096, P100, P101, P103, P104, P105, P106, P108, P120, P122.
- Câu vô hại bị chặn nhầm thường xuyên: P079 ("bỏ qua thông báo lỗi cũ"): mô hình học cụm "bỏ qua" từ các mẫu tấn công.
