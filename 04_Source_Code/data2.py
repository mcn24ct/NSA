import os
import requests

BASE_DIR = r"D:\MCN\Hackathon_NASA_AI\03_Datasets_NASA"


def download_experiment_pdfs_from_ntrs() -> None:
    """Tự động tìm và tải PDF báo cáo chính thức từ NASA NTRS API vào đúng thư mục chủ đề."""
    ntrs_queries = [
        {
            "topic": "01_Prevention",
            "code": "BASS-II",
            "query": "Burning and Suppression of Solids BASS-II microgravity"
        },
        {
            "topic": "01_Prevention",
            "code": "SAFFIRE-II",
            "query": "Spacecraft Fire Safety Demonstration Saffire microgravity"
        },
        {
            "topic": "01_Prevention",
            "code": "ACME-CFI-G",
            "query": "Cool Flames Investigation with Gases ACME spherical flame"
        },
        {
            "topic": "02_Detection",
            "code": "SAME-R",
            "query": "Smoke Aerosol Measurement Experiment SAME microgravity"
        },
        {
            "topic": "03_Suppression",
            "code": "FLEX",
            "query": "Flame Extinguishment Experiment FLEX droplet cool flame"
        },
        {
            "topic": "04_Partial_Gravity",
            "code": "ACME-E-FIELD",
            "query": "Electric-Field Effects on Laminar Diffusion Flames ACME"
        }
    ]

    headers = {"User-Agent": "Mozilla/5.0 (NASA-SpaceApps-SI-Dashboard)"}
    print("\n[+] Đang tự động tải PDF báo cáo riêng của từng thí nghiệm từ NASA NTRS...")

    for item in ntrs_queries:
        # Lưu trực tiếp vào thư mục thí nghiệm bên trong nhánh chủ đề tương ứng
        save_dir = os.path.join(BASE_DIR, item["topic"], item["code"])
        os.makedirs(save_dir, exist_ok=True)

        search_api = (
            f"https://ntrs.nasa.gov/api/citations/search?"
            f"q={requests.utils.quote(item['query'])}&page.size=5"
        )

        try:
            res = requests.get(search_api, headers=headers, timeout=20).json()
            for record in res.get("results", []):
                downloads = record.get("downloads", [])
                pdf_link = next(
                    (d.get("links", {}).get("pdf") for d in downloads if d.get("links", {}).get("pdf")),
                    None
                )

                if pdf_link:
                    full_pdf_url = (
                        f"https://ntrs.nasa.gov{pdf_link}"
                        if pdf_link.startswith("/")
                        else pdf_link
                    )
                    pdf_name = f"{item['code']}_NASA_Report_{record.get('id')}.pdf"
                    pdf_path = os.path.join(save_dir, pdf_name)

                    if not os.path.exists(pdf_path):
                        r_pdf = requests.get(full_pdf_url, headers=headers, timeout=45)
                        if r_pdf.status_code == 200 and len(r_pdf.content) > 50_000:
                            with open(pdf_path, "wb") as f:
                                f.write(r_pdf.content)
                            print(
                                f"  -> Đã tải PDF vào [{item['topic']}\\{item['code']}]: "
                                f"{pdf_name} ({len(r_pdf.content) // 1024} KB)"
                            )
                            break  # Mỗi thí nghiệm lấy 1 file PDF báo cáo chuẩn nhất
                    else:
                        print(f"  -> Đã có sẵn PDF tại [{item['topic']}\\{item['code']}]: {pdf_name}")
                        break
        except Exception as e:
            print(f"  [!] Bỏ qua NTRS {item['code']}: {e}")


if __name__ == "__main__":
    # Nếu ghép chung vào file trước thì gọi cả 2 hàm:
    # build_all_data()
    download_experiment_pdfs_from_ntrs()