@echo off

call venv\Scripts\activate
SET TWINE_USERNAME=hyjiacan
python -m twine upload dist/*