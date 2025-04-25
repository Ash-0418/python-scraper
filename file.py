import csv


def save_to_file(keyword, jobs):
    filename = f"{keyword}.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Title", "Company", "Link"])  # 헤더
        for job in jobs:
            writer.writerow([
                job.get("title", ""),
                job.get("company", ""),
                job.get("link", ""),
            ])
