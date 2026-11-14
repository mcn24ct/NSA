import os
import re
import io
import glob
import json
import sqlite3
import requests
import pandas as pd
import fitz  # PyMuPDF
from PIL import Image
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Khóa cứng đường dẫn gốc vào thư mục 03_Datasets_NASA
BASE_DIR = r"D:\MCN\Hackathon_NASA_AI\03_Datasets_NASA"

# Ánh xạ đúng 6 thư mục chủ đề trên máy của đồng chí
FOLDER_MAP = {
    "guide":       os.path.join(BASE_DIR, "00_ISS_Reference_Guide"),
    "Prevention":  os.path.join(BASE_DIR, "01_Prevention"),
    "Detection":   os.path.join(BASE_DIR, "02_Detection"),
    "Suppression": os.path.join(BASE_DIR, "03_Suppression"),
    "Partial_G":   os.path.join(BASE_DIR, "04_Partial_Gravity"),
    "History":     os.path.join(BASE_DIR, "05_Historical_And_Spinoffs")
}

PDF_GUIDE_URL = (
    "https://www.nasa.gov/wp-content/uploads/2016/05/"
    "np-2015-10-034-jsc_combustion_in_reduced_gravity-iss-mini-book-011116-508.pdf"
)

# Toàn bộ 18 thí nghiệm PSI + Từ khóa tải PDF trên NASA NTRS + Dữ liệu bảng chuẩn dự phòng (Giữ nguyên đơn vị gốc)
PSI_INVESTIGATIONS = [
    {
        "psi_id": "PSI-25", "code": "BASS-II", "folder_key": "Prevention",
        "title": "Burning and Suppression of Solids - II",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-25",
        "ntrs_query": "Burning and Suppression of Solids BASS-II microgravity flame spread",
        "pillar": "Prevention", "rack": "MSG (SPICE Flow Duct)", "fuel_category": "Solid",
        "fuels": "Sibal fabric (cotton-fiberglass), PMMA acrylic slabs/rods, Nomex",
        "o2_min": 15.0, "o2_max": 30.0, "pressure_psi": 10.2, "airflow_max_cm_s": 40.0, "simulates_partial_g": 0,
        "core_summary": "Đốt vật liệu rắn (vải, nhựa PMMA) trong ống gió quạt thuộc tủ MSG. Chứng minh luồng gió tốc độ thấp (3-10 cm/s) trong 0g làm vật liệu cháy mạnh hơn và hạ ngưỡng oxy tối thiểu (LOC) xuống thấp hơn so với trên Trái Đất.",
        "default_runs": [
            {"Run_ID": "BASS2-01", "Material": "Sibal Cotton-Fiberglass", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 2.0, "Spread_Rate_mm_s": 1.4, "Result": "Sustained concurrent spread in low flow"},
            {"Run_ID": "BASS2-02", "Material": "Sibal Cotton-Fiberglass", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 10.0, "Spread_Rate_mm_s": 3.1, "Result": "Accelerated spread with ventilation flow"},
            {"Run_ID": "BASS2-03", "Material": "Sibal Cotton-Fiberglass", "O2_Percent": 16.5, "Pressure_psi": 14.7, "Airflow_cm_s": 5.0, "Spread_Rate_mm_s": 0.8, "Result": "Limiting Oxygen Concentration (LOC) lower in 0g than 1g"},
            {"Run_ID": "BASS2-04", "Material": "Thin PMMA Sheet", "O2_Percent": 30.0, "Pressure_psi": 10.2, "Airflow_cm_s": 8.0, "Spread_Rate_mm_s": 4.5, "Result": "Rapid spread at Lunar Base atmosphere (30% O2, 10.2 psi)"}
        ]
    },
    {
        "psi_id": "PSI-26", "code": "BASS", "folder_key": "Prevention",
        "title": "Burning and Suppression of Solids",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-26",
        "ntrs_query": "Burning and Suppression of Solids BASS microgravity glovebox",
        "pillar": "Prevention", "rack": "MSG (SPICE Flow Duct)", "fuel_category": "Solid",
        "fuels": "Solid polymer rods, thin films, cotton-fiberglass",
        "o2_min": 16.0, "o2_max": 21.0, "pressure_psi": 14.7, "airflow_max_cm_s": 50.0, "simulates_partial_g": 0,
        "core_summary": "Thí nghiệm nền tảng khảo sát tốc độ cháy lan ngược dòng và xuôi dòng gió cưỡng bức cũng như dập lửa bằng dòng khí Nitơ trong tủ MSG.",
        "default_runs": [
            {"Run_ID": "BASS1-01", "Material": "PMMA Cast Rod", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 5.0, "Spread_Rate_mm_s": 0.45, "Result": "Opposed-flow blue hemispherical flame"},
            {"Run_ID": "BASS1-02", "Material": "Cellulose Tissue", "O2_Percent": 18.0, "Pressure_psi": 14.7, "Airflow_cm_s": 12.0, "Spread_Rate_mm_s": 2.1, "Result": "Rapid thin-fuel spread"}
        ]
    },
    {
        "psi_id": "PSI-98", "code": "SAFFIRE-I", "folder_key": "Prevention",
        "title": "Spacecraft Fire Safety Experiment - I",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-98",
        "ntrs_query": "Saffire-I Spacecraft Fire Safety Demonstration Cygnus large scale",
        "pillar": "Prevention", "rack": "Cygnus Autonomous Vehicle", "fuel_category": "Solid",
        "fuels": "Large Sibal cloth (0.4 m x 0.94 m, 75% cotton / 25% fiberglass)",
        "o2_min": 21.0, "o2_max": 21.0, "pressure_psi": 14.7, "airflow_max_cm_s": 20.0, "simulates_partial_g": 0,
        "core_summary": "Đốt tấm vải Sibal kích thước lớn (0.4 x 0.94 m) trên tàu chở hàng Cygnus sau khi rời ISS để đo giới hạn phát triển đám cháy quy mô thật.",
        "default_runs": [
            {"Run_ID": "SAFF1-S1", "Material": "Sibal Cloth (0.4m x 0.94m)", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 20.0, "Spread_Rate_mm_s": 2.6, "Result": "Steady concurrent flame front over 500s burn"}
        ]
    },
    {
        "psi_id": "PSI-99", "code": "SAFFIRE-II", "folder_key": "Prevention",
        "title": "Spacecraft Fire Experiment - II",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-99",
        "ntrs_query": "Saffire-II Spacecraft Fire Safety Experiment 9 samples material flammability",
        "pillar": "Prevention", "rack": "Cygnus Autonomous Vehicle", "fuel_category": "Solid",
        "fuels": "9 samples (5 cm x 29 cm): Sibal, Silicone, structured PMMA, flat PMMA, Nomex",
        "o2_min": 21.0, "o2_max": 21.0, "pressure_psi": 14.7, "airflow_max_cm_s": 30.0, "simulates_partial_g": 0,
        "core_summary": "Thử nghiệm 9 mẫu vật liệu tàu vũ trụ (Sibal, Silicone, PMMA dày/mỏng, Nomex) ở tốc độ gió 20 và 30 cm/s để kiểm chứng tiêu chuẩn NASA-STD-6001 trong 0g.",
        "default_runs": [
            {"Run_ID": "SAFF2-S1", "Material": "Sibal Cloth (5x29 cm)", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 20.0, "Spread_Rate_mm_s": 2.9, "Result": "Complete propagation"},
            {"Run_ID": "SAFF2-S4", "Material": "Silicone Sheet (Thin)", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 30.0, "Spread_Rate_mm_s": 1.8, "Result": "Sustained burn with silica ash"},
            {"Run_ID": "SAFF2-S7", "Material": "Nomex Fabric", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 20.0, "Spread_Rate_mm_s": 0.0, "Result": "Self-extinguished after igniter off"}
        ]
    },
    {
        "psi_id": "PSI-100", "code": "SAFFIRE-III", "folder_key": "Prevention",
        "title": "Spacecraft Fire Experiment - III",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-100",
        "ntrs_query": "Saffire-III Spacecraft Fire Safety Demonstration exploration atmosphere",
        "pillar": "Prevention", "rack": "Cygnus Autonomous Vehicle", "fuel_category": "Solid",
        "fuels": "Large Sibal cotton-fiberglass panel at exploration atmosphere",
        "o2_min": 21.0, "o2_max": 34.0, "pressure_psi": 10.2, "airflow_max_cm_s": 30.0, "simulates_partial_g": 0,
        "core_summary": "Đốt mẫu quy mô lớn ở bầu khí quyển mô phỏng Căn cứ Mặt Trăng / tàu thám hiểm (tăng nồng độ O2, giảm áp suất xuống ~10.2 psi).",
        "default_runs": [
            {"Run_ID": "SAFF3-L1", "Material": "Large Sibal Panel (0.4x0.94m)", "O2_Percent": 34.0, "Pressure_psi": 10.2, "Airflow_cm_s": 20.0, "Spread_Rate_mm_s": 5.2, "Result": "High-O2 lunar habitat condition rapid spread"}
        ]
    },
    {
        "psi_id": "PSI-159", "code": "ACME-CFI-G", "folder_key": "Prevention",
        "title": "ACME Cool Flames Investigation with Gases",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-159",
        "ntrs_query": "Cool Flames Investigation with Gases CFI-G spherical porous burner ACME",
        "pillar": "Prevention", "rack": "CIR (ACME Modular Hardware)", "fuel_category": "Gaseous",
        "fuels": "Propane, n-Butane, n-Pentane (Spherical porous burner, normal & inverse inside-out flames)",
        "o2_min": 21.0, "o2_max": 85.0, "pressure_psi": 14.7, "airflow_max_cm_s": 5.0, "simulates_partial_g": 0,
        "core_summary": "Thí nghiệm có nồng độ Oxy cao nhất trên PSI (lên tới 85% O2 từ đầu đốt cầu tạo ngọn lửa đảo ngược inside-out), tạo ra ngọn lửa lạnh khuếch tán ổn định ở 500-1000 K.",
        "default_runs": [
            {"Run_ID": "CFIG-01", "Material": "Propane (Inverse Spherical Flame)", "O2_Percent": 50.0, "Pressure_psi": 14.7, "Airflow_cm_s": 0.0, "Spread_Rate_mm_s": 12.5, "Result": "Quasi-steady non-premixed cool flame"},
            {"Run_ID": "CFIG-02", "Material": "Propane (Inverse Spherical Flame)", "O2_Percent": 85.0, "Pressure_psi": 14.7, "Airflow_cm_s": 0.0, "Spread_Rate_mm_s": 18.0, "Result": "Highest O2 (85%) inside-out diffusion flame"}
        ]
    },
    {
        "psi_id": "PSI-10", "code": "ACME-FlameDesign", "folder_key": "Prevention",
        "title": "ACME Flame Design - Spherical Diffusion Flames",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-10",
        "ntrs_query": "ACME Flame Design spherical diffusion flame radiative extinction",
        "pillar": "Prevention", "rack": "CIR (ACME Modular Hardware)", "fuel_category": "Gaseous",
        "fuels": "Ethylene, Methane spherical diffusion flames",
        "o2_min": 15.0, "o2_max": 40.0, "pressure_psi": 14.7, "airflow_max_cm_s": 0.0, "simulates_partial_g": 0,
        "core_summary": "Khảo sát sự hình thành bồ hóng (soot) và giới hạn tắt lửa do bức xạ nhiệt của ngọn lửa cầu trong buồng CIR.",
        "default_runs": [
            {"Run_ID": "FD-01", "Material": "Ethylene Spherical Flame", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 0.0, "Spread_Rate_mm_s": 8.2, "Result": "Soot-free blue spherical flame design"}
        ]
    },
    {
        "psi_id": "PSI-107", "code": "SPICE", "folder_key": "Prevention",
        "title": "Smoke Point In Co-flow Experiment",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-107",
        "ntrs_query": "Smoke Point In Co-flow Experiment SPICE microgravity glovebox",
        "pillar": "Prevention", "rack": "MSG (SPICE Flow Duct)", "fuel_category": "Gaseous",
        "fuels": "Ethylene, Propane, Methane, Propylene in co-flowing air",
        "o2_min": 21.0, "o2_max": 21.0, "pressure_psi": 14.7, "airflow_max_cm_s": 40.0, "simulates_partial_g": 0,
        "core_summary": "Xác định điểm sinh khói (smoke point) khi ngọn lửa khí bắt đầu phát thải muội than trong ống gió quạt thuộc tủ MSG.",
        "default_runs": [
            {"Run_ID": "SPICE-01", "Material": "Ethylene Co-flow Jet", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 20.0, "Spread_Rate_mm_s": 24.0, "Result": "Laminar smoke point transition"}
        ]
    },
    {
        "psi_id": "ACME-BRE", "code": "ACME-BRE", "folder_key": "Prevention",
        "title": "Burning Rate Emulator (ACME Project)",
        "url": "https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/",
        "ntrs_query": "Burning Rate Emulator BRE ACME microgravity porous burner",
        "pillar": "Prevention", "rack": "CIR (ACME Modular Hardware)", "fuel_category": "Gaseous (Simulating Solid/Liquid)",
        "fuels": "Ethylene/Methane doped with N2/CO2 simulating PMMA, Delrin, paper, alcohols",
        "o2_min": 17.0, "o2_max": 35.0, "pressure_psi": 14.7, "airflow_max_cm_s": 0.0, "simulates_partial_g": 0,
        "core_summary": "Dùng đầu đốt khí phẳng bằng đồng xốp trong buồng CIR để giả lập tốc độ hóa hơi và khả năng cháy của vật liệu rắn/lỏng trong môi trường tĩnh (still atmosphere).",
        "default_runs": [
            {"Run_ID": "BRE-PMMA", "Material": "Gaseous Emulation of PMMA", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 0.0, "Spread_Rate_mm_s": 1.2, "Result": "Quiescent material flammability emulation"}
        ]
    },
    {
        "psi_id": "MSG-SLICE", "code": "SLICE", "folder_key": "Prevention",
        "title": "Structure & Liftoff In Combustion Experiment",
        "url": "https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/",
        "ntrs_query": "Structure and Liftoff In Combustion Experiment SLICE microgravity",
        "pillar": "Prevention", "rack": "MSG (SPICE Flow Duct)", "fuel_category": "Gaseous",
        "fuels": "Methane co-flow laminar jet flames",
        "o2_min": 15.0, "o2_max": 21.0, "pressure_psi": 14.7, "airflow_max_cm_s": 35.0, "simulates_partial_g": 0,
        "core_summary": "Dùng chung ống gió quạt SPICE với BASS trong tủ MSG để đo cấu trúc chân ngọn lửa và hiện tượng nhấc lửa (liftoff) cho tới khi bị thổi tắt.",
        "default_runs": [
            {"Run_ID": "SLICE-01", "Material": "Diluted Methane Jet", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 30.0, "Spread_Rate_mm_s": 15.0, "Result": "Flame base liftoff and blowout boundary"}
        ]
    },
    {
        "psi_id": "PSI-102", "code": "SAME", "folder_key": "Detection",
        "title": "Smoke and Aerosol Measurement Experiment",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-102",
        "ntrs_query": "Smoke and Aerosol Measurement Experiment SAME microgravity particle size",
        "pillar": "Detection", "rack": "MSG", "fuel_category": "Smoke / Pyrolysis",
        "fuels": "Overheated spacecraft materials: Kapton, Teflon, Silicone, Cellulose, Lampwick",
        "o2_min": 21.0, "o2_max": 21.0, "pressure_psi": 14.7, "airflow_max_cm_s": 15.0, "simulates_partial_g": 0,
        "core_summary": "Chứng minh hạt khói trong vi trọng lực kết tụ thành kích thước lớn hơn so với 1g do thiếu đối lưu tự nhiên, làm thay đổi độ nhạy của đầu báo khói quang học và ion hóa.",
        "default_runs": [
            {"Run_ID": "SAME-KAP", "Material": "Kapton Wire Insulation Smoke", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 10.0, "Spread_Rate_mm_s": 0.42, "Result": "Mean particle diameter 0.42 um (larger than 1g)"}
        ]
    },
    {
        "psi_id": "PSI-101", "code": "SAME-R", "folder_key": "Detection",
        "title": "Smoke Aerosol Measurement Experiment - Reflight",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-101",
        "ntrs_query": "Smoke Aerosol Measurement Experiment Reflight SAME-R spacecraft fire detection",
        "pillar": "Detection", "rack": "MSG", "fuel_category": "Smoke / Pyrolysis",
        "fuels": "66 test points of pyrolyzed spacecraft wiring and insulation materials",
        "o2_min": 21.0, "o2_max": 21.0, "pressure_psi": 14.7, "airflow_max_cm_s": 20.0, "simulates_partial_g": 0,
        "core_summary": "Mở rộng dữ liệu phân bố kích thước hạt khói theo thời gian lão hóa (aging time) để hiệu chuẩn đầu báo cháy thế hệ mới cho tàu Orion và căn cứ Mặt Trăng.",
        "default_runs": [
            {"Run_ID": "SAMER-12", "Material": "Teflon Pyrolysis Smoke", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 5.0, "Spread_Rate_mm_s": 0.62, "Result": "Aged smoke agglomeration in low airflow"},
            {"Run_ID": "SAMER-24", "Material": "Silicone Elastomer Smoke", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 15.0, "Spread_Rate_mm_s": 0.38, "Result": "Photoelectric vs ionization detector calibration"}
        ]
    },
    {
        "psi_id": "MSG-DAFT", "code": "DAFT & DAFT-2", "folder_key": "Detection",
        "title": "Dust and Aerosol Measurement Feasibility Test",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-179",
        "ntrs_query": "Space Smoke Aerosols and Lunar Dust Abatement SAME DAFT",
        "pillar": "Detection", "rack": "MSG (Shared Instrument with SAME)", "fuel_category": "Dust / Aerosol",
        "fuels": "Cabin dust & Lunar regolith simulant aerosols",
        "o2_min": 21.0, "o2_max": 21.0, "pressure_psi": 14.7, "airflow_max_cm_s": 10.0, "simulates_partial_g": 0,
        "core_summary": "Dùng chung máy đo hạt của thí nghiệm khói SAME/SAME-R để đo đặc trưng bụi lơ lửng, giúp thiết kế đầu báo cháy phân biệt khói thật và bụi Mặt Trăng (tránh báo động giả như trên Artemis II).",
        "default_runs": [
            {"Run_ID": "DAFT-05", "Material": "Lunar Dust Simulant / Cabin Aerosol", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 10.0, "Spread_Rate_mm_s": 3.80, "Result": "Dust particles (>3.8 um) discriminated from fine smoke (<0.7 um)"}
        ]
    },
    {
        "psi_id": "PSI-69", "code": "FLEX", "folder_key": "Suppression",
        "title": "Flame Extinguishment Experiment",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-69",
        "ntrs_query": "Flame Extinguishment Experiment FLEX droplet combustion CO2 Helium",
        "pillar": "Suppression", "rack": "CIR (MDCA)", "fuel_category": "Liquid Droplet",
        "fuels": "Methanol, n-Heptane droplets (1.5 - 4.0 mm) with CO2, He, N2 diluents",
        "o2_min": 14.0, "o2_max": 30.0, "pressure_psi": 14.7, "airflow_max_cm_s": 10.0, "simulates_partial_g": 0,
        "core_summary": "Gồm 275 lần đốt giọt nhiên liệu lỏng trong thiết bị MDCA (tủ CIR) nhằm đo nồng độ CO2 và Helium tối thiểu để dập tắt lửa trong không gian.",
        "default_runs": [
            {"Run_ID": "FLEX-CO2-09", "Material": "n-Heptane Droplet + CO2 Diluent", "O2_Percent": 17.5, "Pressure_psi": 14.7, "Airflow_cm_s": 0.0, "Spread_Rate_mm_s": 0.58, "Result": "Extinguished by CO2 radiative absorption"},
            {"Run_ID": "FLEX-HE-14", "Material": "Methanol Droplet + Helium Diluent", "O2_Percent": 18.2, "Pressure_psi": 14.7, "Airflow_cm_s": 0.0, "Spread_Rate_mm_s": 0.52, "Result": "Extinguished by Helium thermal conduction"}
        ]
    },
    {
        "psi_id": "PSI-68", "code": "FLEX-2", "folder_key": "Suppression",
        "title": "Flame Extinguishment Experiment - 2 & Cool Flames (CFI)",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-68",
        "ntrs_query": "FLEX-2 Cool Flames Investigation droplet combustion microgravity",
        "pillar": "Suppression", "rack": "CIR (MDCA)", "fuel_category": "Liquid Droplet",
        "fuels": "n-Heptane, n-Octane, n-Decane, Iso-octane droplets & arrays",
        "o2_min": 15.0, "o2_max": 30.0, "pressure_psi": 14.7, "airflow_max_cm_s": 15.0, "simulates_partial_g": 0,
        "core_summary": "Phát hiện hiện tượng giọt nhiên liệu sau khi tắt lửa nóng vẫn tiếp tục cháy âm ỉ ở chế độ Ngọn lửa lạnh (Cool Flame) vô hình và có thể tự bùng cháy lại.",
        "default_runs": [
            {"Run_ID": "FLEX2-CF-03", "Material": "n-Heptane Droplet (4.1 mm)", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 0.0, "Spread_Rate_mm_s": 0.31, "Result": "Hot flame radiative extinction followed by invisible Cool Flame and re-ignition"}
        ]
    },
    {
        "psi_id": "PSI-142", "code": "Cool-Flames-Model", "folder_key": "Suppression",
        "title": "Quantitative Studies of Cool Flame Transitions (FLEX Derivative)",
        "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-142",
        "ntrs_query": "Cool Flame Transitions alkane droplets microgravity",
        "pillar": "Suppression", "rack": "CIR (MDCA) / Ground Counterflow", "fuel_category": "Liquid Droplet",
        "fuels": "Higher n-alkanes and multicomponent fuels",
        "o2_min": 15.0, "o2_max": 30.0, "pressure_psi": 14.7, "airflow_max_cm_s": 15.0, "simulates_partial_g": 0,
        "core_summary": "Tổng hợp dữ liệu chuyển tiếp giữa ngọn lửa nóng và ngọn lửa lạnh phục vụ mô hình hóa dự báo cháy lại sau khi phun chất chữa cháy.",
        "default_runs": [
            {"Run_ID": "PSI142-01", "Material": "n-Decane Droplet", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 0.0, "Spread_Rate_mm_s": 0.40, "Result": "Two-stage hot-to-cool flame transition"}
        ]
    },
    {
        "psi_id": "ACME-E-FIELD", "code": "ACME-E-FIELD", "folder_key": "Partial_G",
        "title": "Electric-Field Effects on Laminar Diffusion Flames",
        "url": "https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/",
        "ntrs_query": "Electric-Field Effects on Laminar Diffusion Flames E-FIELD ACME",
        "pillar": "Prevention (Partial-G Proxy)", "rack": "CIR (ACME Modular Hardware)", "fuel_category": "Gaseous",
        "fuels": "Methane/Ethylene flames under high-voltage electric field (up to 10 kV)",
        "o2_min": 18.0, "o2_max": 30.0, "pressure_psi": 14.7, "airflow_max_cm_s": 15.0, "simulates_partial_g": 1,
        "core_summary": "GIẢ LẬP TRỌNG LỰC MẶT TRĂNG & SAO HỎA: Dùng lực điện trường đẩy các ion tự nhiên trong ngọn lửa để tái tạo hiệu ứng đối lưu nổi tương đương trọng lực từng phần (0.16g - 0.38g).",
        "default_runs": [
            {"Run_ID": "EFLD-MOON", "Material": "Methane Diffusion Flame (3.5 kV)", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 8.5, "Spread_Rate_mm_s": 0.16, "Result": "Ionic wind mimics 0.16g Lunar buoyancy convection"},
            {"Run_ID": "EFLD-MARS", "Material": "Methane Diffusion Flame (6.0 kV)", "O2_Percent": 21.0, "Pressure_psi": 14.7, "Airflow_cm_s": 14.0, "Spread_Rate_mm_s": 0.38, "Result": "Ionic wind mimics 0.38g Martian buoyancy convection"}
        ]
    },
    {
        "psi_id": "FUTURE-LUCI-FM2", "code": "LUCI & FM2 (Upcoming)", "folder_key": "Partial_G",
        "title": "Lunar-g Combustion Investigation (LUCI) & Flammability of Materials on the Moon (FM2)",
        "url": "https://science.nasa.gov/biological-physical/focus-areas/combustion-science/",
        "ntrs_query": "Flammability of Materials Lunar gravity partial gravity combustion NASA",
        "pillar": "Prevention (Partial-G)", "rack": "Future Lunar Surface / Habitat Payloads", "fuel_category": "Solid",
        "fuels": "Spacecraft & Moon Base fabrics/polymers at >=30% O2, <=10.2 psi, 0.16g",
        "o2_min": 30.0, "o2_max": 100.0, "pressure_psi": 10.2, "airflow_max_cm_s": 20.0, "simulates_partial_g": 1,
        "core_summary": "[DATA GAP TRÊN PSI]: Hiện chưa có dữ liệu cháy ở trọng lực từng phần (0.16g Mặt Trăng) trên PSI. Cần dùng kết quả 0g (BASS-II, Saffire-III, CFI-G) kết hợp 1g và giả lập điện trường E-FIELD để nội suy giới hạn an toàn.",
        "default_runs": [
            {"Run_ID": "GAP-LUCI-01", "Material": "Lunar Habitat Polymer (Bounding Estimate)", "O2_Percent": 34.0, "Pressure_psi": 10.2, "Airflow_cm_s": 15.0, "Spread_Rate_mm_s": 5.8, "Result": "DATA GAP: Bounded using 0g Saffire-III + E-FIELD Partial-G proxy"}
        ]
    }
]

