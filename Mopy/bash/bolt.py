# -*- coding: utf-8 -*-
#
# GPL License and Copyright Notice ============================================
#  This file is part of Wrye Bash.
#
#  Wrye Bash is free software: you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation, either version 3
#  of the License, or (at your option) any later version.
#
#  Wrye Bash is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Wrye Bash.  If not, see <https://www.gnu.org/licenses/>.
#
#  Wrye Bash copyright (C) 2005-2009 Wrye, 2010-2020 Wrye Bash Team
#  https://github.com/wrye-bash
#
# =============================================================================

# Imports ---------------------------------------------------------------------
#--Standard
from __future__ import division, print_function

import cPickle as pickle  # PY3
import codecs
import collections
import copy
import csv
import datetime
import errno
import io
import os
import re
import shutil
import stat
import string
import struct
import subprocess
import sys
import tempfile
import textwrap
import traceback
from binascii import crc32
from functools import partial
from itertools import chain, izip
from keyword import iskeyword
from operator import attrgetter
from urllib import quote

import chardet

# Internal
from . import exception

# structure aliases, mainly introduced to reduce uses of 'pack' and 'unpack'
struct_pack = struct.pack
struct_unpack = struct.unpack
struct_error = struct.error
struct_calcsize = struct.calcsize

#-- To make commands executed with Popen hidden
startupinfo = None
if os.name == u'nt':
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

# speed up os.walk
try:
    import scandir
    _walk = walkdir = scandir.walk
except ImportError:
    _walk = walkdir = os.walk
    scandir = None

# Unicode ---------------------------------------------------------------------
#--decode unicode strings
#  This is only useful when reading fields from mods, as the encoding is not
#  known.  For normal filesystem interaction, these functions are not needed
encodingOrder = (
    u'ascii',    # Plain old ASCII (0-127)
    u'gbk',      # GBK (simplified Chinese + some)
    u'cp932',    # Japanese
    u'cp949',    # Korean
    u'cp1252',   # English (extended ASCII)
    u'utf8',
    u'cp500',
    u'UTF-16LE',
)
if os.name == u'nt':
    encodingOrder += (u'mbcs',)

_encodingSwap = {
    # The encoding detector reports back some encodings that
    # are subsets of others.  Use the better encoding when
    # given the option
    # 'reported encoding':'actual encoding to use',
    u'GB2312': u'gbk',        # Simplified Chinese
    u'SHIFT_JIS': u'cp932',   # Japanese
    u'windows-1252': u'cp1252',
    u'windows-1251': u'cp1251',
    u'utf-8': u'utf8',
}

# Preferred encoding to use when decoding/encoding strings in plugin files
# None = auto
# setting it tries the specified encoding first
pluginEncoding = None

# Encodings that we can't use because Python doesn't even support them
_blocked_encodings = {u'EUC-TW'}

def getbestencoding(bitstream):
    """Tries to detect the encoding a bitstream was saved in.  Uses Mozilla's
       detection library to find the best match (heuristics)"""
    result = chardet.detect(bitstream)
    encoding_, confidence = result[u'encoding'], result[u'confidence']
    encoding_ = _encodingSwap.get(encoding_,encoding_)
    ## Debug: uncomment the following to output stats on encoding detection
    #print('%s: %s (%s)' % (repr(bitstream),encoding,confidence))
    return encoding_,confidence

def decoder(byte_str, encoding=None, avoidEncodings=()):
    """Decode a byte string to unicode, using heuristics on encoding."""
    if isinstance(byte_str, unicode) or byte_str is None: return byte_str
    # Try the user specified encoding first
    if encoding:
        # TODO(ut) monkey patch
        if encoding == u'cp65001':
            encoding = u'utf-8'
        try: return unicode(byte_str, encoding)
        except UnicodeDecodeError: pass
    # Try to detect the encoding next
    encoding, confidence = getbestencoding(byte_str)
    if encoding and confidence >= 0.55 and (
            encoding not in avoidEncodings or confidence == 1.0) and (
            encoding not in _blocked_encodings):
        try: return unicode(byte_str, encoding)
        except UnicodeDecodeError: pass
    # If even that fails, fall back to the old method, trial and error
    for encoding in encodingOrder:
        try: return unicode(byte_str, encoding)
        except UnicodeDecodeError: pass
    raise UnicodeDecodeError(u'Text could not be decoded using any method')

def encode(text_str, encodings=encodingOrder, firstEncoding=None,
           returnEncoding=False):
    """Encode unicode string to byte string, using heuristics on encoding."""
    if isinstance(text_str, bytes) or text_str is None:
        if returnEncoding: return text_str, None
        else: return text_str
    # Try user specified encoding
    if firstEncoding:
        try:
            text_str = text_str.encode(firstEncoding)
            if returnEncoding: return text_str, firstEncoding
            else: return text_str
        except UnicodeEncodeError:
            pass
    goodEncoding = None
    # Try the list of encodings in order
    for encoding in encodings:
        try:
            test_encoded = text_str.encode(encoding)
            detectedEncoding = getbestencoding(test_encoded)
            if detectedEncoding[0] == encoding:
                # This encoding also happens to be detected
                # By the encoding detector as the same thing,
                # which means use it!
                if returnEncoding: return test_encoded, encoding
                else: return test_encoded
            # The encoding detector didn't detect it, but
            # it works, so save it for later
            if not goodEncoding: goodEncoding = (test_encoded, encoding)
        except UnicodeEncodeError:
            pass
    # Non of the encodings also where detectable via the
    # detector, so use the first one that encoded without error
    if goodEncoding:
        if returnEncoding: return goodEncoding
        else: return goodEncoding[0]
    raise UnicodeEncodeError(u'Text could not be encoded using any of the following encodings: %s' % encodings)

def encode_complex_string(string_val, max_size=None, min_size=None,
                          preferred_encoding=None):
    """Handles encoding of a string that must satisfy certain conditions. Any
    of the keyword arguments may be omitted, in which case they will simply not
    apply.

    :param string_val: The unicode string to encode.
    :param max_size: The maximum size of the unicode string. If string_val is
        longer than this, it will be truncated.
    :param min_size: The minimum size of the encoded string. If the result of
        encoding string_val is shorter than this, it will be right-padded with
        null bytes.
    :param preferred_encoding: The encoding to try first. Defaults to
        bolt.pluginEncoding.
    :return: The encoded string."""
    preferred_encoding = preferred_encoding or pluginEncoding
    if max_size:
        string_val = winNewLines(string_val.rstrip())
        truncated_size = min(max_size, len(string_val))
        test, tested_encoding = encode(string_val,
                                       firstEncoding=preferred_encoding,
                                       returnEncoding=True)
        extra_encoded = len(test) - max_size
        if extra_encoded > 0:
            total = 0
            i = -1
            while total < extra_encoded:
                total += len(string_val[i].encode(tested_encoding))
                i -= 1
            truncated_size += i + 1
            string_val = string_val[:truncated_size]
            string_val = encode(string_val, firstEncoding=tested_encoding)
        else:
            string_val = test
    else:
        string_val = encode(string_val, firstEncoding=preferred_encoding)
    if min_size and len(string_val) < min_size:
        string_val += b'\x00' * (min_size - len(string_val))
    return string_val

def timestamp(): return datetime.datetime.now().strftime(u'%Y-%m-%d %H.%M.%S')

##: Keep an eye on https://bugs.python.org/issue31749
def round_size(size_bytes):
    """Returns the specified size in bytes as a human-readable size string."""
    ##: Maybe offer an option to switch between KiB and KB?
    prefix_pt2 = u'B' # if bass.settings[...] else u'iB'
    size_bytes /= 1024 # Don't show bytes
    for prefix_pt1 in (u'K', u'M', u'G', u'T', u'P', u'E', u'Z', u'Y'):
        if size_bytes < 1024:
            # Show a single decimal digit, but never show trailing zeroes
            return u'%s %s' % (
                    (u'%.1f' % size_bytes).rstrip(u'0').rstrip(u'.'),
                    prefix_pt1 + prefix_pt2)
        size_bytes /= 1024
    return _(u'<very large>') # ;)

# Helpers ---------------------------------------------------------------------
def sortFiles(files, __split=os.path.split):
    """Utility function. Sorts files by directory, then file name."""
    return sorted(files, key=lambda x: __split(x.lower()))

# PY3: Dicts are ordered by default on py3.7, so drop this in favor of just
# collections.defaultdict
class OrderedDefaultDict(collections.OrderedDict, collections.defaultdict):
    """A defaultdict that preserves order."""
    def __init__(self, default_factory=None, *args, **kwargs):
        super(OrderedDefaultDict, self).__init__(*args, **kwargs)
        self.default_factory = default_factory

# LowStrings ------------------------------------------------------------------
class CIstr(unicode):
    """See: http://stackoverflow.com/q/43122096/281545"""
    __slots__ = ()

    #--Hash/Compare
    def __hash__(self):
        return hash(self.lower())
    def __eq__(self, other):
        if isinstance(other, CIstr):
            return self.lower() == other.lower()
        return NotImplemented
    def __ne__(self, other):
        if isinstance(other, CIstr):
            return self.lower() != other.lower()
        return NotImplemented
    def __lt__(self, other):
        if isinstance(other, CIstr):
            return self.lower() < other.lower()
        return NotImplemented
    def __ge__(self, other):
        if isinstance(other, CIstr):
            return self.lower() >= other.lower()
        return NotImplemented
    def __gt__(self, other):
        if isinstance(other, CIstr):
            return self.lower() > other.lower()
        return NotImplemented
    def __le__(self, other):
        if isinstance(other, CIstr):
            return self.lower() <= other.lower()
        return NotImplemented
    #--repr
    def __repr__(self):
        return u'%s(%s)' % (type(self).__name__, super(CIstr, self).__repr__())

class LowerDict(dict):
    """Dictionary that transforms its keys to CIstr instances.
    See: https://stackoverflow.com/a/43457369/281545
    """
    __slots__ = () # no __dict__ - that would be redundant

    @staticmethod # because this doesn't make sense as a global function.
    def _process_args(mapping=(), **kwargs):
        if hasattr(mapping, u'iteritems'): # PY3: items
            mapping = getattr(mapping, u'iteritems')()
        # PY3: fix mess below - kwargs keys are bytes im py2
        return ((CIstr(k) if type(k) is unicode else k, v) for k, v in chain(
            ((k.decode(u'ascii') if type(k) is bytes else k, v) for k, v in
             mapping),
            ((k.decode(u'ascii') if type(k) is bytes else k, v) for k, v in
             getattr(kwargs, u'iteritems')())))

    def __init__(self, mapping=(), **kwargs):
        # dicts take a mapping or iterable as their optional first argument
        super(LowerDict, self).__init__(self._process_args(mapping, **kwargs))

    def __getitem__(self, k):
        return super(LowerDict, self).__getitem__(
            CIstr(k) if type(k) is unicode else k)

    def __setitem__(self, k, v):
        return super(LowerDict, self).__setitem__(
            CIstr(k) if type(k) is unicode else k, v)

    def __delitem__(self, k):
        return super(LowerDict, self).__delitem__(
            CIstr(k) if type(k) is unicode else k)

    def copy(self): # don't delegate w/ super - dict.copy() -> dict :(
        return type(self)(self)

    def get(self, k, default=None):
        return super(LowerDict, self).get(
            CIstr(k) if type(k) is unicode else k, default)

    def setdefault(self, k, default=None):
        return super(LowerDict, self).setdefault(
            CIstr(k) if type(k) is unicode else k, default)

    __no_default = object()
    def pop(self, k, v=__no_default):
        if v is LowerDict.__no_default:
            # super will raise KeyError if no default and key does not exist
            return super(LowerDict, self).pop(
                CIstr(k) if type(k) is unicode else k)
        return super(LowerDict, self).pop(
            CIstr(k) if type(k) is unicode else k, v)

    def update(self, mapping=(), **kwargs):
        super(LowerDict, self).update(self._process_args(mapping, **kwargs))

    def __contains__(self, k):
        return super(LowerDict, self).__contains__(
            CIstr(k) if type(k) is unicode else k)

    @classmethod
    def fromkeys(cls, keys, v=None):
        return super(LowerDict, cls).fromkeys((CIstr(k) if type(
            k) is unicode else k for k in keys), v)

    def __repr__(self):
        return u'%s(%s)' % (
            type(self).__name__, super(LowerDict, self).__repr__())

