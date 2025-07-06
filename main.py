import requests
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from my_secrets import user, password, url, email_password, email_sender, html_code1 as response
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
import json
import smtplib
import ssl
from email.message import EmailMessage
import os


def get_html_dsb(requests_url=''):
    def safe_html_code(html_code):
        date = datetime.datetime.today().strftime('%Y-%m-%d')
        week_day = datetime.datetime.today().strftime('%A')

        with open(r'C:\Users\Kelbig\PycharmProjects\HILDA_DSB\html_code.json', 'r', encoding='UTF-8') as json_file:
            html_code_history = json.load(json_file)

        html_code_history[date + ' | ' + week_day] = html_code

        with open(r'C:\Users\Kelbig\PycharmProjects\HILDA_DSB\html_code.json', 'w', encoding='UTF-8') as json_file:
            json.dump(html_code_history, json_file, ensure_ascii=False, indent=4, separators=(',', ': '))

    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Mobile Safari/537.36'}

    if requests_url == '':
        # opening chrome and website
        ser = Service(r'C:\Users\Kelbig\PycharmProjects\HILDA_DSB\chromedriver.exe')
        options = Options()
        # options.add_argument('--headless')
        driver = webdriver.Chrome(service=ser, options=options)
        driver.get(url)

        # login in
        WebDriverWait(driver, 7).until(EC.element_to_be_clickable((By.ID, 'txtUser'))).send_keys(user)
        WebDriverWait(driver, 7).until(EC.element_to_be_clickable((By.ID, 'txtPass'))).send_keys(password + Keys.ENTER)

        # clicking on right timetable
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'timetable-wrapper'))).click()

        # getting request url
        requests_url = WebDriverWait(driver, 7).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="slider"]/div/div/div/div[2]/iframe')))
        requests_url = requests_url.get_attribute('src')
        # print(f' url = {requests_url}')
        print(requests_url)
    response = requests.get(requests_url, headers=headers).text
    # print(requests_url)
    safe_html_code(html_code=response)
    return response


