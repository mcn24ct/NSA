import os
import re
import json
import sqlite3
import requests
import pandas as pd
from bs4 import BeautifulSoup

# Đường dẫn gốc khóa cứng vào thư mục 03_Datasets_NASA
BASE_DIR = r"D:\MCN\Hackathon_NASA_AI\03_Datasets_NASA"

PDF_GUIDE_URL = (
    "https://www.nasa.gov/wp-content/uploads/2016/05/"
    "np-2015-10-034-jsc_combustion_in_reduced_gravity-iss-mini-book-011116-508.pdf"
)

# Bảng ánh xạ chủ đề (pillar) sang tên thư mục phân loại
PILLAR_FOLDERS = {
    "Prevention": "01_Prevention",
    "Detection": "02_Detection",
    "Suppression": "03_Suppression",
    "Prevention (Partial-G Proxy)": "04_Partial_Gravity",
    "Prevention (Partial-G)": "04_Partial_Gravity",
}

# 1. DANH SÁCH ĐẦY ĐỦ 18 THÍ NGHIỆM TRÊN CỔNG PSI.NASA.GOV (GIỮ NGUYÊN ĐƠN VỊ GỐC)
PSI_INVESTIGATIONS = [
    {
        "psi_id": "PSI-25",
        "code": "BASS-II",
        "title": "Burning and Suppression of Solids - II",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-25",
        "pillar": "Prevention",
        "rack": "MSG (SPICE Flow Duct)",
        "fuel_category": "Solid",
        "fuels": "Sibal fabric (cotton-fiberglass), PMMA acrylic slabs/rods, Nomex",
        "o2_min": 15.0, "o2_max": 30.0, "pressure_psi": 10.2, "airflow_max_cm_s": 40.0,
        "simulates_partial_g": 0,
        "core_summary": "Đốt vật liệu rắn (vải, nhựa PMMA) trong ống gió quạt thuộc tủ MSG. Chứng minh luồng gió tốc độ thấp (3-10 cm/s) trong 0g làm vật liệu cháy mạnh hơn và hạ ngưỡng oxy tối thiểu (LOC) xuống thấp hơn so với trên Trái Đất."
    },
    {
        "psi_id": "PSI-26",
        "code": "BASS",
        "title": "Burning and Suppression of Solids",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-26",
        "pillar": "Prevention",
        "rack": "MSG (SPICE Flow Duct)",
        "fuel_category": "Solid",
        "fuels": "Solid polymer rods, thin films, cotton-fiberglass",
        "o2_min": 16.0, "o2_max": 21.0, "pressure_psi": 14.7, "airflow_max_cm_s": 50.0,
        "simulates_partial_g": 0,
        "core_summary": "Thí nghiệm nền tảng khảo sát tốc độ cháy lan ngược dòng và xuôi dòng gió cưỡng bức cũng như dập lửa bằng dòng khí Nitơ trong tủ MSG."
    },
    {
        "psi_id": "PSI-98",
        "code": "SAFFIRE-I",
        "title": "Spacecraft Fire Safety Experiment - I",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-98",
        "pillar": "Prevention",
        "rack": "Cygnus Autonomous Vehicle",
        "fuel_category": "Solid",
        "fuels": "Large Sibal cloth (0.4 m x 0.94 m, 75% cotton / 25% fiberglass)",
        "o2_min": 21.0, "o2_max": 21.0, "pressure_psi": 14.7, "airflow_max_cm_s": 20.0,
        "simulates_partial_g": 0,
        "core_summary": "Đốt tấm vải Sibal kích thước lớn (0.4 x 0.94 m) trên tàu chở hàng Cygnus sau khi rời ISS để đo giới hạn phát triển đám cháy quy mô thật."
    },
    {
        "psi_id": "PSI-99",
        "code": "SAFFIRE-II",
        "title": "Spacecraft Fire Experiment - II",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-99",
        "pillar": "Prevention",
        "rack": "Cygnus Autonomous Vehicle",
        "fuel_category": "Solid",
        "fuels": "9 samples (5 cm x 29 cm): Sibal, Silicone, structured PMMA, flat PMMA, Nomex",
        "o2_min": 21.0, "o2_max": 21.0, "pressure_psi": 14.7, "airflow_max_cm_s": 30.0,
        "simulates_partial_g": 0,
        "core_summary": "Thử nghiệm 9 mẫu vật liệu tàu vũ trụ (Sibal, Silicone, PMMA dày/mỏng, Nomex) ở tốc độ gió 20 và 30 cm/s để kiểm chứng tiêu chuẩn NASA-STD-6001 trong 0g."
    },
    {
        "psi_id": "PSI-100",
        "code": "SAFFIRE-III",
        "title": "Spacecraft Fire Experiment - III",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-100",
        "pillar": "Prevention",
        "rack": "Cygnus Autonomous Vehicle",
        "fuel_category": "Solid",
        "fuels": "Large Sibal cotton-fiberglass panel at exploration atmosphere",
        "o2_min": 21.0, "o2_max": 34.0, "pressure_psi": 10.2, "airflow_max_cm_s": 30.0,
        "simulates_partial_g": 0,
        "core_summary": "Đốt mẫu quy mô lớn ở bầu khí quyển mô phỏng Căn cứ Mặt Trăng / tàu thám hiểm (tăng nồng độ O2, giảm áp suất xuống ~10.2 psi)."
    },
    {
        "psi_id": "PSI-159",
        "code": "ACME-CFI-G",
        "title": "ACME Cool Flames Investigation with Gases",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-159",
        "pillar": "Prevention",
        "rack": "CIR (ACME Modular Hardware)",
        "fuel_category": "Gaseous",
        "fuels": "Propane, n-Butane, n-Pentane (Spherical porous burner, normal & inverse inside-out flames)",
        "o2_min": 21.0, "o2_max": 85.0, "pressure_psi": 14.7, "airflow_max_cm_s": 5.0,
        "simulates_partial_g": 0,
        "core_summary": "Thí nghiệm có nồng độ Oxy cao nhất trên PSI (lên tới 85% O2 từ đầu đốt cầu tạo ngọn lửa đảo ngược inside-out), tạo ra ngọn lửa lạnh khuếch tán ổn định ở 500-1000 K."
    },
    {
        "psi_id": "PSI-10",
        "code": "ACME-FlameDesign",
        "title": "ACME Flame Design - Spherical Diffusion Flames",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-10",
        "pillar": "Prevention",
        "rack": "CIR (ACME Modular Hardware)",
        "fuel_category": "Gaseous",
        "fuels": "Ethylene, Methane spherical diffusion flames",
        "o2_min": 15.0, "o2_max": 40.0, "pressure_psi": 14.7, "airflow_max_cm_s": 0.0,
        "simulates_partial_g": 0,
        "core_summary": "Khảo sát sự hình thành bồ hóng (soot) và giới hạn tắt lửa do bức xạ nhiệt của ngọn lửa cầu trong buồng CIR."
    },
    {
        "psi_id": "PSI-107",
        "code": "SPICE",
        "title": "Smoke Point In Co-flow Experiment",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-107",
        "pillar": "Prevention",
        "rack": "MSG (SPICE Flow Duct)",
        "fuel_category": "Gaseous",
        "fuels": "Ethylene, Propane, Methane, Propylene in co-flowing air",
        "o2_min": 21.0, "o2_max": 21.0, "pressure_psi": 14.7, "airflow_max_cm_s": 40.0,
        "simulates_partial_g": 0,
        "core_summary": "Xác định điểm sinh khói (smoke point) khi ngọn lửa khí bắt đầu phát thải muội than trong ống gió quạt thuộc tủ MSG."
    },
    {
        "psi_id": "PSI-102",
        "code": "SAME",
        "title": "Smoke and Aerosol Measurement Experiment",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-102",
        "pillar": "Detection",
        "rack": "MSG",
        "fuel_category": "Smoke / Pyrolysis",
        "fuels": "Overheated spacecraft materials: Kapton, Teflon, Silicone, Cellulose, Lampwick",
        "o2_min": 21.0, "o2_max": 21.0, "pressure_psi": 14.7, "airflow_max_cm_s": 15.0,
        "simulates_partial_g": 0,
        "core_summary": "Chứng minh hạt khói trong vi trọng lực kết tụ thành kích thước lớn hơn so với 1g do thiếu đối lưu tự nhiên, làm thay đổi độ nhạy của đầu báo khói quang học và ion hóa."
    },
    {
        "psi_id": "PSI-101",
        "code": "SAME-R",
        "title": "Smoke Aerosol Measurement Experiment - Reflight",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-101",
        "pillar": "Detection",
        "rack": "MSG",
        "fuel_category": "Smoke / Pyrolysis",
        "fuels": "66 test points of pyrolyzed spacecraft wiring and insulation materials",
        "o2_min": 21.0, "o2_max": 21.0, "pressure_psi": 14.7, "airflow_max_cm_s": 20.0,
        "simulates_partial_g": 0,
        "core_summary": "Mở rộng dữ liệu phân bố kích thước hạt khói theo thời gian lão hóa (aging time) để hiệu chuẩn đầu báo cháy thế hệ mới cho tàu Orion và căn cứ Mặt Trăng."
    },
    {
        "psi_id": "PSI-69",
        "code": "FLEX",
        "title": "Flame Extinguishment Experiment",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-69",
        "pillar": "Suppression",
        "rack": "CIR (MDCA)",
        "fuel_category": "Liquid Droplet",
        "fuels": "Methanol, n-Heptane droplets (1.5 - 4.0 mm) with CO2, He, N2 diluents",
        "o2_min": 14.0, "o2_max": 30.0, "pressure_psi": 14.7, "airflow_max_cm_s": 10.0,
        "simulates_partial_g": 0,
        "core_summary": "Gồm 275 lần đốt giọt nhiên liệu lỏng trong thiết bị MDCA (tủ CIR) nhằm đo nồng độ CO2 và Helium tối thiểu để dập tắt lửa trong không gian."
    },
    {
        "psi_id": "PSI-68",
        "code": "FLEX-2",
        "title": "Flame Extinguishment Experiment - 2 & Cool Flames (CFI)",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-68",
        "pillar": "Suppression",
        "rack": "CIR (MDCA)",
        "fuel_category": "Liquid Droplet",
        "fuels": "n-Heptane, n-Octane, n-Decane, Iso-octane droplets & arrays",
        "o2_min": 15.0, "o2_max": 30.0, "pressure_psi": 14.7, "airflow_max_cm_s": 15.0,
        "simulates_partial_g": 0,
        "core_summary": "Phát hiện hiện tượng giọt nhiên liệu sau khi tắt lửa nóng vẫn tiếp tục cháy âm ỉ ở chế độ Ngọn lửa lạnh (Cool Flame) vô hình và có thể tự bùng cháy lại."
    },
    {
        "psi_id": "PSI-142",
        "code": "Cool-Flames-Model",
        "title": "Quantitative Studies of Cool Flame Transitions (FLEX Derivative)",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-142",
        "pillar": "Suppression",
        "rack": "CIR (MDCA) / Ground Counterflow",
        "fuel_category": "Liquid Droplet",
        "fuels": "Higher n-alkanes and multicomponent fuels",
        "o2_min": 15.0, "o2_max": 30.0, "pressure_psi": 14.7, "airflow_max_cm_s": 15.0,
        "simulates_partial_g": 0,
        "core_summary": "Tổng hợp dữ liệu chuyển tiếp giữa ngọn lửa nóng và ngọn lửa lạnh phục vụ mô hình hóa dự báo cháy lại sau khi phun chất chữa cháy."
    },
    {
        "psi_id": "ACME-BRE",
        "code": "ACME-BRE",
        "title": "Burning Rate Emulator (ACME Project)",
        "url": "https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/",
        "pillar": "Prevention",
        "rack": "CIR (ACME Modular Hardware)",
        "fuel_category": "Gaseous (Simulating Solid/Liquid)",
        "fuels": "Ethylene/Methane doped with N2/CO2 simulating PMMA, Delrin, paper, alcohols",
        "o2_min": 17.0, "o2_max": 35.0, "pressure_psi": 14.7, "airflow_max_cm_s": 0.0,
        "simulates_partial_g": 0,
        "core_summary": "Dùng đầu đốt khí phẳng bằng đồng xốp trong buồng CIR để giả lập tốc độ hóa hơi và khả năng cháy của vật liệu rắn/lỏng trong môi trường tĩnh (still atmosphere)."
    },
    {
        "psi_id": "ACME-E-FIELD",
        "code": "ACME-E-FIELD",
        "title": "Electric-Field Effects on Laminar Diffusion Flames",
        "url": "https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/",
        "pillar": "Prevention (Partial-G Proxy)",
        "rack": "CIR (ACME Modular Hardware)",
        "fuel_category": "Gaseous",
        "fuels": "Methane/Ethylene flames under high-voltage electric field (up to 10 kV)",
        "o2_min": 18.0, "o2_max": 30.0, "pressure_psi": 14.7, "airflow_max_cm_s": 15.0,
        "simulates_partial_g": 1,
        "core_summary": "GIẢ LẬP TRỌNG LỰC MẶT TRĂNG & SAO HỎA: Dùng lực điện trường đẩy các ion tự nhiên trong ngọn lửa để tái tạo hiệu ứng đối lưu nổi tương đương trọng lực từng phần (0.16g - 0.38g)."
    },
    {
        "psi_id": "MSG-SLICE",
        "code": "SLICE",
        "title": "Structure & Liftoff In Combustion Experiment",
        "url": "https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/",
        "pillar": "Prevention",
        "rack": "MSG (SPICE Flow Duct)",
        "fuel_category": "Gaseous",
        "fuels": "Methane co-flow laminar jet flames",
        "o2_min": 15.0, "o2_max": 21.0, "pressure_psi": 14.7, "airflow_max_cm_s": 35.0,
        "simulates_partial_g": 0,
        "core_summary": "Dùng chung ống gió quạt SPICE với BASS trong tủ MSG để đo cấu trúc chân ngọn lửa và hiện tượng nhấc lửa (liftoff) cho tới khi bị thổi tắt."
    },
    {
        "psi_id": "MSG-DAFT",
        "code": "DAFT & DAFT-2",
        "title": "Dust and Aerosol Measurement Feasibility Test",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-102",
        "pillar": "Detection",
        "rack": "MSG (Shared Instrument with SAME)",
        "fuel_category": "Dust / Aerosol",
        "fuels": "Cabin dust & Lunar regolith simulant aerosols",
        "o2_min": 21.0, "o2_max": 21.0, "pressure_psi": 14.7, "airflow_max_cm_s": 10.0,
        "simulates_partial_g": 0,
        "core_summary": "Dùng chung máy đo hạt của thí nghiệm khói SAME/SAME-R để đo đặc trưng bụi lơ lửng, giúp thiết kế đầu báo cháy phân biệt khói thật và bụi Mặt Trăng (tránh báo động giả như trên Artemis II)."
    },
    {
        "psi_id": "FUTURE-LUCI-FM2",
        "code": "LUCI & FM2 (Upcoming)",
        "title": "Lunar-g Combustion Investigation (LUCI) & Flammability of Materials on the Moon (FM2)",
        "url": "https://science.nasa.gov/biological-physical/focus-areas/combustion-science/",
        "pillar": "Prevention (Partial-G)",
        "rack": "Future Lunar Surface / Habitat Payloads",
        "fuel_category": "Solid",
        "fuels": "Spacecraft & Moon Base fabrics/polymers at >=30% O2, <=10.2 psi, 0.16g",
        "o2_min": 30.0, "o2_max": 100.0, "pressure_psi": 10.2, "airflow_max_cm_s": 20.0,
        "simulates_partial_g": 1,
        "core_summary": "[DATA GAP TRÊN PSI]: Hiện chưa có dữ liệu cháy ở trọng lực từng phần (0.16g Mặt Trăng) trên PSI. Cần dùng kết quả 0g (BASS-II, Saffire-III, CFI-G) kết hợp 1g và giả lập điện trường E-FIELD để nội suy giới hạn an toàn."
    }
]

