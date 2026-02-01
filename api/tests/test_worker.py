import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from sqlmodel import Session, select

from models import QueueItem, Link
from constants import QueueStatus, MAX_RETRY_COUNT
from worker import process_queue_item


def test_process_queue_item_success(session: Session, sample_link: Link, sample_queue_item: QueueItem):
    """Test successful queue item processing"""
    session.add(sample_link)
    session.add(sample_queue_item)
    session.commit()
    session.refresh(sample_queue_item)
    
    with patch('worker.download_book') as mock_download:
        mock_download.return_value = {
            'filename': 'test.epub',
            'destination': '/path/to/test.epub'
        }
        
        result = process_queue_item(sample_queue_item, session)
        
        assert result is True
        assert sample_queue_item.status == QueueStatus.COMPLETED.value
        assert sample_queue_item.completed_at is not None
        assert sample_queue_item.error_message is None
        
        # Verify link was marked as downloaded
        link = session.exec(select(Link).where(Link.book_url == sample_link.book_url)).first()
        assert link.downloaded == 1


def test_process_queue_item_failure_with_retry(session: Session, sample_queue_item: QueueItem):
    """Test queue item failure with retry"""
    session.add(sample_queue_item)
    session.commit()
    session.refresh(sample_queue_item)
    
    with patch('worker.download_book') as mock_download:
        mock_download.side_effect = Exception("Download failed")
        
        result = process_queue_item(sample_queue_item, session)
        
        assert result is False
        assert sample_queue_item.status == QueueStatus.PENDING.value
        assert sample_queue_item.retry_count == 1
        assert sample_queue_item.error_message == "Download failed"


def test_process_queue_item_max_retries(session: Session, sample_queue_item: QueueItem):
    """Test queue item failure after max retries"""
    sample_queue_item.retry_count = MAX_RETRY_COUNT - 1
    session.add(sample_queue_item)
    session.commit()
    session.refresh(sample_queue_item)
    
    with patch('worker.download_book') as mock_download:
        mock_download.side_effect = Exception("Download failed")
        
        result = process_queue_item(sample_queue_item, session)
        
        assert result is False
        assert sample_queue_item.status == QueueStatus.FAILED.value
        assert sample_queue_item.retry_count == MAX_RETRY_COUNT
        assert "Failed after" in sample_queue_item.error_message
        assert str(MAX_RETRY_COUNT) in sample_queue_item.error_message


def test_process_queue_item_updates_status_to_in_progress(session: Session, sample_queue_item: QueueItem):
    """Test that queue item status is updated to in_progress when processing starts"""
    session.add(sample_queue_item)
    session.commit()
    session.refresh(sample_queue_item)
    
    with patch('worker.download_book') as mock_download:
        def check_status(*args, **kwargs):
            item = session.exec(select(QueueItem).where(QueueItem.id == sample_queue_item.id)).first()
            assert item.status == QueueStatus.IN_PROGRESS.value
            assert item.started_at is not None
            return {'filename': 'test.epub', 'destination': '/path'}
        
        mock_download.side_effect = check_status
        
        result = process_queue_item(sample_queue_item, session)
        assert result is True


def test_process_queue_item_no_matching_link(session: Session, sample_queue_item: QueueItem):
    """Test processing queue item when there's no matching link in database"""
    session.add(sample_queue_item)
    session.commit()
    session.refresh(sample_queue_item)
    
    with patch('worker.download_book') as mock_download:
        mock_download.return_value = {
            'filename': 'test.epub',
            'destination': '/path/to/test.epub'
        }
        
        result = process_queue_item(sample_queue_item, session)
        
        assert result is True
        assert sample_queue_item.status == QueueStatus.COMPLETED.value
