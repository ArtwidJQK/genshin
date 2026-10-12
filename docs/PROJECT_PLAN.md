# Kế hoạch A–Z: Genshin Artifact & Wish Simulator (mô phỏng ~99%)

Tài liệu giao việc cho AI agent, xây tiếp trên repo `ArtwidJQK/genshin` (Python, FastAPI, pytest). Ngày lập: 11/10/2026.

## 0. Mục tiêu và định nghĩa "99% chính xác"

**Mục tiêu:** một trình mô phỏng gồm (1) hệ thống sinh và nâng cấp thánh di vật, (2) gacha nhân vật (Wish), (3) frontend có cảm giác như game thật.

**Không dùng một con số "99%" tổng hợp.** Dự án có ba bảng nghiệm thu độc lập. Điểm cao ở trục này không bù được trục khác, và chỉ gọi là đạt khi từng tiêu chí bắt buộc đạt riêng:

1. **Rule fidelity:** bảng từng cơ chế (số dòng phụ, nhịp +4, loại trừ, làm tròn, pity, 50/50, Capturing Radiance) kèm nguồn, độ tin cậy và trạng thái xác minh (VERIFIED, UNKNOWN, EXPERIMENTAL).
2. **Probability fidelity:** phân phối chính xác hoặc chuẩn đối chiếu được định nghĩa trước, sai số cho phép và điều kiện áp dụng.
3. **UX fidelity:** checklist luồng thao tác và visual regression.

**Giới hạn phải nói thẳng:** server của HoYoverse không công khai mã. Một số số liệu (đường cong soft pity, xác suất Capturing Radiance) là do cộng đồng suy ra từ lượng dữ liệu lớn. Vì vậy mọi hằng số trong dự án phải gắn nhãn độ tin cậy:

- **[A]** Chính thức: văn bản trong game, thông báo của HoYoverse.
- **[B]** Datamine: dữ liệu bảng cấu hình trích từ client.
- **[C]** Cộng đồng suy ra bằng thống kê.
- **[?]** Chưa xác minh. Agent phải kiểm chứng trước khi dùng.

## 1. Phạm vi

**Trong phạm vi**

- Artifact: sinh 5★ (và 4★ nếu còn thời gian), nâng cấp 0→20, nguồn rơi (domain, strongbox), Sanctifying Elixir, Artifact Transmuter, Reshaping (Dust of Enlightenment, Hallowed Exegesis).
- Wish: Character Event Wish và Character Event Wish-2 (dùng chung bộ đếm), Standard Wish (Wanderlust Invocation). Tùy chọn: Weapon Event Wish, Beginners' Wish, Chronicled Wish.
- Frontend, lưu trữ hồ sơ, lịch sử, thống kê.

**Ngoài phạm vi:** tính sát thương/build, thanh toán thật, tài khoản online, đăng nhập mạng xã hội, và dùng lại asset gốc của game.

## 2. Quy tắc cứng cho agent