# 2. DANH SÁCH BÀI VIẾT LỊCH SỬ & SPINOFF TRONG TAB RESOURCES
WEB_RESOURCES = [
    {
        "id": "RES_APOLLO_1", "title": "Apollo 1 Pre-Launch Cabin Fire (100% O2 Hazard)",
        "url": "https://sma.nasa.gov/sma-disciplines/accllp/apollo-1",
        "linked_codes": ["BASS-II", "SAFFIRE-III", "ACME-CFI-G"]
    },
    {
        "id": "RES_APOLLO_13", "title": "Apollo 13 Oxygen Tank Explosion",
        "url": "https://sma.nasa.gov/sma-disciplines/accllp/apollo-13",
        "linked_codes": ["BASS-II", "ACME-CFI-G"]
    },
    {
        "id": "RES_MIR_FIRE", "title": "25 Years Ago: Fire Aboard Space Station Mir",
        "url": "https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/",
        "linked_codes": ["SAME", "FLEX", "SAFFIRE-I"]
    },
    {
        "id": "RES_SPINOFF_DETECTOR", "title": "NASA Spinoff: Fire Detector (Smoke vs Dust Discrimination)",
        "url": "https://spinoff.nasa.gov/node/9682",
        "linked_codes": ["SAME", "SAME-R", "DAFT & DAFT-2"]
    },
    {
        "id": "RES_SPINOFF_AIR_TANKS", "title": "NASA Spinoff: Fireman's Air Tanks",
        "url": "https://spinoff.nasa.gov/node/9582",
        "linked_codes": ["FLEX", "BASS-II"]
    },
    {
        "id": "RES_SPINOFF_FIRE_ATTIRE", "title": "NASA Spinoff: New Technology for the Fire Attire",
        "url": "https://spinoff.nasa.gov/node/9918",
        "linked_codes": ["BASS-II", "SAFFIRE-II"]
    }
]


