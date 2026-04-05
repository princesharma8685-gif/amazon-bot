import os
import json
import time
import random
import re
import requests

BOT_TOKEN = "8646128893:AAGsVsoxof9eF8YUtEXHZRGRB1eHhPFOCuE"
CHANNEL = "-1003708673134"
SEEN_FILE = "seen_jobs.json"

URL = "https://www.amazon.jobs/en/search.json?base_query=warehouse"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}


def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)


def send_telegram_message(message):
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            params={
                "chat_id": CHANNEL,
                "text": message,
                "disable_web_page_preview": True
            },
            timeout=20
        )
        print("Telegram status:", r.status_code)
    except Exception as e:
        print("Telegram send error:", e)


def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def get_jobs():
    try:
        r = requests.get(URL, headers=HEADERS, timeout=30)
        print("Status:", r.status_code)

        if r.status_code != 200:
            return []

        data = r.json()
        jobs = data.get("jobs", [])
        print("Total jobs:", len(jobs))
        return jobs

    except Exception as e:
        print("Fetch error:", e)
        return []


def is_uk_job(job_title, job_location, job_description=""):
    text = f"{job_title} {job_location} {job_description}".lower()

    uk_keywords = [
        "uk",
        "united kingdom",
        "london",
        "manchester",
        "birmingham",
        "leeds",
        "bristol",
        "glasgow",
        "liverpool",
        "sheffield",
        "edinburgh",
        "england",
        "scotland",
        "wales",
        "northern ireland"
    ]

    warehouse_keywords = [
        "warehouse",
        "fulfilment",
        "fulfillment",
        "sortation",
        "associate",
        "operations",
        "amazon operations"
    ]

    return any(u in text for u in uk_keywords) and any(w in text for w in warehouse_keywords)


def main():
    seen = load_seen()
    print("Loaded seen jobs:", len(seen))

    while True:
        jobs = get_jobs()
        found_new = False

        for job in jobs:
            job_id = str(job.get("id", ""))
            job_title = clean_text(job.get("title", "No title"))
            job_location = clean_text(job.get("location", "No location"))
            job_description = clean_text(job.get("description_short", ""))
            job_path = job.get("job_path", "")
            job_url = f"https://www.amazon.jobs{job_path}" if job_path else ""

            unique_key = job_id or job_url or f"{job_title}-{job_location}"

            print("TITLE:", job_title)
            print("LOCATION:", job_location)
            print("URL:", job_url)
            print("------")

            if unique_key in seen:
                continue

            if is_uk_job(job_title, job_location, job_description):
                message = (
                    f"🇬🇧 UK Amazon warehouse job alert\n\n"
                    f"📌 {job_title}\n"
                    f"📍 {job_location}\n"
                    f"🔗 {job_url}"
                )

                send_telegram_message(message)
                seen.add(unique_key)
                save_seen(seen)
                found_new = True
            else:
                print("Not UK job:", job_title, "-", job_location)

        if not found_new:
            print("No new UK job")

        wait = random.randint(4, 6)
        print(f"Waiting {wait} sec...")
        time.sleep(wait)


if __name__ == "__main__":
    main()