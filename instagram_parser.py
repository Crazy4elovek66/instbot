import os
import time
import random
from threading import Thread
from queue import Queue
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from config import INSTAGRAM_CREDENTIALS
from filter import FEMALE_KEYWORDS, MALE_KEYWORDS

class InstagramParser:
    def __init__(self):
        self.driver = None
        self.logged_in = False
        self.current_username = None
        self.parsed_users = set()
        
        try:
            self.load_parsed_users()
            self.setup_driver()
            self.disable_graphics_errors()
        except Exception as e:
            print(f"Ошибка инициализации: {str(e)}")
            if self.driver:
                self.driver.quit()
            raise Exception("Не удалось инициализировать парсер") from e

    def disable_graphics_errors(self):
        """Отключаем ненужные сообщения об ошибках графики"""
        if not self.driver:
            return
            
        try:
            self.driver.execute_cdp_cmd('Browser.setBrowserLoggingPreference', {
                'level': 'disable'
            })
            self.driver.execute_cdp_cmd('Browser.setGraphicsLoggingPreference', {
                'level': 'disable'
            })
        except:
            pass

    def setup_driver(self):
        """Настройка драйвера с автоматическим принятием cookie"""
        options = webdriver.ChromeOptions()
        
        # Основные настройки
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--enable-unsafe-webgl-software')
        options.add_argument('--enable-unsafe-swiftshader')
        
        # Настройки для обхода защиты
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'")
        
        # User-Agent
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
        options.add_argument(f'user-agent={user_agent}')
        
        # Инициализация драйвера
        driver_path = r'C:\Users\Odmin\Desktop\Inst\chromedriver-win64\chromedriver.exe'
        self.driver = webdriver.Chrome(
            service=Service(driver_path),
            options=options
        )
        
        # Изменяем свойство webdriver
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Принимаем cookie при первом открытии
        self._accept_cookies()
    
    def human_scroll(self, element):
        """Плавная прокрутка как у человека"""
        for _ in range(3):
            scroll_amount = random.randint(200, 400)
            self.driver.execute_script(
                f"arguments[0].scrollBy(0, {scroll_amount})", element)
            time.sleep(random.uniform(0.5, 1.5))
            
    def _accept_cookies(self):
        """Улучшенное принятие cookie для нового интерфейса Instagram"""
        try:
            # Проверка, нужно ли вообще принимать cookie
            if self._are_cookies_accepted():
                return True

            # Ожидаем появление диалогового окна cookie
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, 
                        "//div[@role='dialog']//h2[contains(., 'Разрешить использование файлов cookie')]"))
                        )
            except TimeoutException:
                print("Cookie-окно не появилось")
                return False

            # Ищем основную кнопку принятия
            try:
                accept_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//div[@role='dialog']//button[contains(., 'Разрешить все cookie') or "
                        "contains(., 'Allow all cookies') or "
                        "contains(., 'Принять все')]"))
                )
                accept_btn.click()
                print("Cookie приняты (основная кнопка)")
                return True
            except:
                pass

            # Альтернативный вариант (если основная кнопка не сработала)
            try:
                accept_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//button[contains(@class, '_a9--') and "
                        "contains(., 'Разрешить все cookie')]"))
                )
                accept_btn.click()
                print("Cookie приняты (альтернативная кнопка)")
                return True
            except:
                pass

            # Если не нашли кнопку, делаем скриншот для отладки
            self._debug_screenshot("cookie_not_found")
            return False

        except Exception as e:
            print(f"Ошибка при принятии cookie: {str(e)}")
            self._debug_screenshot("cookie_error")
            return False        
            
    def _are_cookies_accepted(self):
        """Проверка, приняты ли уже cookie"""
        try:
            # Проверяем отсутствие cookie-диалога
            return len(self.driver.find_elements(By.XPATH, 
                "//div[@role='dialog']//h2[contains(., 'Разрешить использование файлов cookie')]")) == 0
        except:
            return False       
    
    def human_like_delay(self, min_sec=1, max_sec=3):
        """Имитация человеческой задержки"""
        time.sleep(random.uniform(min_sec, max_sec))
        
    def _type_like_human(self, element, text):
        """Человекообразный ввод текста"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))    
    
    def load_parsed_users(self):
        """Загрузка проверенных пользователей"""
        if os.path.exists('users.csv'):
            with open('users.csv', 'r', encoding='utf-8') as f:
                for line in f.readlines()[1:]:
                    if line.strip():
                        username = line.split('|')[0].strip()
                        self.parsed_users.add(username)
    
    def save_session_cookies(self):
        """Сохранение сессии"""
        with open('session.txt', 'w', encoding='utf-8') as f:
            f.write(f"{self.current_username}\n")
            for cookie in self.driver.get_cookies():
                f.write(f"{cookie['name']}={cookie['value']}\n")
    
    def load_session_cookies(self):
        """Загрузка сессии"""
        if os.path.exists('session.txt'):
            with open('session.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    self.current_username = lines[0].strip()
                    self.driver.get("https://www.instagram.com/")
                    for line in lines[1:]:
                        if '=' in line:
                            name, value = line.strip().split('=', 1)
                            cookie = {'name': name, 'value': value, 'domain': '.instagram.com'}
                            self.driver.add_cookie(cookie)
                    self.logged_in = True
                    return True
        return False
    
    def login(self):
        """Улучшенный метод входа с обработкой подтверждения"""
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            print(f"\nПопытка входа {attempt}/{max_attempts}")
            
            try:
                # Пытаемся использовать сохраненную сессию
                if self.load_session_cookies():
                    print("Проверяем сохраненную сессию...")
                    if self._check_logged_in():
                        print("Успешный вход с сохраненной сессией")
                        return True
                    
                # Если сессии нет или она невалидна - логинимся заново
                print("Выполняем новый вход...")
                self.driver.get("https://www.instagram.com/accounts/login/")
                self.human_like_delay(2, 4)
                
                # Принимаем cookie, если появились
                self._accept_cookies()
                self.human_like_delay(2, 4)
                
                # Вводим данные
                username_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                self._type_like_human(username_field, INSTAGRAM_CREDENTIALS['username'])
                
                password_field = self.driver.find_element(By.NAME, "password")
                self._type_like_human(password_field, INSTAGRAM_CREDENTIALS['password'])
                
                password_field.send_keys(Keys.RETURN)
                self.human_like_delay(3, 5)
                
                # Обрабатываем возможные проверки
                if self._handle_login_checks():
                    if self._check_logged_in():
                        print("Успешный вход!")
                        self.current_username = INSTAGRAM_CREDENTIALS['username']
                        self.save_session_cookies()
                        # После успешного входа
                        print("Текущий URL:", self.driver.current_url)
                        print("Найдены элементы навигации:", len(self.driver.find_elements(By.XPATH, "//nav | //div[@role='navigation']")))
                        print("Найдены аватары:", len(self.driver.find_elements(By.XPATH, "//img[contains(@alt, 'аватар')]")))
                        return True
                
            except Exception as e:
                print(f"Ошибка при попытке входа: {str(e)}")
                self.human_like_delay(5, 10)
        
        print("Все попытки входа исчерпаны")
        return False

    def _handle_login_checks(self):
        """Обработка проверок при входе"""
        try:
            # Проверка на подтверждение по почте/телефону
            confirm_elements = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, 
                    "//h2[contains(., 'Подтвердите') or contains(., 'Confirm')] | "
                    "//div[contains(., 'код подтверждения') or contains(., 'confirmation code')]"))
            )
            if confirm_elements:
                print("\nТребуется подтверждение входа!")
                print("1. Проверьте почту/телефон")
                print("2. Подтвердите вход")
                print("3. После подтверждения в браузере, вернитесь сюда")
                
                # Ждем, пока пользователь подтвердит вход
                input("Нажмите Enter в этом окне после подтверждения в браузере...")
                
                # Даем время на обработку подтверждения
                self.human_like_delay(5, 8)
                return True
                
        except TimeoutException:
            pass
        
        try:
            # Проверка на "Сохранить данные для входа?"
            save_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(., 'Не сейчас') or contains(., 'Not Now')]"))
            )
            save_button.click()
            self.human_like_delay(2, 3)
        except:
            pass
        
        try:
            # Проверка на уведомления
            notif_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(., 'Не сейчас') or contains(., 'Not Now')]"))
            )
            notif_button.click()
            self.human_like_delay(2, 3)
        except:
            pass
        
        return True

    def _check_logged_in(self, timeout=30):
        """Улучшенная проверка успешного входа"""
        try:
            # Проверяем несколько признаков успешного входа
            WebDriverWait(self.driver, timeout).until(
                lambda d: 
                    "accounts/login" not in d.current_url and  # URL не содержит страницу входа
                    any([
                        # Проверяем наличие различных элементов, указывающих на успешный вход
                        len(d.find_elements(By.XPATH, "//nav[@role='navigation']")) > 0,
                        len(d.find_elements(By.XPATH, "//div[@role='navigation']")) > 0,
                        len(d.find_elements(By.XPATH, "//a[contains(@href, 'direct/inbox')]")) > 0,
                        len(d.find_elements(By.XPATH, "//img[contains(@alt, 'аватар') or contains(@alt, 'avatar')]")) > 0,
                        len(d.find_elements(By.XPATH, "//span[contains(text(), 'Главная') or contains(text(), 'Home')]")) > 0
                    ])
            )
            return True
        except TimeoutException:
            # Делаем скриншот для отладки
            self._debug_screenshot("login_failed")
            print("Не удалось подтвердить вход. Возможные причины:")
            print("- Instagram потребовал дополнительную проверку")
            print("- Медленное интернет-соединение")
            print("- Изменения в интерфейсе Instagram")
            return False

    def _debug_screenshot(self, name):
        """Создание скриншота для отладки"""
        try:
            if not os.path.exists('debug'):
                os.makedirs('debug')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.driver.save_screenshot(f"debug/{name}_{timestamp}.png")
            print(f"Скриншот сохранен: debug/{name}_{timestamp}.png")
        except Exception as e:
            print(f"Не удалось сохранить скриншот: {str(e)}")

    def _attempt_login(self):
        """Одна попытка входа с улучшенной обработкой"""
        try:
            self.driver.get("https://www.instagram.com/accounts/login/")
            self.human_like_delay(2, 5)
            
            # Проверяем, не перенаправило ли нас уже на главную страницу
            if "accounts/login" not in self.driver.current_url:
                print("Уже авторизованы, перенаправление на главную страницу")
                return self._check_logged_in()
            
            # Вводим данные
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            self._type_like_human(username_field, INSTAGRAM_CREDENTIALS['username'])
            
            password_field = self.driver.find_element(By.NAME, "password")
            self._type_like_human(password_field, INSTAGRAM_CREDENTIALS['password'])
            
            password_field.send_keys(Keys.RETURN)
            self.human_like_delay(3, 5)
            
            # Обрабатываем возможные проверки
            self._handle_login_checks()
            
            # Проверяем успешный вход
            if not self._check_logged_in():
                return False
            
            # Дополнительная проверка - пробуем получить имя пользователя
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//header//img[@alt='Profile photo']"))
                )
                self.current_username = INSTAGRAM_CREDENTIALS['username']
                self.save_session_cookies()
                print("Успешный вход!")
                return True
            except:
                print("Не удалось подтвердить имя пользователя после входа")
                return False
                
        except Exception as e:
            print(f"Ошибка входа: {str(e)}")
            self._debug_screenshot("login_error")
            return False

    def check_suspicious_activity(self):
        """Проверка подозрительной активности"""
        try:
            suspicious = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'подозрительная') or contains(text(), 'suspicious')]"))
            )
            if suspicious:
                print("Instagram обнаружил подозрительную активность!")
                return True
        except:
            return False
    
    def get_account_info(self, username):
        """Получение информации об аккаунте с новыми локаторами"""
        try:
            self.safe_get(f"https://www.instagram.com/{username}/")
            
            # Проверка доступности страницы
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda d: "страница недоступна" not in d.page_source.lower() and 
                             "this page isn't available" not in d.page_source.lower()
                )
            except TimeoutException:
                print(f"Не удалось загрузить страницу {username}")
                return None

            # Проверка на закрытый аккаунт
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, 
                        "//h2[contains(., 'Этот аккаунт закрыт') or contains(., 'This account is private')]"))
                )
                print(f"Аккаунт {username} закрыт")
                return None
            except TimeoutException:
                pass

            # Получение основной информации
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//h1 | //header"))
                )
                
                full_name = self.driver.find_element(By.XPATH, "//h1").text if len(self.driver.find_elements(By.XPATH, "//h1")) > 0 else ""
                bio = self.driver.find_element(By.XPATH, "//div[contains(@class, '-vDIg')]").text if len(self.driver.find_elements(By.XPATH, "//div[contains(@class, '-vDIg')]")) > 0 else ""
                
                # Новые локаторы для статистики
                stats = self.driver.find_elements(By.XPATH, "//ul/li[contains(.//span, 'подписчиков') or contains(.//span, 'followers')]")
                
                if len(stats) >= 3:
                    posts = stats[0].text.split()[0]
                    followers = stats[1].text.split()[0]
                    following = stats[2].text.split()[0]
                else:
                    # Альтернативные локаторы
                    stats = self.driver.find_elements(By.XPATH, "//header//section//ul//li")
                    if len(stats) >= 3:
                        posts = stats[0].find_element(By.TAG_NAME, "span").text
                        followers = stats[1].find_element(By.TAG_NAME, "span").text
                        following = stats[2].find_element(By.TAG_NAME, "span").text
                    else:
                        posts = followers = following = "0"

                return {
                    'username': username,
                    'full_name': full_name,
                    'bio': bio,
                    'posts': posts,
                    'followers': followers,
                    'following': following
                }

            except Exception as e:
                print(f"Ошибка при получении информации: {str(e)}")
                return None

        except Exception as e:
            print(f"Критическая ошибка при обработке аккаунта {username}: {str(e)}")
            return None

    def parse_followers(self, target_username):
        """Парсинг подписчиков с параллельной обработкой в двух вкладках"""
        try:
            # Сохраняем текущую вкладку (главную)
            main_window = self.driver.current_window_handle
            
            # Открываем страницу профиля
            self.safe_get(f"https://www.instagram.com/{target_username}/")
            self.human_like_delay(3, 5)

            # Открываем подписчиков в новой вкладке
            followers_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//a[contains(@href, '/followers/')]"))
            )
            
            # Кликаем с зажатым Ctrl для открытия в новой вкладке
            ActionChains(self.driver)\
                .key_down(Keys.CONTROL)\
                .click(followers_button)\
                .key_up(Keys.CONTROL)\
                .perform()
            
            self.human_like_delay(2, 4)
            
            # Переключаемся на новую вкладку (список подписчиков)
            followers_window = [w for w in self.driver.window_handles if w != main_window][0]
            self.driver.switch_to.window(followers_window)
            
            # Ожидаем загрузки диалога
            dialog = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, 
                    "//div[@role='dialog']//div[contains(@class, '_aano')]"))
            )
            
            # Создаем третью вкладку для проверки пользователей
            self.driver.execute_script("window.open('about:blank', '_blank');")
            check_window = [w for w in self.driver.window_handles if w not in [main_window, followers_window]][0]
            
            followers = set()
            processed = set()
            scroll_attempts = 0
            max_scroll_attempts = 50
            last_count = 0
            no_new_users_count = 0
            
            print("Начинаем параллельный сбор и проверку...")
            
            while scroll_attempts < max_scroll_attempts and no_new_users_count < 5:
                # 1. Прокручиваем список подписчиков в основной вкладке
                self.driver.switch_to.window(followers_window)
                self.human_scroll(dialog)
                
                # 2. Собираем новых подписчиков
                new_links = dialog.find_elements(By.XPATH,
                    ".//a[contains(@href, '/')][@tabindex='0'] | " + 
                    ".//a[contains(@href, '/')][@role='link']")
                
                new_users = 0
                for link in new_links:
                    try:
                        href = link.get_attribute("href")
                        username = href.split("/")[-2] if href and "/" in href else None
                        if username and username not in followers:
                            followers.add(username)
                            new_users += 1
                    except:
                        continue
                
                # 3. Проверяем прогресс
                current_count = len(followers)
                print(f"Всего подписчиков: {current_count} | Новые: {new_users} | Обработано: {len(processed)}")
                
                if current_count == last_count:
                    no_new_users_count += 1
                else:
                    no_new_users_count = 0
                last_count = current_count
                
                # 4. Проверяем новых пользователей во второй вкладке
                self.driver.switch_to.window(check_window)
                
                # Обрабатываем только новых пользователей
                for user in followers - processed:
                    try:
                        # Быстрая проверка доступности профиля
                        self.driver.get(f"https://www.instagram.com/{user}/")
                        WebDriverWait(self.driver, 10).until(
                            lambda d: d.execute_script("return document.readyState") == "complete"
                        )
                        
                        # Проверяем, не закрыт ли аккаунт
                        if "страница недоступна" in self.driver.page_source.lower():
                            processed.add(user)
                            continue
                            
                        # Быстрое получение информации
                        user_info = self._quick_get_user_info()
                        if user_info:
                            user_info['gender'] = self.determine_gender(user_info)
                            self.save_user_data(user_info)
                            processed.add(user)
                        
                        # Случайная задержка между проверками
                        self.human_like_delay(3, 7)
                        
                    except Exception as e:
                        print(f"Ошибка проверки {user}: {str(e)}")
                        continue
                
                # 5. Проверяем условия завершения
                if len(followers) > 100 and len(processed) / len(followers) > 0.95:
                    break
                    
                scroll_attempts += 1
                self.human_like_delay(1, 3)
            
            # Закрываем вкладки
            self.driver.switch_to.window(followers_window)
            self.driver.close()
            self.driver.switch_to.window(check_window)
            self.driver.close()
            self.driver.switch_to.window(main_window)
            
            return list(processed)
            
        except Exception as e:
            print(f"Ошибка параллельного парсинга: {str(e)}")
            # В случае ошибки закрываем все дополнительные вкладки
            for handle in self.driver.window_handles[1:]:
                self.driver.switch_to.window(handle)
                self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            return []

    def _quick_get_user_info(self):
        """Быстрое получение информации о пользователе без детальных проверок"""
        try:
            # Быстрые локаторы для основных данных
            full_name = self.driver.find_element(By.XPATH, "//h1").text if len(self.driver.find_elements(By.XPATH, "//h1")) > 0 else ""
            bio = self.driver.find_element(By.XPATH, "//div[contains(@class, '-vDIg')]").text if len(self.driver.find_elements(By.XPATH, "//div[contains(@class, '-vDIg')]")) > 0 else ""
            
            # Статистика (упрощенный вариант)
            stats = self.driver.find_elements(By.XPATH, "//header//section//ul//li//span")
            posts = stats[0].text if len(stats) > 0 else "0"
            followers = stats[1].text if len(stats) > 1 else "0"
            following = stats[2].text if len(stats) > 2 else "0"

            return {
                'username': self.driver.current_url.split("/")[-2],
                'full_name': full_name,
                'bio': bio,
                'posts': posts,
                'followers': followers,
                'following': following
            }
        except Exception as e:
            print(f"Ошибка быстрого получения информации: {str(e)}")
            return None
    
    def check_for_block(self):
        """Проверка на блокировку"""
        try:
            block_msg = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH,
                    "//*[contains(text(), 'Попробуйте позже') or "
                    "contains(text(), 'Try Again') or "
                    "contains(text(), 'ограничен') or "
                    "contains(text(), 'limit')]"))
            )
            if block_msg:
                print("Обнаружена блокировка Instagram!")
                return True
        except:
            return False   
            
    def safe_get(self, url, driver=None, max_attempts=3):
        if driver is None:
            driver = self.driver
        for attempt in range(1, max_attempts + 1):
            try:
                driver.get(url)
                WebDriverWait(driver, 15).until(
                    lambda d: d.execute_script("return document.readyState") == "complete")
                return True
            except Exception as e:
                print(f"Попытка {attempt}/{max_attempts} не удалась: {str(e)}")
                if attempt < max_attempts:
                    self.human_like_delay(5, 10)
        return False
    
    def scroll_followers_modal(self):
        scroll_box = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//div[@class='_aano']"))
        )

        last_height = self.driver.execute_script("return arguments[0].scrollHeight", scroll_box)

        while True:
            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_box)
            time.sleep(random.uniform(1.0, 2.0))

            new_height = self.driver.execute_script("return arguments[0].scrollHeight", scroll_box)
            if new_height == last_height:
                break
            last_height = new_height
        
    def parse_followers_with_dual_drivers(self, target_username):
        self.queue = Queue()
        self.processed = set()
        
        def setup_new_driver():
            parser = InstagramParser()
            if not parser.login():
                raise Exception("Второй драйвер не смог залогиниться")
            return parser.driver

        def scroll_and_collect(driver):
            self.safe_get(f"https://www.instagram.com/{target_username}/", driver)
            time.sleep(2)

            followers_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/followers/')]"))
            )
            followers_button.click()

            # Ждём контейнер
            try:
                scroll_box = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//div[contains(@class, '_aano')]"))
                )
            except TimeoutException:
                print("❌ Не удалось найти окно подписчиков — Instagram не загрузил его.")
                return

            seen = set()
            scroll_attempts = 0
            max_scroll_attempts = 50
            last_height = 0

            print("🔁 Начинаем скроллинг и сбор...")

            while scroll_attempts < max_scroll_attempts:
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_box)
                time.sleep(random.uniform(1.2, 2.2))

                new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_box)

                if new_height == last_height:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                    last_height = new_height

                links = scroll_box.find_elements(By.XPATH, ".//a[contains(@href, '/') and contains(@tabindex, '0')]")
                new_users = 0
                for link in links:
                    href = link.get_attribute("href")
                    if not href:
                        continue
                    username = href.split("/")[-2]
                    if username not in seen:
                        self.queue.put(username)
                        seen.add(username)
                        new_users += 1

                print(f"✅ Подписчиков собрано: {len(seen)} | Новых: {new_users}")

                if new_users == 0 and scroll_attempts > 10:
                    print("⏹ Прекращаем — новых пользователей нет.")
                    break

            print(f"[✓] Всего собрано: {len(seen)}")


        def check_profiles(driver):
            while True:
                username = self.queue.get()
                if username in self.processed or username in self.parsed_users:
                    self.queue.task_done()
                    continue
                try:
                    driver.get(f"https://www.instagram.com/{username}/")
                    WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
                    user_info = self._quick_get_user_info()
                    if user_info:
                        user_info['gender'] = self.determine_gender(user_info)
                        self.save_user_data(user_info)
                        self.processed.add(username)
                except Exception as e:
                    print(f"Ошибка при обработке {username}: {e}")
                finally:
                    self.queue.task_done()
                time.sleep(random.uniform(3, 7))

        scroll_driver = self.driver
        check_driver = setup_new_driver()

        Thread(target=scroll_and_collect, args=(scroll_driver,), daemon=True).start()
        Thread(target=check_profiles, args=(check_driver,), daemon=True).start()

        print("[i] Работа запущена. Нажмите Ctrl+C для остановки.")
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            scroll_driver.quit()
            check_driver.quit()
            print("Парсинг остановлен.")    
        
    def determine_gender(self, user_info):
        """Определение пола пользователя на основе фильтров"""
        text_data = f"{user_info['full_name']} {user_info['bio']}".lower()
        
        # Проверка женских ключевых слов
        for keyword in FEMALE_KEYWORDS:
            if keyword.lower() in text_data:
                return "девушка"
        
        # Проверка мужских ключевых слов
        for keyword in MALE_KEYWORDS:
            if keyword.lower() in text_data:
                return "парень"
        
        # Если ключевые слова не найдены, возвращаем "не определен"
        return "не определен"
    
    def save_user_data(self, user_data):
        """Сохранение данных пользователя в файл"""
        file_exists = os.path.exists('users.csv')
        
        with open('users.csv', 'a', encoding='utf-8') as f:
            if not file_exists:
                f.write("username|user_id|full_name|gender|parsed_at\n")
            
            line = (
                f"{user_data['username']}|{user_data.get('user_id', '')}|"
                f"{user_data['full_name']}|{user_data['bio']}|"
                f"{user_data['posts']}|{user_data['followers']}|"
                f"{user_data['following']}|{user_data['gender']}|"
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            f.write(line)
        
        self.parsed_users.add(user_data['username'])
    
    def run(self):
        if not self.login():
            print("Не удалось войти. Проверьте данные и попробуйте позже.")
            return

        current_info = self.get_account_info(self.current_username)
        if current_info:
            print("\nВаш аккаунт:")
            print(f"Ник: {current_info['username']}")
            print(f"Имя: {current_info['full_name']}")
            print(f"Подписчики: {current_info['followers']}")
            print(f"Подписки: {current_info['following']}\n")

        while True:
            target = input("Введите логин для парсинга (или 'exit'): ").strip()
            if target.lower() == 'exit':
                break

            target_info = self.get_account_info(target)
            if not target_info:
                print(f"Аккаунт {target} не найден.")
                continue

            print(f"\nИнформация о {target}:")
            print(f"Имя: {target_info['full_name']}")
            print(f"Подписчики: {target_info['followers']}")

            choice = input("Парсить подписчиков? (да/нет): ").strip().lower()
            if choice != 'да':
                continue

            self.parse_followers_with_dual_drivers(target)

        self.driver.quit()
        print("Работа завершена.")

if __name__ == "__main__":
    parser = InstagramParser()
    parser.run()