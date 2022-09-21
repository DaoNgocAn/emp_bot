import os
import random
import time
import argparse

from utils import get_with_retry, logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class Bot:
    url = 'https://csgoempire.com/'
    max_lose_streak = 11
    amount_init = 1
    side = 0
    amount_dice = 0.05

    def __init__(self, headless, profile='profile'):
        options = Options()
        options.headless = headless
        if headless:
            options.add_argument("--kiosk")
        options.add_argument(f"user-data-dir=/home/an/PycharmProjects/empire_bot/{profile}")
        path = os.path.abspath('chromedriver')
        self.driver = webdriver.Chrome(options=options, executable_path=path)
        get_with_retry(self.driver, Bot.url)
        # time.sleep(30)

    def __del__(self):
        self.driver.close()

    def init(self):
        self.current_lose_streak = 0
        self.state = self.get_current_status()
        self.balance = self.get_current_balance()
        self.amount = Bot.amount_init
        self.start_balance = self.get_current_balance()

    def get_current_balance(self):
        element = self.driver.find_element(By.XPATH, "//div[@class='balance']")
        text = element.text.replace(",", "")
        return float(text)

    def get_current_status(self):
        state = {i: None for i in range(9)}
        elements = self.driver.find_elements(By.XPATH, "//div[@class='previous-rolls-item']")[:10]
        for i, e in enumerate(elements):
            name = e.find_element(By.XPATH, ".//*").get_attribute("class").split()[-1]
            state[i] = name
        return state

    def compare_state(self, other_stare):
        for k, v in self.state.items():
            if self.state[k] != other_stare[k]:
                return False
        return True

    def set_value(self, value):
        input_element = self.driver.find_element(By.XPATH,
                                                 "//input[@class='bg-transparent w-full h-full relative z-10']")
        input_element.clear()
        value = str(value)
        input_element.send_keys(value)

    def place_bet(self, type=0):
        elements = self.driver.find_elements(By.XPATH, "//button[@class='bet-btn']")
        text = [e.text for e in elements]
        text = "|".join(text).replace("\n", " ")
        logger.error(f"elements : {len(elements)}\t{text}")
        elements[type].click()

    def place_dice(self):
        element = self.driver.find_element(By.XPATH, "//button[@class='bet-btn']")
        element.click()

    def check_change_state(self):
        while True:
            state = self.get_current_status()
            if self.compare_state(state):
                time.sleep(2)
            else:
                self.state = self.get_current_status()
                time.sleep(2)
                break
    def bet(self):
        if Bot.side == 1000:
            side = random.choice([0, -1])
        else:
            side = Bot.side
        self.set_value(self.amount)
        self.place_bet(side)
        if Bot.amount_dice > 0:
            time.sleep(1)
            self.set_value(Bot.amount_dice)
            time.sleep(1)
            self.place_dice()

    def run(self):
        self.init()
        self.bet()
        while True:
            self.check_change_state()
            current_balance = self.get_current_balance()
            if current_balance > self.balance:
                logger.info(f"win\t{current_balance}\t\t{self.amount}")
                win = True
            else:
                logger.error(f"lose\t{current_balance}\t\t{self.amount}")
                win = False
            time.sleep(4)
            self.balance = self.get_current_balance()
            if win or self.current_lose_streak > Bot.max_lose_streak:
                self.amount = Bot.amount_init
                self.current_lose_streak = 0
                #if current_balance - self.start_balance > 50 * self.amount_init:
                #    self.start_balance = self.get_current_balance()
                #    Bot.side = 2 - Bot.side
            else:
                self.amount *= 2
                self.current_lose_streak += 1
            try:
                self.bet()
            except Exception as e:
                logger.exception("tack!", e)
                logger.info(str(self))

    def __str__(self):
        return f"\nAmount:\t\t {self.amount}\nCurrent_lose_streak:\t\t{self.current_lose_streak}\nBalance:\t\t{self.get_current_balance()}\nside:\t\t{Bot.side}"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action='store_true')
    parser.add_argument("--headless", action='store_true')
    parser.add_argument("--amount_init", default=0.5, type=float)
    parser.add_argument("--amount_dice", default=0.05, type=float)
    parser.add_argument("--side", default=0, type=int)
    parser.add_argument("--profile", default="profile", type=str)
    opt = parser.parse_args()

    Bot.amount_init = opt.amount_init
    Bot.amount_dice = opt.amount_dice
    Bot.side = opt.side
    bot = Bot(opt.headless, opt.profile)
    if opt.run:
        time.sleep(10)
        bot.run()