1. **Không bịa số.** Mọi hằng số trong dữ liệu cấu hình (hiện là `config/`) có `value`, `source` kèm locator chính xác, `confidence` (A/B/C) và `status` (VERIFIED, UNKNOWN, EXPERIMENTAL). Với thông số UNKNOWN, engine không được gắn nhãn kết quả là "chính thức" và phải có test xác nhận điều đó. `xfail` hoặc `skip` không được dùng làm bằng chứng nghiệm thu; mọi test bị skip phải có lý do, người chịu trách nhiệm và điều kiện bỏ skip.
2. **Hai loại mặc định.** Mặc định kỹ thuật không ảnh hưởng cơ chế game: được chọn, ghi ADR rồi làm tiếp. Mặc định ảnh hưởng xác suất hoặc state machine khi luật chưa rõ: chỉ được cài như strategy thử nghiệm có tên rõ ràng, tắt mặc định và nằm ngoài chế độ fidelity chính. Nếu không làm được vậy thì dừng, ghi `OPEN_QUESTIONS.md` và chờ phê duyệt.
3. **Engine thuần:** không I/O, không gọi thời gian hệ thống, RNG luôn được inject. Cùng seed phải cho cùng kết quả từng bit.
4. **Mọi thao tác ghi audit trail:** mỗi roll, mỗi lần kích hoạt pity hoặc guarantee đều có sự kiện kèm trạng thái trước và sau.
5. **Số học theo từng bài toán:** xác suất rời rạc dùng số nguyên hoặc `Fraction`; giá trị roll dùng `Decimal` hoặc số nguyên có scale; phân tích thống kê có thể dùng float nhưng phải ghi chú sai số. Không so sánh float bằng `==`. Làm tròn chỉ xảy ra ở lớp hiển thị.
6. **PR nhỏ, một mục tiêu, có test.** Không sửa test cho khớp code. Không merge khi CI đỏ.
7. **Mỗi phase kết thúc bằng Gate** (mục 6): đủ tiêu chí nghiệm thu mới sang phase sau.
8. **Cập nhật `AGENTS.md` và `docs/`** cùng PR khi đổi quy ước hoặc kiến trúc. Thay đổi cấu trúc thư mục chỉ qua ADR nêu lợi ích, chi phí, kế hoạch migration và tiêu chí nghiệm thu.

## 3. Kiến trúc và công nghệ

Giữ cấu trúc hiện có của repo và không di chuyển thư mục chỉ để khớp một sơ đồ. Python vẫn là nguồn sự thật duy nhất cho luật. Thư mục mới chỉ thêm khi có nhu cầu thật, và mọi thay đổi cấu trúc cần ADR (mục 2).

```
app/core/rng, probability, artifact   engine hiện có (giữ nguyên)
app/main.py                           FastAPI (hiện mới có /health)
config/artifacts/                     cấu hình hiện có; thêm config/wish/ khi làm gacha
docs/, tests/                         giữ nguyên; thêm SPEC_*.md, ADR/, OPEN_QUESTIONS.md
web/    (mới, tới P8)                 React + TypeScript + Vite
tools/  (mới, khi cần)                importer datamine, DP/Monte Carlo
```

- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy + SQLite (Alembic cho migration).
- **Frontend:** React 18 + TypeScript, Vite, TanStack Query (dữ liệu API), Zustand (trạng thái UI), Framer Motion/CSS (hoạt ảnh), Tailwind (hoặc CSS Modules).
- **Chất lượng:** ruff, mypy (strict cho `engine`), pytest, Hypothesis, Playwright, GitHub Actions, pre-commit.
- **Hồ sơ người chơi:** ẩn danh qua profile ID, không cần đăng nhập. Hỗ trợ export/import JSON.
- **Tùy chọn sau:** đóng gói engine chạy trong trình duyệt (Pyodide) để triển khai tĩnh, không cần server.

**API dự kiến (tối thiểu):** `POST /artifacts/generate`, `POST /artifacts/{id}/enhance`, `POST /domains/{id}/run`, `POST /wish/{banner}/pull` (1 hoặc 10), `GET /wish/state`, `GET /wish/history`, `GET /analytics/wish`, `GET /inventory`, `GET /health`. Mọi endpoint ghi kết quả có `seed` hoặc `replay_token` để tái lập.

## 4. Đặc tả hệ thống Artifact

Phần này agent phải chuyển thành `docs/SPEC_ARTIFACT.md` và `data/artifact/*.json`, đối chiếu từng dòng với nguồn.

### 4.1 Cấu trúc một artifact 5★