def dsb(timetable, response, school_class, tomorrow_boolean):
    tomorrow_boolean = False if tomorrow_boolean else True
    if school_class == 11:
        school_class = '11  1. Jahrgangsstufe'
    elif school_class == 12:
        school_class = '12  2. Jahrgangsstufe'

    classes = ['05a', '05b', '05c', '05d', '05e', '05f', '05g', '06a', '06b', '06c', '06d', '06e', '06f', '07a', '07b',
               '07c', '07d', '07e', '07f', '08a', '08b', '08c', '08d', '08e', '08f', '09a', '09b', '09c', '09d', '09e',
               '09f', '10a', '10b', '10c', '10d', '10e', '10f', '11  1. Jahrgangsstufe', '12  2. Jahrgangsstufe',
               'colspan="9"']

    week_day = datetime.datetime.today().weekday()
    global email_content
    email_content = ' '
    global first_time
    first_time = True
    current_school_class = False
    tomorrow = False
    global previos_day_printed
    previos_day_printed = ''
    global first_round
    first_round = True
    global day_added
    day_added = False

    def is_hour_in_teacher_hours():
        global affected_hours
        affected_hours = []
        teacher_hours_list = teacher_hours.replace(',', '').replace('[', '').replace(']', '').split(' ')
        dsb_hours = splitted_line[2].split('<')[0].replace(' ', '')
        if "1-12" in dsb_hours:
            print('RANGE 1-12')
            for hour in teacher_hours_list:
                affected_hours.append(hour)
        elif "6-12" in dsb_hours:
            print('RANGE 6-12')
            for hour in teacher_hours_list:
                #print(f"hours : {hour}")
                if int(hour) >= 6:
                    affected_hours.append(hour)
        else:
            #print("teacher_hours_list", teacher_hours_list, "\ndsb_hours", dsb_hours)
            for hour in teacher_hours_list:
                pos = dsb_hours.find(hour)
                #print(pos, dsb_hours == -1, dsb_hours)
                try:
                    if dsb_hours[pos + 1] in range(3):
                        print("         SPECIAL EVENT LINE 104", dsb_hours[pos], dsb_hours[pos + 1])
                    if not pos == -1 and not dsb_hours[pos - 1] == 1 and not dsb_hours[pos + 1] in range(3):
                        affected_hours.append(hour)
                except IndexError as err:
                    #print("     error line 108", pos, dsb_hours[pos - 1], err)
                    affected_hours.append(hour)
            # print(f'affected hours = {affected_hours}')
            #print(f"affected_hours = {affected_hours}")
        return True if not affected_hours == [] else False

    def handle_event():
        global affected_hours
        global email_content
        global first_time
        global previos_day_printed
        global first_round
        global day_added
        lines_per_event = {
            'Entfall': 8,
            'Veranst.': 7,
            'Verlegung': 9,
            'Betreuung': 8,
            'Raum-Vtr.': 8,
            'KL-Stunde': 7,
            'Vertretung': 8,
            'Diskussion Prof Görlach': 8,
            'Trotz Absenz': 8,
            'Vals Gruppe 1': 8,
            'Hochschule': 8,
        }

        event_boolean = False
        for event in lines_per_event:
            if event + '<' in line:
                event_boolean = True
                # print(event)
                if first_time:
                    print(f' ')
                    first_time = False
                # print(teacher, event, affected_hours)
                if tomorrow_boolean:
                    if not previos_day_printed == current_day:
                        #print(f"prev: '{previos_day_printed}', curr: '{current_day}'")
                        #print(not previos_day_printed == current_day)
                        previos_day_printed = current_day
                        if tomorrow:
                            print(f'\n\n    {current_day} ({current_day_idx})')
                            if not first_round:
                                email_content = email_content + '#' + current_day + ': '
                                day_added = True
                            else:
                                first_round = False
                        else:
                            print(f'\n\n    {current_day} ({current_day_idx})')

                break
            else:
                event = ''
        if not event_boolean:
            print(f'\n       NOT EVENT FOUND! MORE INFOS: {teacher}: {teacher_hours}\n       Possibilties:',  splitted_line[5].split('<')[0])
        hours_string = ''
        affected_hours_len = len(affected_hours)
        for idx, hour in enumerate(affected_hours):
            hours_string += str(hour) + '.'
            if not idx + 1 == affected_hours_len: hours_string += '- '
        hours_string += ' Stunde'

        if not email_content == ' ':
            if day_added:
                day_added = False
            else:
                email_content += ' | '

        if event == 'Entfall' or event == 'Veranst.' or event == 'KL-Stunde' or event == 'Trotz Absenz' or event == 'Vals Gruppe 1' or event == 'Hochschule':
            print()
            email_content += f'{event} {hours_string}: Hr/Fr {teacher}.'



        elif event == 'Verlegung' or event == 'Raum-Vtr.' or event == 'Vertretung':
            room = splitted_line[5].split('<')[0]
            instead_of_room = splitted_line[8].split('<')[0]
            current_teacher = splitted_line[3].split('<')[0]
            instead_of_teacher = splitted_line[7].split('<')[0]
            # print(f'room: {room}, instead_of_room: {instead_of_room}, teacher: {current_teacher}, instead_of_teacher: {instead_of_teacher}, teacher: {teacher}')
            if room == instead_of_room:
                if current_teacher == instead_of_teacher:
                    email_content += f'{event} {hours_string}: Hr/Fr {current_teacher}.'

                else:
                    email_content += f' {event} {hours_string}: Hr/Fr {current_teacher}. statt {instead_of_teacher}.'

            else:
                if current_teacher == instead_of_teacher:
                    email_content += f'{event} {hours_string}: Hr/Fr {current_teacher}. in Raum {room} statt {instead_of_room}'

                else:
                    email_content += f'{event} {hours_string}: Hr/Fr {current_teacher}. statt {instead_of_teacher}. und Raum {room} statt {instead_of_room}'
        elif event == 'Betreuung':
            room = splitted_line[5].split('<')[0]
            instead_of_room = splitted_line[8].split('<')[0]
            current_teacher = splitted_line[3].split('<')[0]
            instead_of_teacher = splitted_line[7].split('<')[0]
            print(
                f'        room: {room}, instead_of_room: {instead_of_room}, teacher: {current_teacher}, instead_of_teacher: {instead_of_teacher}, teacher: {teacher}')
            if instead_of_teacher == teacher:

                if room == instead_of_room:
                    if current_teacher == instead_of_teacher:
                        email_content += f'{event} {hours_string}: Hr/Fr {current_teacher}.'

                    else:
                        email_content += f' {event} {hours_string}: Hr/Fr {current_teacher}. statt {instead_of_teacher}.'

                else:
                    if current_teacher == instead_of_teacher:
                        email_content += f'{event} {hours_string}: Hr/Fr {current_teacher}. in Raum {room} statt {instead_of_room}'

                    else:
                        email_content += f'{event} {hours_string}: Hr/Fr {current_teacher}. statt {instead_of_teacher}. und Raum {room} statt {instead_of_room}'
        else:
            print('       event does not match ', event)

        if current_day in email_content.split('|')[-1][1:]:
            print('  -', email_content.split(current_day)[-1][2:])
        else:
            print('  -', email_content.split('|')[-1][1:])


    for line in response.splitlines():
        splitted_line = line.split('#010101">')
        #if len(splitted_line) > 0 and 'Betreuung' in line:
        #    room = splitted_line[5].split('<')[0]
        #    instead_of_room = splitted_line[8].split('<')[0]
        #    current_teacher = splitted_line[3].split('<')[0]
        #    instead_of_teacher = splitted_line[7].split('<')[0]
        #    #print(splitted_line[7])
        #    #print(f'room: {room}, instead_of_room: {instead_of_room}, teacher: {current_teacher}, instead_of_teacher: {instead_of_teacher}')
