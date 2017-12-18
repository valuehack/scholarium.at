# scholarium.at
## Setup
### Virtualenv
```
virtualenv -p python3 venv
source venv/bin/activate
```
### Dependencies
```
pip install -r requirements.txt
```
### Server mit localen Settings
```
python manage.py runserver --settings='seite.local_settings'
```
### Datenbank besorgen
```
scp scholarium.at:/home/scholarium/scholarium_production/db.sqlite3 .
```
## Workflow
1) Repository forken
2) Branch erstellen für neue Commits
3) Pull Request erstellen: Issue verlinken, Inhalt beschreiben.
4) Bei größeren Veränderungen: Branch auf Server testen!
### Server
- /home/scholarium/scholarium_production: Immer Master, aktive scholarium.at Umgebung
- /home/scholarium/scholarium_staging: Testumgebung
## Schriftengenerierung
### Prerequisites
```
pandoc >= 0.18.1.0
pandoc-citeproc >= -1.10.0.0.
```
pandoc-citeproc muss from source kompiliert werden. (Stand: 2016-11-22 auf Ubuntu)


### TrelloToSql
|Syntax                     |Funktion                   |
|---------------------------|---------------------------|
`<<<`                       |Trennung des privaten Teils|
`[@title: page]`            |Literaturreferenz erstellen|
`§§ [article slug or tags]` |Individuelle Artikel-Tags (nur Trello Import)|
`§§! [article slug or tags]`|Artikel mit hoher Priorität (nur Trello Import)|
