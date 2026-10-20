(TODO: format this file properly)


To run neoprisma without building:

1. Clone the repo

2. cd to the repo in your terminal

3. make a python venv at the root dir of the repo and enter it 

2. Install requirements.txt

3. If you do not have cmake, install cmake

4. cd to the repo in your terminal (If on windows use developer powershell)

5. run `mkdir build; cd build`

6. if on windows: `cmake .. -A x64` if on mac: `cmake ..`

7. run `cmake --build . --config Release`

8. exit the build dir (cd ..)

9. if on windows: `python src/main.py` if on mac: `python3 src/main.py`