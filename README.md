# Port
### Usage
1. Install the dependencies
```basha
python3 -m venv venv
pip3 install -r requirements.txt
```
2. Run **order.py** to create the `portfolio.csv`
```bash
python3 order.py
```
2. Run **main.py** to generate the report
```bash
python3 main.py
```
Four files are generated in the `reports` folder:
- **latest.html** - latest generated html report
- **{todays_date}.html** - html report generated with todays date (example: 2026_04_09.html)
- **/txt/latest.html** - latest generated text report
- **/txt/{todays_date}.html** - text report generated with todays date (example: 2026_04_09.txt)

Enjoy!
