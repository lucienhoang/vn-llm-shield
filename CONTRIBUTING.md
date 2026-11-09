# Hướng dẫn đóng góp (CONTRIBUTING)

File này mô tả cách làm việc chung để code không đè lên nhau và `main` luôn chạy được.

## 1. Nguyên tắc

- Nhánh `main` **có bảo vệ**: không push thẳng, mọi thay đổi đi qua Pull Request (PR) và cần 1 người duyệt.
- Mỗi việc = một Issue = một nhánh = một PR. Nhánh nhỏ, PR nhỏ thì dễ xem và ít xung đột.
- Nhận việc nào thì gán tên mình vào Issue đó. Vướng thì hỏi ngay trong Issue.
- Commit nhỏ và đều mỗi tuần.
- Được dùng AI hỗ trợ, nhưng **phải giải thích được code mình nộp**.

## 2. Phân chia sở hữu file

| Người       | Sở hữu                                                                                                |
| ----------- | ----------------------------------------------------------------------------------------------------- |
| lucienhoang | `pipeline.py`, `injection.py`, `main.py`, `llm_client.py`, `ui/`, `redteam/`, `data/prompts_eval.csv` |
| B           | `pii.py`, `rag_acl.py`, `crypto_log.py`, `data/docs/`, `data/pii_labeled.csv`                         |

- Chỉ chủ file mới sửa file đó. Cần sửa file của người kia thì **mở Issue hoặc nhắn trước**.
- `pipeline.py` chỉ A sửa; B muốn đổi cách ghép thì ghi vào Issue.
- Gán nhãn chéo: người này viết mẫu dữ liệu, người kia rà lại nhãn.

## 3. Quy trình cho mỗi việc

1. **Tạo nhánh từ `main` mới nhất** (làm TRƯỚC khi sửa file):
   ```powershell
   git checkout main
   git pull
   pip install -r requirements.txt
   git checkout -b feature/<số-issue>-<tên-ngắn>
   ```
2. **Code** trong phạm vi Issue.
3. **Kiểm tra** (xem mục 6).
4. **Commit và push**:
   ```powershell
   git status
   git add <từng file>
   git commit -m "feat: mô tả ngắn"
   git push -u origin feature/<số-issue>-<tên-ngắn>
   ```
5. **Mở PR** vào `main`, điền đủ mẫu mô tả, ghi `Closes #<số issue>`.
6. **Người còn lại xem PR**: đọc code, chạy `pytest` trên nhánh đó, rồi Approve và merge.
7. **Dọn nhánh** sau khi PR đã merge:
   ```powershell
   git checkout main
   git pull
   pip install -r requirements.txt
   git branch -d feature/<số-issue>-<tên-ngắn>
   git remote prune origin
   ```

## 4. Đặt tên

**Nhánh:** `<loại>/<số-issue>-<tên-ngắn-gạch-ngang>`

| Loại        | Dùng cho                        | Ví dụ                           |
| ----------- | ------------------------------- | ------------------------------- |
| `feature/`  | Tính năng mới                   | `feature/6-pii-regex`           |
| `fix/`      | Sửa lỗi                         | `fix/7-phone-dot-format`        |
| `refactor/` | Đổi cấu trúc, không đổi hành vi | `refactor/17-pipeline-switches` |
| `docs/`     | Tài liệu                        | `docs/1-contributing`           |
| `chore/`    | Dọn dẹp, cấu hình               | `chore/deps-update`             |
| `data/`     | Bộ dữ liệu                      | `data/15-eval-prompts-batch1`   |

**Commit:** `<loại>: mô tả ngắn` (feat, fix, refactor, docs, chore, test, data), ví dụ `feat: add phone number regex`.

## 5. Quy ước code