- 5 ô: Flower, Plume, Sands, Goblet, Circlet. Flower luôn là HP cố định, Plume luôn là ATK cố định. [A]
- Cấp 0 → 20. Mỗi cột mốc +4, +8, +12, +16, +20 tạo một lần nâng substat. [A]
- Substat không được trùng nhau và không được trùng main stat. ATK% làm main stat vẫn có thể có ATK phẳng làm substat. [A]
- Khởi đầu có 3 hoặc 4 dòng phụ. **Bản 3 dòng:** dòng thứ 4 được chọn sẵn từ lúc tạo (repo hiện đã làm đúng điều này), nhưng ẩn; đến +4 thì kích hoạt, không roll lại, không đổi giá trị. **Bản 4 dòng:** cả 5 cột mốc đều là lần nâng ngẫu nhiên. Tổng lần nâng ngẫu nhiên: 4-dòng = 5, 3-dòng = 4 (sau khi lộ dòng thứ 4). [A]
- Mỗi lần nâng: chọn **đều 1/4** trong bốn substat đang có, sau đó cộng một giá trị roll. [A/B]

### 4.2 Giá trị roll

- Mỗi substat có **4 mức giá trị rời rạc, xác suất đều 25%**, tương ứng 70%, 80%, 90%, 100% giá trị tối đa. [B]
- Giá trị tối đa 5★ (cần đối chiếu datamine): HP 298.75, ATK 19.45, DEF 23.15, HP% 5.83, ATK% 5.83, DEF% 7.29, ER 6.48, EM 23.31, Crit Rate 3.89, Crit DMG 7.77. Đã khớp một phần với nguồn: Crit DMG ra 5.44 / 6.22 / 6.99 / 7.77, Crit Rate ra khoảng 2.7–3.9. [B]
- Hiển thị theo kiểu game: stat phẳng và EM làm tròn số nguyên, stat phần trăm một chữ số thập phân. **Giá trị nội bộ giữ nguyên độ chính xác**, chỉ làm tròn khi hiển thị. [B, cần kiểm chứng quy tắc làm tròn từng trường hợp]

### 4.3 Trọng số chọn substat (khi sinh và khi chọn dòng mới)

Theo hiểu biết cộng đồng [?]: HP, ATK, DEF phẳng: 6; HP%, ATK%, DEF%, ER, EM: 4; Crit Rate, Crit DMG: 3. Substat trùng main stat bị loại khỏi nhóm chọn, các trọng số còn lại giữ nguyên rồi chuẩn hóa. Agent phải xác minh bằng datamine trước khi khóa.

### 4.4 Main stat theo ô (cần đối chiếu datamine) [?]

- Sands: HP%, ATK%, DEF% (mỗi cái khoảng 26.7%), ER 10%, EM 10%.
- Goblet: HP%, ATK%, DEF% (khoảng 19–19.25%), mỗi hệ nguyên tố và Physical 5%, EM 2.5%.
- Circlet: HP%, ATK%, DEF% (22%), Crit Rate 10%, Crit DMG 10%, Healing 10%, EM 4%.
- Giá trị main stat theo từng cấp 0–20: bắt buộc import từ bảng datamine, không tự nội suy.

### 4.5 Nguồn rơi và hệ thống nâng cao

- **Domain:** một lượt tốn 20 Original Resin, cho 5★ thuộc một trong hai set (50/50) kèm 4★. Số lượng trung bình và xác suất 4-dòng (khoảng 20% là con số hay được nhắc) cần xác minh. [?]
- **Strongbox:** đổi artifact thừa lấy artifact thuộc set chọn. Xác suất 4-dòng cao hơn domain. Quy tắc đổi cần đọc từ tutorial trong game. [?]
- **Sanctifying Elixir và Artifact Transmuter (từ bản 5.0):** chọn 2 substat ưu tiên, được đảm bảo tối thiểu 2 lần nâng vào các substat đó. Chi tiết chi phí và điều kiện: [?].
- **Reshaping (từ bản 5.7):** dùng Dust of Enlightenment để phân bổ lại các lần nâng substat của artifact 5★ +20. Phải chọn 2 substat ưu tiên, được đảm bảo ít nhất 2 lần nâng gộp vào hai substat đó. Chi phí 1 Dust cho Flower/Plume, 2 Dust cho Sands/Goblet/Circlet. Bản 4-dòng phân bổ lại 5 lần nâng, bản 3-dòng là 4 lần. Bộ đếm **Hallowed Exegesis** nâng mức đảm bảo lên 3 rồi 4 ở các mốc tích lũy. **Các nguồn đang mâu thuẫn về mốc (6/12/18 so với 12 và 16)**, và có báo cáo rằng hai lần nâng đảm bảo có thể cùng rơi vào một substat. Agent phải lấy văn bản tutorial trong game làm chuẩn rồi mới triển khai. [A/?]

