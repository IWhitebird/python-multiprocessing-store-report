from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter , BackgroundTasks
from sqlalchemy.orm import Session
from service import StoreReport as StoreReportService
from models import Store
from database import get_db
import multiprocessing

router = APIRouter(tags=['StoreReport'])

@router.get("/trigger_report")
async def trigger_report(background_tasks : BackgroundTasks , db: Session = Depends(get_db)):
    report = Store.StoreReport()
    db.add(report)
    db.commit()
    db.refresh(report)
    #TODO : Send to Queue for processing
    process = multiprocessing.Process(target=StoreReportService.TriggerReport, args=('1' , str(report.report_id)))
    process.start()
    background_tasks.add_task(process.join)
    
    return report

@router.get('/get_report/{report_id}')
async def get_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Store.StoreReport).filter(Store.StoreReport.report_id == report_id).first()
    if report:
        if report.status == Store.StoreReport.PollingStatus.PENDING:
            return "Running"
        else:
            return report
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
