
class License(object):
    def __init__(self, name):
        self.name = name

    def __iter__(self):
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
            for y in iter(x):
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
    _join = '&'

class AnyLicense(Licenses):
    _join = '|'

def parse_licenses(s):
    """
    >>> print parse_licenses("X")
    X
    >>> print parse_licenses("X or Y or Z")
    X | Y | Z
    >>> print parse_licenses("X and Y and Z")
    X & Y & Z
    >>> parse_licenses("X or Y and Z")
    <AnyLicense [<License X>, <AllLicenses [<License Y>, <License Z>]>]>
    >>> print parse_licenses("X or Y and Z")
    X | (Y & Z)
    >>> print parse_licenses("X and Y or Z")
    (X & Y) | Z
    >>> print parse_licenses("X, and Y or Z")
    X & (Y | Z)
    """

    splits = (
        (', and ', AllLicenses),
        (' or ', AnyLicense),
        (' and ', AllLicenses))

    for (split_str, cls) in splits:
        if split_str in s:
            return cls([parse_licenses(sub) for sub in s.split(split_str)])

    return License(s)