#
        #if len(splitted_line) > 0 and 'Veranst.' in line:
        #    print('\n')
        #    for idx, phrase in enumerate(splitted_line):
        #        if not idx > -1:
        #            continue
        #        print(phrase, '.' * (120 - len(phrase)), idx)
        #    email_content = ''
        #    teacher = 'Hr/Fr Gaube'
        #    hours_string = '5. Stunde'
#
        #    print('\n')
        #    #print(f'room: {room}, instead_of_room: {instead_of_room}, teacher: {current_teacher}, instead_of_teacher: {instead_of_teacher}')
#
        #    print(email_content)
        #    print('\n')

        for idx, day in enumerate(timetable):
            if day + '</div>' in line:
                current_day_idx = idx
                current_day = day
                if current_day_idx - week_day == 1 or week_day == 6 and current_day_idx == 0:
                    # print('\n' + current_day + '(' + str(current_day_idx) + ') ~~Morgen:\n')
                    tomorrow = True
                elif not tomorrow_boolean:
                    # print('\n' + current_day + '(' + str(current_day_idx) + ')\n')
                    tomorrow = False

        if tomorrow == True:
            if school_class + '</td></tr>' in line:
                current_school_class = True

            elif current_school_class:
                for possible_school_class in classes:
                    if possible_school_class + '</td></tr>' in line:
                        current_school_class = False

            if current_school_class and len(splitted_line) > 0:
                for teacher_hours in timetable[current_day]:
                    teacher = timetable[current_day][teacher_hours]
                    teacher = teacher[0].upper() + teacher[1:].lower()
                    if teacher + "<" in line or teacher + "," in line or ", " + teacher in line:
                        #current_teacher = splitted_line[3].split('<')[0]
                        #print(current_teacher)
                        # print(teacher)
                        # room = splitted_line[5].split('<')[0]
                        # instead_of_room = splitted_line[8].split('<')[0]
                        #current_teacher = splitted_line[3].split('<')[0]
                        #print(current_teacher)
                        # instead_of_teacher = splitted_line[7].split('<')[0]
                        # print(f'room: {room}, instead_of_room: {instead_of_room}, teacher: {current_teacher}, instead_of_teacher: {instead_of_teacher}')
                        # for i, o in enumerate(splitted_line):
                        #    print(i, o)
                        if is_hour_in_teacher_hours():
                            handle_event()

    return email_content if not email_content == ' ' else None