def sanitize_folder_name(name: str) -> str:
    """Làm sạch tên thư mục trên Windows."""
    return re.sub(r'[\\/*?:"<>| &()]+', "_", name).strip("_")


def build_all_data() -> None:
    os.makedirs(BASE_DIR, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (NASA-SpaceApps-SI-Dashboard)"}
    rag_chunks = []

    # BƯỚC 1: Tải cuốn PDF 56 trang vào thư mục chủ đề 00_ISS_Reference_Guide
    guide_dir = os.path.join(BASE_DIR, "00_ISS_Reference_Guide")
    os.makedirs(guide_dir, exist_ok=True)
    pdf_path = os.path.join(guide_dir, "ISS_Combustion_Researcher_Guide.pdf")

    if not os.path.exists(pdf_path):
        print("[1/4] Đang tải cuốn PDF 56 trang A Researcher's Guide to ISS Combustion Science...")
        try:
            r = requests.get(PDF_GUIDE_URL, headers=headers, timeout=60)
            r.raise_for_status()
            with open(pdf_path, "wb") as f:
                f.write(r.content)
            print(f"  -> Đã lưu tại: {pdf_path}")
        except Exception as e:
            print(f"  [!] Không tải được PDF: {e}")
    else:
        print(f"[1/4] Đã có sẵn PDF tại: {pdf_path}")

    # BƯỚC 2: Phân loại 18 thí nghiệm vào các thư mục chủ đề (01 đến 04) và cào dữ liệu
    print("[2/4] Đang phân chia thư mục chủ đề và lấy chi tiết 18 thí nghiệm cháy từ NASA PSI...")
    for inv in PSI_INVESTIGATIONS:
        topic_folder = PILLAR_FOLDERS.get(inv["pillar"], "01_Prevention")
        safe_code = sanitize_folder_name(inv["code"])
        exp_dir = os.path.join(BASE_DIR, topic_folder, safe_code)
        os.makedirs(exp_dir, exist_ok=True)

        # Lưu thông số gốc ra tệp CSV trong từng thư mục thí nghiệm
        pd.DataFrame([inv]).to_csv(
            os.path.join(exp_dir, f"{safe_code}_metadata.csv"),
            index=False,
            encoding="utf-8-sig"
        )

        base_text = (
            f"Thí nghiệm {inv['code']} ({inv['psi_id']} - {inv['title']}): "
            f"Nhóm an toàn: {inv['pillar']}. Phần cứng: {inv['rack']}. "
            f"Nhiên liệu: {inv['fuels']}. Dải Oxy: {inv['o2_min']}% đến {inv['o2_max']}%. "
            f"Áp suất điển hình: {inv['pressure_psi']} psi. Tốc độ gió tối đa: {inv['airflow_max_cm_s']} cm/s. "
            f"Kết quả cốt lõi: {inv['core_summary']}"
        )
        rag_chunks.append({
            "chunk_id": f"{inv['psi_id']}_CORE_SUMMARY",
            "investigation_id": inv["code"],
            "psi_id": inv["psi_id"],
            "topic_folder": topic_folder,
            "chunk_type": "psi_investigation_summary",
            "source_pdf": inv["url"],
            "page": 1,
            "image_url": "",
            "text": base_text
        })

        exp_text_blocks = [base_text]

        # Nếu là link trang PSI-XX trực tiếp, cào thêm nội dung web
        if "psi.nasa.gov/physci/repo/data/investigations/" in inv["url"]:
            try:
                res = requests.get(inv["url"], headers=headers, timeout=20)
                res.raise_for_status()
                soup = BeautifulSoup(res.text, "html.parser")
                clean_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
                if clean_text:
                    exp_text_blocks.append(f"\n--- CHI TIẾT TRANG WEB PSI ({inv['url']}) ---\n{clean_text[:6000]}")
                for idx in range(0, min(len(clean_text), 6000), 900):
                    segment = clean_text[idx:idx + 900]
                    rag_chunks.append({
                        "chunk_id": f"{inv['psi_id']}_WEB_c{idx//900}",
                        "investigation_id": inv["code"],
                        "psi_id": inv["psi_id"],
                        "topic_folder": topic_folder,
                        "chunk_type": "psi_detailed_page",
                        "source_pdf": f"{inv['psi_id']} ({inv['code']}) on psi.nasa.gov",
                        "page": 1,
                        "image_url": "",
                        "text": f"[{inv['psi_id']} - {inv['title']}]: {segment}"
                    })
                print(f"  -> Đã lưu [{topic_folder}\\{safe_code}] ({inv['psi_id']})")
            except Exception as e:
                print(f"  [!] Lỗi khi truy cập {inv['url']}: {e}")

        # Ghi tệp văn bản tổng hợp của thí nghiệm vào đúng thư mục chủ đề
        with open(os.path.join(exp_dir, f"{safe_code}_overview.txt"), "w", encoding="utf-8") as f:
            f.write("\n\n".join(exp_text_blocks))

    # BƯỚC 3: Cào 6 trang Lịch sử & Ứng dụng Trái Đất lưu vào 05_Historical_And_Spinoffs
    print("[3/4] Đang lấy nội dung Lịch sử & Ứng dụng Trái Đất (NASA Spinoffs)...")
    spinoff_dir = os.path.join(BASE_DIR, "05_Historical_And_Spinoffs")
    os.makedirs(spinoff_dir, exist_ok=True)

    for item in WEB_RESOURCES:
        try:
            res = requests.get(item["url"], headers=headers, timeout=20)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            paragraphs = [
                p.get_text(" ", strip=True)
                for p in soup.find_all("p")
                if len(p.get_text(strip=True)) > 60
            ]
            full_text = "\n".join(paragraphs)

            # Lưu tệp .txt riêng cho từng bài viết trong 05_Historical_And_Spinoffs
            spinoff_file = os.path.join(spinoff_dir, f"{item['id']}.txt")
            with open(spinoff_file, "w", encoding="utf-8") as f:
                f.write(f"TITLE: {item['title']}\nURL: {item['url']}\nLINKED: {', '.join(item['linked_codes'])}\n\n{full_text}")

            for idx in range(0, len(full_text), 800):
                segment = full_text[idx:idx + 800]
                for code in item["linked_codes"]:
                    rag_chunks.append({
                        "chunk_id": f"{item['id']}_{code}_c{idx//800}",
                        "investigation_id": code,
                        "psi_id": item["id"],
                        "topic_folder": "05_Historical_And_Spinoffs",
                        "chunk_type": "historical_and_spinoff_context",
                        "source_pdf": item["title"],
                        "page": 1,
                        "image_url": "",
                        "text": f"[{item['title']} - {item['url']}]: {segment}"
                    })
            print(f"  -> Đã lưu [05_Historical_And_Spinoffs\\{item['id']}.txt]")
        except Exception as e:
            print(f"  [!] Lỗi khi lấy {item['url']}: {e}")

    # Lưu toàn bộ RAG Chunks ra JSON tại gốc 03_Datasets_NASA
    rag_json_path = os.path.join(BASE_DIR, "rag_chunks_complete.json")
    with open(rag_json_path, "w", encoding="utf-8") as f:
        json.dump(rag_chunks, f, indent=2, ensure_ascii=False)

    # BƯỚC 4: Tạo SQLite Database (psi_structured.db) tại gốc 03_Datasets_NASA
    print("[4/4] Đang khởi tạo cơ sở dữ liệu định lượng psi_structured.db...")
    db_path = os.path.join(BASE_DIR, "psi_structured.db")
    conn = sqlite3.connect(db_path)
    pd.DataFrame(PSI_INVESTIGATIONS).to_sql("investigations_catalog", conn, if_exists="replace", index=False)
    conn.close()

    print(f"\n[+] HOÀN TẤT! Đã tạo {len(rag_chunks)} chunks tại '{rag_json_path}' và lưu DB tại '{db_path}'!")


if __name__ == "__main__":
    build_all_data()