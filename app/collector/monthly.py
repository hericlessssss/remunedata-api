"""
app/collector/monthly.py
Serviço de orquestração para coleta de dados de remuneração de um mês específico.
Integra TransparenciaClient com a camada de persistência.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.infra.transparencia_client import TransparenciaClient
from app.persistence.models import ExecutionAnnual, ExecutionMonthly, RemunerationCollected
from app.core.logging import get_logger

logger = get_logger(__name__)


class MonthlyCollector:
    """
    Orquestra a coleta de uma competência mensal (ano + mês).
    Handles pagination, persistence, and status updates.
    """

    def __init__(self, client: TransparenciaClient, session: AsyncSession):
        self.client = client
        self.session = session

    async def collect(self, ano: int, mes: str, annual_execution_id: int) -> ExecutionMonthly:
        """
        Executa a coleta para o mês e ano informados.
        """
        logger.info(f"Iniciando coleta mensal: {ano}/{mes} para execução anual {annual_execution_id}")
        
        # 1. Criar registro de execução mensal
        monthly_exec = ExecutionMonthly(
            execution_id=annual_execution_id,
            mes_referencia=mes,
            status="running",
            started_at=datetime.now(timezone.utc)
        )
        self.session.add(monthly_exec)
        await self.session.commit()
        await self.session.refresh(monthly_exec)

        total_registros_mes = 0
        total_paginas_mes = 0
        
        try:
            page = 0
            size = 150  # Conforme doc 11
            
            while True:
                logger.debug(f"Coletando página {page} para {ano}/{mes}")
                
                # 2. Chamar API
                api_response = await self.client.get_remuneracao(
                    ano=ano, 
                    mes=mes, 
                    page=page, 
                    size=size
                )
                
                content: List[Dict[str, Any]] = api_response.get("content", [])
                is_last = api_response.get("last", True)
                
                # Atualizar info do response na primeira página
                if page == 0:
                    monthly_exec.total_pages_informado = api_response.get("totalPages")
                    monthly_exec.total_elements_informado = api_response.get("totalElements")

                # 3. Processar e Salvar registros
                if content:
                    records = []
                    for item in content:
                        # Mapear campos da API para o modelo
                        # Nota: No futuro, podemos usar um Dto/Schema se a lógica de mapeamento crescer
                        record = RemunerationCollected(
                            execution_id=annual_execution_id,
                            monthly_execution_id=monthly_exec.id,
                            ano_exercicio=ano,
                            mes_referencia=mes,
                            codigo_identificacao=str(item.get("id", "")),
                            codigo_matricula=str(item.get("matricula", "")),
                            cpf_servidor=item.get("cpf"),
                            nome_servidor=item.get("nome", "N/A"),
                            codigo_orgao=item.get("codigoOrgao"),
                            nome_orgao=item.get("orgao"),
                            situacao_funcional=item.get("situacaoFuncional"),
                            cargo=item.get("cargo"),
                            funcao=item.get("funcao"),
                            # Valores financeiros (garantir float)
                            valor_remuneracao_basica=float(item.get("remuneracaoBasica", 0)),
                            valor_beneficios=float(item.get("beneficios", 0)),
                            valor_funcoes=float(item.get("remuneracaoCargoFuncao", 0)),
                            valor_liquido=float(item.get("valorLiquido", 0)),
                            valor_bruto=float(item.get("remuneracaoBruta", 0)),
                            # Payload bruto para auditoria
                            raw_payload_json=json.dumps(item),
                            created_at=datetime.now(timezone.utc)
                        )
                        records.append(record)
                    
                    self.session.add_all(records)
                    total_registros_mes += len(records)
                
                total_paginas_mes += 1
                
                # 4. Condição de parada (Doc 11)
                if is_last or not content:
                    logger.info(f"Fim da paginação: página {page} era a última ou content vazio.")
                    break
                
                page += 1
            
            # 5. Finalizar execução mensal com sucesso
            monthly_exec.status = "success"
            monthly_exec.paginas_consumidas = total_paginas_mes
            monthly_exec.registros_coletados = total_registros_mes
            monthly_exec.finished_at = datetime.now(timezone.utc)
            
            # 6. Atualizar execução anual (contadores)
            # Usando statement para evitar carregar toda a annual_exec se for muito grande
            # Mas aqui é mais simples apenas atualizar o objeto se já tivermos em cache 
            # (assume-se que quem chamou collect() controla a transação anual se necessário)
            # Para este MVP, vamos atualizar no final do mês.
            await self.session.execute(
                update(ExecutionAnnual)
                .where(ExecutionAnnual.id == annual_execution_id)
                .values(
                    total_meses_processados=ExecutionAnnual.total_meses_processados + 1,
                    total_paginas_consumidas=ExecutionAnnual.total_paginas_consumidas + total_paginas_mes,
                    total_registros_coletados=ExecutionAnnual.total_registros_coletados + total_registros_mes
                )
            )
            
            await self.session.commit()
            logger.info(f"Coleta mensal {ano}/{mes} finalizada com sucesso. {total_registros_mes} registros.")
            
        except Exception as e:
            logger.error(f"Erro na coleta mensal {ano}/{mes}: {str(e)}")
            monthly_exec.status = "error"
            monthly_exec.error_message = str(e)
            monthly_exec.finished_at = datetime.now(timezone.utc)
            await self.session.commit()
            raise e
            
        return monthly_exec
