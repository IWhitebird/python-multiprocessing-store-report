import multiprocessing
import threading
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from service import StoreReport
from database import engine 
from models.Store import Store , StoreHours , StoreStatus, StoreReport
from scripts import  TimeUtils

csv_data = "store_id, uptime_last_hour, uptime_last_day, uptime_last_week, downtime_last_hour, downtime_last_day, downtime_last_week\n"
process = []

class CsvModel:
    def __init__(self , store_id , uptime_last_hour , uptime_last_day , uptime_last_week , downtime_last_hour , downtime_last_day , downtime_last_week):
        self.store_id = store_id
        self.uptime_last_hour = uptime_last_hour
        self.uptime_last_day = uptime_last_day
        self.uptime_last_week = uptime_last_week
        self.downtime_last_hour = downtime_last_hour
        self.downtime_last_day = downtime_last_day
        self.downtime_last_week = downtime_last_week
           
def calculateFinalTime(TIMESTAMP , day_wise_start_end_time , store_status , hours : int) -> tuple:
    #2024-05-03 15:54:32.606864 TIMESTAMP
    cur_time = datetime.strptime(str(TIMESTAMP), "%Y-%m-%d %H:%M:%S.%f")
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

    for st , et in start_end_times:
        required_status = []
        for status in store_status:  
            if str(status.timestamp_utc)[-3:] == 'UTC':
                status.timestamp_utc = datetime.strptime(str(status.timestamp_utc), "%Y-%m-%d %H:%M:%S.%f %Z")
            else:
                status.timestamp_utc = datetime.strptime(str(status.timestamp_utc), "%Y-%m-%d %H:%M:%S.%f")
                
            if status.timestamp_utc >= st - timedelta(minutes=30) and status.timestamp_utc <= et +timedelta(minutes=30):
                required_status.append(status)
        #sort required_status by timestamp_utc
        required_status.sort(key = lambda x : x.timestamp_utc)
        for i in range(0 , len(required_status) - 1):
            middle = required_status[i].timestamp_utc 
            if required_status[i].timestamp_utc < st:
                middle = st
            if required_status[i].timestamp_utc > et:
                middle = et
            plus_30_min = required_status[i].timestamp_utc + timedelta(minutes=30)
            minus_30_min = required_status[i].timestamp_utc - timedelta(minutes=30)
            if required_status[i].status == 'active':
                if minus_30_min >= st:
                    uptime += middle - minus_30_min
                if plus_30_min <= et:
                    uptime += plus_30_min - middle
            else:
                if minus_30_min >= st:
                    downtime += middle - minus_30_min
                if plus_30_min <= et:
                    downtime += plus_30_min - middle

    return uptime , downtime

def processStores(store_hours,store_status, stores,report_id , TIMESTAMP):
    store_info = {}
    for sto in stores:
        if sto.store_id not in store_info:
            store_info[sto.store_id] = {
                'store' : sto,
                'store_hours' : [],
                'store_status' : []
            }
        store_info[sto.store_id]['store'] = sto

    for sh in store_hours:
        if sh.store_id in store_info:
            store_info[sh.store_id]['store_hours'].append(sh)

    for ss in store_status:
        if ss.store_id in store_info:
            store_info[ss.store_id]['store_status'].append(ss)
    
    results = []
    for store_id, storeInfo in store_info.items(): 
        timezone = storeInfo['store'].timezone_str
        day_wise_start_end_time = TimeUtils.getStartTime(timezone , storeInfo['store_hours'] , TIMESTAMP)
        uptime_last_hour , downtime_last_hour  = calculateFinalTime(TIMESTAMP ,day_wise_start_end_time , storeInfo['store_status'], 1)
        uptime_last_day  , downtime_last_day   = calculateFinalTime(TIMESTAMP ,day_wise_start_end_time , storeInfo['store_status'], 24)
        uptime_last_week , downtime_last_week  = calculateFinalTime(TIMESTAMP ,day_wise_start_end_time , storeInfo['store_status'], 7 * 24)
        results.append(CsvModel(store_id = store_id , uptime_last_hour = uptime_last_hour , uptime_last_day = uptime_last_day, uptime_last_week = uptime_last_week , downtime_last_hour = downtime_last_hour , downtime_last_day = downtime_last_day , downtime_last_week = downtime_last_week))
    
        
    #csv_data = "store_id, uptime_last_hour, uptime_last_day, uptime_last_week, downtime_last_hour, downtime_last_day, downtime_last_week\n"
    csv_data = ""
    for result in results:
        csv_data += f"{result.store_id}, {result.uptime_last_hour}, {result.uptime_last_day}, {result.uptime_last_week}, {result.downtime_last_hour}, {result.downtime_last_day}, {result.downtime_last_week}\n"
    with open(f"./reports/report_{report_id}.csv", "w") as file:   
        file.write(csv_data)



def TriggerReport(db: Session, report_id: str , TIMESTAMP = datetime.now()):
    report = db.query(StoreReport).filter(StoreReport.report_id == report_id).first()
    if not report:
        return "Report Not Found"
    stores = db.query(Store).all()
      
    processes = []
    chunk_size = 200  # Set your desired chunk size
    
    def getDataThread(idStore):
        with Session(engine) as session:
            # Query store hours and status only for the stores in the current chunk
            store_hours = session.query(StoreHours)\
                .filter(StoreHours.store_id.in_(idStore))\
                .all()
            store_status = session.query(StoreStatus)\
                .filter(StoreStatus.store_id.in_(idStore))\
                .all()
        p = multiprocessing.Process(target=processStores, args=(store_hours , store_status , stores[i:i + chunk_size] ,report_id , TIMESTAMP))
        print(p)
        processes.append(p)  
    threads = []
    # Assuming `stores` is your list of store objects
    for i in range(0, len(stores), chunk_size):
        chunk = stores[i:i+chunk_size]  # Slice the stores list to get the current chunk
        idStore = [store.store_id for store in chunk]  # Extract store IDs from the current chunk
        t = threading.Thread(target=getDataThread, args=(idStore,))
        threads.append(t)
        
        
        
    print("Waiting for Threads...")
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("Threads Completed")
    
    print("Waiting for Processess...")
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    print("Proccesses  Completed")

    # with open(f"./reports/report_{report_id}.csv", "w") as file:
    #     file.write(csv_data)
    report.status = StoreReport.PollingStatus.SUCCESS
    db.commit()
    return "Report Completed"
