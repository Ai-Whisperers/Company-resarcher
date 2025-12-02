# Source-003: Unterschied TIGO TS4-A-S und TIGO TS4-A-O - Komponenten / Bastelecke (Off-Grid) - Photovoltaikforum

## Metadata

| Field | Value |
|-------|-------|
| **URL** | https://www.photovoltaikforum.com/thread/236879-unterschied-tigo-ts4-a-s-und-tigo-ts4-a-o/ |
| **Type** | Web |
| **Date Accessed** | 2025-12-01 |
| **Reliability** | Medium |
| **Language** | Auto-detected |

---

## Content Classification

| Field | Value |
|-------|-------|
| **Sections Used** | competitive_landscape, investment_analysis, sales_intelligence, strategic_context |

---

## Extracted Content

PV-Forum jetzt auf YouTube!
Verpasse keine PV-News mehr –
klicke hier und abonniere unseren Kanal
.
Hallo,
ich will meine bestehende Anlage wegen stark unterschiedlicher Verschattung mit TIGO Optimierern nachrüsten (7 Stück). Im Angebot sind TS4-A-S und TS4-A-O. Nach den Datenblättern gibt es keine Unterschiede. Hat da jemand schon Erfahrungen mit dem einen oder anderen Typ?
Monitoring (also CCA und TAP) ist nicht geplant, weil kein Netz vorhanden.
Danke schon mal im Voraus
schau mal hier:
Unterschied TIGO TS4-A-S und TIGO TS4-A-O
Zitat von Nereus
Hat da jemand schon Erfahrungen mit dem einen oder anderen Typ?
Bestimmt gibts Einige, ich gehöre aber (noch) nicht dazu.
Zitat von Nereus
Nach den Datenblättern gibt es keine Unterschiede.
Doch, muss es.
Es gibt:
- TS4-A-M (blaues Etiket) mit "M" wie "Monitoring" (Überwachung)
- TS4-A-S (rotes Etiket) mit "S" wie "Schnellabschaltung" zuätzlich zu "Monitoring" (Schnellabschaltung ist für Feuerwehr interesannt, da auf Modul/Optimierer-Ebene spannungsfrei geschaltet wird.)
- TS4-A-O (gelbes Etiket) mit "O" wie "Optimierer". Auch hier sind die Funktionen aus "S" und "M" enthalten.
Zitat von Nereus
Monitoring (also CCA und TAP) ist nicht geplant,
Das währe dann der "Blind-Modus", ist aber nicht zu emfehlen. Und ist auch mit eingeschränkter Garantie.
Ich hoffe, ich habe das als "Laie" richtig in Erinnerung.
Gruß Cleo
Der einzige Unterschied zwischen -S und -O ist offensichtlich die "intelligente Optimierung", wer weiß, was das ist. Optimieren sollen sie ja beide.
Ja, Blindmodus, geht nicht anders, kein WLan vorhanden. Ist schon fraglich, was dabei passieren soll..
Gruß Hartmut
Zitat von Nereus
Optimieren sollen sie ja beide.
Nein, der TS4-A-S kann nicht optimieren. Der wurde vermutlich nur mit ins Angebot genommen, um ein Monitoring der nichtoptimierten Module zu ermöglichen.
Tigo TS4-A-S
Sicherheit ist eine Flex-MLPE-Funktion, die eine schnelle Abschaltung und Überwachung auf Modulebene ermöglicht. Es ist UL PV Rapid Shutdown System (PVRSS)…
de.tigoenergy.com
Zitat von Nereus
Ja, Blindmodus, geht nicht anders, kein WLan vorhanden. Ist schon fraglich, was dabei passieren soll.
Thema
TIGO Optimierer TS4-A-O Probleme --- 26/88 defekt
Hallo,
hat von euch auch jemand die TIGO TS4-A-O im Einsatz und hat eine sehr hohe Ausfallrate von knapp einem Drittel der Optimierer (26/88 müssen ausgetauscht werden)?
Unsere Anlage ist nun seit Okt. 2020 in Betrieb und seit Mai kämpfe ich mit den Optimierern. Z.Z. sind 3 komplett ausgefallen und über den TIGO Support wurde die Anlage überprüft und festgestellt, dass insgesamt 26 TS4 einen Defekt haben.
TIGO hat über ihren RMA-Prozess anstandslos Ersatzgeräte rausgeschickt, aber um den…
ds_knx
4. August 2021 um 17:45
Achte dort auf die Beiträge von
Tigo Ambivalenter
, der eigtl. nichts mit der Firma zu tun hat, aber trotzdem gut im Stoff steht.
Gruß Cleo
Ich kaper mal den Thread, da ich ne Frage habe, mit vergleichbaren Vorraussetzungen. Die Frage des TE ist vermutlich bereits geklärt.
Tigo Ambivalenter
Währe ein überwachter Blindmodus mit CCA/TAP ohne Internet möglich?
Noch habe ich nix von Tigo, auch keine Erfahrungen, nur hin und wieder mal etwas aufgeschnapt.
Optimierungsbedarf ist bei mir massiv vorhanden, sowohl auf Modulebene, im Kernwinter (Insel) und auch im Konzept. Aktuell habe ich meine Akkuladung über CTK-Laderegler + nachgeschalteten PWM-LR konzipiert. Funktioniert und jedes Modul hat sein eigenen MPPT. Aber wie bei allen Kompromissen, ist auch mein Weg nur ein Kompromiss. Ein Blick übern Tellerrand kann nicht schaden.
Bisher hat mich die Notwendigkeit einer ständigen Internetverbindung von TIGO abgehalten. (Magenta schaft es seit Jahren nicht, den vorhanden Anschluß zu beschalten.) Ein Monitoring auf Modulebene finde ich aber widerum interessant, also CCA währe bei mir mit auf der Einkaufsliste. Von daher die Eingangsfrage: Funktionieren die Optimierer mit lokaler Überwachung ohne Internet
zuverlässig
? (Sporadisches mobiles Internet über 4G ist möglich und somit auch eine Erstkonfiguration u. ggfls. Updates.)
(Das Inselproblem mit den kurzen parallelgeschalteten Strings an Ladereglern, ist erst mal zweitrangig und vermutlich auch beherschbar. Zur Not geht auch AC-Coupling. Ist aber erst mal unwichtig.)
Gruß Cleo
Ganz theoretisch kann man die Tigos auch ohne Internet mit selbstgemachten Monitoring betreiben.
Das ist allerdings alles andere als Plug&Play.
Danke
erst mal. Tigo hat also kein NoGo bei mir bekommen und bleibt also erst mal auf der Optionen-Liste.
Zitat von Tigo Ambivalenter
Das ist allerdings alles andere als Plug&Play.
Dazu müßte ich mich hier bestimmt einlesen.
Thema
Details, Protokolle, Zugang auf Tigo CCA
Hallo zusammen,
dieser Thread soll dazu dienen, Informationen über die Tigo-Optimizer zu sammeln.
Protokolle RS485
Protokolle Zigbee
Details
Firmware-Versionen, Upgrades
Zugang
Einstellungen und Einstellmöglichkeiten
weiteres
netadair
20. November 2020 um 19:09
Wird für mich bestimmt eine große Herausforderu

---

## Quality Notes

| Aspect | Assessment |
|--------|------------|
| **Reliability** | Medium |
| **Content Length** | 5052 characters |