class DefaultLowerDict(LowerDict, collections.defaultdict):
    """LowerDict that inherits from defaultdict."""
    __slots__ = () # no __dict__ - that would be redundant

    def __init__(self, default_factory=None, mapping=(), **kwargs):
        # note we can't use LowerDict __init__ directly
        super(LowerDict, self).__init__(default_factory,
                                        self._process_args(mapping, **kwargs))

    def copy(self):
        return type(self)(self.default_factory, self)

    def __repr__(self):
        return u'%s(%s, %s)' % (type(self).__name__, self.default_factory,
            super(collections.defaultdict, self).__repr__())

class OrderedLowerDict(LowerDict, collections.OrderedDict):
    """LowerDict that inherits from OrdererdDict."""
    __slots__ = () # no __dict__ - that would be redundant

#------------------------------------------------------------------------------
# cache attrgetter objects
class _AttrGettersCache(dict):
    def __missing__(self, attr_name):
        return self.setdefault(attr_name, attrgetter(attr_name))

attrgetter_cache = _AttrGettersCache()

# noinspection PyDefaultArgument
def setattr_deep(obj, attr, value, __attrgetters=attrgetter_cache,
        __split_cache={}):
    try:
        parent_attr, leaf_attr = __split_cache[attr]
    except KeyError:
        dot_dex = attr.rfind(u'.')
        if dot_dex > 0:
            parent_attr = attr[:dot_dex]
            leaf_attr = attr[dot_dex + 1:]
        else:
            parent_attr = u''
            leaf_attr = attr
        __split_cache[attr] = parent_attr, leaf_attr
    setattr(__attrgetters[parent_attr](obj) if parent_attr else obj,
        leaf_attr, value)

# Paths -----------------------------------------------------------------------
#------------------------------------------------------------------------------
_gpaths = {}

def GPath(str_or_uni):
    """Path factory and cache.

    :rtype: Path"""
    if isinstance(str_or_uni, Path) or str_or_uni is None: return str_or_uni
    if not str_or_uni: return Path(u'') # needed, os.path.normpath(u'') = u'.'!
    if str_or_uni in _gpaths: return _gpaths[str_or_uni]
    return _gpaths.setdefault(str_or_uni, Path(os.path.normpath(str_or_uni)))

##: generally points at file names, masters etc. using Paths, which they should
# not - hunt down and just use strings
def GPath_no_norm(str_or_uni):
    """Alternative to GPath that does not call normpath. It is up to the caller
    to ensure that the precondition name == os.path.normpath(name) holds for
    all values pased into this method.

    :rtype: Path"""
    if isinstance(str_or_uni, Path) or str_or_uni is None: return str_or_uni
    if not str_or_uni: return Path(u'') # needed, os.path.normpath(u'') = u'.'!
    if str_or_uni in _gpaths: return _gpaths[str_or_uni]
    return _gpaths.setdefault(str_or_uni, Path(str_or_uni))

def GPathPurge():
    """Cleans out the _gpaths dictionary of any unused bolt.Path objects.
       We cannot use a weakref.WeakValueDictionary in this case for 2 reasons:
        1) bolt.Path, due to its class structure, cannot be made into weak
           references
        2) the objects would be deleted as soon as the last reference goes
           out of scope (not the behavior we want).  We want the object to
           stay alive as long as we will possibly be needing it, IE: as long
           as we're still on the same tab.
       So instead, we'll manually call our flushing function a few times:
        1) When switching tabs
        2) Prior to building a bashed patch
        3) Prior to saving settings files
    """
    for key in list(_gpaths):
        # Using list() allows us to modify the dictionary while iterating
        if sys.getrefcount(_gpaths[key]) == 2:
            # 1 for the reference in the _gpaths dictionary,
            # 1 for the temp reference passed to sys.getrefcount
            # meanin the object is not reference anywhere else
            del _gpaths[key]

