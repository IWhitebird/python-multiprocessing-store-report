from datetime import datetime, timedelta
import pytz


#timezine can be - America/Denver
#store_hour.day_of_week is number (0 for monday , 6 for sunday)
def getStartTime(timezone : str , store_hours , TIMESTAMP) -> dict:
    
    def localToUtc(day , localTime : datetime.time, timezone : str) -> datetime:
        temp = TIMESTAMP
        
        while temp.weekday() != day:
            temp -= timedelta(days=1)
        
        local_datetime = datetime.combine(temp.date(), localTime)
        
        local_timezone = pytz.timezone(timezone)
        local_datetime = local_timezone.localize(local_datetime)
        utc_datetime = local_datetime.astimezone(pytz.utc)
        

        return utc_datetime.strftime("%Y-%m-%d %H:%M:%S.%f")

    
    day_wise_start_end_time = {}
    for i in range (0 , 6):
        sh = None
        for store_hour in store_hours:
            if store_hour.day_of_week == i:
                sh = store_hour
        if sh:
            day_wise_start_end_time[i] = (localToUtc(i , sh.start_time_local , timezone) , localToUtc(i , sh.end_time_local , timezone) )
    return day_wise_start_end_time
