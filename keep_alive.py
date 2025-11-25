from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot de Música está online!"

def run():
  # O Replit usa a porta 8080 por padrão para expor o serviço
  app.run(host='0.0.0.0', port=8080)

def keep_alive():
  t = Thread(target=run)
  t.start()