#------------------------------------------------------------------------------
class Path(object):
    """Paths are immutable objects that represent file directory paths.
     May be just a directory, filename or full path."""

    #--Class Vars/Methods -------------------------------------------
    sys_fs_enc = sys.getfilesystemencoding() or u'mbcs'
    invalid_chars_re = re.compile(u'' r'(.*)([/\\:*?"<>|]+)(.*)', re.I | re.U)

    @staticmethod
    def getNorm(str_or_path):
        # type: (unicode|bytes|Path) -> unicode
        """Return the normpath for specified basename/Path object."""
        if isinstance(str_or_path, Path): return str_or_path._s
        elif not str_or_path: return u'' # and not maybe b''
        elif isinstance(str_or_path, bytes): str_or_path = decoder(str_or_path)
        return os.path.normpath(str_or_path)

    @staticmethod
    def getcwd():
        return Path(os.getcwdu())

    def setcwd(self):
        """Set cwd."""
        os.chdir(self._s)

    @staticmethod
    def has_invalid_chars(string):
        match = Path.invalid_chars_re.match(string)
        if not match: return None
        return match.groups()[1]

    #--Instance stuff --------------------------------------------------
    #--Slots: _s is normalized path. All other slots are just pre-calced
    #  variations of it.
    __slots__ = (u'_s', u'_cs', u'_sroot', u'_shead', u'_stail', u'_ext',
                 u'_cext', u'_sbody')

    def __init__(self, norm_str):
        # type: (unicode) -> None
        """Initialize with unicode - call only in GPath."""
        self._s = _s = norm_str # path must be normalized
        self._cs = _s.lower()

    def __getstate__(self):
        """Used by pickler. _cs is redundant,so don't include."""
        return self._s

    def __setstate__(self, norm):
        """Used by unpickler. Reconstruct _cs."""
        # Older pickle files stored filename in bytes, not unicode
        norm = decoder(norm)  # decoder will check for unicode
        self._s = norm
        # Reconstruct _cs, lower() should suffice
        self._cs = os.path.normcase(norm)

    def __len__(self):
        return len(self._s)

    def __repr__(self):
        return u'bolt.Path(%r)' % self._s

    def __str__(self):
        return self._s

    #--Properties--------------------------------------------------------
    #--String/unicode versions.
    @property
    def s(self):
        """Path as string."""
        return self._s
    @property
    def cs(self):
        """Path as string in normalized case."""
        return self._cs
    @property
    def sroot(self):
        """Root as string."""
        try:
            return self._sroot
        except AttributeError:
            self._sroot, self._ext = os.path.splitext(self._s)
            return self._sroot
    @property
    def shead(self):
        """Head as string."""
        try:
            return self._shead
        except AttributeError:
            self._shead, self._stail = os.path.split(self._s)
            return self._shead
    @property
    def stail(self):
        """Tail as string."""
        try:
            return self._stail
        except AttributeError:
            self._shead, self._stail = os.path.split(self._s)
            return self._stail
    @property
    def sbody(self):
        """For alpha\beta.gamma returns beta as string."""
        try:
            return self._sbody
        except AttributeError:
            self._sbody = os.path.basename(self.sroot)
            return self._sbody
    @property
    def csbody(self):
        """For alpha\beta.gamma returns beta as string in normalized case."""
        return os.path.normcase(self.sbody)

    #--Head, tail
    @property
    def headTail(self):
        """For alpha\beta.gamma returns (alpha,beta.gamma)"""
        return [GPath(self.shead), GPath(self.stail)]
    @property
    def head(self):
        """For alpha\beta.gamma, returns alpha."""
        return GPath(self.shead)
    @property
    def tail(self):
        """For alpha\beta.gamma, returns beta.gamma."""
        return GPath_no_norm(self.stail)
    @property
    def body(self):
        """For alpha\beta.gamma, returns beta."""
        return GPath_no_norm(self.sbody)

    #--Root, ext
    @property
    def root(self):
        """For alpha\beta.gamma returns alpha\beta"""
        return GPath(self.sroot)
    @property
    def ext(self):
        """Extension (including leading period, e.g. '.txt')."""
        try:
            return self._ext
        except AttributeError:
            self._sroot, self._ext = os.path.splitext(self._s)
            return self._ext
    @property
    def cext(self):
        """Extension in normalized case."""
        try:
            return self._cext
        except AttributeError:
            self._cext = os.path.normcase(self.ext)
            return self._cext
    @property
    def temp(self):
        """Temp file path."""
        baseDir = GPath(unicode(tempfile.gettempdir(), Path.sys_fs_enc)).join(
            u'WryeBash_temp')
        baseDir.makedirs()
        return baseDir.join(self.tail + u'.tmp')

    @staticmethod
    def tempDir(prefix=u'WryeBash_'):
        # workaround for http://bugs.python.org/issue1681974 see there - PY3: ?
        try:
            return GPath(tempfile.mkdtemp(prefix=prefix))
        except UnicodeDecodeError:
            try:
                traceback.print_exc()
                print(u'Trying to pass temp dir in...')
                tempdir = unicode(tempfile.gettempdir(), Path.sys_fs_enc)
                return GPath(tempfile.mkdtemp(prefix=prefix, dir=tempdir))
            except UnicodeDecodeError:
                try:
                    traceback.print_exc()
                    print(u'Trying to encode temp dir prefix...')
                    return GPath(tempfile.mkdtemp(
                        prefix=prefix.encode(Path.sys_fs_enc)).decode(
                        Path.sys_fs_enc))
                except:
                    traceback.print_exc()
                    print(u'Failed to create tmp dir, Bash will not function '
                          u'correctly.')

    @staticmethod
    def baseTempDir():
        return GPath(unicode(tempfile.gettempdir(), Path.sys_fs_enc))

    @property
    def backup(self):
        """Backup file path."""
        return self+u'.bak'

    #--size, atime, ctime
    @property
    def size(self):
        """Size of file or directory."""
        if self.isdir():
            join = os.path.join
            op_size = os.path.getsize
            try:
                return sum(sum(op_size(join(x, f)) for f in files)
                           for x, _y, files in _walk(self._s))
            except ValueError:
                return 0
        else:
            return os.path.getsize(self._s)

    @property
    def atime(self):
        return os.path.getatime(self._s)
    @property
    def ctime(self):
        return os.path.getctime(self._s)

    #--Mtime
    def _getmtime(self):
        """Return mtime for path."""
        return os.path.getmtime(self._s)
    def _setmtime(self, mtime):
        os.utime(self._s, (self.atime, mtime))
    mtime = property(_getmtime, _setmtime, doc=u'Time file was last modified.')

    def size_mtime(self):
        lstat = os.lstat(self._s)
        return lstat.st_size, lstat.st_mtime

    def size_mtime_ctime(self):
        lstat = os.lstat(self._s)
        return lstat.st_size, lstat.st_mtime, lstat.st_ctime

    @property
    def stat(self):
        """File stats"""
        return os.stat(self._s)

    @property
    def version(self):
        """File version (exe/dll) embedded in the file properties."""
        from .env import get_file_version
        return get_file_version(self._s)

    @property
    def strippedVersion(self):
        """.version with leading and trailing zeros stripped."""
        version = list(self.version)
        while len(version) > 1 and version[0] == 0:
            version.pop(0)
        while len(version) > 1 and version[-1] == 0:
            version.pop()
        return tuple(version)

    #--crc
    @property
    def crc(self):
        """Calculates and returns crc value for self."""
        crc = 0
        with self.open(u'rb') as ins:
            for block in iter(partial(ins.read, 2097152), b''):
                crc = crc32(block, crc) # 2MB at a time, probably ok
        return crc & 0xffffffff

    #--Path stuff -------------------------------------------------------
    #--New Paths, subpaths
    def __add__(self,other):
        # you can't add to None: ValueError - that's good
        return GPath(self._s + Path.getNorm(other))
    def join(*args):
        norms = [Path.getNorm(x) for x in args] # join(..,None,..) -> TypeError
        return GPath(os.path.join(*norms))

    def list(self):
        """For directory: Returns list of files."""
        try:
            return [GPath_no_norm(x) for x in os.listdir(self._s)]
        except OSError as e:
            if e.errno != errno.ENOENT: raise
            return []

    def walk(self,topdown=True,onerror=None,relative=False):
        """Like os.walk."""
        if relative:
            start = len(self._s)
            for root_dir,dirs,files in _walk(self._s, topdown, onerror):
                yield (GPath(root_dir[start:]),
                       [GPath_no_norm(x) for x in dirs],
                       [GPath_no_norm(x) for x in files])
        else:
            for root_dir,dirs,files in _walk(self._s, topdown, onerror):
                yield (GPath(root_dir),
                       [GPath_no_norm(x) for x in dirs],
                       [GPath_no_norm(x) for x in files])

    def relpath(self,path): # os.path.relpath(p,[s]): AttributeError if s==None
        return GPath(os.path.relpath(self._s,Path.getNorm(path)))

    def drive(self):
        """Returns the drive part of the path string."""
        return GPath(os.path.splitdrive(self._s)[0])

    #--File system info
    #--THESE REALLY OUGHT TO BE PROPERTIES.
    def exists(self):
        return os.path.exists(self._s)
    def isdir(self):
        return os.path.isdir(self._s)
    def isfile(self):
        return os.path.isfile(self._s)
    def isabs(self):
        return os.path.isabs(self._s)

    #--File system manipulation
    @staticmethod
    def _onerror(func,path,exc_info):
        """shutil error handler: remove RO flag"""
        if not os.access(path,os.W_OK):
            os.chmod(path,stat.S_IWUSR|stat.S_IWOTH)
            func(path)
        else:
            raise

    def clearRO(self):
        """Clears RO flag on self"""
        if not self.isdir():
            os.chmod(self._s,stat.S_IWUSR|stat.S_IWOTH)
        else:
            try:
                clearReadOnly(self)
            except UnicodeError:
                stat_flags = stat.S_IWUSR|stat.S_IWOTH
                chmod = os.chmod
                for root_dir,dirs,files in _walk(self._s):
                    rootJoin = root_dir.join
                    for directory in dirs:
                        try: chmod(rootJoin(directory),stat_flags)
                        except: pass
                    for filename in files:
                        try: chmod(rootJoin(filename),stat_flags)
                        except: pass

    def open(self,*args,**kwdargs): # PY3: drop - open() accepts encoding now
        if self.shead and not os.path.exists(self.shead):
            os.makedirs(self.shead)
        if u'encoding' in kwdargs:
            return codecs.open(self._s,*args,**kwdargs)
        else:
            return open(self._s,*args,**kwdargs)
    def makedirs(self):
        try:
            os.makedirs(self._s)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
    def remove(self):
        try:
            if self.exists(): os.remove(self._s)
        except OSError:
            self.clearRO()
            os.remove(self._s)
    def removedirs(self):
        try:
            if self.exists(): os.removedirs(self._s)
        except OSError:
            self.clearRO()
            os.removedirs(self._s)
    def rmtree(self,safety=u'PART OF DIRECTORY NAME'):
        """Removes directory tree. As a safety factor, a part of the directory name must be supplied."""
        if self.isdir() and safety and safety.lower() in self._cs:
            shutil.rmtree(self._s,onerror=Path._onerror)

    #--start, move, copy, touch, untemp
    def start(self, exeArgs=None):
        """Starts file as if it had been doubleclicked in file explorer."""
        if self.cext == u'.exe':
            if not exeArgs:
                subprocess.Popen([self._s], close_fds=True)
            else:
                subprocess.Popen(exeArgs, executable=self._s, close_fds=True)
        else:
            os.startfile(self._s)
    def copyTo(self,destName):
        """Copy self to destName, make dirs if necessary and preserve mtime."""
        destName = GPath(destName)
        if self.isdir():
            shutil.copytree(self._s,destName._s)
        else:
            if destName.shead and not os.path.exists(destName.shead):
                os.makedirs(destName.shead)
            shutil.copyfile(self._s,destName._s)
            destName.mtime = self.mtime
    def moveTo(self,destName):
        if not self.exists():
            raise exception.StateError(self._s + u' cannot be moved because it does not exist.')
        destPath = GPath(destName)
        if destPath._cs == self._cs: return
        if destPath.shead and not os.path.exists(destPath.shead):
            os.makedirs(destPath.shead)
        elif destPath.exists():
            destPath.remove()
        try:
            shutil.move(self._s,destPath._s)
        except OSError:
            self.clearRO()
            shutil.move(self._s,destPath._s)

    def tempMoveTo(self,destName):
        """Temporarily rename/move an object.  Use with the 'with' statement"""
        class _temp_file(object):
            def __init__(self,oldPath,newPath):
                self.newPath = GPath(newPath)
                self.oldPath = GPath(oldPath)

            def __enter__(self): return self.newPath
            def __exit__(self, exc_type, exc_value, exc_traceback): self.newPath.moveTo(self.oldPath)
        self.moveTo(destName)
        return _temp_file(self,destName)

    def unicodeSafe(self): # PY3: investigate if obsoleted.
        """Temporarily rename (only if necessary) the file to a unicode safe
        name. Use with the 'with' statement. Meant to be used with Popen (which
        automatically tries to encode the name)."""
        try:
            self._s.encode(u'ascii')
            class _noop_file(object):
                def __init__(self, _fpath):
                    self._fpath = _fpath
                def __enter__(self): return self._fpath
                def __exit__(self, exc_type, exc_value, exc_traceback): pass
            return _noop_file(self)
        except UnicodeEncodeError:
            safe_path = unicode(self._s.encode(u'ascii', u'xmlcharrefreplace'),
                u'ascii') + u'_unicode_safe.tmp'
            return self.tempMoveTo(safe_path)

    def untemp(self,doBackup=False):
        """Replaces file with temp version, optionally making backup of file first."""
        if self.temp.exists():
            if self.exists():
                if doBackup:
                    self.backup.remove()
                    shutil.move(self._s, self.backup._s)
                else:
                    # this will fail with Access Denied (!) if self._s is
                    # (unexpectedly) a directory
                    try:
                        os.remove(self._s)
                    except OSError as e:
                        if e.errno != errno.EACCES:
                            raise
                        self.clearRO()
                        os.remove(self._s)
            shutil.move(self.temp._s, self._s)

    def editable(self):
        """Safely check whether a file is editable."""
        delete = not os.path.exists(self._s)
        try:
            with open(self._s,u'ab'):
                return True
        except:
            return False
        finally:
            # If the file didn't exist before, remove the created version
            if delete:
                try:
                    os.remove(self._s)
                except:
                    pass

    #--Hash/Compare, based on the _cs attribute so case insensitive. NB: Paths
    # directly compare to unicode|bytes|Path|None and will blow for anything
    # else
    def __hash__(self):
        return hash(self._cs)
    def __eq__(self, other):
        if isinstance(other, Path):
            return self._cs == other._cs
        # get unicode or None - will blow on most other types - identical below
        dec = other if isinstance(other, unicode) else decoder(other)
        return self._cs == (os.path.normcase(os.path.normpath(dec)) if dec
            else dec)
    def __ne__(self, other):
        if isinstance(other, Path):
            return self._cs != other._cs
        dec = other if isinstance(other, unicode) else decoder(other)
        return self._cs != (os.path.normcase(os.path.normpath(dec)) if dec
            else dec)
    def __lt__(self, other):
        if isinstance(other, Path):
            return self._cs < other._cs
        dec = other if isinstance(other, unicode) else decoder(other)
        return self._cs < (os.path.normcase(os.path.normpath(dec)) if dec
            else dec)
    def __ge__(self, other):
        if isinstance(other, Path):
            return self._cs >= other._cs
        dec = other if isinstance(other, unicode) else decoder(other)
        return self._cs >= (os.path.normcase(os.path.normpath(dec)) if dec
            else dec)
    def __gt__(self, other):
        if isinstance(other, Path):
            return self._cs > other._cs
        dec = other if isinstance(other, unicode) else decoder(other)
        return self._cs > (os.path.normcase(os.path.normpath(dec)) if dec
            else dec)
    def __le__(self, other):
        if isinstance(other, Path):
            return self._cs <= other._cs
        dec = other if isinstance(other, unicode) else decoder(other)
        return self._cs <= (os.path.normcase(os.path.normpath(dec)) if dec
            else dec)

def clearReadOnly(dirPath):
    """Recursively (/S) clear ReadOnly flag if set - include folders (/D)."""
    cmd = u'' r'attrib -R "%s\*" /S /D' % dirPath
    subprocess.call(cmd, startupinfo=startupinfo)

# TMP functions to deprecate Paths functionality for simple filenames - SLOW!
def cext_(string_val):
    return os.path.splitext(string_val)[-1].lower()
def body_(string_val):
    return os.path.basename(os.path.splitext(string_val)[0])

# Util Constants --------------------------------------------------------------
#--Unix new lines
reUnixNewLine = re.compile(u'' r'(?<!\r)\n', re.U)

# Util Classes ----------------------------------------------------------------
#------------------------------------------------------------------------------
class CsvReader(object):
    """For reading csv files. Handles comma, semicolon and tab separated (excel) formats.
       CSV files must be encoded in UTF-8"""
    @staticmethod
    def utf_8_encoder(unicode_csv_data):
        for line in unicode_csv_data:
            yield line.encode(u'utf8')

    def __init__(self,path): ##: Py3 Revisit - is Csv reader still bytes?  get rid of BOM?
        self.ins = GPath(path).open(u'r', encoding=u'utf-8-sig')
        first_line = self.ins.readline()
        excel_fmt = b'excel-tab' if u'\t' in first_line else b'excel'
        self.ins.seek(0)
        if excel_fmt == b'excel':
            # TypeError: "delimiter" must be string, not unicode
            delimiter = b';' if b';' in first_line else b','
            self.reader = csv.reader(CsvReader.utf_8_encoder(self.ins),
                                     excel_fmt, delimiter=delimiter)
        else:
            self.reader = csv.reader(CsvReader.utf_8_encoder(self.ins),
                                     excel_fmt)

    def __enter__(self): return self
    def __exit__(self, exc_type, exc_value, exc_traceback): self.ins.close()

    def __iter__(self):
        for row in self.reader:
            yield [unicode(x, u'utf8') for x in row]

    def close(self):
        self.reader = None
        self.ins.close()

