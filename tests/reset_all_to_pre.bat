@echo off
cd case01_add_field/ && del models.py > nul && copy models.py.pre models.py > nul && cd ..
cd case02_rename_field/ && del models.py > nul && copy models.py.pre models.py > nul && cd ..
cd case03_rename_model/ && del models.py > nul && copy models.py.pre models.py > nul && cd ..
cd case04_change_flag/ && del models.py > nul && copy models.py.pre models.py > nul && cd ..
cd case05_remove_field/ && del models.py > nul && copy models.py.pre models.py > nul && cd ..
cd case666_everything/ && del models.py > nul && copy models.py.pre models.py > nul && cd ..

cd issue3_intfield_default_value/ && del models.py > nul && copy models.py.pre models.py > nul && cd ..
cd issue4_textfield_add/ && del models.py > nul && copy models.py.pre models.py > nul && cd ..
