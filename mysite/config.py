from decouple import config

AMAZON_CREDENTIAL = {
    'AWS_ACCESS_KEY_ID': config('AWS_STORAGE_BUCKET_NAME'),
    'AWS_SECRET_ACCESS_KEY': config('AWS_SECRET_ACCESS_KEY'),
    'AWS_STORAGE_BUCKET_NAME' : config('AWS_STORAGE_BUCKET_NAME')
}

OTP_KEY = "Some Random Secret Key"
SECRET_KEY = 'fhg$#j9_ubon58_ml7-dm%@!m9@+4$1-5mfw&+(yk!*f3nnyo3'
HOST_PASSWORD = 'xxxx'

ALLOWED_HOSTS = ['192.168.43.112','localhost','127.0.0.1']
