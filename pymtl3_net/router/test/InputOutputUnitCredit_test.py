"""
==========================================================================
InputOutputUnitCredit_test.py
==========================================================================
Composition test for input/output unit with credit based interfaces.

Author : Yanghui Ou
  Date : June 22, 2019
"""
from pymtl3 import *
from pymtl3.stdlib.stream.queues import BypassQueueRTL
from pymtl3.stdlib.stream.SourceRTL import SourceRTL as TestSrcRTL
from pymtl3_net.ocnlib.ifcs.CreditIfc import (
  CreditRecvRTL2SendRTL,
  RecvRTL2CreditSendRTL
)
from pymtl3_net.ocnlib.ifcs.packets import mk_generic_pkt
from pymtl3_net.ocnlib.utils import run_sim
from pymtl3_net.ocnlib.test.stream_sinks import NetSinkRTL as TestNetSinkRTL

from ..InputUnitCreditRTL import InputUnitCreditRTL
from ..OutputUnitCreditRTL import OutputUnitCreditRTL
from ..SwitchUnitRTL import SwitchUnitRTL

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Component ):
  def construct( s, Type, src_msgs, sink_msgs, vc=2, credit_line=2 ):

    s.src   = TestSrcRTL( Type, src_msgs )
    s.output_unit = OutputUnitCreditRTL( Type, vc=vc, credit_line=credit_line )
    s.input_unit  = InputUnitCreditRTL( Type, vc=vc, credit_line=credit_line )
    s.switch_unit = SwitchUnitRTL( Type, num_inports=vc )
    s.sink = TestNetSinkRTL( Type, sink_msgs )

    s.src.send             //= s.output_unit.recv
    s.output_unit.send     //= s.input_unit.recv
    s.switch_unit.send.msg //= s.sink.recv.msg
    for i in range( vc ):
      s.input_unit.send[i] //= s.switch_unit.recv[i]

    s.switch_unit.send     //= s.sink.recv

  def line_trace( s ):
    return "{} >>> {} >>> {} >>> {} >>> {}".format(
      s.src.line_trace(),
      s.output_unit.line_trace(),
      s.input_unit.line_trace(),
      s.switch_unit.line_trace(),
      s.sink.line_trace()
    )

  def done( s ):
    return s.src.done() and s.sink.done()

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

def test_simple():
  Pkt = mk_generic_pkt( vc=2, payload_nbits=32 )
  msgs = [
    Pkt( 0, 1, 0x04, 0, 0xdeadbabe ),
    Pkt( 0, 2, 0x02, 1, 0xfaceb00c ),
    Pkt( 0, 3, 0x03, 0, 0xdeadface ),
  ]
  th = TestHarness( Pkt, msgs, msgs )
  run_sim( th )

def test_backpresure():
  Pkt = mk_generic_pkt( vc=2, payload_nbits=32 )
  msgs = [
      # src dst opq vc_id payload
    Pkt( 0, 1, 0x04, 0, 0xdeadbabe ),
    Pkt( 0, 2, 0x02, 1, 0xfaceb00c ),
    Pkt( 0, 3, 0x03, 0, 0xdeadface ),
    Pkt( 0, 3, 0x03, 1, 0xdeadface ),
    Pkt( 0, 3, 0x03, 1, 0xdeadface ),
    Pkt( 0, 3, 0x03, 0, 0xdeadface ),
    Pkt( 0, 3, 0x03, 0, 0xdeadface ),
  ]
  th = TestHarness( Pkt, msgs, msgs )
  th.set_param( "top.sink.construct", initial_delay=20 )
  run_sim( th )
