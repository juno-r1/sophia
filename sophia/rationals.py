# Originally contributed by Sjoerd Mullender.
# Significantly modified by Jeffrey Yasskin <jyasskin at gmail.com>.
# Adapted for use in the Sophia programming language.
# (https://github.com/python/cpython/blob/3.11/Lib/fractions.py)

"""Fraction, infinite-precision, rational numbers."""

import math
import numbers
import operator
import re
import sys

__all__ = ['Rational']

# Constants related to the hash implementation;  hash(x) is based
# on the reduction of x modulo the prime _PyHASH_MODULUS.
_PyHASH_MODULUS = sys.hash_info.modulus
# Value to be used for rationals that reduce to infinity modulo
# _PyHASH_MODULUS.
_PyHASH_INF = sys.hash_info.inf

_RATIONAL_FORMAT = re.compile(r"""
	\A\s*                                 # optional whitespace at the start,
	(?P<sign>[-+]?)                       # an optional sign, then
	(?=\d|\.\d)                           # lookahead for digit or .digit
	(?P<num>\d*|\d+(_\d+)*)               # numerator (possibly empty)
	(?:                                   # followed by
	   (?:/(?P<denom>\d+(_\d+)*))?        # an optional denominator
	|                                     # or
	   (?:\.(?P<decimal>d*|\d+(_\d+)*))?  # an optional fractional part
	   (?:E(?P<exp>[-+]?\d+(_\d+)*))?     # and optional exponent
	)
	\s*\Z                                 # and optional whitespace to finish
""", re.VERBOSE | re.IGNORECASE)


