## 环境依赖

### 创建一个虚拟环境

python -m venv venv

### 激活虚拟环境

source venv/bin/activate

pip install -r requirements.txt

pip freeze > requirements.txt

### 退出虚拟环境

deactivate


## 运行

### Production环境: 

用到了 vercel 的Edge Function, 调用的是 handler 函数, 所以本地没法调试

### Dev调试(目前比较稳定, 所以这部分代码去掉了): 

自己再copy一下主要代码写 python 脚本测试吧