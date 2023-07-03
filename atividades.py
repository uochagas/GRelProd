import re
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


def get_commits(project, config, year, month, ultimodia):
    useremail = config['GITLAB_EMAIL']
    gitlab_max_branch = config['GITLAB_MAX_BRANCH']
    commit_hashes = []
    commits = []
    branches = project.branches.list(get_all=True)
    print(f"Temos {len(branches)} branchs no projeto {project.name}")
    if gitlab_max_branch > 0:
        print(f"Porém será analisado no máximo {gitlab_max_branch} branchs")
    for branch in tqdm(branches[-gitlab_max_branch:]):
        for commit in (project.commits.list(
                            ref_name=branch.name,
                            since=f"{year}-{month}-01T00:00:00Z",
                            until=f"{year}-{month}-{ultimodia}T23:59:59Z",
                            get_all=True)):
            if (commit.id not in commit_hashes and
                            commit.committer_email == useremail):
                commit_hashes.append(commit.id)
                commit_date = parse(commit.created_at).strftime('%d/%m/%Y')
                try:
                    issue = project.issues.get(branch.name.split('-')[0])
                    issue_id = issue.iid
                    issue_msg = issue.attributes["description"]
                except:
                    issue_id = branch.name
                    issue_msg = f'Atualiando branch {branch.name}'

                activity = {
                    'project': project.name,
                    'message': commit.message,
                    'ref': branch.name,
                    'created_at': commit_date,
                    'url': commit.web_url,
                    'issue_id': issue_id,
                    'issue_msg': issue_msg}
                if "Merge" not in commit.message:
                    commits.append(activity)
    return commits


def get_user_activities(config, month, year, ultimodia):
    gl, config = connect_to_gitlab(config)
    projects = get_projects(gl, config)

    print(f"Obtaining activities for user {config['GITLAB_USER']} in {year}-{month}-31T23:59:59Z...")
    activities = []
    for project in projects:
        if (not config.get('GITLAB_PROJETCTS') or
                            project.name in config['GITLAB_PROJETCTS']):
            print(f"Checking project {project.name}...")
            try:
                commits = get_commits(project, config, year, month, ultimodia)
                activities.extend(commits)
            except:
                pass

    print(f"Found {len(activities)} activities in total.")
    return activities


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
            texto += (f"Project: {activity['project']}\n")
        if subbloco != activity['created_at']:
            subbloco = activity['created_at']
            texto += (f"     Em {activity['created_at']}\n")
        texto += (f"          - {activity['message']}")
    return texto


def write_activities_issues(activities):
    # Se não houver atividades, sair da função
    if not activities:
        return
    # Escrever as atividades no arquivo
    texto = ""
    bloco = ""
    subbloco = ""
    for activity in sorted(activities, key=lambda x: (x['project'], x['issue_msg'])):
        if bloco != activity['project']:
            bloco = activity['project']
            texto += (f"Projeto: {activity['project']}\n")
        if subbloco != activity['issue_msg']:
            subbloco = activity['issue_msg']
            texto += (f"    - {activity['issue_msg']}\n")
            texto += ( "    ===============================================\n")
        # texto += (f"        * {activity['message']}")
    return texto


def generate_report_git_suap(config, month, year, ultimodia):
    # obtém atividades do GitLab
    activities = get_user_activities(config, month, year, ultimodia)

    # Salvar as atividades de modo Resumido em arquivos de texto
    # all_activities = write_activities_issues(activities)

    # Salvar as atividades de modo detalhado em arquivos de texto
    all_activities = write_activities(activities)

    # Gerar o relatório consolidado
    print("Gerando relatório consolidado...")
    consolidated_report = "Relatório Atividades realizadas "
    consolidated_report += f"no Git para {month}/{year}\n\n"
    consolidated_report += "Atividades realizadas:\n"
    consolidated_report += "----------------------------------------------\n"
    consolidated_report += f"{all_activities}\n"

    # Salvar o relatório consolidado em um arquivo de texto
    fname = f"{config['DIR_ATIVIDADES']}atividades_report_{month}_{year}.txt"
    with open(fname, 'w') as file:
        file.write(consolidated_report)

    print(f"Relatório consolidado salvo em {fname}.")
