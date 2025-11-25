import os
os.system ("cls")
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finanzas.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Categoria(db.Model):
    __tablename__ = "categorias"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<Categoria {self.nombre}>"


class Movimiento(db.Model):
    __tablename__ = "movimientos"
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False)  # "ahorro" o "gasto"
    monto = db.Column(db.Float, nullable=False)
    nota = db.Column(db.String(200))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=True)
    categoria = db.relationship("Categoria", backref="movimientos")

    def __repr__(self):
        return f"<Movimiento {self.tipo} {self.monto}>"


def calcular_resumen():
    total_ahorros = db.session.query(db.func.sum(Movimiento.monto))\
        .filter(Movimiento.tipo == "ahorro").scalar() or 0.0

    total_gastos = db.session.query(db.func.sum(Movimiento.monto))\
        .filter(Movimiento.tipo == "gasto").scalar() or 0.0

    saldo = total_ahorros - total_gastos
    return float(total_ahorros), float(total_gastos), float(saldo)


@app.route("/")
def lobby():
    return render_template("lobby.html")
@app.route("/finanzas", methods=["GET", "POST"])

def index():
    error = None

    if request.method == "POST":
        tipo = request.form.get("tipo")
        monto_str = request.form.get("monto", "").strip()
        nota = request.form.get("nota", "").strip()
        categoria_id = request.form.get("categoria_id")

        # Validación de dinero
        try:
            monto = float(monto_str)
            if monto <= 0:
                raise ValueError()
        except ValueError:
            error = "El monto debe ser un número mayor a 0."
        else:
            if tipo not in ("ahorro", "gasto"):
                tipo = "gasto"

            cat_obj = None
            if tipo == "gasto" and categoria_id:
                try:
                    cat_obj = Categoria.query.get(int(categoria_id))
                except ValueError:
                    cat_obj = None

            mov = Movimiento(
                tipo=tipo,
                monto=monto,
                nota=nota,
                categoria=cat_obj
            )
            db.session.add(mov)
            db.session.commit()
            return redirect(url_for("index"))

    # GET
    movimientos = Movimiento.query.order_by(Movimiento.fecha.desc()).all()
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    total_ahorros, total_gastos, saldo = calcular_resumen()

    return render_template(
        "index.html",
        movimientos=movimientos,
        categorias=categorias,
        total_ahorros=total_ahorros,
        total_gastos=total_gastos,
        saldo=saldo,
        error=error
    )


@app.route("/categorias", methods=["GET", "POST"])
def manejar_categorias():
    error = None

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        if not nombre:
            error = "El nombre no puede estar vacío."
        else:
            # Verificar duplicados
            existente = Categoria.query.filter(
                db.func.lower(Categoria.nombre) == nombre.lower()
            ).first()
            if existente:
                error = "Esa categoría ya existe."
            else:
                cat = Categoria(nombre=nombre)
                db.session.add(cat)
                db.session.commit()
                return redirect(url_for("manejar_categorias"))

    eliminar_id = request.args.get("eliminar")
    if eliminar_id:
        cat = Categoria.query.get(eliminar_id)
        if cat:
    
            db.session.delete(cat)
            db.session.commit()
            return redirect(url_for("manejar_categorias"))

    categorias = Categoria.query.order_by(Categoria.nombre).all()
    return render_template("categorias.html", categorias=categorias, error=error)


if __name__ == "__main__":
    with app.app_context():
        db.create_all() 
    app.run(debug=True)
