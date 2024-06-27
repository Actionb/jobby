# Installation

## Voraussetzungen

- [Python](https://www.python.org/)
- Docker
    - Linux: [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/) (oder mit Dockers [convenience script](https://get.docker.com/))

## Linux

Diese Befehle kopieren und in ein Terminal einfügen:

```shell
curl -fsL https://github.com/Actionb/jobby/archive/refs/heads/main.tar.gz -o /tmp/jobby.tar.gz
mkdir ~/jobby && tar -xf /tmp/jobby.tar.gz -C ~/jobby && cd ~/jobby/jobby-main
python3 install.py --uid=$(id -u) --gid=$(id -g) --password=supersecret
rm /tmp/jobby.tar.gz
```

Alternativ, Schritt für Schritt:

1. Herunterladen: https://github.com/Actionb/jobby/archive/refs/heads/main.tar.gz
2. Entpacken: `mkdir jobby && tar -xf jobby-main.tar.gz -C ./jobby`
3. In das Jobby Verzeichnis wechseln: `cd jobby/jobby-main`
4. Installationsskript ausführen: `python3 install.py --uid=$(id -u) --gid=$(id -g) --password=supersecret`

Die Seite sollte nun unter http://localhost:8787/jobby verfügbar sein.

## Erzeugte Ordner und Dateien

Die folgenden Ordner werden bei der Installation erstellt:

* ein Datenordner (unter Linux standardmäßig `~/.local/share/jobby`), welcher die Daten der Datenbank und die
  hochgeladenen Dateien enthält
* ein Ordner für die Konfiguration (unter Linux standardmäßig `~/.config/jobby`), welcher Dinge wie Datenbankpasswort
  und Umgebungsvariable für die Docker Container enthalten

## Deinstallation

Wie man jobby wieder deinstalliert, findest du hier: [Deinstallation](deinstall.md).
