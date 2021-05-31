<h1 align="center">WhatsApp Clone Using Javascript, Python, WebSocket and Redis</h1>

<p align="center"><img width="100%" src="https://github.com/triple07even/Whatsapp_full_clone/blob/main/private_chat_screenshot.png" alt="Private chat screenshot"></p>

This project is a Whatsapp clone using JavaScript and Python
The python framework used in this build in Django

Warning: This app is not a production

Note: Make sure you have Redis Installed (Version >=6)

Linux/ Unix Installation
```shell
sudo apt update
sudo apt-get install redis-server
redis-cli -v
```

Installation
```shell
python3 -m venv env
source env/bin/activate
git clone https://github.com/triple07even/Whatsapp_full_clone
cd Whatsapp_full_clone/
```
  * Install all dependencies required: `pip install -r requirements.txt`
  * Open two command line window
    * For the first window `python manage.py runserver 0:8000`
    * On the second window `celery -A mysite worker -l INFO`
* Open your browser and enter <a>http://localhost.com:8000</a>

<a href="https://channels.readthedocs.io/en/stable" target="_blank" rel="noopener noreferrer"> Check out the Channels Documention on how the WebSocket works</a>