- **Python 3.11**, dùng venv (`py -3.11 -m venv .venv`), luôn bật venv trước khi làm.
- **Hợp đồng giao diện** nằm ở `app/types.py` và `docs/interface_contract.md`; hai người cùng dựa vào đó.
- **Không tự ý đổi** tên, tham số, kiểu trả về. Cần đổi thì mở Issue, hai người đồng ý rồi mới sửa, kèm cập nhật stub.
- Mỗi module có file test trong `tests/` (ví dụ `tests/test_pii.py`). PR mới phải kèm test cho phần mình làm.
- Có type hint cho hàm công khai; tên hàm/biến tiếng Anh, comment có thể tiếng Việt.
- **Thêm thư viện mới:**
  1. Thêm tên vào `requirements.in`.
  2. `pip install -r requirements.in`
  3. `pip freeze > requirements.txt`
  4. Commit cả hai file. Ghi rõ lý do thêm trong PR.
- **Công tắc bảo vệ:** mỗi lớp bảo vệ phải bật/tắt được độc lập (phục vụ thực nghiệm trước/sau).
- **Đo độ trễ:** đo riêng lớp bảo vệ, tách khỏi thời gian LLM sinh chữ.

### Bảo mật khi làm việc

- **Không bao giờ commit:** `.env`, khóa mã hóa, API key, file model, log thật. Cần biến môi trường mới thì thêm vào `.env.example` (để trống giá trị).
- **Dữ liệu giả hoàn toàn:** tên, SĐT, CCCD, số tài khoản trong dataset phải tự bịa. Không dùng thông tin của người thật (kể cả của bạn bè, người thân).
- Trước khi `git add`, luôn chạy `git status` để chắc không có `.env` hoặc file lạ.
- Lỡ commit nhầm khóa: **coi như khóa đã lộ**, tạo khóa mới ngay, rồi báo người kia (xem mục 8).

## 6. Kiểm tra trước khi mở PR

```powershell
pytest
```

Phải xanh hết. Ngoài ra:

- Chạy thử module mình làm bằng tay với vài ví dụ (ghi vào mục "Cách kiểm tra" của PR).
- Với PR liên quan dữ liệu: kiểm tra file CSV mở được, đúng cột theo định dạng đã chốt
  (`prompts_eval.csv`: `id, text, lang, category, label, has_pii, source, note`;
  `pii_labeled.csv`: `id, text, entities`).
- Với PR gọi LLM: đảm bảo Ollama đang chạy (`ollama list`) và ghi rõ model đã dùng.

## 7. Mô tả PR

Gồm 5 mục: **Mục đích / Đã làm / Quyết định thiết kế / Cách kiểm tra / Giới hạn hoặc việc sau**.
Mục "Giới hạn" của các PR là tư liệu cho phần hạn chế trong báo cáo, và các ca thất bại ghi ở đây dùng được cho chương 3.

## 8. Lỗi hay gặp

| Sự cố                                              | Cách xử lý                                                                                                          |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `ModuleNotFoundError` sau khi pull                 | Quên `pip install -r requirements.txt` (hoặc chưa bật venv)                                                         |
| Terminal không có `(.venv)` ở đầu dòng             | `.venv\Scripts\Activate.ps1`                                                                                        |
| PowerShell báo "running scripts is disabled"       | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`                                                               |
| Hai người cùng sửa `requirements.txt` gây xung đột | Sau khi merge, chạy lại `pip install -r requirements.in` rồi `pip freeze > requirements.txt`                        |
| Lỡ commit nhầm trên `main`                         | Tạo nhánh tại chỗ (`git checkout -b feature/...`), push nhánh đó, rồi trả `main` về `origin/main`                   |
| Lỡ commit `.env` hoặc khóa                         | Tạo khóa mới ngay, báo người kia. Xóa khỏi lịch sử Git bằng `git filter-repo` (hoặc tạo lại repo nếu mới ít commit) |
| Push lên `main` bị từ chối                         | Đúng hành vi mong muốn: tạo nhánh và mở PR                                                                          |
| Ollama báo không kết nối được                      | Kiểm tra Ollama đang chạy, `OLLAMA_HOST` trong `.env`, model đã `ollama pull` chưa                                  |
| Cảnh báo `LF will be replaced by CRLF`             | Bình thường trên Windows, bỏ qua                                                                                    |
| Xóa nhánh GitHub trước khi merge                   | `git push -u origin <nhánh>` rồi Reopen PR                                                                          |
