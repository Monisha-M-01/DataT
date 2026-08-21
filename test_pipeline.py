import json
from backend.pipeline import run_pipeline
from backend.store import init_db, create_job, get_job

# Setup mock data for quick testing
rows = [
    {
        "Mfg_Part_Num": "PDSH4816AF",
        "Part_Desc": "PDSH4816AF Dishwasher SS - Display Only",
        "E1_Brand": "",
        "Unilog_Brand": "",
        "DIB_Brand": "",
        "Part_Manuf": "Appliance Dealers Cooperative (APPDE)"
    },
    {
        "Mfg_Part_Num": "TEST1234",
        "Part_Desc": "TEST1234 Widget 120V 15A 24 in W x 24-1/4 in D SS",
        "E1_Brand": "",
        "Unilog_Brand": "",
        "DIB_Brand": "",
        "Part_Manuf": "Appliance Dealers Cooperative (APPDE)"
    }
]

import time
job_id = f"test-job-{int(time.time())}"

if __name__ == "__main__":
    init_db()
    create_job(job_id, len(rows))
    print("Starting pipeline test...")
    run_pipeline(job_id, rows)
    
    job = get_job(job_id)
    print("Pipeline finished.")
    print("Status:", job["status"])
    print("Processed:", job["processed"], "/", job["total"])
    print("Results (First item):")
    if job["results"]:
        print(json.dumps(job["results"][0], indent=2))
    else:
        print("No results returned.")
