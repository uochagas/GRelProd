import psycopg2
from tqdm import tqdm


def get_chamados(config, month, year, ultimodia):

    user = config['ID_USER']

    conn = psycopg2.connect(
        host=config['DB_HOST'],
        database=config['DB_DATABASE'],
        user=config['DB_USERNAME'],
        password=config['DB_PASSWORD']
    )

    cur = conn.cursor()

    cur.execute(f"""
        SELECT cc.chamado_id, texto, to_char(data_hora, 'DD/MM/YYYY') as create_at
        FROM centralservicos_comunicacao cc
        LEFT JOIN auth_user au ON au.id = cc.remetente_id
        WHERE au.username = '{user}' 
        AND data_hora >= '{year}-{month}-01' 
        AND data_hora <= '{year}-{month}-{ultimodia}';
    """)
    rows = cur.fetchall()
    chamados = []
    for row in rows:
        activity = {
            'chamado': row[0],
            'message': row[1],
            'created_at': row[2],
        }
        chamados.append(activity)

    return chamados


def write_chamados(chamados):
    # adicionando os chamados
    texto = ""
    lista = list()
    bloco = ""
    print(f"processando {len(chamados)} encontrados...")
    for chamado in tqdm(chamados):
        if bloco != chamado['created_at']:
            if bloco != "":
                texto += (f"   Em {bloco}: {str(', '.join(lista))}\n")
                lista = list()
            bloco = chamado['created_at']
            lista.append(str(chamado['chamado']))
        else:
            lista.append(str(chamado['chamado']))
    texto += (f"   Em {bloco}: {str(', '.join(lista))}\n\n")
    return texto


def generate_report_chamados(config, month, year, ultimodia):

    chamados = get_chamados(config, month, year, ultimodia)

    # Salvar as atividades e chamados em arquivos de texto
    all_chamados = write_chamados(chamados)

    # Gerar o relatório consolidado
    print("Gerando relatório consolidado...")
    consolidated_report = f"Relatório consolidado para {month}/{year}\n\n"
    consolidated_report += "Atendimento aos chamados:\n"
    consolidated_report += "----------------------------------------------\n"
    consolidated_report += f"{all_chamados}\n\n"

    # Salvar o relatório consolidado em um arquivo de texto
    filename = f"{config['DIR_CHAMADOS']}chamados_report_{month}_{year}.txt"
    with open(filename, 'w') as file:
        file.write(consolidated_report)

    print(f"Relatório consolidado salvo em {filename}.")
