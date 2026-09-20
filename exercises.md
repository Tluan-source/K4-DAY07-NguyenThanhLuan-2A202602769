# Ngày 7 — Bài tập
## Nền tảng Dữ liệu: Embedding & Vector Store | Bài tập thực hành

---

## Phần 1 — Khởi động (Cá nhân)

### Bài tập 1.1 — Cosine Similarity (Độ tương tự Cosine) bằng ngôn ngữ đời thường

Không yêu cầu toán học — hãy giải thích về mặt khái niệm:

- Điều gì xảy ra khi hai đoạn văn bản có độ tương tự cosine cao?
- Đưa ra một ví dụ cụ thể về hai câu sẽ có độ tương tự CAO và hai câu sẽ có độ tương tự THẤP.
- Tại sao độ tương tự cosine lại được ưu tiên hơn khoảng cách Euclid (Euclidean distance) đối với text embeddings?

> **Ghi kết quả vào:** Báo cáo — Phần 1 (Khởi động)

---

### Bài tập 1.2 — Bài toán tính toán Chunking

- Một tài liệu có độ dài 10,000 ký tự. Bạn tiến hành chia nhỏ (chunk) với `chunk_size=500` (kích thước chunk), `overlap=50` (độ chồng chéo). Bạn dự kiến sẽ có bao nhiêu chunks?
- Công thức: `số lượng chunk = làm_tròn_lên((độ_dài_tài_liệu - độ_chồng_chéo) / (kích_thước_chunk - độ_chồng_chéo))`
- Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk sẽ thay đổi như thế nào? Tại sao bạn lại muốn tăng độ chồng chéo?

> **Ghi kết quả vào:** Báo cáo — Phần 1 (Khởi động)

---

## Phần 2 — Lập trình cốt lõi (Cá nhân)

Hoàn thành tất cả các TODOs trong `src/chunking.py`, `src/store.py`, và `src/agent.py`. `Document` dataclass và `FixedSizeChunker` đã được triển khai sẵn làm ví dụ — hãy đọc kỹ để hiểu cấu trúc trước khi lập trình phần còn lại.

Chạy `pytest tests/` để kiểm tra tiến độ.

### Danh sách cần làm (Checklist)
- [x] `Document` dataclass — ĐÃ TRIỂN KHAI SẴN
- [x] `FixedSizeChunker` — ĐÃ TRIỂN KHAI SẴN
- [X] `SentenceChunker` — tách dựa trên ranh giới câu, nhóm lại thành các chunks
- [X] `RecursiveChunker` — thử nghiệm các dấu phân cách (separators) theo thứ tự, thực hiện đệ quy trên các đoạn có kích thước quá lớn
- [X] `compute_similarity` — công thức tính độ tương tự cosine kèm cơ chế bảo vệ chia cho 0
- [X] `ChunkingStrategyComparator` — gọi cả ba chiến lược, tính toán các chỉ số thống kê
- [X] `EmbeddingStore.__init__` — khởi tạo store (lưu trữ trong bộ nhớ hoặc ChromaDB)
- [X] `EmbeddingStore.add_documents` — nhúng (embed) và lưu trữ từng tài liệu
- [X] `EmbeddingStore.search` — nhúng truy vấn, xếp hạng theo tích vô hướng (dot product)
- [X] `EmbeddingStore.get_collection_size` — trả về số lượng
- [X] `EmbeddingStore.search_with_filter` — lọc theo siêu dữ liệu (metadata), sau đó tìm kiếm
- [X] `EmbeddingStore.delete_document` — xóa tất cả các chunks của một doc_id
- [X] `KnowledgeBaseAgent.answer` — truy xuất (retrieve) + tạo prompt + gọi LLM

> **Nộp code:** thư mục `src/`
> **Ghi lại hướng tiếp cận vào:** Báo cáo — Phần 4 (Hướng tiếp cận của tôi)

---

## Phần 3 — So Sánh Chiến Lược Truy Xuất (Nhóm)

### Bài tập 3.0 — Chuẩn Bị Tài Liệu (Giờ đầu tiên)

