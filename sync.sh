#!/usr/bin/env bash

# 获取当前脚本目录
project_path=$(cd `dirname $0`; pwd)

cd ${project_path}

/usr/bin/git pull

/usr/bin/git add .

/usr/bin/git commit -m "更新文档"

/usr/bin/git push
