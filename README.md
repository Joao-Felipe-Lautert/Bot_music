# Tutorial: Bot de Música para Discord 24/7 Gratuito

Este guia completo irá te ajudar a configurar e hospedar seu próprio bot de música para Discord, usando Python e a biblioteca `py-cord`.

## 1. Configuração do Bot no Portal do Desenvolvedor do Discord

Para que seu bot funcione, você precisa criar um aplicativo e obter um **Token** no site do Discord.

### 1.1. Criar o Aplicativo

1.  Acesse o [Portal do Desenvolvedor do Discord](https://discord.com/developers/applications) e faça login.
2.  Clique em **"New Application"** (Nova Aplicação).
3.  Dê um nome ao seu aplicativo (ex: "Manus Music Bot") e clique em **"Create"** (Criar).

### 1.2. Criar o Bot e Obter o Token

1.  No menu lateral esquerdo, clique em **"Bot"**.
2.  Clique em **"Add Bot"** (Adicionar Bot) e confirme.
3.  **Token:** O token do seu bot será exibido. Clique em **"Copy"** (Copiar). **Mantenha este token em segredo!** Ele é a "senha" do seu bot.
    *   *Nota: Se você perder ou expor o token, clique em **"Reset Token"** para gerar um novo.*

### 1.3. Configurar Permissões (Intents)

Para que o bot possa ler mensagens de comando e interagir com canais de voz, você precisa habilitar as permissões (Intents) necessárias:

1.  Na mesma página **"Bot"**, role para baixo até a seção **"Privileged Gateway Intents"**.
2.  Habilite as seguintes opções:
    *   **PRESENCE INTENT** (Opcional, mas recomendado para status)
    *   **SERVER MEMBERS INTENT** (Opcional, mas recomendado)
    *   **MESSAGE CONTENT INTENT** (Obrigatório para ler comandos como `!play`)

### 1.4. Adicionar o Bot ao Seu Servidor

1.  No menu lateral, clique em **"OAuth2"** e depois em **"URL Generator"**.
2.  Em **"Scopes"** (Escopos), selecione:
    *   `bot`
3.  Em **"Bot Permissions"** (Permissões do Bot), selecione as permissões mínimas necessárias para um bot de música:
    *   `Connect` (Conectar)
    *   `Speak` (Falar)
    *   `Send Messages` (Enviar Mensagens)
    *   `Read Message History` (Ler Histórico de Mensagens)
4.  Copie o **URL gerado** na parte inferior da página e cole-o no seu navegador.
5.  Selecione o servidor onde você deseja adicionar o bot e clique em **"Authorize"** (Autorizar).

## 2. Hospedagem Gratuita 24/7 com Replit

Para manter seu bot online 24 horas por dia, 7 dias por semana, de forma gratuita, usaremos o **Replit** em conjunto com um serviço de *uptime* (como o UptimeRobot, embora o Replit tenha métodos internos que funcionam bem para bots).

### 2.1. Preparar os Arquivos

1.  Crie uma conta gratuita no [Replit](https://replit.com/).
2.  Clique em **"Create Repl"** (Criar Repl).
3.  Selecione **"Python"** como template.
4.  Dê um nome ao seu projeto (ex: `discord-music-bot-247`).

### 2.2. Configurar o Ambiente no Replit

1.  **Adicionar o Código:**
    *   No Replit, crie um novo arquivo chamado `bot.py` e cole o código que eu te forneci.
    *   Crie um arquivo chamado `requirements.txt` e adicione as seguintes linhas:
        ```
        py-cord
        yt-dlp
        ffmpeg
        ```
    *   O Replit irá instalar automaticamente as dependências listadas em `requirements.txt`.

2.  **Configurar o Token (Variável de Ambiente):**
    *   No Replit, clique no ícone de **"Secrets"** (Segredos) (um cadeado) no menu lateral.
    *   Clique em **"New Secret"** (Novo Segredo).
    *   Para **KEY** (Chave), digite: `DISCORD_TOKEN`
    *   Para **VALUE** (Valor), cole o **Token do Bot** que você copiou na seção 1.2.
    *   Isso garante que seu token fique seguro e não seja exposto no código.

3.  **Instalar o FFmpeg:**
    *   O FFmpeg é necessário para processar o áudio. No Replit, abra o **Shell** (Terminal).
    *   Execute o seguinte comando para garantir que o FFmpeg esteja instalado (o Replit geralmente já o tem, mas é bom garantir):
        ```bash
        sudo apt update && sudo apt install ffmpeg -y
        ```

### 2.3. Manter o Bot Online 24/7

O Replit é um ambiente de desenvolvimento, e os Repls podem entrar em modo de suspensão. Para evitar isso, você precisa garantir que o bot esteja sempre acessível.

1.  **Expor uma Porta:**
    *   O bot precisa de um servidor web simples para que o Replit o considere "ativo".
    *   Crie um novo arquivo chamado `keep_alive.py` e adicione o seguinte código (usando `flask` ou `http.server` se preferir, mas um servidor simples é o suficiente):

        ```python
        from flask import Flask
        from threading import Thread

        app = Flask('')

        @app.route('/')
        def home():
            return "Bot de Música está online!"

        def run():
          app.run(host='0.0.0.0', port=8080)

        def keep_alive():
          t = Thread(target=run)
          t.start()
        ```

2.  **Integrar ao `bot.py`:**
    *   **Importe** a função `keep_alive` no topo do seu `bot.py`.
    *   **Adicione** a chamada à função `keep_alive()` antes de `asyncio.run(main())` no final do seu `bot.py`.

    Seu `bot.py` modificado (apenas as partes de inicialização) deve ficar assim:

    ```python
    # ... (todo o código do bot) ...

    # --- Configuração e Inicialização do Bot ---

    # ... (código de intents e bot) ...

    # Adicione esta linha no topo do seu bot.py:
    from keep_alive import keep_alive 

    async def main():
        await bot.add_cog(Music(bot))
        if TOKEN:
            await bot.start(TOKEN)
        else:
            print("ERRO: Variável de ambiente DISCORD_TOKEN não definida.")

    if __name__ == '__main__':
        # 1. Inicia o servidor web para manter o Repl ativo
        keep_alive() 
        
        # 2. Inicia o bot
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("Bot desligado.")
        except Exception as e:
            print(f"Erro fatal: {e}")
    ```

3.  **Executar:**
    *   Clique em **"Run"** (Executar) no Replit. O bot deve iniciar e o servidor web deve estar rodando na porta 8080.
    *   O Replit manterá o bot ativo enquanto o servidor web estiver respondendo.

## 3. Comandos do Bot

O prefixo de comando é `!`.

| Comando | Descrição | Exemplo |
| :--- | :--- | :--- |
| `!join` | Faz o bot entrar no seu canal de voz. | `!join` |
| `!play <url/termo>` | Toca uma música do YouTube ou adiciona à fila. | `!play Never Gonna Give You Up` ou `!play https://youtu.be/dQw4w9WgXcQ` |
| `!skip` | Pula a música atual. | `!skip` |
| `!queue` | Mostra a lista de músicas na fila. | `!queue` |
| `!volume <0-100>` | Ajusta o volume de reprodução. | `!volume 50` |
| `!stop` | Para a música e desconecta o bot. | `!stop` |
| `!help` | Mostra a lista de comandos. | `!help` |

**Observação:** O bot usa `yt-dlp` para streaming, o que significa que ele não baixa o arquivo completo, economizando espaço e tempo, mas requer uma conexão estável.
