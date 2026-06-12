
## 1. Estrutura da Aplicação

A aplicação foi construída utilizando **Python** e o framework **FastAPI**, organizada da seguinte forma:

- **`AI/app/api/`**: Camada de interface.
    - `main.py`: Define os endpoints REST (`/health` e `/move`).
    - `schemas.py`: Modelos Pydantic para validação de entrada/saída seguindo o protocolo das aulas.
    - `logic.py`: Ponte entre a API e o núcleo da IA, convertendo o estado do JSON para objetos de jogo.
- **`AI/app/core/`**: O "motor" da aplicação.
    - `gameNumpy.py` / `gameTorch.py`: Implementações otimizadas das regras do jogo usando matrizes para alta performance.
    - `minimax_iterative.py`: Implementação principal do algoritmo de busca.
    - `model.py`: Definição da arquitetura de rede neural (Dueling DQN).
    - `constants.py`: Definições globais (tabuleiro, movimentos, nomes das peças).
- **`AI/app/scripts/`**: Utilitários de desenvolvimento.
    - `train.py`: Script para treinamento por reforço da IA.
    - `test_model.py`: Script para validar a performance da IA contra agentes aleatórios.

---

## 2. Jogador Inteligente - Estratégia

Nossa estratégia foca em uma abordagem híbrida que combina **busca exaustiva otimizada** com **heurísticas avançadas**.

### Construção do Jogador
O jogador foi construído para ser resiliente e eficiente sob restrições de tempo (limite de 4 segundos por jogada). Utilizamos o **Iterative Deepening**, que permite que a IA comece explorando jogadas imediatas e vá aprofundando o raciocínio enquanto houver tempo, garantindo que sempre tenhamos uma resposta válida.

### Algoritmos Utilizados
1.  **Minimax com Alpha-Beta Pruning**: O algoritmo base para prever as jogadas do oponente e maximizar nossa vantagem.
2.  **PVS (Principal Variation Search)**: Uma otimização do Alpha-Beta que assume que a primeira jogada analisada (a melhor da profundidade anterior) é a mais provável de ser a melhor, reduzindo drasticamente o espaço de busca.
3.  **Zobrist Hashing & Transposition Table**: Implementamos um sistema de "memória" que armazena estados já calculados. Se o jogo chegar em uma posição idêntica por caminhos diferentes, a IA não precisa recalcular, economizando tempo precioso.
4.  **Dueling DQN (Deep Q-Network)**: Uma rede neural convolucional que avalia o valor de um estado do tabuleiro. Porém foi descontinuado devido a dificuldade de treinamento.

### Estratégia de Jogo
-   **Agressividade**: A prioridade máxima é dada ao avanço de nível dos professores. A IA busca constantemente subir para o nível 3.
-   **Controle de Centro**: Valorizamos posições centrais que oferecem maior mobilidade e opções de upgrade.
-   **Bloqueio Preventivo**: A IA identifica ameaças do oponente e prioriza "mentorias" (upgrades) em casas que bloqueiam o caminho do adversário.
-   **Inicialmente**: Antes de chegar na estratégia principal que foi usada, usamos o nome do grupo HoneyPot pela estratégia inicial de ao invés de vencer jogando uma peça no slot nivel 4, fazer um xeque-mate (deixando o adversário sem jogadas possiveis), mas não estava dando muito certo.

### Como Testamos
-   **Self-Play**: A IA jogou contra versões anteriores de si mesma para identificar fraquezas em sua defesa.
-   **Stress Tests**: Simulamos partidas contra agentes aleatórios e agentes "gananciosos" (que focam apenas em subir de nível).
-   **Validação de Tempo**: Monitoramos o tempo de execução para garantir que a IA nunca ultrapasse o limite do servidor, ajustando dinamicamente a profundidade da busca.
