# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thành Luân  
**MSSV:** 2A202602769  
**Lớp:** K4-L3B  
**Chủ đề nhóm:** Chính sách thương mại điện tử — Trả hàng/Hoàn tiền Shopee  
**Ngày nộp:** 20/09/2026

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity)

Độ tương tự cosine cao nghĩa là hai vector văn bản có hướng gần nhau trong không gian embedding, tức là chúng biểu diễn nội dung hoặc ý nghĩa gần nhau. Giá trị gần `1` thể hiện tương đồng cao, gần `0` thể hiện ít liên quan và giá trị âm thể hiện hướng đối lập.

**Ví dụ có độ tương tự cao**

- Câu A: “Người mua có thể gửi yêu cầu trả hàng trong vòng 7 ngày.”
- Câu B: “Khách hàng được yêu cầu hoàn trả sản phẩm trong thời hạn 7 ngày.”
- Lý do: cùng chủ thể, hành động và mốc thời gian; khác biệt chủ yếu là cách diễn đạt.

**Ví dụ có độ tương tự thấp**

- Câu A: “Phí vận chuyển trả hàng được Shopee chi trả.”
- Câu B: “Thời tiết hôm nay có mưa lớn ở Hà Nội.”
- Lý do: hai câu thuộc hai chủ đề và nhóm từ vựng hoàn toàn khác nhau.

Cosine similarity được ưu tiên hơn Euclidean distance vì cosine tập trung vào **hướng** của vector thay vì độ lớn. Điều này phù hợp với text embedding, nơi độ dài văn bản có thể làm thay đổi độ lớn vector nhưng không nhất thiết làm thay đổi ý nghĩa.

### Bài toán tính toán Chunking

Với tài liệu dài 10.000 ký tự, `chunk_size=500`, `overlap=50`:

```text
step = 500 - 50 = 450
chunks = ceil((10.000 - 50) / 450)
       = ceil(22,11)
       = 23 chunks
```

Khi tăng overlap lên 100:

```text
step = 500 - 100 = 400
chunks = ceil((10.000 - 100) / 400)
       = ceil(24,75)
       = 25 chunks
```

Overlap lớn hơn tạo thêm 2 chunks và tăng chi phí lưu trữ/tìm kiếm, nhưng giúp giảm nguy cơ mất thông tin tại ranh giới chunk. Cần cân bằng overlap với độ dài ngữ cảnh và chi phí index.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** sử dụng regex `(?<=[.!?])\s+` để tách sau dấu kết thúc câu nhưng vẫn giữ dấu câu trong kết quả. Văn bản được `strip`, input rỗng trả về danh sách rỗng, và số câu mỗi chunk được bảo vệ tối thiểu là 1.

**`RecursiveChunker.chunk` / `_split`** ưu tiên các separator `\n\n`, `\n`, `. `, khoảng trắng rồi chuỗi rỗng. Base case là đoạn đã nhỏ hơn `chunk_size`; nếu không còn separator thì thuật toán cắt cứng theo kích thước. Các phần nhỏ được ghép lại đến sát ngưỡng để tránh sinh quá nhiều chunk ngắn.

Ngoài ba baseline, tôi xây dựng **`HeadingChunker`** cho Markdown. Chunker giữ đường dẫn heading cha–con trong mọi chunk, loại frontmatter khỏi nội dung và dùng `RecursiveChunker` làm fallback khi một section vượt quá ngưỡng.

### Lớp EmbeddingStore

`add_documents` chuyển mỗi `Document` thành record gồm `id`, `content`, `metadata` và embedding rồi lưu trong bộ nhớ. `search` embedding hóa query, tính tích vô hướng với vector đã chuẩn hóa, sắp xếp giảm dần và trả về tối đa `top_k` kết quả kèm score.

`search_with_filter` lọc record theo metadata **trước khi** tính similarity, nhờ đó giảm nhiễu giữa tài liệu buyer/seller. `delete_document` tạo lại danh sách record và loại mọi chunk có `metadata.doc_id` trùng với tài liệu cần xóa; kết quả trả về cho biết có record nào thực sự bị xóa hay không.

### Tác tử KnowledgeBaseAgent

`answer` lấy top-k chunk, gắn số thứ tự và nguồn cho từng context block, sau đó tạo prompt yêu cầu chỉ trả lời từ context và nêu rõ khi thiếu dữ liệu. Hàm LLM được inject qua `llm_fn`, vì vậy phần retrieval có thể kiểm thử độc lập mà không cần API thật.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Đã hoàn thành `SentenceChunker`, `RecursiveChunker`, cosine similarity, comparator, vector store, metadata filter, delete document, RAG agent và chunker tùy chỉnh theo heading.

### Kết quả kiểm thử

