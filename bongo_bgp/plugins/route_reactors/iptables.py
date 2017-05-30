import subprocess

from bongo_bgp.plugins.route_reactors import base


class IptablesReactor(base.ReactorBase):
    """Generates IPTables rules to ban traffic to rejected prefixes.

    Adjust the class-level 'interface' variable to control which
    interface the iptables rules are applied to.
    """

    interface = 'eth100'

    def __init__(self):
        # keep track of all banned prefixes
        self.currently_banned_prefixes = set()

    def route_accepted(self, prefix, next_hop, as_path):
        if prefix in self.currently_banned_prefixes:
            self.currently_banned_prefixes.discard(prefix)
            self._reapply_rules()

    def route_removed(self, prefix, next_hop, as_path):
        # in blacklist approach, removal is same as accepted
        self.route_accepted(prefix, next_hop, as_path)

    def route_rejected(self, prefix, next_hop, as_path):
        if prefix not in self.currently_banned_prefixes:
            self.currently_banned_prefixes.add(prefix)
            self._reapply_rules()

    def _reapply_rules(self):
        existing = self._get_non_bongo_rules()
        rules = [self._prefix_to_block_rule(pref)
                 for pref in self.currently_banned_prefixes]
        jump_rule = "-i %s -j BONGO-CHAIN" % self.interface
        self._iptables_restore(existing + [jump_rule] + rules)

    def _prefix_to_block_rule(self, prefix):
        prefix = str(prefix)
        rule = "BONGO-CHAIN -D %s -P DROP" % prefix
        return rule

    def _get_non_bongo_rules(self):
        return [r for r in self._iptables_save()
                if "BONGO-CHAIN" not in r]

    def _iptables_save(self):
        return self._do_exec(['iptables-save'])

    def _iptables_restore(self, rules):
        self._do_exec(['iptables-restore'], stdin='\n'.join(rules))

    def _do_exec(self, cmd, stdin=None):
        kwargs = {'stdout': subprocess.PIPE}
        if stdin:
            kwargs['stdin'] = subprocess.PIPE
        p = subprocess.Popen(cmd)
        kwargs = {}
        if stdin:
            kwargs['input'] = stdin
        return p.communicate(**kwargs)[0].splitlines()
