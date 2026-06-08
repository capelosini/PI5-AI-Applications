## 1. Tecnologias Utilizadas
- **React (Vite):** Escolhido pela performance, suporte a Fast Refresh e facilidade de configuração.
- **React Router:** Para gestão de navegação entre a Lobby (Home) e a Tela de Espectador.
- **WebSockets:** Para atualização em tempo real das partidas na tela de espectador.

## 2. Organização do Projeto
A estrutura de pastas foi organizada para separar claramente as responsabilidades:

- **`/src/routes`**: Contém os componentes de "página" (Home e Spectate). Eles gerenciam o estado principal e coordenam a busca de dados.
- **`/src/components`**: Componentes de UI reutilizáveis e modulares (GameBoard, MatchList, MatchEntry, etc.).
- **`/src/utils`**: Lógica de negócio, classes de modelo (Entity classes) e gerenciadores de persistência.
- **`/src/styles`**: Centralização da estilização em CSS puro para manter o projeto leve e de fácil customização.

## 3. Decisões de Componentização e Motivações

### Separação de Rotas e Componentes
- **Motivação:** Ao isolar as rotas em `Home.jsx` e `Spectate.jsx`, conseguimos manter os componentes de UI com suas responsabilidades isoladas (`MatchList`, `GameBoard`), ou seja, eles apenas recebem dados via props e emitem eventos. Isso facilita o teste e a reutilização.

### Uso de Classes de Modelo (Match, Player)
- **Motivação:** Em vez de lidar com objetos JSON brutos da API em todo o código, criamos classes em `utils/`.
- **Benefício:** Permite encapsular lógica de formatação (ex: `match.formattedStatus`, `player.winRate`) e garantir que o frontend não quebre se nomes de campos na API mudarem ligeiramente, bastando ajustar o construtor da classe.

### Persistência com AccountManager
- **Motivação:** Para cumprir o requisito de manter o `access_token` do jogador, criamos o `AccountManager`. Ele centraliza o uso do `localStorage`.
- **Decisão:** Optamos por permitir a gestão de múltiplas contas (Import/Export), facilitando testes com diferentes IAs sem precisar recriar jogadores manualmente.

### Tela de Espectador (Real-time)
- **Motivação:** A tela de espectador precisa refletir o estado do jogo instantaneamente.
- **Implementação:** Utilizamos WebSockets para receber updates. Caso a conexão falhe, o componente possui um mecanismo de *fallback* que faz polling periódico via HTTP para garantir que o usuário nunca fique com dados defasados.

## 4. UI/UX
- **Visual "Dark Mode":** Escolhido para dar uma estética moderna e técnica ao projeto de IA.
- **Feedback Visual:** Uso de estados de loading e mensagens de erro claras para melhorar a experiência do usuário durante interações com a API.