#------------------------------------------------------------------------------
class Flags(object):
    """Represents a flag field."""
    __slots__ = [u'_names', u'_field', u'_unknown_is_unused']

    @staticmethod
    def getNames(*names):
        """Returns dictionary mapping names to indices.
        Indices range may not be contiguous.
        Names are either strings or (index,name) tuples.
        E.g., Flags.getNames('isQuest','isHidden',None,(4,'isDark'),(7,'hasWater'))"""
        namesDict = {}
        for index,flg_name in enumerate(names):
            if isinstance(flg_name,tuple):
                namesDict[flg_name[1]] = flg_name[0]
            elif flg_name: #--skip if "name" is 0 or None
                namesDict[flg_name] = index
        return namesDict

    #--Generation
    def __init__(self, value=0, names=None, unknown_is_unused=False):
        """Initialize. Attrs, if present, is mapping of attribute names to
        indices. unknown_is_unused will discard unknown flags."""
        object.__setattr__(self, u'_names', names or {})
        object.__setattr__(self, u'_field', int(value))
        object.__setattr__(self, u'_unknown_is_unused', unknown_is_unused)
        self._clean_unused_flags()

    def __call__(self,newValue=None):
        """Returns a clone of self, optionally with new value."""
        if newValue is not None:
            return Flags(int(newValue), self._names, self._unknown_is_unused)
        else:
            return Flags(self._field, self._names, self._unknown_is_unused)

    def __deepcopy__(self, memo):
        newFlags = Flags(self._field, self._names, self._unknown_is_unused)
        memo[id(self)] = newFlags ##: huh?
        return newFlags

    def _clean_unused_flags(self):
        """Removes all unknown flags if that option was set in __init__."""
        if self._unknown_is_unused:
            final_flags = 0
            for flg_name, flg_idx in self._names.iteritems():
                if getattr(self, flg_name):
                    final_flags |= 1 << flg_idx
            self._field = final_flags

    #--As hex string
    def hex(self):
        """Returns hex string of value."""
        return u'%08X' % (self._field,)
    def dump(self):
        """Returns value for packing"""
        self._clean_unused_flags()
        return self._field

    #--As int
    def __int__(self):
        """Return as integer value for saving."""
        return self._field
    def __index__(self):
        """Same as __int__, needed for packing in py3."""
        return self._field
    def __getstate__(self): ##: do we even use this?
        """Return values for pickling."""
        return self._field, self._names
    def __setstate__(self,fields):
        """Used by unpickler."""
        self._field = fields[0]
        self._names = fields[1]

    #--As list
    def __getitem__(self, index):
        """Get value by index. E.g., flags[3]"""
        return bool((self._field >> index) & 1)

    def __setitem__(self,index,value):
        """Set value by index. E.g., flags[3] = True"""
        value = ((value or 0) and 1) << index
        mask = 1 << index
        self._field = ((self._field & ~mask) | value)

    #--As class
    def __getattr__(self, attr_key):
        """Get value by flag name. E.g. flags.isQuestItem"""
        try:
            names = object.__getattribute__(self, u'_names')
            index = names[attr_key]
            return (object.__getattribute__(self, u'_field') >> index) & 1 == 1
        except KeyError:
            raise AttributeError(attr_key)

    def __setattr__(self, attr_key, value):
        """Set value by flag name. E.g., flags.isQuestItem = False"""
        if attr_key in (u'_field', u'_names'):
            object.__setattr__(self, attr_key, value)
        else:
            self.__setitem__(self._names[attr_key], value)

    #--Native operations
    def __eq__( self, other):
        """Logical equals."""
        if isinstance(other,Flags):
            return self._field == other._field
        else:
            return self._field == other

    def __ne__( self, other):
        """Logical not equals."""
        if isinstance(other,Flags):
            return self._field != other._field
        else:
            return self._field != other

    def __and__(self,other):
        """Bitwise and."""
        if isinstance(other,Flags): other = other._field
        return self(self._field & other)

    def __invert__(self):
        """Bitwise inversion."""
        return self(~self._field)

    def __or__(self,other):
        """Bitwise or."""
        if isinstance(other,Flags): other = other._field
        return self(self._field | other)

    def __xor__(self,other):
        """Bitwise exclusive or."""
        if isinstance(other,Flags): other = other._field
        return self(self._field ^ other)

    def getTrueAttrs(self):
        """Returns attributes that are true."""
        trueNames = [flname for flname in self._names if getattr(self, flname)]
        trueNames.sort(key=lambda xxx: self._names[xxx])
        return tuple(trueNames)

    def __repr__(self):
        """Shows all set flags."""
        all_flags = u', '.join(self.getTrueAttrs()) if self._field else u'None'
        return u'0x%s (%s)' % (self.hex(), all_flags)

#------------------------------------------------------------------------------
class DataDict(object):
    """Mixin class that handles dictionary emulation, assuming that
    dictionary is its 'data' attribute."""

    def __contains__(self,key):
        return key in self._data
    def __getitem__(self,key):
        """Return value for key or raise KeyError if not present."""
        return self._data[key]
    def __setitem__(self,key,value):
        self._data[key] = value
    def __delitem__(self,key):
        del self._data[key]
    def __len__(self):
        return len(self._data)
    def __iter__(self):
        return iter(self._data)
    def values(self):
        return self._data.values()
    def items(self):
        return self._data.items()
    def get(self,key,default=None):
        return self._data.get(key, default)
    def pop(self,key,default=None):
        return self._data.pop(key, default)
    def iteritems(self):
        return self._data.iteritems()
    def itervalues(self):
        return self._data.itervalues()

#------------------------------------------------------------------------------
class AFile(object):
    """Abstract file, supports caching - beta."""
    _null_stat = (-1, None)
    __slots__ = (u'_file_key', u'_file_size', u'_file_mod_time')

    def _stat_tuple(self): return self.abs_path.size_mtime()

    def __init__(self, fullpath, load_cache=False, raise_on_error=False):
        self._file_key = GPath(fullpath) # abs path of the file but see ModInfo
        #Set cache info (mtime, size[, ctime]) and reload if load_cache is True
        try:
            self._reset_cache(self._stat_tuple(), load_cache)
        except (OSError, IOError):
            if raise_on_error: raise
            self._reset_cache(self._null_stat, load_cache=False)

    @property
    def abs_path(self): return self._file_key

    @abs_path.setter
    def abs_path(self, val): self._file_key = val

    def do_update(self, raise_on_error=False):
        """Check cache, reset it if needed. Return True if reset else False.
        If the stat call fails and this instance was previously stat'ed we
        consider the file deleted and return True except if raise_on_error is
        True, whereupon raise the OSError we got in stat(). If raise_on_error
        is False user must check if file exists."""
        try:
            stat_tuple = self._stat_tuple()
        except (OSError, IOError): # PY3: FileNotFoundError case?
            file_was_stated = self._file_changed(self._null_stat)
            self._reset_cache(self._null_stat, load_cache=False)
            if raise_on_error: raise
            return file_was_stated # file previously existed, we need to update
        if self._file_changed(stat_tuple):
            self._reset_cache(stat_tuple, load_cache=True)
            return True
        return False

    def needs_update(self):
        """Returns True if this file changed. Throws an OSErorr if it is
        deleted."""
        return self._file_changed(self._stat_tuple())

    def _file_changed(self, stat_tuple):
        return (self._file_size, self._file_mod_time) != stat_tuple

    def _reset_cache(self, stat_tuple, load_cache):
        """Reset cache flags (size, mtime,...) and possibly reload the cache.
        :param load_cache: if True either load the cache (header in Mod and
        SaveInfo) or reset it so it gets reloaded later
        """
        self._file_size, self._file_mod_time = stat_tuple

    def __repr__(self): return u'%s<%s>' % (self.__class__.__name__,
                                            self.abs_path.stail)

#------------------------------------------------------------------------------
class MainFunctions(object):
    """Encapsulates a set of functions and/or object instances so that they can
    be called from the command line with normal command line syntax.

    Functions are called with their arguments. Object instances are called
    with their method and method arguments. E.g.:
    * bish bar arg1 arg2 arg3
    * bish foo.bar arg1 arg2 arg3"""

    def __init__(self):
        """Initialization."""
        self.funcs = {}

    def add(self, func, func_key=None):
        """Add a callable object.
        func - A function or class instance.
        func_key - Command line invocation for object (defaults to name of
        func).
        """
        func_key = func_key or func.__name__
        self.funcs[func_key] = func
        return func

    def main(self):
        """Main function. Call this in __main__ handler."""
        #--Get func
        args = sys.argv[1:]
        attrs = args.pop(0).split(u'.')
        func_key = attrs.pop(0)
        func = self.funcs.get(func_key)
        if not func:
            msg = _(u'Unknown function/object: %s') % func_key
            try: print(msg)
            except UnicodeError: print(msg.encode(u'mbcs'))
            return
        for attr in attrs:
            func = getattr(func,attr)
        #--Separate out keywords args
        keywords = {}
        argDex = 0
        reKeyArg  = re.compile(u'' r'^-(\D\w+)', re.U)
        reKeyBool = re.compile(u'' r'^\+(\D\w+)', re.U)
        while argDex < len(args):
            arg = args[argDex]
            if reKeyArg.match(arg):
                keyword = reKeyArg.match(arg).group(1)
                value   = args[argDex+1]
                keywords[keyword] = value
                del args[argDex:argDex+2]
            elif reKeyBool.match(arg):
                keyword = reKeyBool.match(arg).group(1)
                keywords[keyword] = True
                del args[argDex]
            else:
                argDex += 1
        #--Apply
        func(*args, **keywords)

#--Commands Singleton
_mainFunctions = MainFunctions()
def mainfunc(func):
    """A function for adding funcs to _mainFunctions.
    Used as a function decorator ("@mainfunc")."""
    _mainFunctions.add(func)
    return func

#------------------------------------------------------------------------------
class PickleDict(object):
    """Dictionary saved in a pickle file.
    Note: self.vdata and self.data are not reassigned! (Useful for some clients.)"""
    def __init__(self, pkl_path, readOnly=False):
        """Initialize."""
        self._pkl_path = pkl_path
        self.backup = pkl_path.backup
        self.readOnly = readOnly
        self.vdata = {}
        self.pickled_data = {}

    def exists(self):
        return self._pkl_path.exists() or self.backup.exists()

    class Mold(Exception):
        def __init__(self, moldedFile):
            msg = (u'Your settings in %s come from an ancient Bash version. '
                   u'Please load them in 306 so they are converted '
                   u'to the newer format' % moldedFile)
            super(PickleDict.Mold, self).__init__(msg)

    def load(self):
        """Loads vdata and data from file or backup file.

        If file does not exist, or is corrupt, then reads from backup file. If
        backup file also does not exist or is corrupt, then no data is read. If
        no data is read, then self.data is cleared.

        If file exists and has a vdata header, then that will be recorded in
        self.vdata. Otherwise, self.vdata will be empty.

        Returns:
          0: No data read (files don't exist and/or are corrupt)
          1: Data read from file
          2: Data read from backup file
        """
        self.vdata.clear()
        self.pickled_data.clear()
        cor = cor_name =  None
        for path in (self._pkl_path, self.backup):
            if cor is not None:
                cor.moveTo(cor_name)
                cor = None
            try:
                with path.open(u'rb') as ins:
                    try:
                        firstPickle = pickle.load(ins)
                    except ValueError:
                        cor = path
                        cor_name = GPath(
                            u'%s (%s).corrupted' % (path, timestamp()))
                        deprint(u'Unable to load %s (will be moved to "%s")' %(
                                path, cor_name.tail), traceback=True)
                        continue  # file corrupt - try next file
                    if firstPickle == b'VDATA2':
                        self.vdata.update(pickle.load(ins))
                        self.pickled_data.update(pickle.load(ins))
                    else:
                        raise PickleDict.Mold(path)
                return 1 + (path == self.backup)
            except (OSError, IOError, EOFError, ValueError,
                    pickle.UnpicklingError): #PY3:FileNotFound
                pass
        else:
            if cor is not None:
                cor.moveTo(cor_name)
        #--No files and/or files are corrupt
        return 0

    def save(self):
        """Save to pickle file.

        Three objects are writen - a version string and the vdata and
        pickled_data dictionaries, in this order. Current version string is
        VDATA2."""
        if self.readOnly: return False
        #--Pickle it
        with self._pkl_path.temp.open(u'wb') as out:
            for pkl in (b'VDATA2', self.vdata, self.pickled_data):
                pickle.dump(pkl, out, -1)
        self._pkl_path.untemp(doBackup=True)
        return True

