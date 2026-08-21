import time
import concurrent.futures
from .store import update_job_status, update_job_progress, save_row_result, get_job_results_dict
from .stages.stage1_ingestion import ingest_and_normalize
from .stages.stage2_brand import resolve_brand
from .stages.stage3_agent import run_enrichment_agent_batch
from .stages.stage4_lov import validate_lovs
from .stages.stage5_scoring import calculate_confidence
from .stages.stage6_output import format_output

def process_batch_tasks(batch: list):
    """
    batch is a list of tuples: (index, original_row)
    """
    parsed_rows = []
    # Stage 1 and 2 for each
    for index, row in batch:
        parsed = ingest_and_normalize(row)
        brand_info = resolve_brand(parsed)
        parsed.update(brand_info)
        parsed_rows.append(parsed)
        
    # Stage 3 for the batch
    agent_results = run_enrichment_agent_batch(parsed_rows)
    
    # Stage 4, 5, 6 for each
    final_results = []
    for i, agent_result in enumerate(agent_results):
        index, original_row = batch[i]
        validated_result = validate_lovs(agent_result)
        scored_result = calculate_confidence(validated_result)
        final_output = format_output(scored_result)
        
        result_wrapper = {
            "input": original_row,
            "output": final_output["data"],
            "_meta": final_output["_meta"]
        }
        final_results.append((index, result_wrapper))
        
    return final_results

def run_pipeline(job_id: str, rows: list):
    import os
    MAX_REQUESTS = int(os.environ.get("MAX_REQUESTS_PER_RUN", "15"))
    BATCH_SIZE = 5
    
    try:
        update_job_status(job_id, "processing")
        
        existing_results = get_job_results_dict(job_id)
        processed_count = len(existing_results)
        
        # We only need to process rows that aren't already in existing_results
        pending_tasks = []
        for i, row in enumerate(rows):
            if i not in existing_results:
                pending_tasks.append((i, row))
        
        # Create batches
        batches = [pending_tasks[i:i + BATCH_SIZE] for i in range(0, len(pending_tasks), BATCH_SIZE)]
        batches_to_run = batches[:MAX_REQUESTS] # Cap the run to MAX_REQUESTS
        
        def task_wrapper(batch):
            return process_batch_tasks(batch)
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(task_wrapper, b) for b in batches_to_run]
            for future in concurrent.futures.as_completed(futures):
                batch_results = future.result()
                
                # Write result immediately
                for index, result_wrapper in batch_results:
                    save_row_result(job_id, index, result_wrapper)
                    processed_count += 1
                
                update_job_progress(job_id, processed_count)
                
        if len(batches) > MAX_REQUESTS:
            update_job_status(job_id, "paused")
        else:
            update_job_status(job_id, "completed")
    except Exception as e:
        import traceback
        print(f"Job {job_id} failed: {e}")
        traceback.print_exc()
        update_job_status(job_id, "failed")