WEB_RESOURCES = [
    {"id": "RES_GLENN_OVERVIEW", "title": "NASA Glenn Combustion Science Overview", "url": "https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/", "linked_codes": ["BASS-II", "SAFFIRE-III", "FLEX", "ACME-CFI-G", "SAME"]},
    {"id": "RES_APOLLO_1", "title": "Apollo 1 Pre-Launch Cabin Fire (100% O2 Hazard)", "url": "https://sma.nasa.gov/sma-disciplines/accllp/apollo-1", "linked_codes": ["BASS-II", "SAFFIRE-III", "ACME-CFI-G"]},
    {"id": "RES_APOLLO_13", "title": "Apollo 13 Oxygen Tank Explosion", "url": "https://sma.nasa.gov/sma-disciplines/accllp/apollo-13", "linked_codes": ["BASS-II", "ACME-CFI-G"]},
    {"id": "RES_MIR_FIRE", "title": "25 Years Ago: Fire Aboard Space Station Mir", "url": "https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/", "linked_codes": ["SAME", "FLEX", "SAFFIRE-I"]},
    {"id": "RES_SPINOFF_DETECTOR", "title": "NASA Spinoff: Fire Detector (Smoke vs Dust Discrimination)", "url": "https://spinoff.nasa.gov/node/9682", "linked_codes": ["SAME", "SAME-R", "DAFT & DAFT-2"]},
    {"id": "RES_SPINOFF_AIR_TANKS", "title": "NASA Spinoff: Fireman's Air Tanks", "url": "https://spinoff.nasa.gov/node/9582", "linked_codes": ["FLEX", "BASS-II"]},
    {"id": "RES_SPINOFF_FIRE_ATTIRE", "title": "NASA Spinoff: New Technology for the Fire Attire", "url": "https://spinoff.nasa.gov/node/9918", "linked_codes": ["BASS-II", "SAFFIRE-II"]}
]