```text
python -m unittest discover -s tests -v
----------------------------------------------------------------------
Ran 45 tests in 0.006s

OK
```

**Số lượng bài test vượt qua:** **45 / 45**  
**Kiểm tra cú pháp:** `python -m compileall -q src main.py demo_server.py bench.py` → thành công.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Phép đo dùng cùng một `TfidfEmbedder` học vocabulary từ 10 câu bên dưới, sau đó gọi `compute_similarity()` trên từng cặp.

| Cặp | Câu A | Câu B | Dự đoán trước khi chạy | Điểm thực tế | Đúng? |
|---|---|---|---|---:|---|
| 1 | Người mua có thể gửi yêu cầu trả hàng trong vòng 7 ngày. | Khách hàng được yêu cầu trả hàng trong thời hạn 7 ngày. | Cao | 0,4007 | Có |
| 2 | Người bán phải phản hồi khiếu nại trong 48 giờ. | Người bán cần trả lời yêu cầu hoàn tiền trong 02 ngày làm việc. | Cao | 0,0920 | Không |
| 3 | Phí vận chuyển trả hàng được Shopee chi trả. | Thời tiết hôm nay có mưa lớn ở Hà Nội. | Thấp | 0,0000 | Có |
| 4 | Shopee Mall xử phạt gian hàng bán hàng giả. | Người bán hàng nhái trên Shopee Mall sẽ bị áp dụng phí phạt. | Cao | 0,2625 | Có |
| 5 | Vector store xếp hạng bằng cosine similarity. | Sản phẩm được bảo hành trong vòng 14 ngày. | Thấp | 0,0000 | Có |

Kết quả bất ngờ nhất là cặp 2: hai câu gần nghĩa nhưng TF-IDF chỉ đạt `0,0920` vì “48 giờ” và “02 ngày làm việc”, “phản hồi” và “trả lời” không được hiểu là tương đương ngữ nghĩa. Điều này cho thấy baseline lexical tốt để kiểm soát thí nghiệm nhưng không thay thế semantic embedding đa ngữ.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chiến lược cá nhân: `HeadingChunker(chunk_size=1400)`, TF-IDF từ đơn + bigram, cosine chuẩn hóa, `top_k=3`; Q2 dùng filter `audience=seller`.

| # | Câu hỏi rút gọn | Top-1 chunk | Score | Liên quan? | Câu trả lời trích xuất/tóm tắt |
|---|---|---|---:|---|---|
| 1 | Các bước gửi yêu cầu trên ứng dụng | `shopee-buyer-return-request-guide#1` | 0,3317 | Có | Vào Tôi → chọn đơn → Trả hàng/Hoàn tiền → chọn tình huống/lý do → tải bằng chứng → Gửi yêu cầu. |
| 2 | Hạn phản hồi của seller | `shopee-seller-return-processing-policy#0` | 0,2983 | Có | Người bán có 02 ngày làm việc (48 giờ); quá hạn Shopee tự động chấp nhận yêu cầu. |
| 3 | Xử lý hàng giả Shopee Mall | `shopee-mall-seller-terms-of-service#12` | 0,2756 | Có | Phạt 9.818.180 VND hoặc 100% giá trị sản phẩm; thanh toán trong 07 ngày; 02 lần vi phạm bị loại khỏi Mall. |
| 4 | Miễn phí vận chuyển trả hàng | `shopee-return-shipping-fee-policy#0` | 0,3744 | Có | Miễn 100% khi Pickup hoặc Drop-off tại bưu cục đối tác với mã vận đơn trả hàng. |
| 5 | Ngoại lệ lý do “Đổi ý” | `shopee-general-return-policy#5` | 0,3429 | Có | Không áp dụng với danh sách hạn chế, Shopee Mart và các sản phẩm Shopee quy định theo từng thời điểm. |

**Top-3 có đúng tài liệu:** **5 / 5**  
**Top-3 chứa đủ bằng chứng:** **5 / 5**  
**Top-1 chứa đủ bằng chứng:** **5 / 5**

Điều quan trọng nhất tôi học được khi so sánh là “đúng tài liệu” chưa đồng nghĩa “đủ bằng chứng”. Sentence chunking vẫn đạt document hit 5/5 nhưng chỉ 1/5 câu có đủ bằng chứng trong top-3; chunk quá nhỏ làm quy trình và điều kiện bị phân tán.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận | 10 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |

## Tệp minh chứng

- `report/STRATEGY_LUAN.md`: giải thích chiến lược và giới hạn phép đo.
- `report/strategy/benchmark_results.json`: kết quả chi tiết mọi chiến lược/query.
- `report/strategy/ket_qua_benchmark.txt`: log top-3 và filter A/B.
- `src/demo.html` + `demo_server.py`: dashboard demo so sánh live.
