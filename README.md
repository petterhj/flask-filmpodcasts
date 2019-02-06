Search film podcasts synced using [redis](https://redis.io/).

```sh
pip install -r requirements.txt
redis-server --daemonize yes
rqscheduler
rq worker --url redis://localhost:6379
```

```sh
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```