#------------------------------------------------------------------------------
class Settings(DataDict):
    """Settings/configuration dictionary with persistent storage.

    Default setting for configurations are either set in bulk (by the
    loadDefaults function) or are set as needed in the code (e.g., various
    auto-continue settings for bash. Only settings that have been changed from
    the default values are saved in persistent storage.

    Directly setting a value in the dictionary will mark it as changed (and thus
    to be archived). However, an indirect change (e.g., to a value that is a
    list) must be manually marked as changed by using the setChanged method."""

    def __init__(self, dictFile):
        """Initialize. Read settings from dictFile."""
        self.dictFile = dictFile
        self.cleanSave = False
        if self.dictFile:
            res = dictFile.load()
            self.cleanSave = res == 0 # no data read - do not attempt to read on save
            self.vdata = dictFile.vdata.copy()
            self._data = dictFile.pickled_data.copy()
        else:
            self.vdata = {}
            self._data = {}
        self.defaults = {}
        self.changed = set()
        self.deleted = set()

    def loadDefaults(self, default_settings):
        """Add default settings to dictionary. Will not replace values that are already set."""
        self.defaults = default_settings
        for key in default_settings: # PY3: ChainMap?
            if key not in self:
                self[key] = copy.deepcopy(default_settings[key])

    def save(self):
        """Save to pickle file. Only key/values marked as changed are saved."""
        dictFile = self.dictFile
        if not dictFile or dictFile.readOnly: return
        # on a clean save ignore BashSettings.dat.bak possibly corrupt
        if not self.cleanSave: dictFile.load()
        dictFile.vdata = self.vdata.copy()
        for del_key in self.deleted:
            dictFile.pickled_data.pop(del_key, None)
        for changed_key in self.changed:
            if self[changed_key] == self.defaults.get(changed_key, None):
                dictFile.pickled_data.pop(changed_key, None)
            else:
                dictFile.pickled_data[changed_key] = self[changed_key]
        dictFile.save()

    def setChanged(self,key):
        """Marks given key as having been changed. Use if value is a dictionary, list or other object."""
        if key not in self:
            raise exception.ArgumentError(u'No settings data for ' + key)
        self.changed.add(key)

    def getChanged(self,key,default=None):
        """Gets and marks as changed."""
        if default is not None and key not in self:
            self[key] = default
        self.setChanged(key)
        return self.get(key)

    #--Dictionary Emulation
    def __setitem__(self,key,value):
        """Dictionary emulation. Marks key as changed."""
        if key in self.deleted: self.deleted.remove(key)
        self.changed.add(key)
        self._data[key] = value

    def __delitem__(self,key):
        """Dictionary emulation. Marks key as deleted."""
        if key in self.changed: self.changed.remove(key)
        self.deleted.add(key)
        del self._data[key]

    def pop(self,key,default=None):
        """Dictionary emulation: extract value and delete from dictionary."""
        if key in self.changed: self.changed.remove(key)
        self.deleted.add(key)
        return self._data.pop(key, default)

# Structure wrappers ----------------------------------------------------------
class _StructsCache(dict):
    __slots__ = ()
    def __missing__(self, key):
        return self.setdefault(key, struct.Struct(key))

structs_cache = _StructsCache()
def unpack_str16(ins, __unpack=structs_cache[u'H'].unpack):
    return ins.read(__unpack(ins.read(2))[0])
def unpack_str32(ins, __unpack=structs_cache[u'I'].unpack):
    return ins.read(__unpack(ins.read(4))[0])
def unpack_int(ins, __unpack=structs_cache[u'I'].unpack):
    return __unpack(ins.read(4))[0]
def pack_int(out, value, __pack=structs_cache[u'=I'].pack):
    out.write(__pack(value))
def unpack_short(ins, __unpack=structs_cache[u'H'].unpack):
    return __unpack(ins.read(2))[0]
def pack_short(out, val, __pack=structs_cache[u'=H'].pack):
    out.write(__pack(val))
def unpack_float(ins, __unpack=structs_cache[u'f'].unpack):
    return __unpack(ins.read(4))[0]
def pack_float(out, val, __pack=structs_cache[u'=f'].pack):
    out.write(__pack(val))
def unpack_double(ins, __unpack=structs_cache[u'd'].unpack):
    return __unpack(ins.read(8))[0]
def pack_double(out, val, __pack=structs_cache[u'=d'].pack):
    out.write(__pack(val))
def unpack_byte(ins, __unpack=structs_cache[u'B'].unpack):
    return __unpack(ins.read(1))[0]
def pack_byte(out, val, __pack=structs_cache[u'=B'].pack):
    out.write(__pack(val))
def unpack_int_signed(ins, __unpack=structs_cache[u'i'].unpack):
    return __unpack(ins.read(4))[0]
def pack_int_signed(out, val, __pack=structs_cache[u'=i'].pack):
    out.write(__pack(val))
def unpack_int64_signed(ins, __unpack=structs_cache[u'q'].unpack):
    return __unpack(ins.read(8))[0]
def unpack_4s(ins, __unpack=structs_cache[u'4s'].unpack):
    return __unpack(ins.read(4))[0]
def pack_4s(out, val, __pack=structs_cache[u'=4s'].pack):
    out.write(__pack(val))
def unpack_str16_delim(ins, __unpack=structs_cache[u'Hc'].unpack):
    str_len = __unpack(ins.read(3))[0]
    # The actual string (including terminator) isn't stored for empty strings
    if not str_len: return b''
    str_value = ins.read(str_len)
    ins.seek(1, 1) # discard string terminator
    return str_value
def unpack_str_int_delim(ins, __unpack=structs_cache[u'Ic'].unpack):
    return __unpack(ins.read(5))[0]
def unpack_str_byte_delim(ins, __unpack=structs_cache[u'Bc'].unpack):
    return __unpack(ins.read(2))[0]
def unpack_str8(ins, __unpack=structs_cache[u'B'].unpack):
    return ins.read(__unpack(ins.read(1))[0])
def pack_str8(out, val, __pack=structs_cache[u'=B'].pack):
    pack_byte(out, len(val))
    out.write(val)
def pack_bzstr8(out, val, __pack=structs_cache[u'=B'].pack):
    pack_byte(out, len(val) + 1)
    out.write(val)
    out.write(b'\x00')
def unpack_string(ins, string_len):
    return struct_unpack(u'%ds' % string_len, ins.read(string_len))[0]
def pack_string(out, val):
    out.write(val)

def pack_byte_signed(out, value, __pack=structs_cache[u'b'].pack):
    out.write(__pack(value))

def unpack_many(ins, fmt):
    return struct_unpack(fmt, ins.read(struct.calcsize(fmt)))

def unpack_spaced_string(ins, replacement_char=b'\x07'):
    """Unpacks a space-terminated string. Occurs if someone used
    std::stringstream to convert struct data into strings. Obviously that means
    a replacement character is needed for spaces, which is \x07 by default."""
    wip_string = []
    while True:
        next_char = ins.read(1)
        if next_char == b' ': break
        wip_string.append(b' ' if next_char == replacement_char else next_char)
    return b''.join(wip_string)

#------------------------------------------------------------------------------
class DataTableColumn(object):
    """DataTable accessor that presents table column as a dictionary."""
    def __init__(self, table, column):
        self._table = table # type: DataTable
        self.column = column
    #--Dictionary Emulation
    def __iter__(self):
        """Dictionary emulation."""
        column = self.column
        return (key for key, col_dict in self._table.iteritems() if
                column in col_dict)
    def items(self):
        """Dictionary emulation."""
        tableData = self._table._data
        column = self.column
        return [(key,tableData[key][column]) for key in self]
    def clear(self):
        """Dictionary emulation."""
        self._table.delColumn(self.column)
    def get(self,key,default=None):
        """Dictionary emulation."""
        return self._table.getItem(key, self.column, default)
    #--Overloaded
    def __contains__(self,key):
        """Dictionary emulation."""
        tableData = self._table._data
        return key in tableData and self.column in tableData[key]
    def __getitem__(self,key):
        """Dictionary emulation."""
        return self._table._data[key][self.column]
    def __setitem__(self,key,value):
        """Dictionary emulation. Marks key as changed."""
        self._table.setItem(key, self.column, value)
    def __delitem__(self,key):
        """Dictionary emulation. Marks key as deleted."""
        self._table.delItem(key, self.column)

#------------------------------------------------------------------------------
class DataTable(DataDict):
    """Simple data table of rows and columns, saved in a pickle file. It is
    currently used by TableFileInfos to represent properties associated with
    mod/save/bsa/ini files, where each file is a row, and each property (e.g.
    modified date or 'mtime') is a column.

    The "table" is actually a dictionary of dictionaries. E.g.
        propValue = table['fileName']['propName']
    Rows are the first index ('fileName') and columns are the second index
    ('propName')."""

    def __init__(self,dictFile):
        """Initialize and read data from dictFile, if available."""
        self.dictFile = dictFile
        dictFile.load()
        self.vdata = dictFile.vdata
        self._data = dictFile.pickled_data
        self.hasChanged = False ##: move to PickleDict

    def save(self):
        """Saves to pickle file."""
        dictFile = self.dictFile
        if self.hasChanged and not dictFile.readOnly:
            self.hasChanged = not dictFile.save()

    def getItem(self,row,column,default=None):
        """Get item from row, column. Return default if row,column doesn't exist."""
        if row in self._data and column in self._data[row]:
            return self._data[row][column]
        else:
            return default

    def getColumn(self,column):
        """Returns a data accessor for column."""
        return DataTableColumn(self, column)

    def setItem(self,row,column,value):
        """Set value for row, column."""
        if row not in self._data:
            self._data[row] = {}
        self._data[row][column] = value
        self.hasChanged = True

    def delItem(self,row,column):
        """Deletes item in row, column."""
        if row in self._data and column in self._data[row]:
            del self._data[row][column]
            self.hasChanged = True

    def delRow(self,row):
        """Deletes row."""
        if row in self._data:
            del self._data[row]
            self.hasChanged = True

    def delColumn(self,column):
        """Deletes column of data."""
        for rowData in self._data.values():
            if column in rowData:
                del rowData[column]
                self.hasChanged = True

    def moveRow(self,oldRow,newRow):
        """Renames a row of data."""
        if oldRow in self._data:
            self._data[newRow] = self._data[oldRow]
            del self._data[oldRow]
            self.hasChanged = True

    def copyRow(self,oldRow,newRow):
        """Copies a row of data."""
        if oldRow in self._data:
            self._data[newRow] = self._data[oldRow].copy()
            self.hasChanged = True

    #--Dictionary emulation
    def __setitem__(self,key,value):
        self._data[key] = value
        self.hasChanged = True
    def __delitem__(self,key):
        del self._data[key]
        self.hasChanged = True
    def pop(self,key,default=None):
        self.hasChanged = True
        return self._data.pop(key, default)

# Util Functions --------------------------------------------------------------
#------------------------------------------------------------------------------
def cmp_(x, y):
    """Compares x and y. For backwards compatibility since py3 drops cmp."""
    # TODO(lojack): Hunt down and rewrite any usages of this
    return (x > y) - (x < y)

def isclose_(a, b, rel_tol=1e-09, abs_tol=0.0):
    """Inexact float comparison. PY3: drop in favor of math.isclose."""
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

def floats_equal(a, b):
    """Checks if the two floats are equal to the sixth place (relatively) or to
    the twelfth place (absolutely). Used for inexact comparisons in tweaks,
    etc. Note that these parameters were picked fairly arbitrarily, so feel
    free to tweak them if they turn out to be a problem."""
    return isclose_(a, b, rel_tol=1e-06, abs_tol=1e-12)

def copyattrs(source,dest,attrs):
    """Copies specified attrbutes from source object to dest object."""
    for attr in attrs:
        setattr(dest,attr,getattr(source,attr))

def cstrip(inString): # TODO(ut): hunt down and deprecate - it's O(n)+
    """Convert c-string (null-terminated string) to python string."""
    zeroDex = inString.find(b'\x00')
    if zeroDex == -1:
        return inString
    else:
        return inString[:zeroDex]

def text_wrap(text_to_wrap, width=60):
    """Wraps paragraph to width characters."""
    pars = [textwrap.fill(line, width) for line in text_to_wrap.split(u'\n')]
    return u'\n'.join(pars)

_formats = dict.fromkeys(u'bBhHiIlLqQ', u'%d')
_formats.update({u'f': u'%f', u'd': u'%f', u's': u'"%s"'})
def csvFormat(format_chars, __formats=_formats):
    """Returns csv format for specified structure format."""
    return u','.join([__formats[c] for c in format_chars])

deprintOn = False

