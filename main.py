from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import os
from random import randint

class WeatherBot:

    def __init__(self):
        self.scrape_url = 'https://weather.com/en-NG/weather/tenday/l/36a7da1656fdfd4979d4d74a65d97b068cb7b3d597b5ea254adfaaaf358d53ca'
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.get(self.scrape_url)
        self.location: str = ""
        self.report = []
        self.date = None

    # Extract the needed information from the data given to it
    def information_processing(self, details, raw_data, data: list):
        print('Processing and Cleaning the needed Information...\n')
        information = {}

        # Convert the data to a list of two element(day, night)
        detail_list = details.split('Night')

        # extract the date and update it in the return information
        day = detail_list[0].split(' | ')[0].replace(' ', '')
        information['date'] = day
        if data.index(raw_data) == 0:
            self.date = day
        # extracting needed weather information from the data
        for timeline in detail_list:
            humidity = "Unavailable"
            wind = 'Unavailable'
            description = 'Unavailable'
            day = timeline.split('\n')
            temp = day[1]
            for info in day:
                if '.' in info:
                    info = info.split('.')
                    description = info[0]
                elif info == 'Humidity':
                    humidity = day[day.index(info) + 1]
                elif 'km/h' in info:
                    wind = day[day.index(info) - 1]
            data = {
                "temperature": temp,
                'wind_speed': wind,
                'humidity': humidity,
                'description': description
            }
            if detail_list.index(timeline) == 0:
                information['day'] = data
            else:
                information['night'] = data

        print('Cleaning and Processing Complete\n')
        return information


    def web_scrapper(self):
        # scrap 10 days data from weather.com
        # temperature(Night/dat), Humidity, wind speed, weather description
        print('Data Extraction ongoing, please wait!!\n')
        rawtext_list = []
        time.sleep(5)
        ten_days = self.driver.find_element(by=By.CLASS_NAME, value="DailyForecast--DisclosureList--xG4Oa")
        if ten_days:
            print("Success !!!")
        days = ten_days.find_elements(by=By.TAG_NAME, value='details')[1:8]

        time.sleep(3)
        scroll = 800
        count = 1
        for day in days:
            self.driver.execute_script(f"window.scrollTo(0, {scroll});")
            dday = day.find_element(by=By.TAG_NAME, value='div')
            if dday:
                time.sleep(2)
                try:
                    dday.click()
                    # print('successful click')
                except Exception:
                    input("couldn't click")
            else:
                input("No element found")
            if count < 5:
                count += 1
                scroll = scroll + (100 * count)
            elif count >= 5:
                scroll = scroll + 220

        for day in days:
            rawtext_list.append(day.text)
        print('Data Extraction Complete!!!\n')
        return rawtext_list


    def save_csv(self):
        print('Saving the Information to csv file...\n')
        dates = []
        d_temperature = []
        d_wind = []
        d_hum = []
        d_desc = []
        n_temperature = []
        n_wind = []
        n_hum = []
        n_desc = []
        for info in self.report:
            dates.append(info['date'])
            d_temperature.append(info['day']['temperature'].replace('°', ''))
            d_wind.append(info['day']['wind_speed'])
            d_hum.append(info['day']['humidity'].replace('%', ''))
            d_desc.append(info['day']['description'])

            # Nighttime data
            n_temperature.append(info['night']['temperature'].replace('°', ''))
            n_wind.append(info['night']['wind_speed'])
            n_hum.append(info['night']['humidity'].replace('%', ''))
            n_desc.append(info['night']['description'])

        dict_ = {
                'dates': dates,
                'dayTemperature(C)': d_temperature,
                'dayWind_speed(km/h)': d_wind,
                'dayHumidity(%)': d_hum,
                'dayDescription': d_desc,
                'nightTemperature(C)': n_temperature,
                'nightWind_speed(km/h)': n_wind,
                'nightHumidity(%)': n_hum,
                'nightDescription': n_desc
            }
        if not os.path.exists('reports'):
            os.mkdir('reports')
        path1 = os.path.join(os.getcwd(), 'reports',)
        filename = f'{self.location.split(",")[0]}{self.date}.csv'
        while os.path.isfile(filename):
            filename = f"{filename}{str(randint(0, 9))}"
        filename = os.path.join(path1, filename)
        print(filename)
        df = pd.DataFrame(dict_)
        df.set_index("dates", inplace=True)
        df.to_csv(filename)
        print(f"File successfully saved as {filename}\n")

    # Search for city to extract weather report
    def SearchLocation(self):
        location = input('Please enter the city name: ')
        if location:
            searchLocation = self.driver.find_element(by=By.ID, value="LocationSearch_input")
            searchLocation.click()
            searchLocation.send_keys(location)
            time.sleep(2)
            searchLocation.send_keys(Keys.DOWN)
            try:
                button = self.driver.find_element(by=By.ID, value='LocationSearch_listbox')
                buttons = button.find_element(by=By.TAG_NAME, value='button')
                print(f'Is {buttons.text} the required location (Y/N)? ')
                answer = input()
                if answer.lower() == 'y':
                    self.location = buttons.text
                    print("selection successful")
                    time.sleep(1)
                    buttons.send_keys(Keys.ENTER)
                else:
                    print("City not found!!!")
                    action = ActionChains(self.driver)
                    action.key_down(Keys.CONTROL).send_keys('A').perform()
                    searchLocation.send_keys(Keys.BACKSPACE)
                    # self.RunBot()
            except NoSuchElementException:
                print("City not found!!!")
                action = ActionChains(self.driver)
                action.key_down(Keys.CONTROL).send_keys('A').perform()
                searchLocation.send_keys(Keys.BACKSPACE)
                # self.RunBot()

    # Run the bot
    def RunBot(self):
        print("Welcome To 7days weather extraction bot")
        while not self.location:
            self.SearchLocation()
        data = self.web_scrapper()
        print('\n')
        for raw_data in data:
            self.report.append(self.information_processing(raw_data, raw_data, data))
        self.save_csv()
        print("Thank you")


if __name__ == '__main__':
    bot = WeatherBot()
    bot.RunBot()