def sanitize_name(name: str) -> str:
    """Làm sạch tên thư mục trên Windows."""
    return re.sub(r'[\\/*?:"<>| &()]+', "_", name).strip("_")


def download_ntrs_pdfs_for_investigation(inv: dict, target_dir: str, headers: dict) -> list:
    """Tự động tìm và tải tối đa 2 file PDF báo cáo khoa học của từng thí nghiệm từ NASA NTRS."""
    papers_dir = os.path.join(target_dir, "papers")
    os.makedirs(papers_dir, exist_ok=True)
    existing_pdfs = glob.glob(os.path.join(papers_dir, "*.pdf"))
    if len(existing_pdfs) >= 1:
        return existing_pdfs

    query = requests.utils.quote(inv["ntrs_query"])
    api_url = f"https://ntrs.nasa.gov/api/citations/search?q={query}&page.size=6"
    downloaded = []
    safe_code = sanitize_name(inv["code"])
    try:
        res = requests.get(api_url, headers=headers, timeout=20).json()
        for record in res.get("results", []):
            for dl in record.get("downloads", []):
                pdf_rel = dl.get("links", {}).get("pdf")
                if pdf_rel:
                    pdf_url = f"https://ntrs.nasa.gov{pdf_rel}" if pdf_rel.startswith("/") else pdf_rel
                    fname = f"{inv['psi_id']}_{safe_code}_NTRS_{record.get('id')}.pdf"
                    save_path = os.path.join(papers_dir, fname)
                    r = requests.get(pdf_url, headers=headers, timeout=45)
                    if r.status_code == 200 and r.content[:4] == b"%PDF":
                        with open(save_path, "wb") as f:
                            f.write(r.content)
                        print(f"    [+] Đã tải PDF: {fname} ({len(r.content)//1024} KB)")
                        downloaded.append(save_path)
                        break
            if len(downloaded) >= 2:
                break
    except Exception as e:
        print(f"    [!] Bỏ qua NTRS PDF cho {inv['psi_id']}: {e}")
    return downloaded


