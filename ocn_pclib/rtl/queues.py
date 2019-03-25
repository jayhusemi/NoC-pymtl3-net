#-------------------------------------------------------------------------
# Library of RTL queues
#-------------------------------------------------------------------------
#
# Author : Yanghui Ou
#   Date : Mar 23, 2019

from pymtl import *
from ocn_pclib.ifcs import EnqIfcRTL, DeqIfcRTL
from pclib.rtl import Mux, Reg, RegEn, RegisterFile

#-------------------------------------------------------------------------
# Dpath and Ctrl for NormalQueueRTL
#-------------------------------------------------------------------------

class NormalQueueDpathRTL( RTLComponent ):

  def construct( s, MsgType, num_entries=2 ):
    
    # Interface

    s.enq_msg =  InVPort( MsgType )
    s.deq_msg = OutVPort( MsgType )

    s.wen   = InVPort( Bits1 )
    s.waddr = InVPort( mk_bits( clog2( num_entries ) ) )
    s.raddr = InVPort( mk_bits( clog2( num_entries ) ) )

    # Component

    s.queue = RegisterFile( MsgType, num_entries )(
      raddr = { 0: s.raddr },
      rdata = { 0: s.deq_msg },
      wen   = { 0: s.wen },
      waddr = { 0: s.waddr },
      wdata = { 0: s.enq_msg }
    )

class NormalQueueCtrlRTL( RTLComponent ):

  def construct( s, num_entries=2 ):
    
    # Constants

    s.num_entries = num_entries
    s.last_idx    = num_entries - 1
    addr_nbits    = clog2( num_entries )

    # Interface
    
    s.enq_en  = InVPort ( Bits1 )
    s.enq_rdy = OutVPort( Bits1 )
    s.deq_en  = InVPort ( Bits1 )
    s.deq_rdy = OutVPort( Bits1 )
    s.credit  = OutVPort( mk_bits( addr_nbits ) )

    s.wen     = OutVPort( Bits1 )
    s.waddr   = OutVPort( mk_bits( addr_nbits ) )
    s.raddr   = OutVPort( mk_bits( addr_nbits ) )
    
    # Registers

    s.head  = Wire( mk_bits( addr_nbits ) )
    s.tail  = Wire( mk_bits( addr_nbits ) )
    # s.count = Wire( mk_bits( addr_nbits ) )

    # Wires

    s.enq_xfer  = Wire( Bits1 )
    s.deq_xfer  = Wire( Bits1 )
    s.head_next = Wire( mk_bits( addr_nbits ) )
    s.tail_next = Wire( mk_bits( addr_nbits ) )

    @s.update
    def up_xfer_signals():

      s.enq_xfer  = s.enq_en and s.enq_rdy
      s.deq_xfer  = s.deq_en and s.deq_rdy
      s.head_next = s.head - 1 if s.head > 0 else s.last_idx
      s.tail_next = s.tail + 1 if s.tail < s.last_idx else 0


      s.wen     = s.enq_xfer
      s.waddr   = s.tail
      s.raddr   = s.head


    @s.update
    def up_rdy_signals():
      s.enq_rdy = s.credit > 0
      s.deq_rdy = s.credit < s.num_entries
      # s.credit  = s.count

    @s.update_on_edge
    def up_reg():

      if s.reset:
        s.head  = 0
        s.tail  = 0
        #s.count = s.num_entries
        s.credit = s.num_entries

      else:
        s.head   = s.head_next if s.deq_xfer else s.head
        s.tail   = s.tail_next if s.enq_xfer else s.tail
        s.credit = s.credit - 1 if s.enq_xfer and not s.deq_xfer else \
                   s.credit + 1 if s.deq_xfer and not s.enq_xfer else \
                   s.credit

#-------------------------------------------------------------------------
# NormalQueueRTL
#-------------------------------------------------------------------------

class NormalQueueRTL( RTLComponent ):

  def construct( s, MsgType, num_entries=2 ):
    
    # Interface

    s.enq    = EnqIfcRTL( MsgType )
    s.deq    = DeqIfcRTL( MsgType )
    s.credit = OutVPort( mk_bits( clog2( num_entries ) ) )
    
    # Components

    s.ctrl  = NormalQueueCtrlRTL ( num_entries )
    s.dpath = NormalQueueDpathRTL( MsgType, num_entries )

    # Connect ctrl to data path

    s.connect( s.ctrl.wen,     s.dpath.wen     )
    s.connect( s.ctrl.waddr,   s.dpath.waddr   )
    s.connect( s.ctrl.raddr,   s.dpath.raddr   )

    # Connect to interface

    s.connect( s.enq.en,  s.ctrl.enq_en   )
    s.connect( s.enq.rdy, s.ctrl.enq_rdy  )
    s.connect( s.deq.en,  s.ctrl.deq_en   )
    s.connect( s.deq.rdy, s.ctrl.deq_rdy  )
    s.connect( s.credit,  s.ctrl.credit   )
    s.connect( s.enq.msg, s.dpath.enq_msg )
    s.connect( s.deq.msg, s.dpath.deq_msg )

  # Line trace

  def line_trace( s ):
    return "{}({}){}".format( s.enq, s.credit, s.deq )