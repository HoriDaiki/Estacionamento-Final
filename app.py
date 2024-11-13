from flask import Flask, render_template, request, redirect, url_for
import datetime
import numpy as np

app = Flask(__name__)

TOTAL_VAGAS = 10
vagas = [None] * TOTAL_VAGAS
historico = []
TARIFA_FIXA = 10.00

@app.route('/')
def index():
    return render_template('index.html', total_vagas=TOTAL_VAGAS, vagas=vagas)

@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
    if request.method == 'POST':
        placa = request.form['placa']
        tipo_veiculo = request.form['tipo_veiculo']
        vaga_id = alocar_vaga(tipo_veiculo)

        if vaga_id is not None:
            vagas[vaga_id] = {'placa': placa, 'entrada': datetime.datetime.now(), 'saida': None}
            return redirect(url_for('confirmacao', vaga_id=vaga_id, placa=placa))
        else:
            mensagem = "Não há vagas disponíveis para o tipo de veículo escolhido."
            return render_template('adicionar.html', total_vagas=TOTAL_VAGAS, vagas=vagas, mensagem=mensagem)

    return render_template('adicionar.html', total_vagas=TOTAL_VAGAS, vagas=vagas)

@app.route('/confirmacao')
def confirmacao():
    vaga_id = request.args.get('vaga_id', type=int)
    placa = request.args.get('placa')

    return render_template('confirmacao.html', vaga_id=vaga_id, placa=placa)

def alocar_vaga(tipo_veiculo):
    if tipo_veiculo == 'acessibilidade':
        for vaga_id in range(3):  # Vagas 0, 1, 2
            if vagas[vaga_id] is None:
                return vaga_id
    elif tipo_veiculo == 'normal':
        for vaga_id in range(3, 7):  # Vagas 3, 4, 5, 6
            if vagas[vaga_id] is None:
                return vaga_id
    elif tipo_veiculo == 'grande':
        for vaga_id in range(7, 11):  # Vagas 7, 8, 9, 10
            if vagas[vaga_id] is None:
                return vaga_id
    return None


@app.route('/saida', methods=['GET', 'POST'])
def saida():
    if request.method == 'POST':
        vaga_id = request.form.get('vaga_id', type=int)
        if vaga_id is not None and 0 <= vaga_id < TOTAL_VAGAS:
            if vagas[vaga_id] is not None:
                return redirect(url_for('remover', vaga_id=vaga_id))
            else:
                print(f"A vaga {vaga_id} está vazia!")
                return redirect(url_for('index'))
    
    return render_template('saida.html', total_vagas=TOTAL_VAGAS, vagas=vagas)

@app.route('/remover/<int:vaga_id>')
def remover(vaga_id):
    print(f"Tentando remover a vaga: {vaga_id}")

    if vaga_id < 0 or vaga_id >= TOTAL_VAGAS:
        return redirect(url_for('index'))

    veiculo = vagas[vaga_id]
    
    if veiculo is None:
        print(f"A vaga {vaga_id} está vazia. Não é possível remover.")
        return redirect(url_for('index'))
    
    saida = datetime.datetime.now()
    tempo_estacionado = saida - veiculo['entrada']
    
    horas_estacionadas = tempo_estacionado.total_seconds() / 3600
    custo = max(TARIFA_FIXA, horas_estacionadas * TARIFA_FIXA)
    
    historico.append({
        'placa': veiculo['placa'],
        'entrada': veiculo['entrada'],
        'saida': saida,
        'custo': custo
    })
    
    atualizar_dados(historico[-1])

    vagas[vaga_id] = None  
    
    return redirect(url_for('recibo', placa=veiculo['placa'], entrada=veiculo['entrada'].isoformat(), saida=saida.isoformat(), custo=custo, vaga_id=vaga_id))

@app.route('/recibo')
def recibo():
    placa = request.args.get('placa')
    entrada = request.args.get('entrada')
    saida = request.args.get('saida')
    custo = request.args.get('custo', type=float)
    vaga_id = request.args.get('vaga_id', type=int)

    return render_template('recibo.html', placa=placa, entrada=datetime.datetime.fromisoformat(entrada), saida=datetime.datetime.fromisoformat(saida), custo=custo, vaga_id=vaga_id)


@app.route('/relatorios')
def relatorios():
    ocupacao_media = np.mean([1 for vaga in vagas if vaga is not None]) / TOTAL_VAGAS * 100
    
    horarios = [veiculo['entrada'].hour for veiculo in historico if veiculo['saida'] is None]
    horario_pico = max(set(horarios), key=horarios.count) if horarios else None
    
    return render_template('relatorios.html', 
                           ocupacao_media=ocupacao_media,
                           receita_total=receita_total,
                           horario_pico=horario_pico,
                           total_entradas=total_entradas,
                           total_saidas=total_saidas)

total_entradas = 0
total_saidas = 0
receita_total = 0.0

def atualizar_dados(entrada):
    global total_entradas, total_saidas, receita_total
    total_entradas += 1
    if entrada['saida'] is not None:
        total_saidas += 1
        receita_total += entrada['custo']

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form['senha']
        if senha == 'admin':
            return redirect(url_for('relatorios'))
        else:
            return render_template('login.html', erro="Senha incorreta!")
    
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
