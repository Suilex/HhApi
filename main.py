import json
from collections import Counter

import requests
from requests.exceptions import ConnectionError


class Videos:
    def __init__(self, name, region_name=['Россия'], experience=None, salary=None, date_from=None, date_to=None,
                 period=None, frequency=5, region_code='RU', lang='ru', count=3):
        """
        Получение ссылок на актуальные видео по ключевым навыкам
        """

        self.name = name
        self.region_name = region_name
        self.experience = experience
        self.salary = salary
        self.date_from = date_from
        self.date_to = date_to
        self.period = period
        self.frequency = frequency
        self.region_code = region_code
        self.lang = lang
        self.count = count

    def __get_areas_id_by_name(self):
        """
        Получение списка кодов регионов по их именам

        Параметры:
            region - название региона
        Возвращаемое значение:
            codes - список кодов регионов
        """

        data = json.loads(requests.get('https://api.hh.ru/areas').content.decode())
        codes = []

        for region in data:
            if region['name'] in self.region_name:
                codes.append(region['id'])
            for state in region['areas']:
                if state['name'] in self.region_name:
                    codes.append(state['id'])
                for city in state['areas']:
                    if city['name'] in self.region_name:
                        codes.append(city['id'])

        return codes

    def __get_list_of_vacancies(self, area):
        """
        Получение списка id вакансий

        Параметры:
            name - ключевые слова в названии вакансии
            area - регион
            experience - опыт работы
            salary - размер заработной платы
            date_from - дата, которая ограничивает снизу диапазон дат публикации вакансий. 'YYYY-MM-DD'
            date_to - дата, которая ограничивает сверху диапазон дат публикации вакансий. 'YYYY-MM-DD'
            period - количество дней, в пределах которых нужно найти вакансии. max=30
            Нельзя указывать вместе с date_from и/или с date_to
        Возвращаемое значение:
            ids - список id вакансий

        Возможные параметры дл аргумента `опыт работы`.
        "noExperience" - Нет опыта
        "between1And3" - От 1 года до 3 лет
        "between3And6" - От 3 до 6 лет
        "moreThan6" - Более 6 лет
        """

        correct_experience = ['noExperience', 'between1And3', 'between3And6', 'moreThan6']

        context = {
            'text': self.name,
            'area': area,
            'experience': self.experience if self.experience in correct_experience else None,
            'salary': self.salary,
            'only_with_salary': True if self.salary else False,
            'date_from': self.date_from,
            'date_to': self.date_to if self.date_from else None,
            'period': self.period if not self.date_from and not self.date_to else None,
            'page': 0,
            'per_page': 50
        }

        data = requests.get('https://api.hh.ru/vacancies/', context).content.decode()
        json_data = json.loads(data)

        ids = []
        for elem in json_data['items']:
            if elem.get('id'):
                ids.append(elem.get('id'))

        return ids

    def __get_frequency_of_key_skills(self, ids):
        """
        Получение наиболее популярных ключевых навыков

        Параметры:
            ids - список id вакансий
            frequency - количество наиболее популярных ключевых навыков
        Возвращаемое значение:
            most_common_skills - список наиболее популярных ключевых навыков
        """

        result = []

        for id in ids:
            data = requests.get('https://api.hh.ru/vacancies/{}'.format(id)).content.decode()
            key_skills = json.loads(data).get('key_skills')

            for elem in key_skills:
                result.append(elem['name'])
        most_common_skills = Counter(result).most_common(self.frequency)

        return most_common_skills

    def __get_relevant_video(self, skills):
        """
        Получение ссылок на релевантные видео по теме

        Параметры:
            skills - список навыков
            region_code - код региона
            lang - язык
            count - количество видео для каждого навыка
        Возвращаемое значение:
            videos - список наиболее актуальных видео по наывыкам
        """

        # api_secret_key = 'AIzaSyDtpOteY23BLHlFo8rVMQcxt1B42pEsKNM'
        api_secret_key = 'AIzaSyBwVBXPEAHFs3R-J-yXTsg_XfdSHyRti3c'
        videos = {}

        for skill in skills:
            params = {
                'part': 'snippet',
                'q': skill[0],
                'type': 'video',
                'maxResults': self.count,
                'regionCode': self.region_code,
                'relevanceLanguage': self.lang,
                'videoDuration': 'medium',
                'key': api_secret_key
            }

            data = requests.get('https://www.googleapis.com/youtube/v3/search', params).content.decode()
            json_data = json.loads(data)

            links = []
            try:
                for video in json_data['items']:
                    links.append('https://www.youtube.com/watch?v=' + video['id']['videoId'])
                videos[skill[0]] = links
            except KeyError:
                print('The request cannot be completed because you have exceeded your quota')

        return videos

    def execute(self):
        video_links = {}

        try:
            areas = self.__get_areas_id_by_name()
            vacancies_id = self.__get_list_of_vacancies(area=areas)
            most_frequency_key_skills = self.__get_frequency_of_key_skills(vacancies_id)
            video_links = self.__get_relevant_video(most_frequency_key_skills)
        except ConnectionError as e:
            print('Ошибка подключения', e)

        return video_links


videos = Videos(region_name=['Россия'], name='Разработчик', date_from='2021-01-10', date_to='2022-02-20').execute()
print(videos)
