from flask import Flask
from globalVar import *

app = Flask(__name__)


@app.route('/')
def index():
    return 'successfully'


if __name__ == '__main__':
    server_args = config['server-args']
    app.run(host=server_args['local_ip'], port=server_args['server_port'],
            ssl_context=(server_args['CA_pem'], server_args['CA_key']))
