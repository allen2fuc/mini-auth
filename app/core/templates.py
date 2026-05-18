"""Jinja2 模板引擎 - 各模块共用一个实例,模板路径在项目根 templates/"""
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="templates")