# restfx

欢迎使用自动路由框架 restfx。

源码仓库: https://gitee.com/hyjiacan/restfx

在线文档: https://gitee.com/hyjiacan/restfx/wikis

如果遇到任何问题，或者有意见或建议，请通过 https://gitee.com/hyjiacan/restfx/issues 提交

## 安装依赖

```bash
python -m venv venv
# Linux
source ./venv/bin/activate
# Windows:
.\venv\Scripts\activate.bat
pip install werkzeug restfx
python main.py
```

然后访问 http://127.0.0.1:9127/api 就能查看接口页面

## 生成项目

执行 `python main.py persist` 以生成 `dist/routes_map.py`，此文件应该在发布前生成