import inspect
def deprint(*args,**keyargs):
    """Prints message along with file and line location."""
    if not deprintOn and not keyargs.get(u'on'): return
    if keyargs.get(u'trace', True):
        stack = inspect.stack()
        file_, line, function = stack[1][1:4]
        msg = u'%s %4d %s: ' % (GPath(file_).tail, line, function)
    else:
        msg = u''
    try:
        msg += u' '.join([u'%s'%x for x in args]) # OK, even with unicode args
    except UnicodeError:
        # If the args failed to convert to unicode for some reason
        # we still want the message displayed any way we can
        for x in args:
            try:
                msg += u' %s' % x
            except UnicodeError:
                msg += u' %r' % x
    if keyargs.get(u'traceback',False):
        exc_fmt = traceback.format_exc()
        # PY3: This should be good to go
        if isinstance(exc_fmt, bytes):
            try:
                msg += u'\n%s' % unicode(exc_fmt, u'utf-8')
            except UnicodeError:
                traceback.print_exc()
                msg += u'\n%r' % exc_fmt
        else:
            msg += u'\n%s' % exc_fmt
    try:
        # Should work if stdout/stderr is going to wxPython output
        print(msg)
    except UnicodeError:
        # Nope, it's going somewhere else
        print(msg.encode(Path.sys_fs_enc))

def getMatch(reMatch,group=0):
    """Returns the match or an empty string."""
    if reMatch: return reMatch.group(group)
    else: return u''

def intArg(arg,default=None):
    """Returns argument as an integer. If argument is a string, then it converts it using int(arg,0)."""
    if arg is None: return default
    elif isinstance(arg, (unicode, bytes)): ##: this smells, hunt down
        return int(arg, 0)
    else: return int(arg)

def winNewLines(inString):
    """Converts unix newlines to windows newlines."""
    return reUnixNewLine.sub(u'\r\n',inString)

# Log/Progress ----------------------------------------------------------------
#------------------------------------------------------------------------------
class Log(object):
    """Log Callable. This is the abstract/null version. Useful version should
    override write functions.

    Log is divided into sections with headers. Header text is assigned (through
    setHeader), but isn't written until a message is written under it. I.e.,
    if no message are written under a given header, then the header itself is
    never written."""

    def __init__(self):
        """Initialize."""
        self.header = None
        self.prevHeader = None

    def setHeader(self,header,writeNow=False,doFooter=True):
        """Sets the header."""
        self.header = header
        if self.prevHeader:
            self.prevHeader += u'x'
        self.doFooter = doFooter
        if writeNow: self()

    def __call__(self,message=None,appendNewline=True):
        """Callable. Writes message, and if necessary, header and footer."""
        if self.header != self.prevHeader:
            if self.prevHeader and self.doFooter:
                self.writeFooter()
            if self.header:
                self.writeLogHeader(self.header)
            self.prevHeader = self.header
        if message: self.writeMessage(message,appendNewline)

    #--Abstract/null writing functions...
    def writeLogHeader(self, header):
        """Write header. Abstract/null version."""
        pass
    def writeFooter(self):
        """Write mess. Abstract/null version."""
        pass
    def writeMessage(self,message,appendNewline):
        """Write message to log. Abstract/null version."""
        pass

#------------------------------------------------------------------------------
class LogFile(Log):
    """Log that writes messages to file."""
    def __init__(self,out):
        self.out = out
        Log.__init__(self)

    def writeLogHeader(self, header):
        self.out.write(header+u'\n')

    def writeFooter(self):
        self.out.write(u'\n')

    def writeMessage(self,message,appendNewline):
        self.out.write(message)
        if appendNewline: self.out.write(u'\n')

#------------------------------------------------------------------------------
class Progress(object):
    """Progress Callable: Shows progress when called."""
    def __init__(self,full=1.0):
        if (1.0*full) == 0: raise exception.ArgumentError(u'Full must be non-zero!')
        self.message = u''
        self.full = 1.0 * full
        self.state = 0
        self.debug = False

    def getParent(self):
        return None

    def setFull(self,full):
        """Set's full and for convenience, returns self."""
        if (1.0*full) == 0: raise exception.ArgumentError(u'Full must be non-zero!')
        self.full = 1.0 * full
        return self

    def plus(self,increment=1):
        """Increments progress by 1."""
        self.__call__(self.state+increment)

    def __call__(self,state,message=u''):
        """Update progress with current state. Progress is state/full."""
        if (1.0*self.full) == 0: raise exception.ArgumentError(u'Full must be non-zero!')
        if message: self.message = message
        if self.debug: deprint(u'%0.3f %s' % (1.0*state/self.full, self.message))
        self._do_progress(1.0 * state / self.full, self.message)
        self.state = state

    def _do_progress(self, state, message):
        """Default _do_progress does nothing."""

    # __enter__ and __exit__ for use with the 'with' statement
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_value, exc_traceback): pass

#------------------------------------------------------------------------------
class SubProgress(Progress):
    """Sub progress goes from base to ceiling."""
    def __init__(self,parent,baseFrom=0.0,baseTo=u'+1',full=1.0,silent=False):
        """For creating a subprogress of another progress meter.
        progress: parent (base) progress meter
        baseFrom: Base progress when this progress == 0.
        baseTo: Base progress when this progress == full
          Usually a number. But string '+1' sets it to baseFrom + 1
        full: Full meter by this progress' scale."""
        Progress.__init__(self,full)
        if baseTo == u'+1': baseTo = baseFrom + 1
        if baseFrom < 0 or baseFrom >= baseTo:
            raise exception.ArgumentError(u'BaseFrom must be >= 0 and BaseTo must be > BaseFrom')
        self.parent = parent
        self.baseFrom = baseFrom
        self.scale = 1.0*(baseTo-baseFrom)
        self.silent = silent

    def __call__(self,state,message=u''):
        """Update progress with current state. Progress is state/full."""
        if self.silent: message = u''
        self.parent(self.baseFrom+self.scale*state/self.full,message)
        self.state = state

#------------------------------------------------------------------------------
def readCString(ins, file_path):
    """Read null terminated string, dropping the final null byte."""
    byte_list = []
    for b in iter(partial(ins.read, 1), b''):
        if b == b'\0': break
        byte_list.append(b)
    else:
        raise exception.FileError(file_path,
                                  u'Reached end of file while expecting null')
    return b''.join(byte_list)

class StringTable(dict):
    """For reading .STRINGS, .DLSTRINGS, .ILSTRINGS files."""
    encodings = {
        # Encoding to fall back to if UTF-8 fails, based on language
        # Default is 1252 (Western European), so only list languages
        # different than that
        u'russian': u'cp1251',
    }

    def load(self, modFilePath, lang=u'English', progress=Progress()):
        baseName = modFilePath.tail.body
        baseDir = modFilePath.head.join(u'Strings')
        files = (baseName + u'_' + lang + x for x in
                 (u'.STRINGS', u'.DLSTRINGS', u'.ILSTRINGS'))
        files = (baseDir.join(file) for file in files)
        self.clear()
        progress.setFull(3)
        for i,file in enumerate(files):
            progress(i)
            self.loadFile(file,SubProgress(progress,i,i+1))

    def loadFile(self, path, progress, lang=u'english'):
        formatted = path.cext != u'.strings'
        backupEncoding = self.encodings.get(lang.lower(), u'cp1252')
        try:
            with open(path.s, u'rb') as ins:
                insSeek = ins.seek
                insTell = ins.tell

                insSeek(0,os.SEEK_END)
                eof = insTell()
                insSeek(0)
                if eof < 8:
                    deprint(u"Warning: Strings file '%s' file size (%d) is "
                            u'less than 8 bytes.  8 bytes are the minimum '
                            u'required by the expected format, assuming the '
                            u'Strings file is empty.' % (path, eof))
                    return

                numIds,dataSize = unpack_many(ins, u'=2I')
                progress.setFull(max(numIds,1))
                stringsStart = 8 + (numIds*8)
                if stringsStart != eof-dataSize:
                    deprint(u"Warning: Strings file '%s' dataSize element "
                            u'(%d) results in a string start location of %d, '
                            u'but the expected location is %d'
                            % (path, dataSize, eof-dataSize, stringsStart))

                id_ = -1
                offset = -1
                for x in xrange(numIds):
                    try:
                        progress(x)
                        id_,offset = unpack_many(ins, u'=2I')
                        pos = insTell()
                        insSeek(stringsStart+offset)
                        if formatted:
                            value = unpack_str32(ins) # TODO(ut): unpack_str32_null
                            # seems needed, strings are null terminated
                            value = cstrip(value)
                        else:
                            value = readCString(ins, path) #drops the null byte
                        try:
                            value = unicode(value, u'utf-8')
                        except UnicodeDecodeError:
                            value = unicode(value,backupEncoding)
                        insSeek(pos)
                        self[id_] = value
                    except:
                        deprint(u'Error reading string file:')
                        deprint(u'id:', id_)
                        deprint(u'offset:', offset)
                        deprint(u'filePos:',  insTell())
                        raise
        except:
            deprint(u'Error loading string file:', path.stail, traceback=True)
            return

#------------------------------------------------------------------------------
_esub_component = re.compile(u'' r'\$(\d+)\(([^)]+)\)')
_rsub_component = re.compile(u'' r'\\(\d+)')
_plain_component = re.compile(u'' r'[^\\\$]+', re.U)

def build_esub(esub_str):
    """Builds an esub (enhanced substitution) callable and returns it. These
    expand normal re.sub syntax to allow the case of a match to be preserved,
    even while the letters change.

    The syntax looks like this:
        my_sub = build_sub('$1(s)tamina')
        print(re.sub(r'\b(f|F)atigue\b', my_sub, u'Fatigue'))
        # prints 'Stamina'

    The $1(s) part is what's important. The $2 identifies which regex group to
    target. The part in parentheses will be what the case of the group gets
    applied to."""
    # Callables we'll chain together at the end
    final_components = []
    i = 0
    while i < len(esub_str):
        esub_match = _esub_component.match(esub_str, i)
        if esub_match:
            # esub substitution - return the target string, with the case of
            # the wanted group's contents
            esub_group = int(esub_match.group(1))
            target_str = esub_match.group(2)
            def esub_impl(ma_obj, g=esub_group, s=target_str):
                wip_str = []
                wip_append = wip_str.append
                for t, o in izip(s, ma_obj.group(g)):
                    # Carry forward the target string, but keep the case
                    wip_append(t.upper() if o.isupper() else t.lower())
                # Add in the rest of the target string unchanged
                return u''.join(wip_str + list(s[len(wip_str):]))
            final_components.append(esub_impl)
            i = esub_match.end(0)
            continue # skip the other match attempts
        rsub_match = _rsub_component.match(esub_str, i)
        if rsub_match:
            # Regular substitution - return the wanted group's contents
            rsub_group = int(rsub_match.group(1))
            def rsub_impl(ma_obj, g=rsub_group):
                return ma_obj.group(g)
            final_components.append(rsub_impl)
            i = rsub_match.end(0)
            continue # skip the plain match attempt
        plain_match = _plain_component.match(esub_str, i)
        if plain_match:
            # Plain component, just return it unaltered (and make sure to
            # capture the value of group(0) so that plain_match can get GC'd)
            plain_contents = plain_match.group(0)
            final_components.append(lambda _ma_obj, p=plain_contents: p)
            i = plain_match.end(0)
            continue # skip the error check
        raise SyntaxError(u'Could not parse esub string %r' % esub_str)
    def final_impl(ma_obj):
        return u''.join(c(ma_obj) for c in final_components)
    return final_impl

#------------------------------------------------------------------------------
# no re.U, we want our record attrs to be ASCII
_valid_rpath_attr = re.compile(u'' r'^[^\d\W]\w*\Z')

class _ARP_Subpath(object):
    """Abstract base class for all subpaths of a larger record path."""
    __slots__ = (u'_subpath_attr', u'_next_subpath',)

    def __init__(self, sub_rpath, rest_rpath):
        # type: (unicode, unicode) -> None
        if not _valid_rpath_attr.match(sub_rpath):
            raise SyntaxError(u"'%s' is not a valid subpath. Your record path "
                              u'likely contains a typo.' % sub_rpath)
        elif iskeyword(sub_rpath):
            raise SyntaxError(u'Record path subpaths may not be Python '
                              u"keywords (was '%s')." % sub_rpath)
        self._subpath_attr = sub_rpath
        self._next_subpath = _parse_rpath(rest_rpath)

    # See RecPath for documentation of these methods
    def rp_eval(self, record):
        """:rtype: list"""
        raise exception.AbstractError(u'rp_eval not implemented')

    def rp_exists(self, record):
        """:rtype: bool"""
        raise exception.AbstractError(u'rp_exists not implemented')

    def rp_map(self, record, func):
        raise exception.AbstractError(u'rp_map not implemented')

