# Deinstallation

In das jobby Source Verzeichnis wechseln und `python3 install.py --uninstall` ausführen.

**ACHTUNG**: Es wird ausgegeben, welche Ordner gelöscht werden - stelle sicher, dass diese nichts enthalten, das du
unbedingt behalten möchtest! So werden zum Beispiel die Daten der Datenbank aber auch alle hochgeladenen Dateien
gelöscht.

Optional: Docker Images löschen: `docker image rm jobby-web:latest postgres:alpine`

Danach kann das jobby Source Verzeichnis gelöscht werden.