class Rational(numbers.Rational):
	"""This class implements rational numbers.

	In the two-argument form of the constructor, Rational(8, 6) will
	produce a rational number equivalent to 4/3. Both arguments must
	be integers. The numerator defaults to 0 and the denominator
	defaults to 1 so that Rational(3) == 3 and Rational() == 0.

	Rationals can also be constructed from:

	  - numeric strings similar to those accepted by the
		float constructor (for example, '-2.3' or '1e10')

	  - strings of the form '123/456'

	  - other Rational instances

	"""

	__slots__ = ('numerator', 'denominator')

	# We're immutable, so use __new__ not __init__
	def __new__(cls, numerator = 0, denominator = None, *, _normalise = True):
		"""Constructs a Rational.

		Takes a string like '3/2' or '1.5', another Rational instance, or a
		numerator/denominator pair of integers.

		Examples
		--------

		>>> Fraction(10, -8)
		Fraction(-5, 4)
		>>> Fraction('-35/4')
		Fraction(-35, 4)
		>>> Fraction('3.1415') # conversion from numeric string
		Fraction(6283, 2000)
		>>> Fraction('-47e-2') # string may include a decimal exponent
		Fraction(-47, 100)

		"""
		self = super(Rational, cls).__new__(cls)

		if denominator is None:
			try: # Fast construction from a single rational
				self.numerator = numerator.numerator
				self.denominator = numerator.denominator
				return self
			except AttributeError: # Handle construction from strings
				m = _RATIONAL_FORMAT.match(numerator)
				if m is None:
					raise ValueError('Invalid literal for Rational: %r' % numerator)
				numerator = int(m.group('num') or '0')
				denom = m.group('denom')
				if denom:
					denominator = int(denom)
				else:
					denominator = 1
					decimal = m.group('decimal')
					if decimal:
						decimal = decimal.replace('_', '')
						scale = 10**len(decimal)
						numerator = numerator * scale + int(decimal)
						denominator *= scale
					exp = m.group('exp')
					if exp:
						exp = int(exp)
						if exp >= 0:
							numerator *= 10**exp
						else:
							denominator *= 10**-exp
				if m.group('sign') == '-':
					numerator = -numerator
			
		if _normalise:
			g = math.gcd(numerator, denominator)
			if denominator < 0:
				g = -g
			numerator //= g
			denominator //= g
		self.numerator = numerator
		self.denominator = denominator
		return self

	def __repr__(self): # No need to distinguish this from other number types
		"""repr(self)"""
		if self.denominator == 1:
			return str(self.numerator)
		else:
			return '%s/%s' % (self.numerator, self.denominator)

	def __str__(self):
		"""str(self)"""
		if self.denominator == 1:
			return str(self.numerator)
		else:
			return '%s/%s' % (self.numerator, self.denominator)

	# No need for operator fallbacks because Sophia only ever operates on Rationals!

	# Rational arithmetic algorithms: Knuth, TAOCP, Volume 2, 4.5.1.
	#
	# Assume input fractions a and b are normalized.
	#
	# 1) Consider addition/subtraction.
	#
	# Let g = gcd(da, db). Then
	#
	#              na   nb    na*db ± nb*da
	#     a ± b == -- ± -- == ------------- ==
	#              da   db        da*db
	#
	#              na*(db//g) ± nb*(da//g)    t
	#           == ----------------------- == -
	#                      (da*db)//g         d
	#
	# Now, if g > 1, we're working with smaller integers.
	#
	# Note, that t, (da//g) and (db//g) are pairwise coprime.
	#
	# Indeed, (da//g) and (db//g) share no common factors (they were
	# removed) and da is coprime with na (since input fractions are
	# normalized), hence (da//g) and na are coprime.  By symmetry,
	# (db//g) and nb are coprime too.  Then,
	#
	#     gcd(t, da//g) == gcd(na*(db//g), da//g) == 1
	#     gcd(t, db//g) == gcd(nb*(da//g), db//g) == 1
	#
	# Above allows us optimize reduction of the result to lowest
	# terms.  Indeed,
	#
	#     g2 = gcd(t, d) == gcd(t, (da//g)*(db//g)*g) == gcd(t, g)
	#
	#                       t//g2                   t//g2
	#     a ± b == ----------------------- == ----------------
	#              (da//g)*(db//g)*(g//g2)    (da//g)*(db//g2)
	#
	# is a normalized fraction.  This is useful because the unnormalized
	# denominator d could be much larger than g.
	#
	# We should special-case g == 1 (and g2 == 1), since 60.8% of
	# randomly-chosen integers are coprime:
	# https://en.wikipedia.org/wiki/Coprime_integers#Probability_of_coprimality
	# Note, that g2 == 1 always for fractions, obtained from floats: here
	# g is a power of 2 and the unnormalized numerator t is an odd integer.
	#
	# 2) Consider multiplication
	#
	# Let g1 = gcd(na, db) and g2 = gcd(nb, da), then
	#
	#            na*nb    na*nb    (na//g1)*(nb//g2)
	#     a*b == ----- == ----- == -----------------
	#            da*db    db*da    (db//g1)*(da//g2)
	#
	# Note, that after divisions we're multiplying smaller integers.
	#
	# Also, the resulting fraction is normalized, because each of
	# two factors in the numerator is coprime to each of the two factors
	# in the denominator.
	#
	# Indeed, pick (na//g1).  It's coprime with (da//g2), because input
	# fractions are normalized.  It's also coprime with (db//g1), because
	# common factors are removed by g1 == gcd(na, db).
	#
	# As for addition/subtraction, we should special-case g1 == 1
	# and g2 == 1 for same reason.  That happens also for multiplying
	# rationals, obtained from floats.

	def __add__(a, b):
		"""a + b"""
		na, da = a.numerator, a.denominator
		nb, db = b.numerator, b.denominator
		g = math.gcd(da, db)
		if g == 1:
			return Rational(na * db + da * nb, da * db, _normalise = False)
		s = da // g
		t = na * (db // g) + nb * s
		g2 = math.gcd(t, g)
		if g2 == 1:
			return Rational(t, s * db, _normalise = False)
		return Rational(t // g2, s * (db // g2), _normalise = False)

	__radd__ = __add__

	def __sub__(a, b):
		"""a - b"""
		na, da = a.numerator, a.denominator
		nb, db = b.numerator, b.denominator
		g = math.gcd(da, db)
		if g == 1:
			return Rational(na * db - da * nb, da * db, _normalise = False)
		s = da // g
		t = na * (db // g) - nb * s
		g2 = math.gcd(t, g)
		if g2 == 1:
			return Rational(t, s * db, _normalise = False)
		return Rational(t // g2, s * (db // g2), _normalise = False)

	def __mul__(a, b):
		"""a * b"""
		na, da = a.numerator, a.denominator
		nb, db = b.numerator, b.denominator
		g1 = math.gcd(na, db)
		if g1 > 1:
			na //= g1
			db //= g1
		g2 = math.gcd(nb, da)
		if g2 > 1:
			nb //= g2
			da //= g2
		return Rational(na * nb, db * da, _normalise = False)

	__rmul__ = __mul__

	def __truediv__(a, b):
		"""a / b"""
		# Same as _mul(), with inversed b.
		na, da = a.numerator, a.denominator
		nb, db = b.numerator, b.denominator
		g1 = math.gcd(na, nb)
		if g1 > 1:
			na //= g1
			nb //= g1
		g2 = math.gcd(db, da)
		if g2 > 1:
			da //= g2
			db //= g2
		n, d = na * db, nb * da
		if d < 0:
			n, d = -n, -d
		return Rational(n, d, _normalise = False)

	__rtruediv__ = __truediv__ # DO NOT CALL

	def __floordiv__(a, b):
		"""a // b"""
		return Rational((a.numerator * b.denominator) // (a.denominator * b.numerator), 1)

	__rfloordiv__ = __floordiv__

	def __divmod__(a, b):
		"""(a // b, a % b)"""
		da, db = a.denominator, b.denominator
		div, n_mod = divmod(a.numerator * db, da * b.numerator)
		return Rational(div, 1), Rational(n_mod, da * db)

	def __mod__(a, b):
		"""a % b"""
		da, db = a.denominator, b.denominator
		return Rational((a.numerator * db) % (b.numerator * da), da * db)

	__rmod__ = __mod__

	def __pow__(a, b):
		"""a ** b

		If b is not an integer, the result will be a float or complex
		since roots are generally irrational. If b is an integer, the
		result will be rational.

		"""
		if b.denominator == 1:
			power = b.numerator
			if power >= 0:
				return Rational(int(a.numerator ** power),
								int(a.denominator ** power),
								_normalise = False)
			elif a.numerator >= 0:
				return Rational(int(a.denominator ** -power),
								int(a.numerator ** -power),
								_normalise = False)
			else:
				return Rational(int((-a.denominator) ** -power),
								int((-a.numerator) ** -power),
								_normalise = False)
		else:
			# A fractional power will generally produce an irrational number, which is rationalised here.
			num, denom = (float(a) ** float(b)).as_integer_ratio()
			return Rational(num, denom)

	__rpow__ = __pow__

	def __pos__(a):
		"""+a: Coerces a subclass instance to Fraction"""
		return Rational(a.numerator, a.denominator, _normalise = False)

	def __neg__(a):
		"""-a"""
		return Rational(-a.numerator, a.denominator, _normalise = False)

	def __abs__(a):
		"""abs(a)"""
		return Rational(abs(a.numerator), a.denominator, _normalise = False)

	def __int__(a, _index = operator.index):
		"""int(a)"""
		if a.numerator < 0:
			return _index(-(-a.numerator // a.denominator))
		else:
			return _index(a.numerator // a.denominator)

	def __trunc__(a):
		"""math.trunc(a)"""
		if a.numerator < 0:
			return -(-a.numerator // a.denominator)
		else:
			return a.numerator // a.denominator

	def __floor__(a):
		"""math.floor(a)"""
		return Rational(a.numerator // a.denominator, 1, _normalise = False)

	def __ceil__(a):
		"""math.ceil(a)"""
		# The negations cleverly convince floordiv to return the ceiling.
		return Rational(-(-a.numerator // a.denominator), 1, _normalise = False)

	def __round__(self):
		"""round(self)"""
		# Rounds half away from 0.
		na, da = self.numerator, self.denominator
		floor, remainder = divmod(na, da)
		if floor < 0: # Normalise negative Rationals
			da += 1
		if remainder * 2 >= da:
			return Rational(floor + 1, 1, _normalise = False)
		else:
			return Rational(floor, 1, _normalise = False)

	def __hash__(self):
		"""hash(self)"""

		# To make sure that the hash of a Fraction agrees with the hash
		# of a numerically equal integer, float or Decimal instance, we
		# follow the rules for numeric hashes outlined in the
		# documentation.  (See library docs, 'Built-in Types').

		try:
			dinv = pow(self.denominator, -1, _PyHASH_MODULUS)
		except ValueError:
			# ValueError means there is no modular inverse.
			hash_ = _PyHASH_INF
		else:
			# The general algorithm now specifies that the absolute value of
			# the hash is
			#    (|N| * dinv) % P
			# where N is self.numerator and P is _PyHASH_MODULUS.  That's
			# optimized here in two ways:  first, for a non-negative int i,
			# hash(i) == i % P, but the int hash implementation doesn't need
			# to divide, and is faster than doing % P explicitly.  So we do
			#    hash(|N| * dinv)
			# instead.  Second, N is unbounded, so its product with dinv may
			# be arbitrarily expensive to compute.  The final answer is the
			# same if we use the bounded |N| % P instead, which can again
			# be done with an int hash() call.  If 0 <= i < P, hash(i) == i,
			# so this nested hash() call wastes a bit of time making a
			# redundant copy when |N| < P, but can save an arbitrarily large
			# amount of computation for large |N|.
			hash_ = hash(hash(abs(self.numerator)) * dinv)
		result = hash_ if self.numerator >= 0 else -hash_
		return -2 if result == -1 else result

	def __eq__(a, b):
		"""a == b"""
		try:
			return (a.numerator == b.numerator and
					a.denominator == b.denominator)
		except AttributeError: # Only occurs at parse time
			return False

	def __lt__(a, b):
		"""a < b"""
		return a.numerator * b.denominator < a.denominator * b.numerator

	def __gt__(a, b):
		"""a > b"""
		return a.numerator * b.denominator > a.denominator * b.numerator

	def __le__(a, b):
		"""a <= b"""
		return a.numerator * b.denominator <= a.denominator * b.numerator

	def __ge__(a, b):
		"""a >= b"""
		return a.numerator * b.denominator >= a.denominator * b.numerator

	def __bool__(a):
		"""a != 0"""
		# bpo-39274: Use bool() because (a.numerator != 0) can return an
		# object which is not a bool.
		return bool(a.numerator)

	# support for pickling, copy, and deepcopy

	def __reduce__(self):
		return (self.__class__, (self.numerator, self.denominator))

	def __copy__(self):
		if type(self) == Rational:
			return self     # I'm immutable; therefore I am my own clone
		return self.__class__(self.numerator, self.denominator)

	def __deepcopy__(self, memo):
		if type(self) == Rational:
			return self     # My components are also immutable
		return self.__class__(self.numerator, self.denominator)