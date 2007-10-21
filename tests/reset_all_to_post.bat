@echo off
cd case01_add_field/ && del models.py && copy models.py.post models.py && cd ..
cd case02_rename_field/ && del models.py && copy models.py.post models.py && cd ..
cd case03_rename_model/ && del models.py && copy models.py.post models.py && cd ..
cd case04_change_flag/ && del models.py && copy models.py.post models.py && cd ..
cd case05_remove_field/ && del models.py && copy models.py.post models.py && cd ..
cd case666_everything/ && del models.py && copy models.py.post models.py && cd ..

cd issue3_intfield_default_value/ && del models.py && copy models.py.post models.py && cd ..
cd issue4_textfield_add/ && del models.py && copy models.py.post models.py && cd ..
