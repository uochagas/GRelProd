import yaml
import pytz
import datetime
import arrow
from tqdm import tqdm
from icalendar import Calendar


def load_calendar_ics():
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
        calendar_ics = config['CALENDAR_ICS']

    return calendar_ics


def get_events(calendar_ics, month, year, ultimodia):

    print(f"Abrindo arquivo em {calendar_ics}...")
    # Abra o arquivo .ics e carregue o conteúdo
    with open(calendar_ics, 'r') as file:
        ics_content = file.read()

    # Crie um objeto Calendar a partir do conteúdo do arquivo .ics
    calendar = Calendar.from_ical(ics_content)

    # Defina o fuso horário

    fuso_horario = pytz.timezone('America/Sao_Paulo')

    # Defina as datas inicial e final para filtragem
    data_inicial = datetime.datetime(year, month, 1)
    data_final = datetime.datetime(year, month, ultimodia)

    # Converter as datas inicial e final para objetos Arrow com fuso horário
    data_inicial = arrow.get(data_inicial).replace(tzinfo=fuso_horario)
    data_final = arrow.get(data_final).replace(tzinfo=fuso_horario)

    # Iterar sobre as linhas do arquivo .ics e
    # filtrar eventos conforme necessário
    events = []
    print(f"Analisando agenda de {calendar_ics}")
    for component in tqdm(calendar.walk()):
        if component.name == 'VEVENT':
            event_start = arrow.get(
                component.get('dtstart').dt).to(fuso_horario)
            event_end = arrow.get(component.get('dtend').dt).to(fuso_horario)
            if (data_inicial <= event_start <= data_final
                and not component.get('class') == 'PRIVATE'):
                event_title = component.get('summary')
                event_duration = event_end - event_start
                event = {
                    'título': event_title,
                    'início':event_start,
                    'fim': event_end,
                    'duração': event_duration,
                }
                events.append(event)
    return events


def write_events(events):

    # adicionando os chamados
    texto = ""
    bloco = ""
    print(f"Ordenando e organizando {len(events)} eventos filtrados...")
    for event in tqdm(sorted(events, key=lambda event: event['início'])):
        dt = event['início'].format('DD/MM/YYYY')
        if bloco != dt:
            bloco = dt
            texto += (f"    Em {dt}:\n")
        texto += (f"        - {event['título']}\n")

    return texto


def generate_report_event(config, month, year, ultimodia):

    print(f"Gerando de reuniões para o mês {month}/{year}...")

    # carrega configurações
    calendar_ics = load_calendar_ics()

    # obtém agendas do calendário
    events = get_events(calendar_ics, month, year, ultimodia)

    # Salvar as atividades e chamados em arquivos de texto
    all_events = write_events(events)

    # Gerar o relatório consolidado
    print("Gerando relatório consolidado...")
    consolidated_report = "Relatório de reuniões realizadas "
    consolidated_report = f"em {month}/{year}\n\n"
    consolidated_report += "----------------------------------------------\n"
    consolidated_report += f"{all_events}\n"

    # Salvar o relatório consolidado em um arquivo de texto
    filename = f"{config['DIR_EVENTOS']}events_report_{month}_{year}.txt"
    with open(filename, 'w') as file:
        file.write(consolidated_report)

    print(f"Relatório de reuniões salvo em {filename}.")
