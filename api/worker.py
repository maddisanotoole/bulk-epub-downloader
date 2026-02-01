import time
import sys
from datetime import datetime
from sqlmodel import Session, select
from models import engine, QueueItem, Link
from constants import QueueStatus, MAX_RETRY_COUNT
from utils.download_utils import download_book

POLL_INTERVAL = 5


def process_queue_item(queue_item: QueueItem, session: Session) -> bool:
    """
    Process a single queue item. Returns True if successful, False otherwise.
    """
    print(f"Processing queue item {queue_item.id}: {queue_item.book_title}")
    
    try:
        queue_item.status = QueueStatus.IN_PROGRESS.value
        queue_item.started_at = datetime.now().isoformat()
        session.add(queue_item)
        session.commit()
        
        result = download_book(queue_item.book_url, queue_item.book_title, None)
        
        link_statement = select(Link).where(Link.book_url == queue_item.book_url)
        link = session.exec(link_statement).first()
        if link:
            link.downloaded = 1
            session.add(link)
        
        queue_item.status = QueueStatus.COMPLETED.value
        queue_item.completed_at = datetime.now().isoformat()
        queue_item.error_message = None
        session.add(queue_item)
        session.commit()
        
        print(f"Successfully downloaded: {result['filename']} to {result['destination']}")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error processing queue item {queue_item.id}: {error_msg}")
        
        queue_item.retry_count += 1
        
        if queue_item.retry_count >= MAX_RETRY_COUNT:
            queue_item.status = QueueStatus.FAILED.value
            queue_item.error_message = f"Failed after {MAX_RETRY_COUNT} retries: {error_msg}"
            print(f"Queue item {queue_item.id} failed permanently after {MAX_RETRY_COUNT} retries")
        else:
            queue_item.status = QueueStatus.PENDING.value
            queue_item.error_message = error_msg
            print(f"Queue item {queue_item.id} will retry (attempt {queue_item.retry_count}/{MAX_RETRY_COUNT})")
        
        session.add(queue_item)
        session.commit()
        return False


def run_worker():
    """
    Main worker loop that continuously polls the queue and processes items.
    """
    print("Starting queue worker...")
    print(f"Polling interval: {POLL_INTERVAL} seconds")
    print(f"Max retry count: {MAX_RETRY_COUNT}")
    
    try:
        while True:
            try:
                with Session(engine) as session:
                    statement = select(QueueItem).where(
                        QueueItem.status == QueueStatus.PENDING.value
                    ).order_by(QueueItem.created_at).limit(1)
                    
                    queue_item = session.exec(statement).first()
                    
                    if queue_item:
                        process_queue_item(queue_item, session)
                    else:
                        print("Queue is empty, waiting...")
                
            except Exception as e:
                print(f"Error in worker loop: {e}")
                import traceback
                traceback.print_exc()
            
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        print("\nWorker stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    run_worker()
