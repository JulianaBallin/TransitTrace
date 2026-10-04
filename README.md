<div align="center">
  <img src="assets/logo-rota-em-dia.png" alt="Logo Rota em Dia" width="280">

  # TransitTrace

  **Projeto Rota em Dia · análise da pontualidade do transporte fretado**

  Projeto integrador do curso de Fundamentos de IA e Programação.

  [![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JulianaBallin/TransitTrace/blob/main/transporte_fretado_rota_em_dia.ipynb)
</div>

---

## Objetivo

Investigar por que os atrasos aumentaram, onde se concentram e quais evidências sustentam a explicação mais plausível. O material foi preparado para apresentação acadêmica e execução no Google Colab.

Equipe:

- Juliana Ballin Lima
- Fernanda de Oliveira da Costa
- Pedro Henrique Oliveira Dias

## Entregáveis

| Arquivo | Finalidade |
| --- | --- |
| [transporte_fretado_rota_em_dia.ipynb](transporte_fretado_rota_em_dia.ipynb) | Notebook Colab executado, com as quatro etapas e a narrativa final |
| [apresentacao_rota_em_dia.pptx](apresentacao_rota_em_dia.pptx) | Apresentação editável de oito slides |
| [apresentacao_rota_em_dia.pdf](apresentacao_rota_em_dia.pdf) | Versão da apresentação para visualização e compartilhamento |
| [relatorio_tecnico_rota_em_dia.pdf](relatorio_tecnico_rota_em_dia.pdf) | Relatório técnico A4 com 14 páginas |
| [projeto_integrador_transporte_fretado.csv](projeto_integrador_transporte_fretado.csv) | Base bruta preservada |
| [dados_tratados_transporte_fretado.csv](dados_tratados_transporte_fretado.csv) | Base resultante do pipeline reproduzível |
| [assets/logo-rota-em-dia.png](assets/logo-rota-em-dia.png) | Logo do projeto com fundo transparente |

## Execução no Google Colab

1. Abra o Google Colab.
2. Faça upload do notebook e do CSV bruto.
3. Abra `transporte_fretado_rota_em_dia.ipynb`.
4. Selecione **Ambiente de execução > Executar tudo**.

Se o CSV não estiver disponível na sessão, o notebook solicitará o upload. A última célula exporta a base tratada.

## Resultado principal

A pontualidade de R03 e R05 caiu nos turnos diurnos desde 6 de abril. Obras no corredor são a explicação mais plausível, ainda dependente de confirmação com GPS e cronogramas.

## Estrutura

```text
TransitTrace/
├── assets/                 # Logos do projeto e institucionais
├── fontes/                 # Scripts reprodutíveis
├── graficos/               # Figuras usadas nos documentos
├── *.csv                   # Bases bruta e tratada
├── *.ipynb                 # Notebook Colab
├── *.pptx                  # Slides editáveis
└── *.pdf                   # Slides e relatório para compartilhamento
```

## Regeneração local

As fontes exigem Python 3.12 ou compatível, LibreOffice e as dependências de [requirements.txt](requirements.txt).

```bash
make menu
```

O alvo `make setup` cria o ambiente `.venv-rota-em-dia`. O alvo `make tudo` reconstrói dados tratados, gráficos, notebook executado, slides e relatório.

## Repositório

[github.com/JulianaBallin/TransitTrace](https://github.com/JulianaBallin/TransitTrace)

O botão no início deste README abre o notebook da branch principal diretamente no Google Colab.
