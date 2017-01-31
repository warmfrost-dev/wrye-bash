# -*- coding: utf-8 -*-
#
# GPL License and Copyright Notice ============================================
#  This file is part of Wrye Bash.
#
#  Wrye Bash is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  Wrye Bash is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Wrye Bash; if not, write to the Free Software Foundation,
#  Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
#  Wrye Bash copyright (C) 2005-2009 Wrye, 2010-2015 Wrye Bash Team
#  https://github.com/wrye-bash
#
# =============================================================================
from collections import OrderedDict
# Local
from ..bolt import formatDate
from . import _EditableMixin, BashTab, SashPanel
from ..balt import UIList
from .. import load_order

class LoDetails(_EditableMixin, SashPanel):
    keyPrefix = 'bash.mods.loadOrders.details' # used in sash/scroll position, sorting

    def __init__(self, parent):
        SashPanel.__init__(self, parent, isVertical=False)
        _EditableMixin.__init__(self, parent)

class LoList(UIList):
    labels = OrderedDict([
        ('Index',    lambda self, p: unicode(p)),
        ('Date',     lambda self, p: formatDate(self.data_store[p].date)),
    ])
    _sort_keys = {
        'Index': None, # just sort by index
        'Date' : lambda self, a: self.data_store[a].date,
    }
    _default_sort_col = 'Index'

class LoPanel(BashTab):
    _details_panel_type = LoDetails
    _ui_list_type = LoList
    keyPrefix = 'bash.mods.loadOrders'

    def __init__(self, parent):
        self.listData = {x: y for x, y in
                         enumerate(load_order._saved_load_orders)}
        super(LoPanel, self).__init__(parent)
