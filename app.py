from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from sqlalchemy import text

app = Flask(__name__)

app.secret_key = "admin123"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["UPLOAD_FOLDER"] = "static/uploads"

db = SQLAlchemy(app)

ADMIN = "Atenas"
SENHA = "159357"


class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    preco = db.Column(db.Float)
    categoria = db.Column(db.String(50))
    imagem = db.Column(db.String(200))
    ordem = db.Column(db.Integer, default=999)


@app.route("/")
def home():

    categoria = request.args.get("cat")

    if categoria:
        produtos = (
            Produto.query
            .filter_by(categoria=categoria)
            .order_by(Produto.ordem.asc())
            .all()
        )
    else:
        produtos = (
            Produto.query
            .order_by(Produto.ordem.asc())
            .all()
        )

    return render_template(
        "index.html",
        produtos=produtos
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form["usuario"]
        senha = request.form["senha"]

        if usuario == ADMIN and senha == SENHA:
            session["admin"] = True
            return redirect("/admin")

    return render_template("login.html")


@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/login")

    produtos = (
        Produto.query
        .order_by(Produto.ordem.asc())
        .all()
    )

    return render_template(
        "admin.html",
        produtos=produtos
    )


@app.route("/adicionar", methods=["POST"])
def adicionar():

    if not session.get("admin"):
        return redirect("/login")

    nome = request.form["nome"]

    preco_texto = request.form["preco"]
    preco_texto = preco_texto.replace(",", ".")

    try:
        preco = float(preco_texto)
    except:
        return "Preço inválido"

    categoria = request.form["categoria"]

    ordem = request.form.get("ordem", "999")

    try:
        ordem = int(ordem)
    except:
        ordem = 999

    arquivo = request.files["imagem"]

    if arquivo.filename == "":
        return "Escolha uma imagem"

    nome_arquivo = secure_filename(
        arquivo.filename
    )

    caminho = os.path.join(
        app.config["UPLOAD_FOLDER"],
        nome_arquivo
    )

    arquivo.save(caminho)

    produto = Produto(
        nome=nome,
        preco=preco,
        categoria=categoria,
        imagem=nome_arquivo,
        ordem=ordem
    )

    db.session.add(produto)
    db.session.commit()

    return redirect("/admin")


@app.route("/editar/<int:id>", methods=["POST"])
def editar(id):

    if not session.get("admin"):
        return redirect("/login")

    produto = Produto.query.get_or_404(id)

    produto.nome = request.form["nome"]

    preco = request.form["preco"]
    preco = preco.replace(",", ".")

    try:
        produto.preco = float(preco)
    except:
        return redirect("/admin")

    ordem = request.form.get("ordem", "999")

    try:
        produto.ordem = int(ordem)
    except:
        produto.ordem = 999

    db.session.commit()

    return redirect("/admin")


@app.route("/excluir/<int:id>")
def excluir(id):

    produto = Produto.query.get_or_404(id)

    db.session.delete(produto)

    db.session.commit()

    return redirect("/admin")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


with app.app_context():

    db.create_all()

    try:
        # verifica se a coluna já existe
        db.session.execute(
            text("SELECT ordem FROM produto LIMIT 1")
        )

    except:

        try:
            db.session.execute(
                text(
                    "ALTER TABLE produto ADD COLUMN ordem INTEGER DEFAULT 999"
                )
            )

            db.session.commit()

        except Exception as e:
            print("Erro:", e)


if __name__ == "__main__":
    app.run()