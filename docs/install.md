# Installation

## Voraussetzungen

- [Python](https://www.python.org/)
- Docker
    - Linux: [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/) (oder mit
      Dockers [convenience script](https://get.docker.com/))

## Linux

Schritt für Schritt Anweisungen:

1. Archiv von github herunterladen: [Download](https://github.com/Actionb/jobby/archive/refs/heads/main.tar.gz)
2. Archiv entpacken:  
    ```
    mkdir jobby && tar -xf jobby-main.tar.gz -C ./jobby && cd jobby/jobby-main
    ```
3. Installationsskript ausführen:  
    ```
    python3 install.py --uid=$(id -u) --gid=$(id -g) --password=supersecret
    ```  

Es wird **dringend** empfohlen, die UID und GID zu setzen, damit die von den Docker Containern erzeugten Dateien
(wie z.B. hochgeladene Unterlagen) dem ausführenden Benutzer gehören und nicht etwa dem root-Benutzer.  

Alternativ dazu, hier alle Befehle zusammen. Befehle kopieren und in ein Terminal einfügen:

```shell
curl -fsL https://github.com/Actionb/jobby/archive/refs/heads/main.tar.gz -o /tmp/jobby.tar.gz
mkdir ~/jobby && tar -xf /tmp/jobby.tar.gz -C ~/jobby && cd ~/jobby/jobby-main
python3 install.py --uid=$(id -u) --gid=$(id -g) --password=supersecret
rm /tmp/jobby.tar.gz
```

Die Seite sollte nun unter [http://localhost:8787/jobby](http://localhost:8787/jobby) verfügbar sein.

## Erzeugte Ordner und Dateien

Die folgenden Ordner werden bei der Installation erstellt:

* ein Datenordner (unter Linux standardmäßig `~/.local/share/jobby`), welcher die Daten der Datenbank und die
  hochgeladenen Dateien enthält
* ein Ordner für die Konfiguration (unter Linux standardmäßig `~/.config/jobby`), welcher Dinge wie Datenbankpasswort
  und Umgebungsvariable für die Docker Container enthalten

## Deinstallation

Wie man jobby wieder deinstalliert, findest du hier: [Deinstallation](deinstall.md).
