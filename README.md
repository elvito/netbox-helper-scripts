# netbox-helper-scripts

*(Deutsche Version weiter unten / German version further below)*

## English

A small, growing collection of standalone helper scripts for
[NetBox](https://github.com/netbox-community/netbox) - mostly written to
scratch a specific itch in my own home/small-business NetBox setup, and
shared here in case they're useful to anyone else running into the same
kind of problem.

There's no grand plan or roadmap here. Scripts get added whenever a new,
self-contained need comes up. Each one lives in its own subfolder with its
own README covering what it does and how to set it up - this top-level
README is just the entry point.

### Scripts in this repo

- [`dhcp-lease-sync/`](./dhcp-lease-sync) - syncs dynamic (non-reserved)
  DHCP leases from a Technitium DNS Server into NetBox IPAM as tagged,
  auto-managed `IPAddress` objects, and removes them again once the lease
  is gone.

(More may be added over time - check each subfolder's own README for
specifics.)

### Who this is for

Anyone running NetBox for a home lab or small business who finds one of
these scripts solves a problem they also have. Take what's useful, adapt
it, ignore the rest. Issues/PRs are welcome, but please don't expect
enterprise-grade support - see the disclaimer below.

### Authorship & disclaimer

Most of the code in this repo was written by **Claude** (Anthropic's AI
assistant), based on requirements, real-world testing, and iteration done
interactively with **elvito**. These are personal hobby-project tools,
built and tested against one specific home/small-business NetBox setup -
not professionally audited or officially supported software.

**No warranty, no liability.** Everything in this repo is provided "as
is", without warranty of any kind, express or implied (see the `LICENSE`
file for the formal terms). Use entirely at your own risk. Neither the
author(s) nor the AI that helped write this code accept any
responsibility for data loss, misconfiguration, network outages, or any
other damage that might result from using these scripts. Read the code,
understand what it does, and test thoroughly (most scripts here support a
`dry_run` mode for exactly this reason) in your own environment before
relying on any of it for anything that matters.

---

## Deutsch

Eine kleine, wachsende Sammlung eigenständiger Helfer-Skripte für
[NetBox](https://github.com/netbox-community/netbox) - größtenteils
geschrieben, um ein konkretes Problem im eigenen privaten/kleinen
NetBox-Setup zu lösen, und hier geteilt, falls sie für jemand anderen mit
einem ähnlichen Problem ebenfalls nützlich sind.

Es gibt keinen großen Plan oder Roadmap dahinter. Skripte kommen dazu,
sobald ein neuer, in sich abgeschlossener Bedarf entsteht. Jedes lebt in
seinem eigenen Unterordner mit eigener README, die beschreibt, was es tut
und wie man es einrichtet - diese oberste README ist nur der Einstiegspunkt.

### Skripte in diesem Repo

- [`dhcp-lease-sync/`](./dhcp-lease-sync) - synchronisiert dynamische
  (nicht reservierte) DHCP-Leases eines Technitium DNS Servers nach NetBox
  IPAM als getaggte, automatisch verwaltete `IPAddress`-Objekte, und
  entfernt sie wieder, sobald der Lease weg ist.

(Es können mit der Zeit weitere dazukommen - Details jeweils in der README
des entsprechenden Unterordners.)

### Für wen das gedacht ist

Für alle, die NetBox in einem Homelab oder kleinen Betrieb betreiben und
in einem dieser Skripte ein Problem gelöst finden, das sie auch haben.
Nimm mit, was nützlich ist, pass es an, ignorier den Rest. Issues/PRs sind
willkommen, aber erwarte bitte keinen Enterprise-Support - siehe
Haftungsausschluss unten.

### Autorenschaft & Haftungsausschluss

Der Großteil des Codes in diesem Repo wurde von **Claude** (Anthropics
KI-Assistent) geschrieben, basierend auf Anforderungen, Praxistests und
Iteration, die interaktiv mit **elvito** durchgeführt wurden. Das sind
persönliche Hobby-Projekt-Tools, gebaut und getestet gegen ein
spezifisches privates/kleines NetBox-Setup - keine professionell
auditierte oder offiziell supportete Software.

**Keine Gewährleistung, keine Haftung.** Alles in diesem Repo wird "wie
besehen" bereitgestellt, ohne jegliche ausdrückliche oder stillschweigende
Gewährleistung (die formalen Bedingungen stehen in der `LICENSE`-Datei).
Die Nutzung erfolgt vollständig auf eigene Gefahr. Weder der/die Autor(en)
noch die KI, die beim Schreiben dieses Codes geholfen hat, übernehmen
Verantwortung für Datenverlust, Fehlkonfigurationen, Netzwerkausfälle oder
sonstige Schäden, die aus der Nutzung dieser Skripte entstehen könnten.
Lies den Code, verstehe, was er tut, und teste gründlich (die meisten
Skripte hier unterstützen genau aus diesem Grund einen `dry_run`-Modus) in
deiner eigenen Umgebung, bevor du dich für irgendetwas Wichtiges darauf
verlässt.