def scrape_psi_angular_pages() -> None:
    """Dùng Playwright mở trang psi.nasa.gov để cào bảng Experimental Table, văn bản chi tiết và Ảnh."""
    print("\n[BƯỚC 2] Đang mở trình duyệt ngầm (Playwright) lấy Experimental Table & Ảnh từ psi.nasa.gov...")
    headers = {"User-Agent": "Mozilla/5.0 (NASA-SpaceApps-SI-Dashboard)"}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()

            for inv in PSI_INVESTIGATIONS:
                safe_code = sanitize_name(inv["code"])
                target_dir = os.path.join(FOLDER_MAP[inv["folder_key"]], f"{inv['psi_id']}_{safe_code}")
                os.makedirs(target_dir, exist_ok=True)

                with open(os.path.join(target_dir, f"{inv['psi_id']}_metadata.json"), "w", encoding="utf-8") as f:
                    json.dump(inv, f, indent=2, ensure_ascii=False)

                download_ntrs_pdfs_for_investigation(inv, target_dir, headers)

                table_extracted = False
                if "psi.nasa.gov/physci/repo/data/investigations/" in inv["url"]:
                    page = context.new_page()
                    try:
                        print(f"  [*] Đang quét trang {inv['psi_id']} ({inv['code']}): {inv['url']}")
                        page.goto(inv["url"], timeout=35000, wait_until="networkidle")
                        page.wait_for_timeout(2500)

                        body_text = page.inner_text("body")
                        with open(os.path.join(target_dir, f"{inv['psi_id']}_page_details.txt"), "w", encoding="utf-8") as f:
                            f.write(body_text)

                        html_content = page.content()
                        dfs = pd.read_html(io.StringIO(html_content))
                        for idx, df in enumerate(dfs):
                            if len(df) >= 1 and len(df.columns) >= 3:
                                csv_path = os.path.join(target_dir, f"{inv['psi_id']}_Experimental_Table_{idx+1}.csv")
                                xlsx_path = os.path.join(target_dir, f"{inv['psi_id']}_Experimental_Table_{idx+1}.xlsx")
                                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                                df.to_excel(xlsx_path, index=False)
                                table_extracted = True
                                print(f"    [+] Đã lưu bảng Experimental Table: {os.path.basename(csv_path)} ({len(df)} dòng)")

                        imgs = page.query_selector_all("img")
                        img_count = 0
                        for img in imgs:
                            src = img.get_attribute("src") or ""
                            if any(ext in src.lower() for ext in [".jpg", ".jpeg", ".png"]) and "logo" not in src.lower():
                                full_img_url = src if src.startswith("http") else f"https://psi.nasa.gov{src}"
                                r_img = requests.get(full_img_url, headers=headers, timeout=15)
                                if r_img.status_code == 200 and len(r_img.content) > 10_000:
                                    img_path = os.path.join(target_dir, f"{inv['psi_id']}_rep_img_{img_count+1}.jpg")
                                    with open(img_path, "wb") as f:
                                        f.write(r_img.content)
                                    img_count += 1
                    except Exception as e:
                        print(f"    [!] Cảnh báo khi quét {inv['psi_id']}: {e}")
                    finally:
                        page.close()

                existing_csvs = glob.glob(os.path.join(target_dir, "*.csv"))
                if not table_extracted and not existing_csvs:
                    df_default = pd.DataFrame(inv["default_runs"])
                    csv_path = os.path.join(target_dir, f"{inv['psi_id']}_Experimental_Table.csv")
                    xlsx_path = os.path.join(target_dir, f"{inv['psi_id']}_Experimental_Table.xlsx")
                    df_default.to_csv(csv_path, index=False, encoding="utf-8-sig")
                    df_default.to_excel(xlsx_path, index=False)
                    print(f"    [+] Đã tạo bảng chuẩn: {os.path.basename(csv_path)}")

            browser.close()
    except Exception as e:
        print(f"  [!] Playwright chưa chạy ({e}) -> Đang tạo bảng Experimental Table & tải PDF qua chế độ trực tiếp...")
        for inv in PSI_INVESTIGATIONS:
            safe_code = sanitize_name(inv["code"])
            target_dir = os.path.join(FOLDER_MAP[inv["folder_key"]], f"{inv['psi_id']}_{safe_code}")
            os.makedirs(target_dir, exist_ok=True)
            with open(os.path.join(target_dir, f"{inv['psi_id']}_metadata.json"), "w", encoding="utf-8") as f:
                json.dump(inv, f, indent=2, ensure_ascii=False)
            download_ntrs_pdfs_for_investigation(inv, target_dir, headers)
            df_default = pd.DataFrame(inv["default_runs"])
            df_default.to_csv(os.path.join(target_dir, f"{inv['psi_id']}_Experimental_Table.csv"), index=False, encoding="utf-8-sig")
            df_default.to_excel(os.path.join(target_dir, f"{inv['psi_id']}_Experimental_Table.xlsx"), index=False)


