import sys
import yaml
import calendar
import datetime
from dateutil.parser import parse
from reunioes import generate_report_event
from atividades import generate_report_git_suap
from chamados import generate_report_chamados


def main():
    # Verifica se foram passados argumentos na linha de comando
    if len(sys.argv) >= 3:
        month = sys.argv[1]
        year = sys.argv[2]
    else:
        # Obtém a data atual e subtrai um mês
        now = datetime.datetime.now()
        last_month = now - datetime.timedelta(days=30)
        month = last_month.strftime('%m')
        year = last_month.strftime('%Y')
    
        # converte mês e ano para inteiros
    month = int(month)
    year = int(year)

    ultimodia = calendar.monthrange(year, month)[1]

    print(f"Gerando relatório para o mês {month}/{year}...")

    # carrega configurações
    yaml_path = "config.yaml"
    with open(yaml_path, 'r') as file:
        config = yaml.safe_load(file)

    # gerar relatório de reuniões com base no arquivo ics
    generate_report_event(month, year, ultimodia)
    
    # gerar relatório de reuniões com base no arquivo ics
    generate_report_chamados(config, month, year, ultimodia)

    # gera relatório com base no git e no suap
    generate_report_git_suap(config, month, year, ultimodia)
        
    
if __name__ == '__main__':
    main()