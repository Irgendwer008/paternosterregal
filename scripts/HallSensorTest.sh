sudo systemctl start pigpiod
sudo ../venv/bin/pip3.11 install -r ../requirements.txt
sudo ../venv/bin/python3.11 ../HallSensorTest.py