## 5. Đặc tả hệ thống Wish

Mục tiêu chính là Character Event Wish. Các số dưới đây đã được đối chiếu với tìm kiếm trên web ngày 11/10/2026 trừ khi đánh dấu khác.

### 5.1 Character Event Wish

- 5★: xác suất cơ bản **0.6%**, hard pity **90**, xác suất quy đổi khoảng **1.6%**. [A]
- Soft pity bắt đầu quanh lượt 74, mỗi lượt sau đó tăng xác suất khá mạnh (mức tăng khoảng 6 điểm phần trăm mỗi lượt là số do cộng đồng suy ra). [C]
- 4★: xác suất cơ bản khoảng 5.1%, đảm bảo 4★ trong 10 lượt, xác suất quy đổi khoảng **13%**. Soft pity của 4★ và tỉ lệ nhân vật/vũ khí trong pool 4★ cần xác minh. [A/C]
- **50/50:** 5★ đầu tiên có 50% là nhân vật nổi bật. Thua thì 5★ tiếp theo chắc chắn là nhân vật nổi bật. [A]
- **Capturing Radiance (từ 5.0):** khi thua 50/50 có cơ hội được "cứu" thành nhân vật nổi bật, không làm đổi bộ đếm pity hay guarantee, và xác suất quy đổi để ra nhân vật nổi bật khi không có guarantee là **55%**. Các nguồn mô tả cơ chế khác nhau (một nguồn nói 10% khi thua, wiki nói xác suất cơ bản 0.018%). **Đây là blocker thiết kế, không phải việc agent tự giải bằng cách tìm công thức khớp 55%** (mục 5.1.1). [A cho con số 55%, ? cho cơ chế]
- **Chuyển banner:** bộ đếm pity và guarantee được giữ khi sang banner nhân vật mới, dùng chung giữa Event Wish và Event Wish-2, không dùng chung với banner vũ khí hay Standard. [A]

#### 5.1.1 Capturing Radiance là blocker thiết kế

Tách bốn lớp thông tin, mỗi lớp có nguồn riêng: (1) thông số HoYoverse công bố; (2) điều kiện bảo đảm được công bố; (3) mô hình thực nghiệm của cộng đồng; (4) strategy mà simulator chọn. Nhiều mô hình khác nhau cho cùng xác suất tổng hợp 55%, nên một test khớp 55% không chứng minh cơ chế nội bộ đúng.

Quy tắc triển khai: engine chỉ cung cấp interface. Mô hình cộng đồng được cài như strategy EXPERIMENTAL, tắt mặc định, nằm ngoài chế độ fidelity chính và UI ghi rõ điều đó. Chế độ fidelity chính chỉ dùng phần công bố chính thức (50/50 và guarantee) cho tới khi người duyệt chốt mô hình. Test 55% chỉ kiểm tra tương thích với số đã công bố. Trước khi code gacha còn phải chốt chính sách khi pity va chạm (pity collision policy) và xác định mô hình soft pity nền.

### 5.2 Các banner khác

- **Weapon Event Wish:** 5★ cơ bản 0.7%, soft pity khoảng lượt 63, hard pity 80, cơ chế 75/25, Epitomized Path còn 1 điểm định mệnh từ 5.0. Số liệu 4★ và các mốc chính xác cần xác minh. [A/C/?]
- **Standard (Wanderlust Invocation):** 5★ lấy từ pool thường trực, 0.6% và hard pity 90, không có 50/50. Chi tiết pool và pity 4★ cần xác minh. [?]
- **Chronicled Wish, Beginners' Wish:** làm sau cùng và chỉ khi có đặc tả đáng tin.
- **Tùy chọn phụ:** Starglitter/Stardust khi trùng nhân vật, các cung chòm sao. Chỉ làm nếu phần lõi đã xong.

