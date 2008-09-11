@echo off
for /D %%a in (case* issue*) do cd %%a\ && del models.py 1>nul 2>nul && copy models.post.py models.py > nul && cd ..
