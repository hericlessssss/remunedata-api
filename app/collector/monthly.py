"""
app/collector/monthly.py
Coleta dados de um mês específico e persiste no banco via Repositórios.
"""

import json
from datetime import datetime, timezone
from app.infra.transparencia_client import TransparenciaClient
from app.persistence.models import ExecutionMonthly, RemunerationCollected
from app.persistence.repositories import ExecutionRepository, RemunerationRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class MonthlyCollector:
    """
    Coleta dados de um mês específico e persiste no banco via Repositórios.
    """

    def __init__(
        self, 
        client: TransparenciaClient, 
        execution_repo: ExecutionRepository,
        remuneration_repo: RemunerationRepository
    ):
        self.client = client
        self.execution_repo = execution_repo
        self.remuneration_repo = remuneration_repo

    async def collect(self, ano: int, mes: str, annual_execution_id: int) -> ExecutionMonthly:
        """
        Executa a coleta para um mês/ano específico.
        """
        logger.info(f"Iniciando coleta: {mes}/{ano}")
        
        # 1. Criar registro mensal via Repo
        monthly_exec = await self.execution_repo.create_monthly(annual_execution_id, mes)
        
        page = 0
        size = 150
        
        try:
            while True:
                logger.debug(f"Coletando {mes}/{ano} - Página {page}")
                data = await self.client.get_remuneracao(ano=ano, mes=mes, page=page, size=size)
                
                content = data.get("content", [])
                num_elements = data.get("numberOfElements", 0)
                is_last = data.get("last", False)
                
                if not content or num_elements == 0:
                    logger.info(f"Fim da paginação em {mes}/{ano}: página {page} vazia.")
                    break
                
                # 2. Mapear e Salvar em lote via Repo
                records = []
                for item in content:
                    records.append(
                        RemunerationCollected(
                            execution_id=annual_execution_id,
                            monthly_execution_id=monthly_exec.id,
                            ano_exercicio=ano,
                            mes_referencia=mes,
                            codigo_identificacao=str(item.get("codigoIdentificacao", "")),
                            codigo_matricula=str(item.get("codigoMatricula", "")),
                            cpf_servidor=item.get("cpfServidor"),
                            nome_servidor=item.get("nomeServidor", "N/A"),
                            codigo_orgao=item.get("codigoOrgao"),
                            nome_orgao=item.get("nomeOrgao"),
                            situacao_funcional=item.get("situacaoFuncional"),
                            situacao_funcional_detalhada=item.get("situacaoFuncionalDetalhada"),
                            cargo=item.get("cargo"),
                            funcao=item.get("funcao"),
                            valor_remuneracao_basica=float(item.get("valorRemuneracaoBasica", 0)),
                            valor_beneficios=float(item.get("valorBeneficios", 0)),
                            valor_funcoes=float(item.get("valorFuncoes", 0)),
                            valor_comissao_conselheiro=float(item.get("valorComissaoConselheiro", 0)),
                            valor_hora_extra=float(item.get("valorHoraExtra", 0)),
                            valor_verbas_eventuais=float(item.get("valorVerbasEventuais", 0)),
                            valor_verbas_judiciais=float(item.get("valorVerbasJudiciais", 0)),
                            valor_receitas_meses_anteriores=float(item.get("valorReceitasMesesAnteriores", 0)),
                            valor_reposicao_descontos_maior=float(item.get("valorReposicaoDescontosMaior", 0)),
                            valor_licenca_premio=float(item.get("valorLicencaPremio", 0)),
                            valor_imposto_renda=float(item.get("valorImpostoRenda", 0)),
                            valor_seguridade_social=float(item.get("valorSeguridadeSocial", 0)),
                            valor_redutor_teto=float(item.get("valorRedutorTeto", 0)),
                            valor_descontos_meses_anteriores=float(item.get("valorDescontosMesesAnteriores", 0)),
                            valor_reposicao_pagamento_maior=float(item.get("valorReposicaoPagamentoMaior", 0)),
                            valor_expurgo=float(item.get("valorExpurgo", 0)),
                            valor_liquido=float(item.get("valorLiquido", 0)),
                            valor_bruto=float(item.get("valorBruto", 0)),
                            raw_payload_json=json.dumps(item)
                        )
                    )
                
                await self.remuneration_repo.save_batch(records)
                
                # 3. Atualizar contadores mensais/anuais via Repo
                monthly_exec.paginas_consumidas += 1
                monthly_exec.registros_coletados += len(records)
                
                await self.execution_repo.update_annual_progress(
                    annual_execution_id, 
                    pages=1, 
                    elements=len(records)
                )
                
                # Commit local para garantir progresso persistido
                await self.execution_repo.session.commit()
                
                # Limpar mapa de identidade para evitar consumo excessivo de memória
                self.execution_repo.session.expunge_all()

                if is_last:
                    logger.info(f"Fim da paginação em {mes}/{ano}: marca 'last=true' na pág {page}.")
                    break
                
                page += 1

            monthly_exec.status = "success"
            monthly_exec.finished_at = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Erro na coleta de {mes}/{ano}: {str(e)}")
            monthly_exec.status = "error"
            monthly_exec.error_message = str(e)
            monthly_exec.finished_at = datetime.now(timezone.utc)
            
        await self.execution_repo.session.commit()
        return monthly_exec
