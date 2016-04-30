from __future__ import (
    print_function,
    absolute_import,
)

import json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/collaborate.db'
db = SQLAlchemy(app)


@app.route("/get_gentrified")
def get_gentrified():
    return json.dumps({
        "memes": "spicy"
    })

if __name__ == '__main__':
    app.run()