### 5.3 Mô hình trạng thái đề xuất

Trạng thái của mỗi "loại banner": `pity_5`, `pity_4`, `guaranteed_featured_5`, `guaranteed_featured_4`, `radiance_counter` (nếu mô hình cần), cùng `history[]`. Hàm thuần `pull(state, banner_cfg, rng) -> (state', result, events)`. Mọi nhánh pity và guarantee phát ra event trong `events` để UI và test cùng đọc.

## 6. Lộ trình theo phase và Gate nghiệm thu

Thứ tự thực thi chính thức là năm bước ở mục 6.1. Các phase P0–P10 bên dưới là danh mục công việc chi tiết, được kéo vào theo thứ tự đó. Thư mục `data/` nhắc trong tài liệu này hiểu là `config/` hiện có. Ký hiệu cỡ việc: S (nhỏ), M (vừa), L (lớn).

### 6.0 Ánh xạ trạng thái repo sang phase

Bảng dựa trên README và nhận xét review, chưa kiểm chứng trong code. Bước 1 của mục 6.1 phải xác nhận từng dòng bằng bằng chứng.

| Hạng mục trong repo | Phase | Việc cần làm |
| --- | --- | --- |
| RNG interface và PythonRNG | P0 | Audit theo Gate mới, không viết lại |
| Probability Engine (dependency injection) | P0 | Audit theo Gate mới |
| Artifact Foundation v1: sinh 5★, dòng 4 ẩn của bản 3 dòng, enhance +4 đến +20, audit history | P0, P2 | Audit đối kháng, chỉ bổ sung phần thiếu đã chứng minh |
| `config/artifacts/` (main stat, trọng số substat, mức roll, rules) | P1 | Đối chiếu provenance, gắn status cho từng hằng số |
| Bộ test (README ghi 67 và 87) | P0 | Đếm lại, sửa README |
| Artifact Research Validation (theo review) | P0, P6 | Xác nhận tồn tại, nối vào Gate xác suất |
| Endpoint `/health` | P7 | Giữ nguyên |
| Chưa có: wish engine, loot source, lưu trữ, frontend | P3 đến P8 | Làm sau Gate tương ứng |

### 6.1 Thứ tự thực thi

1. **Audit và chốt baseline:** đối chiếu HEAD local và remote, trạng thái git, test suite, tài liệu. Audit đối kháng Artifact Foundation; không refactor trước khi có finding.
2. **Mechanics audit theo phiên bản game hiện hành:** lập delta matrix cho Artifact và Character Wish. Agent xác nhận số phiên bản hiện hành từ nguồn chính thức. Chỉ cập nhật SPEC khi có nguồn hoặc quyết định thiết kế được ghi rõ.
3. **Hoàn thiện Artifact Engine theo module:** main stat theo cấp và formatter, rồi loot-source rules, rồi Strongbox, rồi Transmuter và Reshaping. Mỗi module có research và Gate riêng; không làm Reshaping khi nguồn còn mâu thuẫn.
4. **Gacha: SPEC trước, code sau:** giải quyết hoặc cô lập Capturing Radiance, chốt pity collision policy, xác định soft pity nền. Sau đó triển khai từng module và kiểm bằng DP/Markov.
5. **API, lưu trữ, phân tích, frontend:** chỉ bắt đầu khi engine có hợp đồng ổn định. Không đưa logic RNG hay pity sang UI.

### P0. Kiểm toán và củng cố repo (S)

- Audit trước, refactor sau: sửa mâu thuẫn README (67 hay 87 test), kiểm tra HEAD, git, test suite và tài liệu.
- Thêm `pyproject.toml` (pytest, ruff, mypy), LICENSE, description và topics; thêm CI GitHub Actions; cập nhật `AGENTS.md` theo mục 2; xử lý issue đang mở.
- **Gate:** CI xanh, README khớp thực tế, bảng ánh xạ 6.0 được xác nhận bằng bằng chứng, cấu trúc thư mục giữ nguyên.

