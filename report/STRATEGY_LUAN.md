# Chiến lược của Luân — Heading + Recursive fallback

## Cấu hình được chọn

- Chunker: `HeadingChunker(chunk_size=1400)` trong `src/heading.py`.
- Tách theo heading cấp 1–6; mỗi đoạn giữ đường dẫn tiêu đề cha–con.
- Chỉ chunk phần thân, sao chép frontmatter vào metadata từng chunk.
- Mục dài được chia bằng Recursive; kích thước 1.400 ký tự tính cả tiêu đề.
- Không overlap, không ghép nội dung từ các section khác nhau.
- ID chunk là `doc_id#index`; metadata `doc_id` giữ ID tài liệu gốc.
- Top-k = 3; câu 2 lọc `audience=seller` trước khi xếp hạng.

## Kết quả đo ngày 20/09/2026

Chạy cùng 7 tài liệu và 5 câu trong `benchmark.md`. Backend TF-IDF từ đơn và cặp từ, cosine chuẩn hóa; vocabulary và IDF học từ corpus gốc một lần, không học từ query/gold answer. Đây là baseline từ vựng chạy offline, không phải semantic embedding.

| Chiến lược | Số chunk | Top-3 có đủ bằng chứng | Top-1 có đủ bằng chứng |
|---|---:|---:|---:|
| FixedSize 1000, overlap 100 | 31 | 5/5 | 4/5 |
| Sentence 3 câu | 68 | 1/5 | 1/5 |
| Recursive 1000 | 33 | 5/5 | 5/5 |
| Heading 600 | 74 | 5/5 | 1/5 |
| Heading 1000 | 50 | 5/5 | 5/5 |
| **Heading 1400** | **48** | **5/5** | **5/5** |

Chọn Heading 1400 cho vai trò R3 vì giữ cấu trúc điều khoản, đạt kết quả bằng Heading 1000 với ít chunk hơn và đáp ứng yêu cầu tự code heading. Không có bằng chứng Heading chính xác hơn Recursive trên bộ này; Recursive còn dùng ít chunk hơn.

## Phân biệt tác động backend và chunking

Cùng Heading 1400, mock chỉ lấy đúng tài liệu trong top-3 ở 2/5 câu và đủ bằng chứng ở 0/5; TF-IDF đạt 5/5 cho cả hai. Sự cải thiện này chủ yếu là đổi backend từ mock ngẫu nhiên sang truy xuất từ vựng, không được quy toàn bộ cho heading. So sánh các chunker trong bảng trên giữ nguyên TF-IDF.

## Filter A/B và lỗi thật

- Câu 2 với Heading 1400: không filter lấy thêm `shopee-general-return-policy#2` và `shopee-buyer-return-request-guide#3`; filter thay bằng các chunk seller. Top-1 vẫn đúng ở cả hai lượt, vì vậy mới chứng minh giảm nhiễu đối tượng, chưa chứng minh tăng accuracy câu này.
- Heading 600 đạt đủ bằng chứng top-3 ở 5/5 nhưng chỉ 1/5 ở top-1: giới hạn nhỏ làm đáp án phân tán. Tăng ngưỡng 1000/1400 giải quyết trên bộ hiện tại.
- Sentence lấy đúng tài liệu ở 5/5 nhưng đủ bằng chứng top-3 chỉ 1/5. Đúng tên file không đồng nghĩa lấy đủ đáp án.

## Giới hạn đo

“Đủ bằng chứng” nghĩa là các chuỗi kiểm chứng khai báo trong `bench.py` xuất hiện trong các chunk của tài liệu gold đã được truy xuất. Gold chỉ dùng sau bước xếp hạng. Đây là phép kiểm proxy có thể bỏ sót cách diễn đạt tương đương hoặc đánh giá thiếu quan hệ ngữ nghĩa; chưa chấm câu trả lời của LLM và không tương đương điểm rubric /10.

Năm câu hiện tại cũng được dùng để chọn kích thước, nên kết quả không phải accuracy trên tập kiểm tra độc lập. Cần bổ sung câu hỏi chưa dùng để tuning nếu muốn kiểm tra khả năng tổng quát. Nội dung chính sách và gold answer cũng nên được xác minh lại với website nguồn khi cập nhật corpus.

## Tái chạy

Trong môi trường Python đã hoạt động:

```powershell
python bench.py
python bench.py --backend mock --output report/strategy/mock
python -m unittest discover -s tests -v
```

Có thể chạy `python bench.py --backend local --output report/strategy/local` sau khi cài requirements-local và chuẩn bị model. Backend local lỗi sẽ dừng, không âm thầm chuyển sang mock. So sánh TF-IDF/local phải chạy lại tất cả chiến lược.

Môi trường kiểm tra thực tế lần này: Python 3.10.11 trong `.venv`; bộ kiểm thử chuẩn thư viện chạy 45/45. `pytest` được khai báo trong `requirements.txt` nhưng máy demo hiện không tải được package do lỗi chứng chỉ PyPI, vì vậy kết quả đối chứng dùng `unittest discover` tương đương trên cùng test modules.

## Bàn giao

- `report/strategy/benchmark_results.json`: top-3, score, nội dung, metadata và evidence coverage của mọi cấu hình.
- `report/strategy/ket_qua_benchmark.txt`: log đọc được, gồm A/B filter.
- `report/strategy/mock/`: kết quả đối chứng mock.
- `report/strategy/baseline.json`: comparator trên 3 tài liệu đầu theo tên file, bỏ frontmatter, chunk_size=1000. Baseline comparator dùng FixedSize overlap=0 theo implementation có sẵn; không đồng nhất với FixedSize overlap=100 trong bảng benchmark.
- `tests/test_heading.py`: kiểm tra giữ nội dung, tiêu đề cha, ranh giới sibling, frontmatter và quy trình.

Tham chiếu Q2 đã được chuẩn hóa về Mục 1 của `shopee-seller-return-processing-policy.md`. Dashboard `http://127.0.0.1:8766/src/demo.html` và launcher `run_demo.cmd` là minh chứng demo hoàn chỉnh; phần giới hạn còn lại là benchmark chỉ có 5 query phát triển, chưa phải hold-out và chưa chấm LLM semantic.
