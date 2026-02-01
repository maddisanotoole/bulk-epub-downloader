from enum import Enum 

class QueueStatus( Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'

MAX_RETRY_COUNT = 3
