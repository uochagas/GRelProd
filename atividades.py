import gitlab
import psycopg2
from tqdm import tqdm
from dateutil.parser import parse


def connect_to_gitlab(config):
    gl = gitlab.Gitlab(
        config['GITLAB_URL'], 
        private_token=config['GITLAB_TOKEN'], 
        api_version='4'
    )
    print(f"Connecting to GitLab server at {config['GITLAB_URL']}...")
    try:
        gl.auth()
        print("Authentication successful.")
    except gitlab.exceptions.GitlabAuthenticationError:
        print("Authentication failed. Please check your username and password.")
        return
    return gl, config


def get_projects(gl, config):
    projects_search = config.get('GITLAB_PROJETCTS')
    if not projects_search:
        print("No projects specified. Searching in all projects.")
    else:
        print(f"Searching in {len(projects_search)} specific projects.")
        print(projects_search)
    return gl.projects.list(all=True, get_all=True)


def get_commits(project,config, year, month, ultimodia):
    useremail = config['GITLAB_EMAIL']
    commit_hashes = []
    commits = []
    branches = project.branches.list(get_all=True)
    print(f"Temos {len(branches)} branchs no projeto {project.name}")
    for branch in tqdm(branches):
        # print(f"        Analisando branch {branch.name}")
        for commit in (project.commits.list(
                                        ref_name=branch.name,
                                        since=f"{year}-{month}-01T00:00:00Z",
                                        until=f"{year}-{month}-{ultimodia}T23:59:59Z",
                                        get_all=True
                                    )):
            if (commit.id not in commit_hashes and commit.committer_email == useremail):
                commit_hashes.append(commit.id)
                formatted_commit_date = parse(commit.created_at).strftime('%d/%m/%Y')
                activity = {
                    'project': project.name,
                    'message': commit.message ,
                    'ref': branch.name ,
                    'created_at': formatted_commit_date,
                    'url': commit.web_url
                }
                if "Merge" not in commit.message:                    
                    commits.append(activity)
    return commits


def get_user_activities(config, month, year, ultimodia):

    gl, config = connect_to_gitlab(config)
    projects = get_projects(gl, config)   
          
    print(f"Obtaining activities for user {config['GITLAB_USER']} in {year}-{month}-31T23:59:59Z...")
    activities = []
    for project in projects:
        if not config.get('GITLAB_PROJETCTS') or project.name in config['GITLAB_PROJETCTS']:
            print(f"Checking project {project.name}...")
            try:
                commits = get_commits(project, config, year, month, ultimodia)
                activities.extend(commits)
            except:
                pass

    print(f"Found {len(activities)} activities in total.")
    return activities


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
    #adicionando os chamados 
    texto = ""
    lista = list()
    bloco = ""        
    for chamado in chamados:
        if bloco != chamado['created_at']:
            if bloco != "":
                texto +=(f"   Em {bloco}: {str(', '.join(lista))}\n")
                lista = list()
            bloco = chamado['created_at']
            lista.append (str(chamado['chamado']))            
        else:
            lista.append(str(chamado['chamado']))             
    texto +=(f"   Em {bloco}: {str(', '.join(lista))}\n\n")
    return texto


def write_activities(activities):
    
    # Se não houver atividades, sair da função
    if not activities:
        return
    
    # Escrever as atividades no arquivo
    texto = ""
    bloco = ""        
    subbloco = ""
    for activity in activities:
        if bloco != activity['project']:
            bloco = activity['project']
            texto +=(f"Project: {activity['project']}\n")             
        if subbloco != activity['created_at']:
            subbloco = activity['created_at']
            texto +=(f"     Em {activity['created_at']}\n")         
        texto +=(f"          - {activity['message']}")
    return texto
    


def generate_report_git_suap(config, month, year, ultimodia):
    
            
    chamados = get_chamados(config, month,year, ultimodia)

    # obtém atividades do GitLab
    activities = get_user_activities(config, month, year, ultimodia)

    # Salvar as atividades e chamados em arquivos de texto
    all_activities = write_activities(activities)
    all_chamados = write_chamados(chamados)

    # Gerar o relatório consolidado
    print("Gerando relatório consolidado...")
    consolidated_report = f"Relatório Atividades realizadas no Git para {month}/{year}\n\n"
    consolidated_report += f"Atividades realizadas:\n"
    consolidated_report += f"----------------------------------------------\n"
    consolidated_report += f"{all_activities}\n"

    # Salvar o relatório consolidado em um arquivo de texto
    filename = f"atividades/atividades_report_{month}_{year}.txt"
    with open(filename, 'w') as file:
        file.write(consolidated_report)

    print(f"Relatório consolidado salvo em {filename}.")


# def main():
#     # Verifica se foram passados argumentos na linha de comando
#     if len(sys.argv) >= 3:
#         month = sys.argv[1]
#         year = sys.argv[2]
#     else:
#         # Obtém a data atual e subtrai um mês
#         now = datetime.datetime.now()
#         last_month = now - datetime.timedelta(days=30)
#         month = last_month.strftime('%m')
#         year = last_month.strftime('%Y')
    
#         # converte mês e ano para inteiros
#     month = int(month)
#     year = int(year)

#     ultimodia = calendar.monthrange(year, month)[1]

#     print(f"Gerando relatório para o mês {month}/{year}...")

#     # carrega configurações
#     yaml_path = "config.yaml"
#     with open(yaml_path, 'r') as file:
#         config = yaml.safe_load(file)
        
#     chamados = get_chamados(config, month,year, ultimodia)

#     # obtém atividades do GitLab
#     activities = get_user_activities(config, month, year, ultimodia)

#     # gera relatório 
#     generate_report_git_suap(config, activities, chamados, month, year)
    
#     generate_report_event(month, year, ultimodia)
    
# if __name__ == '__main__':
#     main()
