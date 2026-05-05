# godlike-Run   

添加 GODLIKE_EMAIL: 你的登录邮箱。

添加 GODLIKE_PASSWORD: 你的登录密码。

cron-job.org 配置:   
```
https://api.github.com/repos/你的用户名/仓库名/dispatches
```

Accept: application/vnd.github.v3+json

Authorization: Bearer <你的TOKEN>

Body 填写:
```
{"event_type": "renew_event"}