class _RP_Subpath(_ARP_Subpath):
    """A simple, intermediate subpath. Simply forwards all calls to the next
    part of the record path."""
    def rp_eval(self, record):
        return self._next_subpath.rp_eval(getattr(record, self._subpath_attr))

    def rp_exists(self, record):
        try:
            return self._next_subpath.rp_exists(getattr(
                record, self._subpath_attr))
        except AttributeError:
            return False

    def rp_map(self, record, func):
        self._next_subpath.rp_map(getattr(record, self._subpath_attr), func)

    def __repr__(self):
        return u'%s.%r' % (self._subpath_attr, self._next_subpath)

class _RP_LeafSubpath(_ARP_Subpath):
    """The final part of a record path. This the part that actually gets and
    sets values."""
    def rp_eval(self, record):
        return [getattr(record, self._subpath_attr)]

    def rp_exists(self, record):
        return hasattr(record, self._subpath_attr)

    def rp_map(self, record, func):
        s_attr = self._subpath_attr
        setattr(record, s_attr, func(getattr(record, s_attr)))

    def __repr__(self):
        return self._subpath_attr

class _RP_IteratedSubpath(_ARP_Subpath):
    """An iterated part of a record path. A record path can't resolve to more
    than one value unless it involves at least one of these."""
    def __init__(self, sub_rpath, rest_rpath):
        if not rest_rpath: raise SyntaxError(u'A RecPath may not end with an '
                                             u'iterated subpath.')
        super(_RP_IteratedSubpath, self).__init__(sub_rpath, rest_rpath)

    def rp_eval(self, record):
        eval_next = self._next_subpath.rp_eval
        return chain.from_iterable(eval_next(iter_attr) for iter_attr
                                   in getattr(record, self._subpath_attr))

    def rp_exists(self, record):
        num_iterated = 0
        next_exists = self._next_subpath.rp_exists
        for iter_attr in getattr(record, self._subpath_attr):
            if not next_exists(iter_attr):
                return False # short-circuit
            num_iterated += 1
        return num_iterated > 0 # faster than bool()

    def rp_map(self, record, func):
        map_next = self._next_subpath.rp_map
        for iter_attr in getattr(record, self._subpath_attr):
            map_next(iter_attr, func)

    def __repr__(self):
        return u'%s[i].%r' % (self._subpath_attr, self._next_subpath)

class _RP_OptionalSubpath(_RP_Subpath):
    """An optional part of a record path. If it doesn't exist, mapping and
    evaluating will simply not continue past this part."""
    def __init__(self, sub_rpath, rest_rpath):
        if not rest_rpath: raise SyntaxError(u'A RecPath may not end with an '
                                             u'optional subpath.')
        super(_RP_OptionalSubpath, self).__init__(sub_rpath, rest_rpath)

    def rp_eval(self, record):
        try:
            return super(_RP_OptionalSubpath, self).rp_eval(record)
        except AttributeError:
            return [] # Attribute did not exist, rest of the path evals to []

    def rp_map(self, record, func):
        try:
            super(_RP_OptionalSubpath, self).rp_map(record, func)
        except AttributeError:
            pass # Attribute did not exist, can't map any further

    def __repr__(self):
        return u'%s?.%r' % (self._subpath_attr, self._next_subpath)

class RecPath(object):
    """Record paths (or 'rpaths' for short) provide a way to get and set
    attributes from a record, even if the way to those attributes is very
    complex (e.g. contains repeated or optional attributes). Does quite a bit
    of validation and preprocessing, making it much faster and safer than a
    'naive' solution. See the wiki page '[dev] Record Paths' for a full
    overview of syntax and usage."""
    __slots__ = (u'_root_subpath',)

    def __init__(self, rpath_str): # type: (unicode) -> None
        self._root_subpath = _parse_rpath(rpath_str)

    def rp_eval(self, record):
        """Evaluates this record path for the specified record, returning a
        list of all attribute values that it resolved to."""
        return self._root_subpath.rp_eval(record)

    def rp_exists(self, record):
        """Returns True if this record path will resolve to a non-empty list
        for the specified record."""
        return self._root_subpath.rp_exists(record)

    def rp_map(self, record, func):
        """Maps the specified function over all the values that this record
        path points to and assigns the altered values to the corresponding
        attributes on the specified record."""
        self._root_subpath.rp_map(record, func)

    def __repr__(self):
        return repr(self._root_subpath)

def _parse_rpath(rpath_str): # type: (unicode) -> _ARP_Subpath
    """Parses the given unicode string as an RPath subpath."""
    if not rpath_str: return None
    sub_rpath, rest_rpath = (rpath_str.split(u'.', 1) if u'.' in rpath_str
                             else (rpath_str, None))
    # Iterated subpath
    if sub_rpath.endswith(u'[i]'):
        return _RP_IteratedSubpath(sub_rpath[:-3], rest_rpath)
    # Optional subpath
    elif sub_rpath.endswith(u'?'):
        return _RP_OptionalSubpath(sub_rpath[:-1], rest_rpath)
    else:
        return (_RP_Subpath if rest_rpath else
                _RP_LeafSubpath)(sub_rpath, rest_rpath)

#------------------------------------------------------------------------------
_digit_re = re.compile(u'([0-9]+)')

def natural_key():
    """Returns a sort key for 'natural' sort order, i.e. similar to how most
    file managers display it - a1.png, a2.png, a10.png. Can handle both strings
    and paths. Inspired by
    https://blog.codinghorror.com/sorting-for-humans-natural-sort-order/."""
    def _to_cmp(sub_str):
        """Helper function that prepares substrings for comparison."""
        return int(sub_str) if sub_str.isdigit() else sub_str.lower()
    return lambda curr_str: [_to_cmp(s) for s in
                             _digit_re.split(u'%s' % curr_str)]

def dict_sort(di, id_eid_=None, keys_dex=(), values_dex=(), by_value=False):
    if id_eid_ is not None: # we passed id_eid in sort by eid
        key_f=lambda k: id_eid_.get(k, u'Unknown').lower()
        for k in sorted(di, key=key_f):
            yield k, di[k], id_eid_[k]
    elif keys_dex or values_dex:
        key_f = lambda k: tuple((u'%s' % k[x]).lower() for x in keys_dex) + tuple(
            di[k][x] for x in values_dex)
        for k in sorted(di, key=key_f):
            yield k, di[k]
    elif by_value:
        key_f = lambda k: di[k]
        for k in sorted(di, key=key_f):
            yield k, di[k]
    else:
        for k in sorted(di):
            yield k, di[k]

