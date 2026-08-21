import os
os.environ["MAX_REQUESTS_PER_RUN"] = "10000"
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

import csv
import hashlib
from backend.store import init_db, create_job, get_job, update_job_status
from backend.pipeline import run_pipeline

init_db()

input_file = "Unihack_ Sample Dataset - Input.csv"
with open(input_file, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

with open(input_file, "rb") as f:
    content = f.read()
    job_id = hashlib.md5(content).hexdigest()

print(f"Creating job {job_id} for {len(rows)} rows...")
job = get_job(job_id)
if not job:
    create_job(job_id, len(rows))
else:
    update_job_status(job_id, "processing")

# Run pipeline synchronously
run_pipeline(job_id, rows)

job = get_job(job_id)
results = job["results"]

export_filename = f"job_{job_id}_export.csv"
print(f"Exporting to {export_filename}...")

if len(results) > 0:
    first_result = results[0]["output"]
    headers = list(first_result.keys())
    with open(export_filename, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in results:
            writer.writerow(row["output"])

print(f"Done! File saved as {export_filename}")
