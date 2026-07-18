# NetBox ↔ Technitium Dynamic DHCP Lease Sync

*(Deutsche Version weiter unten / German version further below)*

## English

### What this does

This script keeps NetBox IPAM in sync with **dynamic** (non-reserved) DHCP
leases from a [Technitium DNS Server](https://technitium.com/dns/) instance.

Statically reserved leases (devices you've manually configured a
`HostReservation` for, e.g. via the
[netbox-plugin-dhcp](https://github.com/sys4/netbox-plugin-dhcp) plugin) are
never touched by this script - it only ever creates, updates, or deletes
NetBox `IPAddress` objects tagged `dhcp-dynamic`, so your manually maintained
data stays untouched no matter what.

Specifically, on each run it:
1. Fetches current leases from Technitium's DHCP API.
2. Filters for `type == "Dynamic"`.
3. Creates or updates a matching NetBox `IPAddress` for each one, tagged
   `dhcp-dynamic`, matched by MAC address (stored in a custom field, since
   these devices intentionally have no Device/Interface object in NetBox).
4. Looks up the correct subnet mask *and* VRF for each address from NetBox's
   own `Prefix` data, rather than hardcoding either - so it keeps working
   correctly across multiple subnets/VRFs of different sizes.
5. Deletes any `dhcp-dynamic` tagged `IPAddress` whose MAC no longer appears
   in the current lease list (device gone / lease expired).

### Installation (this is a NetBox Custom Script - runs inside NetBox)

This runs *inside* NetBox with direct database access (no NetBox API
token needed), viewable/runnable from the NetBox UI, with its own job log
history.

### Prerequisites (create these once in NetBox before running the script)

- A **Custom Field** named exactly `dhcp_lease_mac` (type: Text) on object
  type `IPAM > IP Address`.
- A **Tag** named `dhcp-dynamic` (the script creates this automatically on
  first run if it doesn't exist yet).
- A Technitium user/API token with at least `DhcpServer: View` permission
  (create via Technitium's `createToken` API call). Using a dedicated,
  low-privilege user rather than your admin account is recommended.

### Installing the script

1. Push this repo to your own GitHub (or clone it wherever).
2. In NetBox: `Operations > Data Sources > Add`, type **Git**, point it at
   your repo, then sync it. (Alternatively: `Customization > Scripts > Add
   > Upload` the `.py` file directly for a quick one-off test, without
   setting up a Data Source.)
3. `Customization > Scripts > Add`, select the script file from the synced
   Data Source (or from your upload).
4. Run it once with the `dry_run` option checked to confirm it does what
   you expect before letting it write anything.
5. Optionally schedule it as a recurring job directly from the script's run
   form. Note: recurring script scheduling has had bugs in some NetBox
   4.1.x releases (a completed recurring job occasionally fails to
   reschedule the next run) - if that happens to you, trigger it externally
   on a schedule instead (e.g. cron/Semaphore hitting the
   `/api/extras/scripts/<name>/` endpoint).

### Known limitations

- If the same IP range exists in more than one VRF in your NetBox instance,
  the prefix/VRF lookup can't disambiguate between them - it picks the most
  specific (longest mask) match. Fine for a single-VRF-per-subnet setup;
  something to be aware of otherwise.
- Devices using randomized/rotating MAC addresses (e.g. iOS "Rotating"
  Private Wi-Fi Address) will appear as a series of different MAC entries
  rather than one consistent device, since matching is MAC-based.
- This does not talk to Technitium's DNS side at all - it only reads DHCP
  lease data. If you also want dynamic DNS records for these devices,
  that's a separate consideration (and will interact with your existing
  IPAM→DNS plugin automation, since `dns_name` triggers it for *any*
  `IPAddress`, not just statically reserved ones).

### Authorship & disclaimer

The bulk of this code was written by **Claude** (Anthropic's AI assistant),
based on requirements and testing done interactively with **elvito**. This 
is a personal hobby-project tool, written for a
home/small-business NetBox + Technitium setup, tested manually against that
specific environment - it is **not** a professionally audited or
officially supported piece of software.

**No warranty, no liability.** This script is provided "as is", without
warranty of any kind, express or implied. Use it entirely at your own risk.
The author(s) accept no responsibility for any data loss, misconfiguration,
network outage, or other damage that may result from using it. Read the
code, understand what it does, and test thoroughly (with `dry_run` enabled)
in your own environment before relying on it for anything that matters.

---

## Deutsch

### Was dieses Skript macht

Dieses Skript hält NetBox IPAM synchron mit **dynamischen** (nicht
reservierten) DHCP-Leases eines [Technitium DNS Server](https://technitium.com/dns/).

Statisch reservierte Leases (Geräte, für die du manuell eine
`HostReservation` angelegt hast, z. B. über das
[netbox-plugin-dhcp](https://github.com/sys4/netbox-plugin-dhcp)-Plugin)
werden von diesem Skript **niemals** angefasst - es erstellt, aktualisiert
oder löscht ausschließlich NetBox-`IPAddress`-Objekte mit dem Tag
`dhcp-dynamic`. Eure manuell gepflegten Daten bleiben also in jedem Fall
unberührt.

Im Detail passiert bei jedem Lauf:
1. Aktuelle Leases werden über Technitiums DHCP-API abgerufen.
2. Nur Einträge mit `type == "Dynamic"` werden weiterverarbeitet.
3. Für jeden davon wird eine passende NetBox-`IPAddress` erstellt oder
   aktualisiert, getaggt mit `dhcp-dynamic`, abgeglichen über die
   MAC-Adresse (gespeichert in einem Custom Field, da diese Geräte
   bewusst kein Device-/Interface-Objekt in NetBox haben).
4. Die passende Subnetzmaske **und** das passende VRF werden für jede
   Adresse aus den vorhandenen NetBox-`Prefix`-Daten abgeleitet, statt
   fest codiert zu sein - funktioniert dadurch auch über mehrere
   Subnetze/VRFs unterschiedlicher Größe hinweg korrekt.
5. `IPAddress`-Objekte mit Tag `dhcp-dynamic`, deren MAC nicht mehr in der
   aktuellen Lease-Liste auftaucht, werden gelöscht (Gerät weg / Lease
   abgelaufen).

### Installation (dieses NetBox Custom Script - läuft innerhalb von NetBox)

Läuft *innerhalb* von NetBox mit direktem Datenbankzugriff (kein
NetBox-API-Token nötig), über die NetBox-UI einsehbar/ausführbar, mit
eigener Job-Log-Historie.

### Voraussetzungen (einmalig in NetBox anzulegen, bevor das Script läuft)

- Ein **Custom Field** mit exaktem Namen `dhcp_lease_mac` (Typ: Text) auf
  Objekttyp `IPAM > IP Address`.
- Ein **Tag** namens `dhcp-dynamic` (das Script legt diesen beim ersten
  Lauf automatisch an, falls er fehlt).
- Ein Technitium-Nutzer/API-Token mit mindestens `DhcpServer: View`-Recht
  (per Technitiums `createToken`-API-Aufruf erzeugen). Ein eigener,
  rechte-eingeschränkter Nutzer statt des Admin-Accounts wird empfohlen.

### Installation des Scripts

1. Dieses Repo auf dein eigenes GitHub pushen (oder irgendwo klonen).
2. In NetBox: `Operations > Data Sources > Add`, Typ **Git**, URL deines
   Repos eintragen, dann syncen. (Alternativ für einen schnellen Test ohne
   Data Source: `Customization > Scripts > Add > Upload` und die `.py`-Datei
   direkt hochladen.)
3. `Customization > Scripts > Add`, die Skriptdatei aus der gesyncten Data
   Source auswählen (oder aus deinem Upload).
4. Einmal mit aktivierter `dry_run`-Option ausführen, um zu bestätigen,
   dass es das tut, was du erwartest, bevor irgendwas tatsächlich
   geschrieben wird.
5. Optional als wiederkehrenden Job direkt im Ausführungsformular des
   Scripts einplanen. Hinweis: Wiederkehrende Script-Zeitplanung hatte in
   manchen NetBox-4.1.x-Versionen Bugs (ein abgeschlossener wiederkehrender
   Job wird gelegentlich nicht für den nächsten Lauf neu eingeplant) -
   falls dir das passiert, stattdessen von außen zeitgesteuert triggern
   (z. B. Cron/Semaphore gegen den `/api/extras/scripts/<name>/`-Endpunkt).

### Bekannte Einschränkungen

- Falls derselbe IP-Bereich in eurer NetBox-Instanz in mehr als einem VRF
  existiert, kann die Prefix-/VRF-Zuordnung nicht zwischen ihnen
  unterscheiden - es wird die spezifischste (längste Maske) Übereinstimmung
  gewählt. Bei einem Setup mit einem VRF pro Subnetz kein Problem, sonst
  beachtenswert.
- Geräte mit randomisierten/rotierenden MAC-Adressen (z. B. iOS
  "Rotating" Private Wi-Fi Address) erscheinen als mehrere verschiedene
  MAC-Einträge statt als ein durchgängiges Gerät, da der Abgleich
  MAC-basiert erfolgt.
- Dieses Skript spricht überhaupt nicht mit der DNS-Seite von Technitium -
  es liest ausschließlich DHCP-Lease-Daten. Falls ihr für diese Geräte auch
  dynamische DNS-Einträge wollt, ist das eine separate Überlegung (und
  wirkt mit eurer bestehenden IPAM→DNS-Plugin-Automatik zusammen, da
  `dns_name` diese für **jede** `IPAddress` auslöst, nicht nur für
  statisch reservierte).

### Autorenschaft & Haftungsausschluss

Der Großteil dieses Codes wurde von **Claude** (Anthropics KI-Assistent)
geschrieben, basierend auf Anforderungen und Tests, die interaktiv mit
**elvito** durchgeführt wurden. Dies ist ein
persönliches Hobby-Projekt-Tool, geschrieben für ein privates/kleines
NetBox + Technitium Setup, manuell gegen diese spezifische Umgebung
getestet - es ist **keine** professionell auditierte oder offiziell
supportete Software.

**Keine Gewährleistung, keine Haftung.** Dieses Skript wird "wie besehen"
bereitgestellt, ohne jegliche ausdrückliche oder stillschweigende
Gewährleistung. Die Nutzung erfolgt vollständig auf eigene Gefahr. Der/die
Autor(en) übernehmen keine Verantwortung für Datenverlust,
Fehlkonfigurationen, Netzwerkausfälle oder sonstige Schäden, die aus der
Nutzung entstehen könnten. Lies den Code, verstehe, was er tut, und teste
gründlich (mit aktiviertem `dry_run`) in deiner eigenen Umgebung, bevor du
dich für irgendetwas Wichtiges darauf verlässt.