### P1. Sổ đặc tả và dữ liệu (M)

- Dùng `config/` hiện có làm kho dữ liệu; thêm schema kiểm (Pydantic hoặc JSON Schema) và trường provenance (nguồn kèm locator, confidence, status) cho mọi hằng số.
- Viết `SPEC_ARTIFACT.md` và `SPEC_WISH.md` từ mục 4–5, mỗi dòng ghi nguồn và độ tin cậy. Viết importer datamine có locator chính xác cho main stat theo cấp, trọng số và giá trị roll; không suy cả bảng từ vài ví dụ.
- Lập `OPEN_QUESTIONS.md` cho mọi điểm UNKNOWN, tách mặc định kỹ thuật và mặc định ảnh hưởng cơ chế (mục 2).
- **Gate:** không còn hằng số thiếu nguồn; mọi UNKNOWN có mục trong OPEN_QUESTIONS và test xác nhận engine không gắn nhãn chính thức.

### P2. Artifact lõi hoàn chỉnh (L)

- Đủ 5 ô, set bonus (dữ liệu), sinh main stat theo trọng số từng ô, sinh substat theo trọng số và luật loại trừ, sinh 3/4 dòng.
- Nâng cấp đến cấp bất kỳ (nâng nhiều cấp một lần sẽ roll tại từng cột mốc đã đi qua), main stat theo từng cấp, khóa/mở khóa, serialize/deserialize ổn định.
- Lớp hiển thị làm tròn tách biệt khỏi giá trị nội bộ.
- **Gate:** toàn bộ property test (mục 7) xanh; so sánh chéo với bảng giá trị của một công cụ độc lập (Genshin Optimizer) khớp 100% trên bảng roll và main stat.

### P3. Nguồn rơi artifact (M)

- Domain (20 resin, Condensed Resin), chọn set 50/50, số lượng 4★/5★ trung bình, xác suất 4-dòng theo nguồn. Strongbox.
- **Gate:** sau 10^6 lượt, tần suất khớp bảng đặc tả trong ngưỡng 4σ.

### P4. Hệ thống nâng cao (M–L)

- Mỗi module (Sanctifying Elixir, Transmuter, Reshaping và Hallowed Exegesis) chỉ bắt đầu khi OPEN_QUESTIONS của module đó đã chốt. Không triển khai Reshaping khi các nguồn còn mâu thuẫn về mốc Hallowed Exegesis.
- **Gate:** test thuộc tính: ít nhất 2 lần nâng rơi vào substat ưu tiên; tổng số lần nâng khớp 4/5; chi phí và bộ đếm đúng theo đặc tả.

### P5. Wish engine (L)

- Cấu hình banner theo dữ liệu, pity 5★/4★, 50/50, carry-over giữa các banner cùng loại, Wish-2, Standard. Capturing Radiance chỉ qua interface strategy theo mục 5.1.1; pity collision policy được chốt trước khi code. Weapon banner là tùy chọn.
- **Gate:** DP/Markov chính xác ra phân phối số lượt tới 5★ và tới nhân vật nổi bật; mô phỏng khớp theo mục 7; Capturing Radiance không nằm trong chế độ fidelity chính cho tới khi người duyệt chốt mô hình.

### P6. Bộ kiểm chứng thống kê và phân tích (M)

- `tools/validate`: DP chính xác, Monte Carlo có khoảng tin cậy, chi-square, báo cáo HTML/Markdown mỗi lần CI chạy bản "nặng" (nightly).
- Endpoint `/analytics/wish`: kỳ vọng số lượt, phân phối, xác suất đạt mục tiêu với N lượt.
- **Gate:** báo cáo nightly xanh ít nhất 7 ngày liên tiếp.

### P7. API và lưu trữ (M)

- Hồ sơ ẩn danh, inventory, lịch sử wish, export/import JSON, replay bằng seed, idempotency key cho thao tác ghi.
- **Gate:** test API đầy đủ (httpx), migration chạy sạch từ DB trống, OpenAPI sinh type cho frontend.

