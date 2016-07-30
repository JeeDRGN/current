# -*- coding: UTF-8 -*-
from django.conf import settings
from commands.command import MuxCommand


class CmdAccess(MuxCommand):
    """
    Displays your current world access levels for
    your current player and character account.
    Usage:
      access
    Switches:
    /groups  - Also displays the system's permission groups hierarchy.
    """
    key = 'access'
    locks = 'cmd:all()'
    help_category = 'System'

    def func(self):
        """Load the permission groups"""
        char = self.character
        player = self.player
        hierarchy_full = settings.PERMISSION_HIERARCHY
        string = ''
        if 'groups' in self.switches:
            string = "|wPermission Hierarchy|n (climbing): %s|/" % ", ".join(hierarchy_full)
        if player.is_superuser:
            cperms = "<|ySuperuser|n> " + ", ".join(char.permissions.all())
            pperms = "<|ySuperuser|n> " + ", ".join(player.permissions.all())
        else:
            cperms = ", ".join(char.permissions.all())
            pperms = ", ".join(player.permissions.all())
        string += "|wYour Player/Character access|n: "
        if hasattr(char, 'player'):
            string += "Player: (%s: %s) and " % (player.get_display_name(self.session), pperms)
        string += "Character (%s: %s)" % (char.get_display_name(self.session), cperms)
        player.msg(string)