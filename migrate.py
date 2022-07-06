import yaml

file = open ('migrate.yml', 'r', encoding="utf-8")
#使用文件对象作为参数
date = yaml.load(file)
print(data)
