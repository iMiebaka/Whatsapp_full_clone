<h1 align="center">WhatsApp Clone Using Javascript, Python, WebSocket and Redis</h1>

<p align="center"><img width="100%" src="https://github.com/triple07even/Whatsapp_full_clone/blob/main/private_chat_screenshot.png" alt="Private chat screenshot"></p>

Warning: This app is not a production

This project is a Whatsapp clone using JavaScript and Python </br>
The python framework used in this build in Django

Install Redis on Linux/ Unix (Version >=6)
```shell
sudo apt update
sudo apt-get install redis-server
redis-cli -v
```

Application Installation
```shell
python3 -m venv env
source env/bin/activate
git clone https://github.com/triple07even/Whatsapp_full_clone
cd Whatsapp_full_clone/
```
  * Install all dependencies required
  ```shell
  pip install -r requirements.txt
  ```
  * Open two command line window
    * For the first window, use this command to run the Python app
    ```shell
    python manage.py runserver 0:8000
    ```
    * On the second window, use this command to run the task Queuing service
    ```shell
    celery -A mysite worker -l INFO
    ```
* Open your browser and enter <a href="http://localhost.com:8000" target="_blank" rel="noopener noreferrer""> Go to WhatsApp Clone page</a>

<a href="https://channels.readthedocs.io/en/stable" target="_blank" rel="noopener noreferrer"> Need more knowledge on Django Websocket? Check out the Channels Documention</a> </br>
<a href="https://docs.djangoproject.com/en/3.2/releases/3.0/" target="_blank" rel="noopener noreferrer"> Check out the Django 3 Document for recents update to the framework</a>