Mỗi nhóm chọn một chủ đề (domain) và chuẩn bị bộ tài liệu:

**Bước 1 — Chọn chủ đề:** FAQ (Câu hỏi thường gặp), SOP (Quy trình chuẩn), chính sách, tài liệu kỹ thuật, công thức nấu ăn, luật, y tế, v.v.

**Bước 2 — Thu thập 5-10 tài liệu.** Chỉ dùng nguồn công khai hoặc nguồn nhóm có quyền sử dụng; lưu dưới dạng `.txt` hoặc `.md` vào thư mục `data/`.

**Quy tắc dữ liệu bắt buộc:**
- Không đưa dữ liệu cá nhân, thông tin đăng nhập, hồ sơ nội bộ hoặc nội dung có quyền sử dụng không rõ ràng vào repo.
- Với mỗi tài liệu, ghi `source_url`, `retrieved_at` (ngày lấy) và `document_version` hoặc ngày hiệu lực nếu nguồn có nêu.
- Đưa ba trường trên vào siêu dữ liệu (metadata) khi nạp (ingest); chúng giúp kiểm tra độ mới và truy vết câu trả lời.

> **Mẹo chuyển PDF sang Markdown:**
> - `pip install marker-pdf` → `marker_single input.pdf output/` (chất lượng cao, giữ cấu trúc)
> - `pip install pymupdf4llm` → `pymupdf4llm.to_markdown("input.pdf")` (nhanh, đơn giản)
> - Hoặc sao chép-dán (copy-paste) nội dung từ PDF/web vào file `.txt`

