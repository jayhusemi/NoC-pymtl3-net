'''
==========================================================================
commons.py
==========================================================================
Common utility functions.

Author : Yanghui Ou
  Date : Feb 9, 2020
'''
from pymtl3 import *
from pymtl3.datatypes.bitstructs import(
  is_bitstruct_class, 
  _FIELDS as bitstruct_fields,
)

#-------------------------------------------------------------------------
# get_nbits
#-------------------------------------------------------------------------

def get_nbits( cls ):
  if issubclass( cls, Bits ):
    return cls.nbits

  else:
    assert is_bitstruct_class( cls ) 
    fields_dict = getattr( cls, bitstruct_fields )
    total_nbits = 0
    for _, ftype in fields_dict.items():
      total_nbits +=  get_nbits( ftype )
    return total_nbits


#-------------------------------------------------------------------------
# get_plen_type
#-------------------------------------------------------------------------
# Returns the type of feild payload length from the header format.

def get_plen_type( cls, plen_field_name='plen' ):
  assert is_bitstruct_class( cls )
  fields_dict = getattr( cls, bitstruct_fields )

  if not plen_field_name in fields_dict:
    raise AssertionError( f'{cls.__qualname__} does not have field {plen_field_name}!' )

  return fields_dict[ plen_field_name ]

