# MINDCoat OS

## Sobre
O MINDCoat OS é um sistema de controle para o equipamento de recobrimento por imersão (dip coater) PTL-6PB. O projeto tem como objetivo substituir os controladores legados de fábrica por uma interface moderna e intuitiva, permitindo o gerenciamento preciso de processos de deposição de filmes finos.

## O que este sistema faz
* **Automação de Movimento:** Controle do Eixo Z com parâmetros ajustáveis de velocidade, tempo de imersão e ciclos de repetição.
* **Monitoramento Térmico:** Gerenciamento independente das 6 estações de aquecimento, permitindo controle de temperatura e detecção de falhas nos sensores.
* **Agitação Controlada:** Ativação individual dos motores de agitação para cada béquere.
* **Gerenciamento de Receitas:** Interface para salvar e carregar configurações de processo recorrentes.

## Tecnologias Utilizadas
* **Backend:** Python com Flask para o servidor e processamento da lógica de controle.
* **Frontend:** Interface Web (SPA) construída com HTML5, Tailwind CSS e Vanilla JavaScript.
* **Integração:** Arquitetura baseada em API para comunicação entre o hardware de controle e a interface do usuário.

## Status
Em desenvolvimento.
