"""
Celery 配置

用于异步任务处理（视频处理、ASR、LLM 等）
"""
from celery import Celery
from loguru import logger

# Celery 配置
celery_app = Celery(
    'course_ai',
    broker='redis://localhost:6379/0',  # Redis Broker
    backend='redis://localhost:6379/1',  # Redis Backend（存储结果）
    include=[
        'app.tasks.video_tasks',  # 视频处理任务
        'app.tasks.asr_tasks',    # ASR 任务
        'app.tasks.llm_tasks',    # LLM 任务
    ]
)

# Celery 配置优化
celery_app.conf.update(
    # 任务序列化
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # 时区
    timezone='Asia/Shanghai',
    enable_utc=True,
    
    # 任务结果过期时间（秒）
    result_expires=3600,
    
    # 任务acks
    task_acks_late=True,
    task_reject_on_worker_or_lost=True,
    
    # 并发数
    worker_prefetch_multiplier=1,
    
    # 任务路由
    task_routes={
        'app.tasks.video_tasks.process_video_task': {'queue': 'video_processing'},
        'app.tasks.asr_tasks.transcribe_task': {'queue': 'asr'},
        'app.tasks.llm_tasks.summarize_task': {'queue': 'llm'},
    },
    
    # 队列定义
    task_queues={
        'video_processing': {
            'exchange': 'video_processing',
            'routing_key': 'video_processing',
        },
        'asr': {
            'exchange': 'asr',
            'routing_key': 'asr',
        },
        'llm': {
            'exchange': 'llm',
            'routing_key': 'llm',
        },
    },
    
    # 重试配置
    task_default_retry_delay=60,  # 重试间隔 60 秒
    task_max_retries=3,  # 最大重试 3 次
)


# 启动 Celery Worker 的命令
# celery -A app.core.celery_app worker -l info -Q video_processing,asr,llm -c 4


# 用于测试的简单任务
@celery_app.task(bind=True, max_retries=3)
def test_task(self, x, y):
    """测试任务"""
    try:
        logger.info(f"执行测试任务：{x} + {y}")
        return x + y
    except Exception as exc:
        logger.error(f"测试任务失败：{exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True)
def debug_task(self):
    """调试任务"""
    logger.info(f"请求：{self.request}")
    return 'Debug task completed'


if __name__ == '__main__':
    # 测试 Celery 配置
    print("Celery 配置测试:")
    print(f"Broker: {celery_app.conf.broker_url}")
    print(f"Backend: {celery_app.conf.result_backend}")
    print(f"Tasks: {celery_app.conf.include}")
    print(f"Queues: {list(celery_app.conf.task_queues.keys())}")