### P8. Frontend nền tảng và tính năng (L)

- Design system, routing, trạng thái, client API sinh tự động từ OpenAPI.
- Màn hình theo mục 8. Mock API để dev FE độc lập.
- **Gate:** Playwright e2e cho luồng chính (tạo artifact → nâng cấp; kéo wish 1 và 10 lượt; xem lịch sử), kiểm tra a11y không lỗi nghiêm trọng.

### P9. Hoàn thiện và phát hành (M)

- Hoạt ảnh và âm thanh gốc, i18n (vi/en), responsive, hiệu năng, tài liệu người dùng, CHANGELOG, Docker Compose hoặc triển khai tĩnh.
- **Gate:** phát hành v1.0 có README hướng dẫn chạy bằng một lệnh, ảnh chụp màn hình, tuyên bố miễn trừ (mục 10).

### P10. Bảo trì theo bản cập nhật game (liên tục)

- Quy trình khi game đổi luật (ví dụ 5.0 thêm Capturing Radiance, 5.7 thêm Reshaping): mở issue, sửa data trước, code sau, thêm test hồi quy, ghi vào CHANGELOG và `data/` có trường `valid_from_version`.

## 7. Chiến lược kiểm thử và xác thực

1. **Unit theo bảng:** mỗi luật một nhóm test (số dòng, nhịp +4, loại trừ, làm tròn, từng nhánh pity).
2. **Property-based (Hypothesis):** với mọi seed và mọi cấu hình hợp lệ:
    - luôn có đúng 4 slot khái niệm; không trùng substat; không trùng main stat;
    - giá trị mỗi roll luôn thuộc đúng bốn mức; số lần nâng tổng đúng 5 (4-dòng) hoặc 4 (3-dòng, sau khi lộ);
    - cấp tăng đơn điệu; cùng seed cho cùng kết quả; pity luôn trong [0, hard_pity).
3. **Tính chính xác để làm chuẩn:** Wish dùng DP/Markov trên trạng thái (pity_5, guarantee, bộ đếm); Artifact dùng đếm tổ hợp hoặc tích chập cho phân phối Crit Value và số lần roll vào substat.
4. **Kiểm định thống kê, đăng ký trước:** trước khi chạy phải định nghĩa phân phối kỳ vọng, cách chia bin, điều kiện độc lập giữa các mẫu và cách hiệu chỉnh nhiều phép kiểm (Bonferroni, Holm hoặc FDR). Monte Carlo 10^6–10^7 mẫu, seed cố định; ngưỡng (ví dụ 4σ hoặc chi-square) chốt trong tài liệu trước khi xem kết quả. Hai chế độ: nhanh (mỗi PR) và nặng (nightly).
5. **Đối chiếu độc lập:** so bảng dữ liệu với một công cụ cộng đồng khác, ghi vào `docs/CROSSCHECK.md`.
6. **Frontend:** Playwright e2e và chụp ảnh so sánh cho thẻ artifact và màn kết quả wish; axe cho a11y.
7. **Mutation testing** cho phần engine ở phase cuối để chắc test không bỏ sót lỗi logic.
8. **`xfail` và `skip` không phải bằng chứng nghiệm thu.** Mỗi test bị skip có lý do, người chịu trách nhiệm và điều kiện bỏ skip.

## 8. Đặc tả frontend

**Nguyên tắc:** bố cục, hoạt ảnh và luồng thao tác bám sát game; **toàn bộ hình ảnh, âm thanh, icon là tự vẽ hoặc dùng nguồn có giấy phép**, không dùng asset trích từ game.

**Artifact**

