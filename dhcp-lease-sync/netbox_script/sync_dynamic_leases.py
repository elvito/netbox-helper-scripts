"""
NetBox Custom Script: Sync Dynamic Technitium DHCP Leases into IPAM.

This runs INSIDE NetBox (via Customization > Scripts), not as an
external process - so it uses NetBox's own database models directly
instead of pynetbox/an API token. Only the Technitium side still needs
plain HTTP + its own API token, entered as script input fields below
so nothing is hardcoded in this file.

What this does (identical logic to the standalone version, see
sync_dynamic_leases.py):
  1. Fetches current leases from Technitium's DHCP API.
  2. Keeps only leases with type == "Dynamic" (Reserved leases are your
     manually-maintained static entries and are never touched here).
  3. Looks up the correct subnet mask for each IP from NetBox's own
     Prefix data - no hardcoded mask, works across any number/size of
     subnets.
  4. Creates or updates a matching NetBox IPAddress, tagged
     "dhcp-dynamic", keyed by MAC address via a custom field.
  5. Deletes any "dhcp-dynamic"-tagged IPAddress whose MAC no longer
     appears in the current dynamic lease list.

Prerequisites in NetBox (create these once, manually, before running):
  - Custom field "dhcp_lease_mac" (type: Text) on object type IPAM > IP Address
  - Tag "dhcp-dynamic"
  - A user/token running this needs permissions: extras.run_script,
    plus view/add/change/delete on ipam.ipaddress and view on ipam.prefix

How to install via a Git-backed Data Source (so you can update this by
just pushing to GitHub and hitting "Sync" in NetBox):
  1. Push this file to a GitHub repo.
  2. In NetBox: Operations > Data Sources > Add > type "Git",
     point it at your repo.
  3. Sync the Data Source.
  4. Customization > Scripts > Add, select this file from that
     Data Source. It will then show up as a runnable script in the UI,
     with its own history/logs, and can optionally be scheduled to
     run on a recurring interval directly from the run form.

Known caveat: recurring script scheduling has had bugs in some NetBox
4.1.x releases (a completed recurring job sometimes fails to
reschedule the next run). If recurring runs stop appearing after the
first execution, check your NetBox version's release notes, or fall
back to triggering this script on a schedule from outside (e.g. cron
calling the /api/extras/scripts/<name>/ endpoint with schedule_at).
"""

import requests

from extras.scripts import Script, StringVar, BooleanVar
from extras.models import Tag
from ipam.models import IPAddress, Prefix


DYNAMIC_TAG_SLUG = "dhcp-dynamic"
MAC_CUSTOM_FIELD = "dhcp_lease_mac"