# WryeText --------------------------------------------------------------------
codebox = None
class WryeText(object):
    """This class provides a function for converting wtxt text files to html
    files.

    Headings:
    = HHHH >> H1 "HHHH"
    == HHHH >> H2 "HHHH"
    === HHHH >> H3 "HHHH"
    ==== HHHH >> H4 "HHHH"
    Notes:
    * These must start at first character of line.
    * The XXX text is compressed to form an anchor. E.g == Foo Bar gets anchored as" FooBar".
    * If the line has trailing ='s, they are discarded. This is useful for making
      text version of level 1 and 2 headings more readable.

    Bullet Lists:
    * Level 1
      * Level 2
        * Level 3
    Notes:
    * These must start at first character of line.
    * Recognized bullet characters are: - ! ? . + * o The dot (.) produces an invisible
      bullet, and the * produces a bullet character.

    Styles:
      __Text__
      ~~Italic~~
      **BoldItalic**
    Notes:
    * These can be anywhere on line, and effects can continue across lines.

    Links:
     [[file]] produces <a href=file>file</a>
     [[file|text]] produces <a href=file>text</a>
     [[!file]] produces <a href=file target="_blank">file</a>
     [[!file|text]] produces <a href=file target="_blank">text</a>

    Contents
    {{CONTENTS=NN}} Where NN is the desired depth of contents (1 for single level,
    2 for two levels, etc.).
    """

    # Data ------------------------------------------------------------------------
    htmlHead = u"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
    <head>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
    <title>%s</title>
    <style type="text/css">%s</style>
    </head>
    <body>
    """
    defaultCss = u"""
    h1 { margin-top: 0in; margin-bottom: 0in; border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: none; border-right: none; padding: 0.02in 0in; background: #c6c63c; font-family: "Arial", serif; font-size: 12pt; page-break-before: auto; page-break-after: auto }
    h2 { margin-top: 0in; margin-bottom: 0in; border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: none; border-right: none; padding: 0.02in 0in; background: #e6e64c; font-family: "Arial", serif; font-size: 10pt; page-break-before: auto; page-break-after: auto }
    h3 { margin-top: 0in; margin-bottom: 0in; font-family: "Arial", serif; font-size: 10pt; font-style: normal; page-break-before: auto; page-break-after: auto }
    h4 { margin-top: 0in; margin-bottom: 0in; font-family: "Arial", serif; font-style: italic; page-break-before: auto; page-break-after: auto }
    a:link { text-decoration:none; }
    a:hover { text-decoration:underline; }
    p { margin-top: 0.01in; margin-bottom: 0.01in; font-family: "Arial", serif; font-size: 10pt; page-break-before: auto; page-break-after: auto }
    p.empty {}
    p.list-1 { margin-left: 0.15in; text-indent: -0.15in }
    p.list-2 { margin-left: 0.3in; text-indent: -0.15in }
    p.list-3 { margin-left: 0.45in; text-indent: -0.15in }
    p.list-4 { margin-left: 0.6in; text-indent: -0.15in }
    p.list-5 { margin-left: 0.75in; text-indent: -0.15in }
    p.list-6 { margin-left: 1.00in; text-indent: -0.15in }
    .code-n { background-color: #FDF5E6; font-family: "Lucide Console", monospace; font-size: 10pt; white-space: pre; }
    pre { border: 1px solid; overflow: auto; width: 750px; word-wrap: break-word; background: #FDF5E6; padding: 0.5em; margin-top: 0in; margin-bottom: 0in; margin-left: 0.25in}
    code { background-color: #FDF5E6; font-family: "Lucida Console", monospace; font-size: 10pt; }
    td.code { background-color: #FDF5E6; font-family: "Lucida Console", monospace; font-size: 10pt; border: 1px solid #000000; padding:5px; width:50%;}
    body { background-color: #ffffcc; }
    """

    # Conversion ---------------------------------------------------------------
    @staticmethod
    def genHtml(ins,out=None,*cssDirs):
        """Reads a wtxt input stream and writes an html output stream."""
        # Path or Stream? -----------------------------------------------
        if isinstance(ins, (Path, unicode)):
            srcPath = GPath(ins)
            outPath = GPath(out) or srcPath.root+u'.html'
            cssDirs = (srcPath.head,) + cssDirs
            ins = srcPath.open(encoding=u'utf-8-sig')
            out = outPath.open(u'w',encoding=u'utf-8-sig')
        else:
            srcPath = outPath = None
        # Setup
        outWrite = out.write

        cssDirs = (GPath(d) for d in cssDirs)
        # Setup ---------------------------------------------------------
        #--Headers
        reHead = re.compile(u'(=+) *(.+)',re.U)
        headFormat = u"<h%d><a id='%s'>%s</a></h%d>\n"
        headFormatNA = u'<h%d>%s</h%d>\n'
        #--List
        reWryeList = re.compile(u'( *)([-x!?.+*o])(.*)',re.U)
        #--Code
        reCode = re.compile(u'' r'\[code\](.*?)\[/code\]', re.I | re.U)
        reCodeStart = re.compile(u'' r'(.*?)\[code\](.*?)$', re.I | re.U)
        reCodeEnd = re.compile(u'' r'(.*?)\[/code\](.*?)$', re.I | re.U)
        reCodeBoxStart = re.compile(u'' r'\s*\[codebox\](.*?)', re.I | re.U)
        reCodeBoxEnd = re.compile(u'' r'(.*?)\[/codebox\]\s*', re.I | re.U)
        reCodeBox = re.compile(u'' r'\s*\[codebox\](.*?)\[/codebox\]\s*', re.I | re.U)
        codeLines = None
        codeboxLines = None
        def subCode(match):
            try:
                return u' '.join(codebox([match.group(1)],False,False))
            except:
                return match(1)
        #--Misc. text
        reHr = re.compile(u'^------+$',re.U)
        reEmpty = re.compile(u'' r'\s+$', re.U)
        reMDash = re.compile(u' -- ',re.U)
        rePreBegin = re.compile(u'<pre',re.I|re.U)
        rePreEnd = re.compile(u'</pre>',re.I|re.U)
        anchorlist = [] #to make sure that each anchor is unique.
        def subAnchor(match):
            text = match.group(1)
            # This one's weird.  Encode the url to utf-8, then allow urllib to do it's magic.
            # urllib will automatically take any unicode characters and escape them, so to
            # convert back to unicode for purposes of storing the string, everything will
            # be in cp1252, due to the escapings.
            anchor = unicode(quote(reWd.sub(u'', text).encode(u'utf8')),
                             u'cp1252')
            count = 0
            if re.match(u'' r'\d', anchor):
                anchor = u'_' + anchor
            while anchor in anchorlist and count < 10:
                count += 1
                if count == 1:
                    anchor += unicode(count)
                else:
                    anchor = anchor[:-1] + unicode(count)
            anchorlist.append(anchor)
            return u"<a id='%s'>%s</a>" % (anchor,text)
        #--Bold, Italic, BoldItalic
        reBold = re.compile(u'__',re.U)
        reItalic = re.compile(u'~~',re.U)
        reBoldItalic = re.compile(u'' r'\*\*',re.U)
        states = {u'bold':False,u'italic':False,u'boldItalic':False,u'code':0}
        def subBold(match):
            state = states[u'bold'] = not states[u'bold']
            return u'<b>' if state else u'</b>'
        def subItalic(match):
            state = states[u'italic'] = not states[u'italic']
            return u'<i>' if state else u'</i>'
        def subBoldItalic(match):
            state = states[u'boldItalic'] = not states[u'boldItalic']
            return u'<i><b>' if state else u'</b></i>'
        #--Preformatting
        #--Links
        reLink = re.compile(u'' r'\[\[(.*?)\]\]', re.U)
        reHttp = re.compile(u' (http://[_~a-zA-Z0-9./%-]+)',re.U)
        reWww = re.compile(u'' r' (www\.[_~a-zA-Z0-9./%-]+)', re.U)
        reWd = re.compile(u'' r'(<[^>]+>|\[\[[^\]]+\]\]|\s+|[%s]+)' % re.escape(string.punctuation.replace(u'_',u'')), re.U)
        rePar = re.compile(u'' r'^(\s*[a-zA-Z(;]|\*\*|~~|__|\s*<i|\s*<a)', re.U)
        reFullLink = re.compile(u'' r'(:|#|\.[a-zA-Z0-9]{2,4}$)', re.U)
        reColor = re.compile(u'' r'\[\s*color\s*=[\s\"\']*(.+?)[\s\"\']*\](.*?)\[\s*/\s*color\s*\]', re.I | re.U)
        reBGColor = re.compile(u'' r'\[\s*bg\s*=[\s\"\']*(.+?)[\s\"\']*\](.*?)\[\s*/\s*bg\s*\]', re.I | re.U)
        def subColor(match):
            return u'<span style="color:%s;">%s</span>' % (match.group(1),match.group(2))
        def subBGColor(match):
            return u'<span style="background-color:%s;">%s</span>' % (match.group(1),match.group(2))
        def subLink(match):
            address = text = match.group(1).strip()
            if u'|' in text:
                (address,text) = [chunk.strip() for chunk in text.split(u'|',1)]
                if address == u'#': address += unicode(quote(reWd.sub(
                    u'', text).encode(u'utf8')), u'cp1252')
            if address.startswith(u'!'):
                newWindow = u' target="_blank"'
                if address == text:
                    # We have no text, cut off the '!' here too
                    text = text[1:]
                address = address[1:]
            else:
                newWindow = u''
            if not reFullLink.search(address):
                address += u'.html'
            return u'<a href="%s"%s>%s</a>' % (address,newWindow,text)
        #--Tags
        reAnchorTag = re.compile(u'{{A:(.+?)}}',re.U)
        reContentsTag = re.compile(u'' r'\s*{{CONTENTS=?(\d+)}}\s*$', re.U)
        reAnchorHeadersTag = re.compile(u'' r'\s*{{ANCHORHEADERS=(\d+)}}\s*$', re.U)
        reCssTag = re.compile(u'' r'\s*{{CSS:(.+?)}}\s*$',re.U)
        #--Defaults ----------------------------------------------------------
        title = u''
        level = 1
        spaces = u''
        cssName = None
        #--Init
        outLines = []
        contents = []
        outLinesAppend = outLines.append
        outLinesExtend = outLines.extend
        addContents = 0
        inPre = False
        anchorHeaders = True
        #--Read source file --------------------------------------------------
        for line in ins:
            line = line.replace(u'\r\n',u'\n')
            #--Codebox -----------------------------------
            if codebox:
                if codeboxLines is not None:
                    maCodeBoxEnd = reCodeBoxEnd.match(line)
                    if maCodeBoxEnd:
                        codeboxLines.append(maCodeBoxEnd.group(1))
                        outLinesAppend(u'<pre style="width:850px;">')
                        try:
                            codeboxLines = codebox(codeboxLines)
                        except:
                            pass
                        outLinesExtend(codeboxLines)
                        outLinesAppend(u'</pre>\n')
                        codeboxLines = None
                        continue
                    else:
                        codeboxLines.append(line)
                        continue
                maCodeBox = reCodeBox.match(line)
                if maCodeBox:
                    outLines.append(u'<pre style="width:850px;">')
                    try:
                        outLinesExtend(codebox([maCodeBox.group(1)]))
                    except:
                        outLinesAppend(maCodeBox.group(1))
                    outLinesAppend(u'</pre>\n')
                    continue
                maCodeBoxStart = reCodeBoxStart.match(line)
                if maCodeBoxStart:
                    codeboxLines = [maCodeBoxStart.group(1)]
                    continue
            #--Code --------------------------------------
                if codeLines is not None:
                    maCodeEnd = reCodeEnd.match(line)
                    if maCodeEnd:
                        codeLines.append(maCodeEnd.group(1))
                        try:
                            codeLines = codebox(codeLines,False)
                        except:
                            pass
                        outLinesExtend(codeLines)
                        codeLines = None
                        line = maCodeEnd.group(2)
                    else:
                        codeLines.append(line)
                        continue
                line = reCode.sub(subCode,line)
                maCodeStart = reCodeStart.match(line)
                if maCodeStart:
                    line = maCodeStart.group(1)
                    codeLines = [maCodeStart.group(2)]
            #--Preformatted? -----------------------------
            maPreBegin = rePreBegin.search(line)
            maPreEnd = rePreEnd.search(line)
            if inPre or maPreBegin or maPreEnd:
                inPre = maPreBegin or (inPre and not maPreEnd)
                outLinesAppend(line)
                continue
            #--Font/Background Color
            line = reColor.sub(subColor,line)
            line = reBGColor.sub(subBGColor,line)
            #--Re Matches -------------------------------
            maContents = reContentsTag.match(line)
            maAnchorHeaders = reAnchorHeadersTag.match(line)
            maCss = reCssTag.match(line)
            maHead = reHead.match(line)
            maList  = reWryeList.match(line)
            maPar   = rePar.match(line)
            maEmpty = reEmpty.match(line)
            #--Contents
            if maContents:
                if maContents.group(1):
                    addContents = int(maContents.group(1))
                else:
                    addContents = 100
                inPar = False
            elif maAnchorHeaders:
                anchorHeaders = maAnchorHeaders.group(1) != u'0'
                continue
            #--CSS
            elif maCss:
                #--Directory spec is not allowed, so use tail.
                cssName = GPath(maCss.group(1).strip()).tail
                continue
            #--Headers
            elif maHead:
                lead,text = maHead.group(1,2)
                text = re.sub(u' *=*#?$', u'', text.strip())
                anchor = unicode(quote(reWd.sub(u'', text).encode(u'utf8')),
                                 u'cp1252')
                level = len(lead)
                if anchorHeaders:
                    if re.match(u'' r'\d', anchor):
                        anchor = u'_' + anchor
                    count = 0
                    while anchor in anchorlist and count < 10:
                        count += 1
                        if count == 1:
                            anchor += unicode(count)
                        else:
                            anchor = anchor[:-1] + unicode(count)
                    anchorlist.append(anchor)
                    line = (headFormatNA,headFormat)[anchorHeaders] % (level,anchor,text,level)
                    if addContents: contents.append((level,anchor,text))
                else:
                    line = headFormatNA % (level,text,level)
                #--Title?
                if not title and level <= 2: title = text
            #--Paragraph
            elif maPar and not states[u'code']:
                line = u'<p>'+line+u'</p>\n'
            #--List item
            elif maList:
                spaces = maList.group(1)
                bullet = maList.group(2)
                text = maList.group(3)
                if bullet == u'.': bullet = u'&nbsp;'
                elif bullet == u'*': bullet = u'&bull;'
                level = len(spaces)//2 + 1
                line = spaces+u'<p class="list-%i">'%level+bullet+u'&nbsp; '
                line = line + text + u'</p>\n'
            #--Empty line
            elif maEmpty:
                line = spaces+u'<p class="empty">&nbsp;</p>\n'
            #--Misc. Text changes --------------------
            line = reHr.sub(u'<hr>',line)
            line = reMDash.sub(u' &#150; ',line)
            #--Bold/Italic subs
            line = reBold.sub(subBold,line)
            line = reItalic.sub(subItalic,line)
            line = reBoldItalic.sub(subBoldItalic,line)
            #--Wtxt Tags
            line = reAnchorTag.sub(subAnchor,line)
            #--Hyperlinks
            line = reLink.sub(subLink,line)
            line = reHttp.sub(u'' r' <a href="\1">\1</a>', line)
            line = reWww.sub(u'' r' <a href="http://\1">\1</a>', line)
            #--Save line ------------------
            #print line,
            outLines.append(line)
        #--Get Css -----------------------------------------------------------
        if not cssName:
            css = WryeText.defaultCss
        else:
            if cssName.ext != u'.css':
                raise exception.BoltError(u'Invalid Css file: %s' % cssName)
            for css_dir in cssDirs:
                cssPath = GPath(css_dir).join(cssName)
                if cssPath.exists(): break
            else:
                raise exception.BoltError(u'Css file not found: %s' % cssName)
            with cssPath.open(u'r', encoding=u'utf-8-sig') as cssIns:
                css = u''.join(cssIns.readlines())
            if u'<' in css:
                raise exception.BoltError(u'Non css tag in %s' % cssPath)
        #--Write Output ------------------------------------------------------
        outWrite(WryeText.htmlHead % (title,css))
        didContents = False
        for line in outLines:
            if reContentsTag.match(line):
                if contents and not didContents:
                    baseLevel = min([level for (level,name_,text) in contents])
                    for (level,name_,text) in contents:
                        level = level - baseLevel + 1
                        if level <= addContents:
                            outWrite(u'<p class="list-%d">&bull;&nbsp; <a href="#%s">%s</a></p>\n' % (level,name_,text))
                    didContents = True
            else:
                outWrite(line)
        outWrite(u'</body>\n</html>\n')
        #--Close files?
        if srcPath:
            ins.close()
            out.close()

# Main -------------------------------------------------------------------------
if __name__ == u'__main__' and len(sys.argv) > 1:
    #--Commands----------------------------------------------------------------
    @mainfunc
    def genHtml(*args,**keywords):
        """Wtxt to html. Just pass through to WryeText.genHtml."""
        if not len(args):
            args = [u'..\\Wrye Bash.txt']
        WryeText.genHtml(*args,**keywords)

    #--Command Handler --------------------------------------------------------
    _mainFunctions.main()
