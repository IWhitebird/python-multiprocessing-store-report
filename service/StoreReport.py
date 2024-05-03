import csv
import multiprocessing
from datetime import datetime, timedelta
from typing import Tuple
from sqlalchemy.orm import Session
from database import engine
from models.Store import Store , StoreHours , StoreStatus, StoreReport
from scripts import TimeUtils



def calculateFinalTime(day_wise_start_end_time , store_status , hours, TIMESTAMP) -> Tuple[float, float]:
    cur_time = TIMESTAMP
    old_time = TIMESTAMP - timedelta(hours=hours)

    uptime = 0
    downtime = 0
    start_end_times = []
    
    while(old_time <= cur_time):
        new_old_time = old_time
        new_cur_time = cur_time
        
        if old_time.weekday() not in day_wise_start_end_time:
            old_time += timedelta(days=1)
            continue
        
        
        start_time_local = datetime.strptime(day_wise_start_end_time[old_time.weekday()][0] , "%Y-%m-%d %H:%M:%S.%f")
        end_time_local = datetime.strptime(day_wise_start_end_time[old_time.weekday()][1] , "%Y-%m-%d %H:%M:%S.%f")
        
        if start_time_local > new_old_time:
            new_old_time = start_time_local
        if end_time_local < new_cur_time:
            new_cur_time = end_time_local
        start_end_times.append((new_old_time , new_cur_time))
        old_time += timedelta(days=1)

    store_status = sorted(store_status, key=lambda x: x.timestamp_utc)
    for st , et in start_end_times:  
        for status in store_status: 
            if status.timestamp_utc < st - timedelta(minutes=30) or status.timestamp_utc > et + timedelta(minutes=30):
                continue
            
            middle = status.timestamp_utc 
            plus_30_min = middle + timedelta(minutes=30)
            minus_30_min = middle - timedelta(minutes=30)
            if status.timestamp_utc < st:
                middle = st
            if status.timestamp_utc > et:
                middle = et
            
            if status.status == StoreStatus.Status.ACTIVE:
                if minus_30_min >= st:
                    uptime += (middle - minus_30_min).total_seconds()   
                if plus_30_min <= et:
                    uptime += (plus_30_min - middle).total_seconds()   
            else:
                if minus_30_min >= st:
                    downtime += (middle - minus_30_min).total_seconds()   
                if plus_30_min <= et:
                    downtime += (plus_30_min - middle).total_seconds()  
            st += timedelta(seconds=(plus_30_min - middle).total_seconds()   ) 

    return uptime / 60 , downtime / 60

def processStores(chunk_id, stores, report_id, TIMESTAMP):
    chunk_results = []
    time_to_Get = datetime.now()
    store_ids = [store.store_id for store in stores]
    metric = []
    metric.append(chunk_id)
    print("PROCESSING CHUNK", chunk_id)
    with Session(engine) as db:
        store_hours = db.query(StoreHours)\
        .filter(StoreHours.store_id.in_(store_ids))\
        .all()
        
        store_status = db.query(StoreStatus)\
           .filter(
        StoreStatus.store_id.in_(store_ids),
        StoreStatus.timestamp_utc >= TIMESTAMP - timedelta(days=7) - timedelta(minutes=30),
        StoreStatus.timestamp_utc <= TIMESTAMP + timedelta(minutes=30))\
        .all()
    
        
    metric.append(datetime.now() - time_to_Get)
    time_to_Get = datetime.now()
    
    store_info = {}

    for store in stores:
        store_info[store.store_id] = {
            'store': store,
            'store_hours': [],
            'store_status': []
    }
    for store_hour in store_hours:
        store_info[store_hour.store_id]['store_hours'].append(store_hour)
    for status in store_status:
        store_info[status.store_id]['store_status'].append(status)
        
    for store_id, info in store_info.items():
        day_wise_start_end_time = TimeUtils.getStartTime(info['store'].timezone_str, info['store_hours'], TIMESTAMP)
        uptime_last_hour, downtime_last_hour = calculateFinalTime(day_wise_start_end_time, info['store_status'], 1, TIMESTAMP)
        uptime_last_day , downtime_last_day = calculateFinalTime(day_wise_start_end_time, info['store_status'], 24, TIMESTAMP)
        uptime_last_week, downtime_last_week = calculateFinalTime(day_wise_start_end_time, info['store_status'], 7 * 24, TIMESTAMP)
        chunk_results.append([store_id, uptime_last_hour, uptime_last_day / 60, uptime_last_week / 60, downtime_last_hour, downtime_last_day / 60, downtime_last_week / 60])
    
    metric.append(datetime.now() - time_to_Get)
    time_to_Get = datetime.now()

    with open(f"./reports/report_{report_id}.csv", "a", newline='') as file:
        writer = csv.writer(file)
        for result in chunk_results:
            # print(result)
            writer.writerow([result[0], result[1], result[2], result[3], result[4], result[5], result[6]])

    metric.append(datetime.now() - time_to_Get)
    time_to_Get = datetime.now()
    
    with open(f"./performance/performance_report_{report_id}.csv", "a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow([metric[0] , metric[1] , metric[2] , metric[3]])


def TriggerReport(numba , report_id):
    db = Session(engine)
    report_time = datetime.now()
    TIMESTAMP = datetime.strptime("2023-01-22 12:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")
    report = db.query(StoreReport).filter(StoreReport.report_id == report_id).first()
    if not report:
        return "Report Not Found"
    
    with open(f"./reports/report_{report_id}.csv", "a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["store_id", "uptime_last_hour", "uptime_last_day", "uptime_last_week", "downtime_last_hour", "downtime_last_day", "downtime_last_week"])
    
    with open(f"./performance/performance_report_{report_id}.csv", "a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["process_no","get_data_from_db" ,"process_data" , "time_to_write_on_csv" ])

    stores = db.query(Store).all()

    chunk_size = 15000
    num_chunks = (len(stores) + chunk_size - 1) // chunk_size
    pool = multiprocessing.Pool(8)
     
    for chunk_id in range(num_chunks):
        chunk_start = chunk_id * chunk_size
        chunk_end = min((chunk_id + 1) * chunk_size, len(stores))
        chunk_stores = stores[chunk_start:chunk_end]
        pool.apply_async(processStores, args=(chunk_id, chunk_stores, report_id, TIMESTAMP))
        # processStores(chunk_id, chunk_stores, report_id, TIMESTAMP)
        # break

    pool.close()
    pool.join()

    report.status = StoreReport.PollingStatus.SUCCESS
    with open(f"./reports/report_{report_id}.csv") as file:
        report.report_csv = file.read()
    db.commit()
    
    print("Report Generated in"  , datetime.now() - report_time)
    return True

