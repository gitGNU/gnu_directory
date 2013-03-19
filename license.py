
class License(object):
    def __init__(self, name):
        self.name = name

    def __iter__(self):
        yield self

    def flatten(self):
        yield self.name

    def __str__(self, depth=0):
        return self.name

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)

class Licenses(object):
    def __init__(self, xs):
        self.xs = xs

    def __iter__(self):
        for x in self.xs:
            yield x

    def flatten(self):
        for x in self.xs:
            for y in x.flatten():
                yield y

    def __str__(self, depth=0):
        j = ' %s ' % (self._join,)
        ss = [x.__str__(depth=depth+1) for x in self.xs]
        s = j.join(ss)

        if depth > 0:
            s = '(%s)' % s

        return s

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.xs)

class AllLicenses(Licenses):
    _join = 'and'

class AnyLicense(Licenses):
    _join = 'or'

def parse_licenses(s):
    """
    >>> ls = parse_licenses("X")
    >>> ls
    <License X>
    >>> print ls
    X
    >>> list(ls)
    [<License X>]
    >>> list(ls.flatten())
    ['X']

    >>> ls = parse_licenses("X or Y or Z")
    >>> ls
    <AnyLicense [<License X>, <License Y>, <License Z>]>
    >>> print ls
    X or Y or Z
    >>> list(ls)
    [<License X>, <License Y>, <License Z>]
    >>> list(ls.flatten())
    ['X', 'Y', 'Z']

    >>> ls = parse_licenses("X and Y and Z")
    >>> ls
    <AllLicenses [<License X>, <License Y>, <License Z>]>
    >>> print ls
    X and Y and Z
    >>> list(ls)
    [<License X>, <License Y>, <License Z>]
    >>> list(ls.flatten())
    ['X', 'Y', 'Z']

    >>> print parse_licenses("X or Y and Z")
    X or (Y and Z)

    >>> print parse_licenses("X and Y or Z")
    (X and Y) or Z

    >>> print parse_licenses("X, and Y or Z")
    X and (Y or Z)

    >>> print parse_licenses("X | Y")
    X or Y
    """

    splits = (
        (', and ', AllLicenses),
        (' or ', AnyLicense),
        (' | ', AnyLicense),
        (' and ', AllLicenses))

    for (split_str, cls) in splits:
        if split_str in s:
            return cls([parse_licenses(sub) for sub in s.split(split_str)])

    return License(s)