Ghi vào bảng:

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Buyer return request guide | [Shopee 79233](https://help.shopee.vn/portal/4/article/79233) | 20/09/2026 · 2024-v2 | 2.321 | buyer, returns-guide, vi |
| 2 | Buyer return timeline policy | [Shopee 77244](https://help.shopee.vn/portal/4/article/77244) | 20/09/2026 · 2024-v1 | 1.818 | buyer, returns-policy, vi |
| 3 | General return policy | [Shopee 188931](https://help.shopee.vn/portal/4/article/188931) | 20/09/2026 · not stated | 5.857 | buyer, returns, vi |
| 4 | Shopee Mall seller terms | [Shopee 77262](https://help.shopee.vn/portal/4/article/77262) | 20/09/2026 · not stated | 12.387 | seller, terms, vi |
| 5 | Return shipping fee policy | [Shopee 77247](https://help.shopee.vn/portal/4/article/77247) | 20/09/2026 · not stated | 1.464 | buyer, shipping-policy, vi |
| 6 | Seller return processing policy | [Shopee 77245](https://help.shopee.vn/portal/4/article/77245) | 20/09/2026 · 2024-v1 | 1.953 | seller, seller-policy, vi |
| 7 | Seller warranty responsibility | [Shopee 77246](https://help.shopee.vn/portal/4/article/77246) | 20/09/2026 · 2024-v1 | 1.761 | seller, warranty-policy, vi |

**Bước 3 — Thiết kế cấu trúc metadata (metadata schema):** Mỗi tài liệu cần `source_url`, `retrieved_at`, `document_version` và ít nhất 2 trường hữu ích cho việc truy xuất (ví dụ: `audience`, `department`, `category`, `language`, `difficulty`).

**Kết quả đã thực hiện:** 7/7 tài liệu có `source_url`, `retrieved_at`, `document_version`, `audience`, `category` và `language`. File đối soát 1-1 là `data/exchange_policy/sources.csv`.

> **Ghi kết quả vào:** Báo cáo — Phần 2 (Lựa chọn tài liệu)

---

### Bài tập 3.1 — Thiết Kế Chiến Lược Truy Xuất (Mỗi người thử riêng)

Mỗi thành viên **tự chọn chiến lược riêng** để thử nghiệm trên cùng bộ tài liệu của nhóm.

**Bước 1 — Đường cơ sở (Baseline):** Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu. Ghi lại kết quả.

Kết quả comparator trên ba tài liệu đầu tiên, `chunk_size=1000`:

| Tài liệu | Fixed size | Sentence (3 câu) | Recursive |
|---|---:|---:|---:|
| buyer-return-request-guide | 3 chunks · 685,7 chars | 6 · 341,2 | 4 · 512,8 |
| buyer-return-timeline-policy | 2 · 766,5 | 6 · 254,2 | 2 · 765,5 |
| general-return-policy | 6 · 901,8 | 9 · 599,9 | 6 · 900,3 |

Trong benchmark đầy đủ 7 tài liệu, tôi mở rộng so sánh thêm Heading 600/1000/1400 và đo Evidence@3, Top-1, coverage, số chunk và latency trong dashboard.

**Bước 2 — Chọn hoặc thiết kế chiến lược của bạn:**
- Dùng 1 trong 3 chiến lược có sẵn (built-in strategies) với tham số tối ưu, HOẶC
- Thiết kế chiến lược tùy chỉnh cho chủ đề của bạn (ví dụ: chia nhỏ theo cặp Câu hỏi-Đáp án, theo các phần (sections), theo tiêu đề (headers))
- Mỗi thành viên nên thử một chiến lược **khác nhau** để có cơ sở so sánh

```python
class CustomChunker:
    """Chiến lược chia nhỏ theo heading cho chính sách thương mại điện tử.

    Lý do thiết kế: điều khoản Markdown đã có cấu trúc mục; giữ heading giúp
    retrieval giữ được ngữ cảnh của quy trình và ngoại lệ.
    """

    def chunk(self, text: str) -> list[str]:
        from src.heading import HeadingChunker
        return HeadingChunker(chunk_size=1400).chunk(text)
```

**Cấu hình được chọn:** `HeadingChunker(1400)` tạo 48 chunks, giữ heading cha–con và đạt 5/5 Complete Evidence@3, 5/5 Complete Top-1 trên bộ benchmark.

**Bước 3 — So sánh:** So sánh chiến lược tùy chỉnh/được tinh chỉnh (custom/tuned strategy) với đường cơ sở (baseline) trên cùng tài liệu.

> **Ghi kết quả vào:** Báo cáo — Phần 3 (Chiến lược chia nhỏ - Chunking Strategy)

---

### Bài tập 3.2 — Chuẩn Bị Câu Hỏi Đánh Giá (Benchmark Queries)

Mỗi nhóm viết **đúng 5 câu hỏi đánh giá** kèm theo **câu trả lời chuẩn (gold answers)**.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Các bước gửi yêu cầu Trả hàng/Hoàn tiền trên ứng dụng? | Tôi → đơn hàng → Trả hàng/Hoàn tiền → chọn tình huống/lý do → tải bằng chứng → Gửi yêu cầu. | `shopee-buyer-return-request-guide` · Mục 1, Cách 1 |
| 2 | Seller có bao nhiêu thời gian để phản hồi khiếu nại? *(filter seller)* | 02 ngày làm việc (48 giờ); quá hạn Shopee tự động chấp nhận. | `shopee-seller-return-processing-policy` · Mục 1.1 |
| 3 | Phạt hàng giả/hàng nhái tại Shopee Mall? | 9.818.180 VND hoặc 100% giá trị sản phẩm; trả trong 07 ngày; 02 lần bị loại Mall. | `shopee-mall-seller-terms-of-service` · Mục 3.3 |
| 4 | Khi nào miễn 100% phí vận chuyển trả hàng? | Dùng Pickup hoặc Drop-off tại bưu cục đối tác với mã vận đơn trả hàng. | `shopee-return-shipping-fee-policy` · Mục 1 |
| 5 | Ngoại lệ của lý do “Đổi ý”? | Danh sách hạn chế trả hàng, Shopee Mart và sản phẩm được quy định riêng theo từng thời điểm. | `shopee-general-return-policy` · Mục 1.3 |

**Yêu cầu:**
- Câu hỏi phải đa dạng (không hỏi 5 câu có nội dung/cấu trúc giống hệt nhau)
- Câu trả lời chuẩn phải cụ thể và có thể kiểm chứng (verify) từ tài liệu
- Ít nhất 1 câu hỏi yêu cầu lọc bằng metadata (metadata filtering) để trả lời tốt

> **Ghi kết quả vào:** Báo cáo — Phần 6 (Kết quả — Câu hỏi đánh giá & Câu trả lời chuẩn)

---

### Bài tập 3.3 — Dự Đoán Độ Tương Tự Cosine (Cá nhân)

Gọi hàm `compute_similarity()` trên 5 cặp câu. **Trước khi chạy**, hãy dự đoán xem cặp câu nào sẽ có độ tương tự cao nhất/thấp nhất. Ghi lại các dự đoán của bạn và kết quả thực tế. Suy ngẫm xem điều gì khiến bạn ngạc nhiên nhất.

> **Ghi kết quả vào:** Báo cáo — Phần 5 (Dự đoán độ tương tự)

---

### Bài tập 3.4 — Chạy Đánh Giá & So Sánh Trong Nhóm

**Bước 1:** Mỗi thành viên chạy 5 câu hỏi đánh giá với chiến lược riêng. Ghi lại kết quả top-3 cho mỗi câu hỏi.

**Bước 2:** So sánh kết quả trong nhóm:
- Chiến lược nào cho việc truy xuất tốt nhất? Tại sao?
- Có câu hỏi nào mà chiến lược A tốt hơn B nhưng lại ngược lại ở câu hỏi khác không?
- Lọc bằng metadata (Metadata filtering) có giúp ích không?

**Bước 3:** Thảo luận và rút ra bài học — chuẩn bị cho phần demo (thuyết trình) với các nhóm khác.

> **Ghi kết quả vào:** Báo cáo — Phần 6 (Kết quả)
> **Gợi ý đánh giá:** xem danh sách kiểm tra ngắn trong `README.md` mục **Cách Tự Đánh Giá Kết Quả Retrieval** hoặc chi tiết hơn trong file `docs/EVALUATION.md`.

---

### Bài tập 3.5 — Phân Tích Lỗi (Failure Analysis)

Tìm ít nhất **1 trường hợp lỗi (failure case)** trong quá trình so sánh. Mô tả:
- Câu hỏi nào mà quá trình truy xuất gặp thất bại?
- Tại sao? (do chunk quá nhỏ/quá lớn, thiếu metadata, câu hỏi mơ hồ, v.v.)
- Đề xuất cải thiện?

> **Ghi kết quả vào:** Báo cáo — Phần 7 (Những gì tôi học được)
> **Gợi ý:** phân tích lỗi nên tham chiếu từ các góc nhìn như độ chính xác (precision), tính mạch lạc của chunk (chunk coherence), tính hữu dụng của metadata, và chất lượng thông tin nền (grounding quality).

**Failure case đã ghi nhận:** `SentenceChunker(3)` tìm đúng tài liệu gold trong top-3 ở cả 5 query nhưng chỉ đạt Complete Evidence@3 ở 1/5. Với Q1, các bước “chọn đơn”, “tải bằng chứng” và “gửi yêu cầu” bị tách thành nhiều chunk nhỏ; retrieval lấy đúng nguồn nhưng không gom đủ bằng chứng. Cải thiện: dùng HeadingChunker 1000–1400 để giữ trọn section, hoặc tăng số context đưa vào agent.

**Kết quả A/B metadata:** Q2 có 48 chunks nếu không lọc và 29 chunks seller nếu lọc `audience=seller`. Top-1 vẫn đúng ở cả hai lượt, nhưng pre-filter loại các chunk buyer nhiễu khỏi top-3 và làm chủ thể câu trả lời rõ ràng hơn.

---

## Danh Sách Kiểm Tra Nộp Bài (Submission Checklist)

- [x] Vượt qua tất cả 45 bài kiểm thử: `python -m unittest discover -s tests -v` → 45/45
- [x] Cập nhật thư mục `src/` (cá nhân)
- [x] Hoàn thành báo cáo nhóm (`report/REPORT_NHOM.md`)
- [x] Hoàn thành báo cáo cá nhân (`report/REPORT_CANHAN.md`)
- [x] Có `benchmark.md`, `sources.csv`, kết quả benchmark và dashboard demo
- [x] Có ít nhất một failure case và phân tích metadata A/B
