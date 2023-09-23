import uuid

from flask import Flask, request, jsonify, Response
from sqlalchemy.dialects.postgresql import UUID

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from sqlalchemy import cast, String


app = Flask(__name__)

# Configuração do banco de dados PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://rinha:rinha@postgres/rinha'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 100
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 50
db = SQLAlchemy(app)




class Pessoa(db.Model):
    __tablename__ = 'pessoa'

    uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    apelido = db.Column(db.String(32), nullable=False, unique=True)
    nome = db.Column(db.String(100), nullable=False)
    nascimento = db.Column(db.Date, nullable=False)
    stack = db.Column(db.ARRAY(db.String(32)))

@app.route('/pessoas', methods=['POST'])
def criar_pessoa():
    uuid_var = str(uuid.uuid4())
    data = request.json

    
    if 'apelido' not in data or 'nome' not in data or 'nascimento' not in data:
        return Response(status = 422)

    if Pessoa.query.filter_by(apelido=data['apelido']).first() is not None:
        return Response(status = 422)

    try:
        nascimento = db.func.to_date(data['nascimento'], 'YYYY-MM-DD')
    except:
        return Response(status = 422)

    if 'stack' in data and (not isinstance(data['stack'], list) or not all(isinstance(item, str) for item in data['stack'])):
        return Response(status = 400)


    nova_pessoa = Pessoa(
        uuid = uuid_var,
        apelido=data['apelido'],
        nome=data['nome'],
        nascimento=nascimento,
        stack=data.get('stack', [])
    )

    db.session.add(nova_pessoa) 
    db.session.commit()

    headers = {'Location': f'/pessoas/{uuid_var}'}

    return Response(status=201, headers=headers)

@app.route('/pessoas/<uuid:obj_uuid>', methods=['GET'])
def buscar_pessoa(obj_uuid):
    obj_uuid = str(obj_uuid)

    pessoa = Pessoa.query.filter(cast(Pessoa.uuid, String) == str(obj_uuid)).first()

    if pessoa is None:
        return Response(status=404)
    else:
        return jsonify({
            'id': pessoa.uuid,
            'apelido': pessoa.apelido,
            'nome': pessoa.nome,
            'nascimento': str(pessoa.nascimento),
            'stack': pessoa.stack
        }), 200

@app.route('/limpar', methods=['GET'])
def limpar():
    Pessoa.query.delete()
    db.session.commit()
    return Response('.', status= 200)

@app.route('/pessoas', methods=['GET'])
def buscar_pessoas():
    termo_busca = request.args.get('t')
    if termo_busca:
        resultados = Pessoa.query.filter(or_(
            Pessoa.apelido.ilike(f'%{termo_busca}%'),
            Pessoa.nome.ilike(f'%{termo_busca}%'),
            Pessoa.stack.any(termo_busca)
        )).limit(50).all()
        resultados_json = [
            {
                'id': pessoa.uuid,
                'apelido': pessoa.apelido,
                'nome': pessoa.nome,
                'nascimento': str(pessoa.nascimento),
                'stack': pessoa.stack
            }
            for pessoa in resultados
        ]
        return jsonify(resultados_json), 200
    else:
        return jsonify([]), 200
    

@app.route('/contagem-pessoas', methods=['GET'])
def pessoas_count():
    return jsonify(Pessoa.query.count()), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  

    app.run(host='0.0.0.0', port=5000, debug=True)
