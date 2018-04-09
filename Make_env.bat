call conda remove -n weather_report --all --yes
call conda create -n weather_report python=3.6 html5lib lxml pandas numpy beautifulsoup4 --yes
call activate weather_report
call pip install https://github.com/Geosyntec/python-pdfkit/archive/master.zip
pause

