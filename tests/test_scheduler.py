"""
tests/test_scheduler.py
Testes para verificação do agendamento (Celery Beat).
"""

import pytest
from unittest.mock import patch
from app.core.celery_app import celery_app
from app.workers.tasks import sync_recent_years_task


def test_celery_beat_schedule_defined():
    """Verifica se o agendamento está presente na configuração do Celery."""
    schedule = celery_app.conf.beat_schedule
    assert "sync-recent-years-weekly" in schedule
    assert schedule["sync-recent-years-weekly"]["task"] == "sync_recent_years_task"


def test_sync_recent_years_task_queues_two_tasks():
    """Verifica se a tarefa de sincronização enfileira o ano atual e o anterior."""
    from datetime import datetime
    current_year = datetime.now().year
    previous_year = current_year - 1
    
    with patch("app.workers.tasks.collect_annual_task.delay") as mock_delay:
        result = sync_recent_years_task()
        
        assert result["status"] == "queued"
        assert previous_year in result["years"]
        assert current_year in result["years"]
        
        # Deve ter sido chamado duas vezes (um para cada ano)
        assert mock_delay.call_count == 2
        
        # Verificar chamadas específicas
        # Note: Ordem importa no assert_any_call, mas o sync_recent_years_task faz previous depois current
        mock_delay.assert_any_call(previous_year)
        mock_delay.assert_any_call(current_year)
