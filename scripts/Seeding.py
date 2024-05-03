import csv
from sqlalchemy.orm import Session
from database import engine 
from models.Store import Store , StoreHours , StoreStatus

#TODO : Add MultiProcessing
class Seed:
    def __init__(self):
        self.storeSet : set = set()
        
    def SeedIt(self):
        self.StoreSeeder()
        self.StoreHoursSeeder()
        self.StoreStatusSeeder()
       
    def StoreSeeder(self):
        with open('csv/store.csv' , 'r') as file:
            reader = csv.reader(file)
            data = [row for row in reader]
            data.remove(data[0]) 
        with Session(engine) as session:
            stores = []
            for row in data:
                self.storeSet.add(row[0])
                model_instance = Store(store_id=row[0], timezone_str=row[1])
                stores.append(model_instance)
            session.add_all(stores)
            session.commit()  
    
    def StoreHoursSeeder(self):
        with open('csv/store_hours.csv', 'r') as file:
            reader = csv.reader(file)
            data = [row for row in reader]
            data.remove(data[0])
        
        with Session(engine) as session:
            #Check if Store Exist
            stores = []
            store_hours = []
            for row in data:
                if not row[0] in self.storeSet:
                    stores.append(Store(store_id=row[0], timezone_str='America/Chicago'))
                    self.storeSet.add(row[0])
                store_hour = StoreHours(store_id=row[0], day_of_week=row[1], start_time_local=row[2], end_time_local=row[3])
                store_hours.append(store_hour)
            session.add_all(stores)
            session.commit()
            session.add_all(store_hours)
            session.commit()
    
    def StoreStatusSeeder(self):
        with open('csv/store_status.csv', 'r') as file:
            reader = csv.reader(file)
            data = [row for row in reader]
            data.remove(data[0])
        
        with Session(engine) as session:
            store_status = []
            stores = []
            for row in data:
                if not row[0] in self.storeSet:
                    stores.append(Store(store_id=row[0], timezone_str='America/Chicago'))
                    self.storeSet.add(row[0])
                store_status.append(StoreStatus(store_id=row[0], status=StoreStatus.Status.ACTIVE if row[1] == 'active' else StoreStatus.Status.INACTIVE, timestamp_utc=row[2]))
            session.add_all(stores)
            session.commit()
            session.add_all(store_status)
            session.commit()    