def send_email_and_update_history(email_content, email_receiver, name,
                                  safe_in_event_history, email_as_kelvin, send_email_boolean,
                                  send_to_everyone_except, automation=''):
    possible_week_day = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag']
    body = ''''''
    splitted_email_content = email_content.split('#')
    email_title = splitted_email_content[0]
    splitted_email_content_lenght = len(splitted_email_content)
    desc_1, desc_2 = '', ''

    if splitted_email_content_lenght > 1:
        first_day = splitted_email_content[1].split(' ')
        for word in first_day[1:]:
            desc_1 += word + ' '

        body = f"""
                        {str(first_day[0])}
                        {desc_1}
                    """

    if splitted_email_content_lenght > 2:
        second_day = splitted_email_content[2].split(' ')
        for word in second_day[1:]:
            desc_2 += word + ' '

        body = f"""
        {str(first_day[0])}
        {desc_1}
        
        {str(second_day[0])}
        {desc_2}
    """

    print('\n')
    if automation:
        email_as_kelvin = False
        safe_in_event_history = True
        send_email_boolean = True
    elif automation == False:
        email_as_kelvin = True
        safe_in_event_history = False
        send_email_boolean = True

    if email_as_kelvin:
        email_receiver = 'kelvinenergie1@web.de'

    def send_email():

        if '|' in email_content:
            subject = 'Mehrere Ereignisse: ' + email_title
        else:
            subject = email_title

        em = EmailMessage()
        em['From'] = email_sender
        em['To'] = email_receiver
        em['Subject'] = subject
        em.set_content(body)

        # Add SSL (layer of security)
        context = ssl.create_default_context()

        # Log in and send the email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, email_password)
            smtp.sendmail(email_sender, email_receiver, em.as_string())
        print(f'    ---> Email was sent to {name} ({email_receiver}) with Email_Title: \n         "{subject}"\n         Description: "{body}"')

    with open(r'C:\Users\Kelbig\PycharmProjects\HILDA_DSB\event_history.json', 'r', encoding='UTF-8') as json_file:
        event_history = json.load(json_file)

    credentials = name + ' | ' + email_receiver

    today = datetime.datetime.today().strftime('%Y-%m-%d') + ' | ' + datetime.datetime.today().strftime('%A')

    if not today in event_history.keys():
        event_history[today] = {}

    if credentials in event_history[today].keys() and event_history[today][credentials] == email_content:
        print('    ---> Already sent')

    else:
        if send_email_boolean:
            if not email_receiver in send_to_everyone_except:
                send_email()
            else:
                print('         (E-mail was not sent, because it is in the Banned_Email_List!)')
        else:
            print('         (E-mail was not sent!)')
        if safe_in_event_history is True:
            event_history[today][credentials] = email_content
            with open(r'C:\Users\Kelbig\PycharmProjects\HILDA_DSB\event_history.json', 'w',
                      encoding='UTF-8') as json_file:
                json.dump(event_history, json_file, ensure_ascii=False, indent=4, separators=(',', ': '))
            print(f'         (Successfully saved in Event_history!)')
        else:
            print(f'         (Not saved in Event_history!)')

    print(' ')


def main():
    print('\n\n')
    with open(r'C:\Users\Kelbig\PycharmProjects\HILDA_DSB\timetables_of_students.json', 'r',
              encoding='UTF-8') as json_file:
        data_of_students = json.load(json_file)

    response = get_html_dsb(requests_url="")

    # with open('html_code.json', encoding='UTF-8') as json_file:
    #    response = json.load('2023-01-31 | Tuesday')

    for name in data_of_students:
        print(f'{f"{name}":-^90}')
        # print(data_of_students[name], '\n', data_of_students[name]["timetable"])
        timetable = data_of_students[name]["timetable"]
        school_class = data_of_students[name]["class"]
        email = data_of_students[name]["email"]
        email_content = dsb(response=response, timetable=timetable, school_class=school_class, tomorrow_boolean=True)

        if email_content is not None:
            send_email_and_update_history(email_content=email_content[1:], email_receiver=email, name=name,
                                          safe_in_event_history=True, email_as_kelvin=True,
                                          send_email_boolean=True, send_to_everyone_except=[],
                                          automation=False)

    print(datetime.datetime.now().strftime('%H:%M:%S'))
    #os.system(r"C:\Users\Kelbig\PycharmProjects\Test\Sleep_Mode.lnk")


if __name__ == '__main__':
    #try:
        main()
    #    #sleep(50)
    #except Exception as err:
    #    print(err)
    #    sleep(100)
