import discord
from keep_alive import keep_alive # Importação para manter o bot online no Replit
from discord.ext import commands
import yt_dlp
import asyncio
import os

# Configuração do yt-dlp
yt_dlp.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # Pega o primeiro item se for uma playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = {} # Fila de músicas por guild_id
        self.is_playing = {} # Estado de reprodução por guild_id

    async def check_queue(self, ctx):
        guild_id = ctx.guild.id
        if self.queue.get(guild_id) and self.queue[guild_id]:
            # Pega a próxima música da fila
            next_song = self.queue[guild_id].pop(0)
            
            # Toca a próxima música
            source = await YTDLSource.from_url(next_song['url'], loop=self.bot.loop, stream=True)
            ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(self.check_queue(ctx), self.bot.loop).result())
            
            await ctx.send(f'Tocando agora: **{source.title}**')
        else:
            # Se a fila estiver vazia, desconecta após um tempo
            await asyncio.sleep(300) # 5 minutos
            if ctx.voice_client and not ctx.voice_client.is_playing():
                await ctx.voice_client.disconnect()
                self.is_playing[guild_id] = False

    @commands.command(name='join', help='Faz o bot entrar no canal de voz atual')
    async def join(self, ctx):
        if not ctx.author.voice:
            return await ctx.send('Você precisa estar em um canal de voz para usar este comando.')

        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        
        await channel.connect()
        await ctx.send(f'Conectado ao canal: **{channel.name}**')

    @commands.command(name='play', help='Toca uma música do YouTube (ou adiciona à fila)')
    async def play(self, ctx, *, url):
        if not ctx.voice_client:
            await ctx.invoke(self.join)

        guild_id = ctx.guild.id
        
        async with ctx.typing():
            try:
                # Usa from_url com stream=True para não baixar o arquivo, apenas o link de stream
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            except Exception as e:
                await ctx.send(f'Ocorreu um erro ao tentar carregar a música: {e}')
                return

            if ctx.voice_client.is_playing():
                # Adiciona à fila
                if guild_id not in self.queue:
                    self.queue[guild_id] = []
                
                # Para adicionar à fila, precisamos apenas da URL e do título (se disponível)
                # O YTDLSource.from_url já faz a extração de info, vamos re-extrair para a fila
                # para garantir que temos o título correto.
                try:
                    info = await self.bot.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
                    if 'entries' in info:
                        info = info['entries'][0]
                    
                    self.queue[guild_id].append({'url': url, 'title': info.get('title', 'Música desconhecida')})
                    await ctx.send(f'**{info.get("title", "Música desconhecida")}** adicionada à fila.')
                except Exception as e:
                    await ctx.send(f'Erro ao adicionar à fila: {e}')
            else:
                # Toca imediatamente
                ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.check_queue(ctx), self.bot.loop).result())
                self.is_playing[guild_id] = True
                await ctx.send(f'Tocando agora: **{player.title}**')

    @commands.command(name='volume', help='Muda o volume de reprodução (0-100)')
    async def volume(self, ctx, volume: int):
        if ctx.voice_client is None:
            return await ctx.send("Não estou conectado a um canal de voz.")

        if 0 <= volume <= 100:
            ctx.voice_client.source.volume = volume / 100
            await ctx.send(f"Volume alterado para {volume}%")
        else:
            await ctx.send("O volume deve ser um número entre 0 e 100.")

    @commands.command(name='stop', help='Para a música e desconecta o bot')
    async def stop(self, ctx):
        guild_id = ctx.guild.id
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.is_playing[guild_id] = False
            if guild_id in self.queue:
                self.queue[guild_id].clear()
            await ctx.send('Parado e desconectado.')

    @commands.command(name='skip', help='Pula a música atual')
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send('Música pulada.')
        else:
            await ctx.send('Não há música tocando para pular.')

    @commands.command(name='queue', help='Mostra a fila de músicas')
    async def show_queue(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in self.queue and self.queue[guild_id]:
            q = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(self.queue[guild_id])])
            await ctx.send(f'**Fila de Músicas:**\n{q}')
        else:
            await ctx.send('A fila de músicas está vazia.')

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("Você não está conectado a um canal de voz.")
                raise commands.CommandError("Autor não conectado a um canal de voz.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

# --- Configuração e Inicialização do Bot ---

# O token do bot será lido de uma variável de ambiente para segurança
TOKEN = os.environ.get('DISCORD_TOKEN')

# Definindo as permissões (Intents) necessárias
intents = discord.Intents.default()
intents.message_content = True # Necessário para ler o conteúdo dos comandos
intents.voice_states = True # Necessário para interagir com canais de voz

# Criação do objeto Bot
bot = commands.Bot(
    command_prefix='!', # Prefixo para os comandos (ex: !play)
    intents=intents,
    help_command=None # Remove o comando de ajuda padrão para simplificar
)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user} (ID: {bot.user.id})')
    print('------')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="música! Use !help"))

@bot.command(name='help', help='Mostra a lista de comandos disponíveis')
async def help_command(ctx):
    help_text = "Comandos disponíveis:\n"
    for command in bot.commands:
        if command.help:
            help_text += f"**!{command.name}**: {command.help}\n"
    await ctx.send(help_text)

async def main():
    await bot.add_cog(Music(bot))
    if TOKEN:
        await bot.start(TOKEN)
    else:
        print("ERRO: Variável de ambiente DISCORD_TOKEN não definida.")

if __name__ == '__main__':
    keep_alive() # Inicia o servidor web para manter o Repl ativo
    # O bot.run() é bloqueante, mas para usar o asyncio.run() e o main()
    # de forma mais limpa, usamos o loop do asyncio.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot desligado.")
    except Exception as e:
        print(f"Erro fatal: {e}")

# O bot.run() é bloqueante, mas para usar o asyncio.run() e o main()
# de forma mais limpa, usamos o loop do asyncio.
# bot.run(TOKEN) # Alternativa mais simples, mas menos flexível com asyncio.run()