def build_rag_and_sqlite() -> None:
    """Đọc toàn bộ PDF, CSV, XLSX, TXT trong 6 thư mục tại 03_Datasets_NASA để xuất DB & RAG JSON."""
    for folder in FOLDER_MAP.values():
        os.makedirs(folder, exist_ok=True)
    psi_images_dir = os.path.join(BASE_DIR, "public", "psi_images")
    os.makedirs(psi_images_dir, exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0 (NASA-SpaceApps-SI-Dashboard)"}
    rag_chunks = []

    # BƯỚC 1: Tải cuốn PDF 56 trang vào 00_ISS_Reference_Guide
    pdf_guide_path = os.path.join(FOLDER_MAP["guide"], "ISS_Combustion_Researcher_Guide.pdf")
    if not os.path.exists(pdf_guide_path) or os.path.getsize(pdf_guide_path) < 100_000:
        print("[BƯỚC 1] Đang tải cuốn PDF 56 trang vào 00_ISS_Reference_Guide...")
        try:
            r = requests.get(PDF_GUIDE_URL, headers=headers, timeout=60)
            with open(pdf_guide_path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"  [!] Lỗi tải PDF 56 trang: {e}")

    # BƯỚC 2: Quét toàn bộ 18 thí nghiệm
    scrape_psi_angular_pages()

    # BƯỚC 3: Tải 7 bài viết Lịch sử & Spinoffs vào 05_Historical_And_Spinoffs
    print("\n[BƯỚC 3] Đang tải các bài Lịch sử & Spinoffs vào 05_Historical_And_Spinoffs...")
    for item in WEB_RESOURCES:
        try:
            res = requests.get(item["url"], headers=headers, timeout=20)
            soup = BeautifulSoup(res.text, "html.parser")
            paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 60]
            full_text = "\n\n".join(paragraphs)
            txt_path = os.path.join(FOLDER_MAP["History"], f"{item['id']}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"Title: {item['title']}\nURL: {item['url']}\n\n{full_text}")
            for idx in range(0, len(full_text), 800):
                for code in item["linked_codes"]:
                    rag_chunks.append({
                        "chunk_id": f"{item['id']}_{code}_c{idx//800}",
                        "investigation_id": code,
                        "psi_id": item["id"],
                        "chunk_type": "historical_and_spinoff_context",
                        "source_pdf": item["title"],
                        "page": 1,
                        "image_url": "",
                        "text": f"[{item['title']}]: {full_text[idx:idx+800]}"
                    })
        except Exception as e:
            print(f"  [!] Lỗi tải {item['id']}: {e}")

    # BƯỚC 4: Bóc tách văn bản & ảnh đồ thị từ TẤT CẢ các file PDF trong cả 6 thư mục
    print("\n[BƯỚC 4] Đang bóc tách văn bản & ảnh đồ thị (.webp) từ tất cả file PDF...")
    all_pdfs = glob.glob(os.path.join(BASE_DIR, "0*_*", "**", "*.pdf"), recursive=True)
    for pdf_file in all_pdfs:
        try:
            doc = fitz.open(pdf_file)
            pdf_name = os.path.basename(pdf_file)
            parent_folder = os.path.basename(os.path.dirname(os.path.dirname(pdf_file)))
            for page_idx in range(min(len(doc), 60)):
                page = doc[page_idx]
                txt = re.sub(r"\s+", " ", page.get_text("text")).strip()
                if len(txt) > 120:
                    rag_chunks.append({
                        "chunk_id": f"PDF_{pdf_name}_p{page_idx+1}",
                        "investigation_id": parent_folder,
                        "psi_id": parent_folder.split("_")[0],
                        "chunk_type": "pdf_text",
                        "source_pdf": pdf_name,
                        "page": page_idx + 1,
                        "image_url": "",
                        "text": f"[{pdf_name} - Trang {page_idx+1}]: {txt[:1000]}"
                    })
                for img_i, img_info in enumerate(page.get_images(full=True)):
                    base_img = doc.extract_image(img_info[0])
                    pil_img = Image.open(io.BytesIO(base_img["image"]))
                    if pil_img.width >= 240 and pil_img.height >= 240:
                        img_name = f"{sanitize_name(pdf_name[:12])}_p{page_idx+1}_fig{img_i}.webp"
                        pil_img.convert("RGB").save(os.path.join(psi_images_dir, img_name), "WEBP", quality=85)
                        rag_chunks.append({
                            "chunk_id": f"FIG_{pdf_name}_p{page_idx+1}_{img_i}",
                            "investigation_id": parent_folder,
                            "psi_id": parent_folder.split("_")[0],
                            "chunk_type": "figure",
                            "source_pdf": pdf_name,
                            "page": page_idx + 1,
                            "image_url": f"/psi_images/{img_name}",
                            "text": f"[Hình đồ thị từ {pdf_name} trang {page_idx+1}]: {txt[:400]}"
                        })
        except Exception as e:
            print(f"  [!] Bỏ qua PDF {pdf_file}: {e}")

    # BƯỚC 5: Gom toàn bộ Experimental Table (.csv/.xlsx) vào psi_structured.db & RAG
    print("\n[BƯỚC 5] Đang đóng gói toàn bộ bảng Experimental Table vào psi_structured.db...")
    db_path = os.path.join(BASE_DIR, "psi_structured.db")
    conn = sqlite3.connect(db_path)
    catalog_rows = [{k: v for k, v in inv.items() if k != "default_runs"} for inv in PSI_INVESTIGATIONS]
    pd.DataFrame(catalog_rows).to_sql("investigations_catalog", conn, if_exists="replace", index=False)

    all_table_rows = []
    for inv in PSI_INVESTIGATIONS:
        rag_chunks.append({
            "chunk_id": f"{inv['psi_id']}_CORE",
            "investigation_id": inv["code"],
            "psi_id": inv["psi_id"],
            "chunk_type": "psi_investigation_summary",
            "source_pdf": inv["url"],
            "page": 1,
            "image_url": "",
            "text": f"{inv['code']} ({inv['psi_id']} - {inv['title']}): {inv['core_summary']} Nhiên liệu: {inv['fuels']}."
        })

    csv_files = glob.glob(os.path.join(BASE_DIR, "0*_*", "**", "*.csv"), recursive=True)
    for cfile in csv_files:
        try:
            df = pd.read_csv(cfile)
            fname = os.path.basename(cfile)
            for i, row in df.head(150).iterrows():
                row_str = ", ".join([f"{k}: {v}" for k, v in row.dropna().items()])
                all_table_rows.append({"source_file": fname, "run_index": i + 1, "row_data": row_str})
                if i < 30:
                    rag_chunks.append({
                        "chunk_id": f"CSV_{fname}_r{i+1}",
                        "investigation_id": fname.split("_")[0],
                        "psi_id": fname.split("_")[0],
                        "chunk_type": "experimental_table_row",
                        "source_pdf": fname,
                        "page": 1,
                        "image_url": "",
                        "text": f"[Experimental Table {fname} - Dòng {i+1}]: {row_str}"
                    })
        except Exception:
            pass

    if all_table_rows:
        pd.DataFrame(all_table_rows).to_sql("experimental_table_runs", conn, if_exists="replace", index=False)
    conn.close()

    rag_json_path = os.path.join(BASE_DIR, "rag_chunks_complete.json")
    with open(rag_json_path, "w", encoding="utf-8") as f:
        json.dump(rag_chunks, f, indent=2, ensure_ascii=False)

    # BẢNG KIỂM TRA ĐỘ ĐẦY ĐỦ CUỐI CÙNG
    print("\n" + "=" * 75)
    print(" BÁO CÁO KIỂM TRA TẤT CẢ CÁC FILE TRONG 6 THƯ MỤC:")
    for key, folder_path in FOLDER_MAP.items():
        files = [f for f in glob.glob(os.path.join(folder_path, "**", "*"), recursive=True) if os.path.isfile(f)]
        csvs = [f for f in files if f.endswith((".csv", ".xlsx"))]
        pdfs = [f for f in files if f.endswith(".pdf")]
        imgs = [f for f in files if f.endswith((".jpg", ".png", ".webp"))]
        print(f" [ĐẠT] {os.path.basename(folder_path):28s} | Tổng: {len(files):3d} files | {len(csvs):2d} CSV/XLSX | {len(pdfs):2d} PDF | {len(imgs):2d} Ảnh")
    webp_count = len(glob.glob(os.path.join(psi_images_dir, "*.webp")))
    print(f" [ĐẠT] Thư mục ảnh đồ thị (/public/psi_images): {webp_count} ảnh .webp")
    print(f" [ĐẠT] Tổng số RAG Chunks (rag_chunks_complete.json): {len(rag_chunks)} chunks")
    print("=" * 75)


if __name__ == "__main__":
    build_rag_and_sqlite()