class SyncDynamicLeases(Script):

    class Meta:
        name = "Sync Dynamic DHCP Leases (Technitium)"
        description = (
            "Pulls dynamic (non-reserved) DHCP leases from a Technitium "
            "server and mirrors them into IPAM as dhcp-dynamic tagged "
            "IP addresses, removing entries for leases that are gone."
        )
        scheduling_enabled = True
        commit_default = True

    technitium_url = StringVar(
        description="Technitium base URL, e.g. http://100.64.x.x:5380 "
                     "(reachable via your Tailscale tunnel)",
    )
    technitium_token = StringVar(
        description="Technitium API token (created via createToken, "
                     "ideally for a low-privilege, view-only user)",
    )
    dry_run = BooleanVar(
        description="If checked: only log what would happen, change nothing",
        default=False,
    )
    verify_ssl = BooleanVar(
        description="Verify Technitium's TLS certificate. Uncheck only if "
                     "Technitium uses a self-signed certificate you haven't "
                     "added to the trust store, and you're aware this "
                     "connection isn't certificate-verified (fine for a "
                     "purely internal Tailscale-tunneled connection).",
        default=True,
    )

    # ----------------------------------------------------------------
    # Technitium side
    # ----------------------------------------------------------------

    def fetch_dynamic_leases(self, base_url, token, verify_ssl):
        if not verify_ssl:
            # Suppress the noisy per-request warning since the user has
            # explicitly and knowingly opted out of certificate checking.
            requests.packages.urllib3.disable_warnings(
                requests.packages.urllib3.exceptions.InsecureRequestWarning
            )

        resp = requests.get(
            f"{base_url.rstrip('/')}/api/dhcp/leases/list",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
            verify=verify_ssl,
        )
        resp.raise_for_status()
        payload = resp.json()

        if payload.get("status") != "ok":
            raise RuntimeError(f"Technitium API returned an error: {payload}")

        leases = payload["response"]["leases"]
        dynamic = [lease for lease in leases if lease.get("type") == "Dynamic"]
        self.log_info(
            f"Technitium: {len(leases)} leases total, {len(dynamic)} dynamic"
        )
        return dynamic

    @staticmethod
    def normalize_mac(mac: str) -> str:
        return mac.strip().upper().replace("-", ":")

    # ----------------------------------------------------------------
    # NetBox side
    # ----------------------------------------------------------------

    def get_matching_prefix(self, ip_str: str) -> Prefix:
        """
        Find the NetBox Prefix object that actually contains this IP.

        Returns the whole Prefix object (not just the mask length) so
        the caller can also read its VRF - important because a newly
        created IPAddress with no VRF set lands in NetBox's "global"
        address space, which is treated as separate from a VRF-scoped
        one even if the numeric IP ranges overlap. Without copying the
        VRF from the matching Prefix, dhcp-dynamic addresses would
        silently end up in the wrong (global) address space - which is
        also very likely why the DNS plugin's automatic IPAM sync
        didn't pick these up: its Prefix-to-view mapping is scoped per
        VRF, and a global address matches no such mapping.
        """
        matches = [
            p for p in Prefix.objects.all()
            if ip_str in p.prefix
        ]
        if not matches:
            raise RuntimeError(
                f"No matching NetBox Prefix found containing {ip_str}. "
                "Create/check the corresponding Prefix in IPAM first."
            )
        # Most specific (longest mask) match wins - relevant if prefixes
        # are nested. Note: if the same address range exists in more
        # than one VRF, this doesn't disambiguate between them; for a
        # single-VRF-per-subnet setup like this one that's not an issue.
        return max(matches, key=lambda p: p.prefix.prefixlen)

    def fetch_existing_dynamic_addresses(self, tag):
        existing = {}
        for ip in IPAddress.objects.filter(tags=tag):
            mac = ip.custom_field_data.get(MAC_CUSTOM_FIELD)
            if mac:
                existing[self.normalize_mac(mac)] = ip
        self.log_info(f"NetBox: {len(existing)} existing dhcp-dynamic addresses")
        return existing

    def create_address(self, lease, tag, commit, dry_run):
        mac = self.normalize_mac(lease["hardwareAddress"])
        prefix = self.get_matching_prefix(lease["address"])
        address = f'{lease["address"]}/{prefix.prefix.prefixlen}'
        hostname = lease.get("hostName", "")

        self.log_info(
            f"CREATE {address} (mac={mac}, host={hostname}, vrf={prefix.vrf})"
        )
        if not commit or dry_run:
            return

        ip = IPAddress(
            address=address,
            vrf=prefix.vrf,
            status="active",
            dns_name=hostname,
            description=f"Dynamic DHCP lease (scope: {lease.get('scope')})",
            custom_field_data={MAC_CUSTOM_FIELD: mac},
        )
        ip.save()
        ip.tags.add(tag)

    def update_address_if_changed(self, ip, lease, commit, dry_run):
        mac = self.normalize_mac(lease["hardwareAddress"])
        prefix = self.get_matching_prefix(lease["address"])
        new_address = f'{lease["address"]}/{prefix.prefix.prefixlen}'
        new_hostname = lease.get("hostName", "")

        changed = False
        if str(ip.address) != new_address:
            self.log_info(f"UPDATE {mac}: address {ip.address} -> {new_address}")
            ip.address = new_address
            changed = True

        if ip.vrf != prefix.vrf:
            self.log_info(f"UPDATE {mac}: vrf {ip.vrf} -> {prefix.vrf}")
            ip.vrf = prefix.vrf
            changed = True

        # NetBox always stores dns_name lowercased, regardless of what's
        # written to it. Technitium's client-reported hostnames aren't
        # guaranteed to be consistently cased between lease renewals, so
        # comparing case-sensitively here would flag a "change" on every
        # single run even though nothing meaningful changed.
        if (ip.dns_name or "").lower() != new_hostname.lower():
            self.log_info(f"UPDATE {mac}: dns_name {ip.dns_name} -> {new_hostname}")
            ip.dns_name = new_hostname
            changed = True

        if changed and commit and not dry_run:
            ip.save()

    def delete_stale_addresses(self, existing, current_macs, commit, dry_run):
        for mac, ip in existing.items():
            if mac not in current_macs:
                self.log_info(
                    f"DELETE {ip.address} (mac={mac}) - "
                    "no longer an active dynamic lease"
                )
                if commit and not dry_run:
                    ip.delete()

    # ----------------------------------------------------------------
    # Entry point
    # ----------------------------------------------------------------

    def run(self, data, commit):
        dry_run = data["dry_run"]
        if dry_run:
            self.log_warning("Dry run enabled - no changes will be made")

        tag, _ = Tag.objects.get_or_create(
            slug=DYNAMIC_TAG_SLUG,
            defaults={"name": DYNAMIC_TAG_SLUG},
        )

        dynamic_leases = self.fetch_dynamic_leases(
            data["technitium_url"], data["technitium_token"], data["verify_ssl"]
        )
        existing = self.fetch_existing_dynamic_addresses(tag)

        current_macs = set()
        for lease in dynamic_leases:
            mac = self.normalize_mac(lease["hardwareAddress"])
            current_macs.add(mac)

            if mac in existing:
                self.update_address_if_changed(existing[mac], lease, commit, dry_run)
            else:
                self.create_address(lease, tag, commit, dry_run)

        self.delete_stale_addresses(existing, current_macs, commit, dry_run)

        self.log_success("Sync complete.")