- Kho artifact: lưới thẻ, nền chuyển màu theo độ hiếm (5★ vàng), lọc theo ô/set/main stat/substat, sắp xếp, khóa, tìm kiếm.
- Thẻ chi tiết: ô, tên set, sao, cấp, main stat lớn, các dòng substat kèm các lần nâng đã vào (mũi tên hoặc số lần), dòng phụ chưa kích hoạt hiển thị dưới dạng "chưa kích hoạt" cho bản 3 dòng.
- Màn nâng cấp: chọn cấp mục tiêu, xem trước các cột mốc sẽ đi qua, nhấn nâng thì phát hoạt ảnh từng cột mốc, dòng vừa được nâng nhấp sáng, có nút xem lịch sử roll.
- Domain: nút chạy 1 lượt/Condensed Resin, bộ đếm resin, màn nhận thưởng.
- Về sau: Strongbox, Transmuter, Reshaping có giao diện riêng.

**Wish**

- Màn banner: carousel banner, nút kéo 1 và 10, hiển thị pity hiện tại, guarantee đang có.
- Hoạt ảnh kéo theo độ hiếm (xanh dương, tím, vàng), có nút bỏ qua, màn kết quả dạng lưới.
- Lịch sử wish có đánh dấu các mốc pity, xuất JSON, bảng thống kê cá nhân so với kỳ vọng lý thuyết.
- Cảnh báo rõ khi kích hoạt Capturing Radiance (hoạt ảnh riêng).

**Chung:** responsive (điện thoại/máy tính), chế độ giảm chuyển động, bàn phím điều hướng được, hai ngôn ngữ vi/en.

## 9. Nguồn tham chiếu (agent phải ghi cụ thể vào provenance)

- Văn bản hướng dẫn trong game (Artifact Reshaping, Artifact Definition and Extraction, Wish details) và thông báo bản cập nhật chính thức.
- Genshin Impact Wiki (Fandom), trang Wish: https://genshin-impact.fandom.com/wiki/Wish
- Bài giải thích Reshaping/Dust of Enlightenment: https://www.icy-veins.com/genshin-impact/artifact-rerolling (lưu ý các nguồn khác nhau mâu thuẫn ở mốc Hallowed Exegesis).
- Dữ liệu datamine công khai (bảng cấu hình thánh di vật và wish) và các công cụ cộng đồng như Genshin Optimizer, paimon.moe để đối chiếu chéo.

## 10. Rủi ro và pháp lý

| Rủi ro | Giảm thiểu |
|---|---|
| Số liệu cộng đồng lệch thực tế | Gắn nhãn độ tin cậy, tách thành `data/`, sửa không cần đụng code |
| Game đổi luật | Trường `valid_from_version`, quy trình P10 |
| Capturing Radiance mô hình sai | Strategy EXPERIMENTAL tắt mặc định; test 55% chỉ kiểm tra tương thích, không chứng minh đúng cơ chế |
| Agent "tự tin quá" bịa chi tiết | Quy tắc cứng số 1–2, review bắt buộc ở mỗi Gate |
| Vấn đề bản quyền/thương hiệu | Dự án fan, phi thương mại, không dùng asset gốc, không tích hợp thanh toán, ghi rõ không liên kết với HoYoverse, kiểm tra chính sách nội dung fan của HoYoverse trước khi phát hành công khai |

## 11. Prompt mẫu để giao cho agent

> Bạn là kỹ sư phụ trách dự án trong repo này. Đọc `AGENTS.md`, `docs/SPEC_*.md`, `docs/OPEN_QUESTIONS.md` và kế hoạch dự án. Làm theo thứ tự ở mục 6.1, bắt đầu từ bước 1 (audit, chưa refactor). Mỗi lần chỉ làm một task nhỏ, mở một nhánh/PR riêng, có test. Không tự bịa hằng số: mọi con số nằm trong `config/` kèm nguồn có locator, độ tin cậy và status. Mặc định kỹ thuật không ảnh hưởng cơ chế game thì ghi ADR rồi làm tiếp; mặc định ảnh hưởng xác suất hoặc state machine thì chỉ làm strategy thử nghiệm tắt mặc định, hoặc dừng chờ phê duyệt. Không đổi cấu trúc thư mục nếu chưa có ADR. Không sửa test để cho qua, không dùng xfail/skip làm bằng chứng. Hết mỗi bước, báo cáo Gate rule/probability/UX đã đạt hay chưa và dừng chờ xác nhận.
