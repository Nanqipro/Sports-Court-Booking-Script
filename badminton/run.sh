# 后台运行
python badminton_while1.py &
python badminton_while2.py &
python badminton_while3.py &
python badminton_while4.py &

# 后台运行不受终端影响
nohup python badminton_while1.py > output1.log 2>&1 &
nohup python badminton_while2.py > output2.log 2>&1 &
nohup python badminton_while3.py > output3.log 2>&1 &
nohup python badminton_while4.py > output4.log 2>&1 &

# 检查后台python进程 
ps aux | grep python
ps -ef | grep python | grep -v grep

# 终止进程
kill 2018860
pkill python
