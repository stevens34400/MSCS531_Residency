import m5
from m5.objects import *
from m5.util import addToPath
import os

# Adjust path to gem5 root from configs/deprecated/example/
addToPath('../../..')

# Define binary path (use your custom hello binary)
binary_path = "./hello"
if not os.path.exists(binary_path):
    raise FileNotFoundError(f"Binary not found: {binary_path}")

# Set the stats file name
m5.options.stats_file = "m5out/stats64.txt"

# Define cache classes based on Phase 1
class L1ICache(Cache):
    size = '64KiB'  # Larger size
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 8
    tgts_per_mshr = 16

class L1DCache(Cache):
    size = '64KiB'  # Larger size
    assoc = 4
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 8
    tgts_per_mshr = 16

class L2Cache(Cache):
    size = '2MiB'  # Larger size
    assoc = 8
    tag_latency = 10
    data_latency = 10
    response_latency = 10
    mshrs = 20
    tgts_per_mshr = 20

# Create the system
system = System()
system.clk_domain = SrcClockDomain(clock='2GHz', voltage_domain=VoltageDomain(voltage='1.0V'))
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('2GiB')]

# Create memory bus early (before CPU configuration)
system.membus = SystemXBar()

# Configure 4-core CPU (Atom-like)
system.cpu = [DerivO3CPU() for _ in range(4)]
for cpu in system.cpu:
    cpu.fetchWidth = 2
    cpu.decodeWidth = 2
    cpu.renameWidth = 2
    cpu.dispatchWidth = 2
    cpu.issueWidth = 2
    cpu.wbWidth = 2
    cpu.commitWidth = 2
    cpu.fetchToDecodeDelay = 3
    cpu.decodeToRenameDelay = 2
    cpu.renameToIEWDelay = 4
    cpu.iewToCommitDelay = 3
    cpu.branchPred = TournamentBP()
    cpu.branchPred.localPredictorSize = 2048
    cpu.branchPred.globalPredictorSize = 8192
    cpu.fuPool = DefaultFUPool()
    cpu.fuPool.FUList[0].count = 2  # IntALU
    cpu.clk_domain = SrcClockDomain(clock='2GHz', voltage_domain=VoltageDomain(voltage='1.0V'))
    cpu.mmu = X86MMU()
    cpu.mmu.itb.size = 64
    cpu.mmu.dtb.size = 64
    cpu.createInterruptController()
    cpu.interrupts[0].pio = system.membus.mem_side_ports
    cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
    cpu.interrupts[0].int_responder = system.membus.mem_side_ports

# Configure cache hierarchy
for cpu in system.cpu:
    cpu.icache = L1ICache()
    cpu.dcache = L1DCache()
    cpu.icache.cpu_side = cpu.icache_port
    cpu.dcache.cpu_side = cpu.dcache_port

# L2 bus and shared L2 cache
system.l2bus = L2XBar()
for cpu in system.cpu:
    cpu.icache.mem_side = system.l2bus.cpu_side_ports
    cpu.dcache.mem_side = system.l2bus.cpu_side_ports
system.l2cache = L2Cache()
system.l2cache.cpu_side = system.l2bus.mem_side_ports

# Connect L2 cache to memory bus
system.l2cache.mem_side = system.membus.cpu_side_ports

# Create memory controller
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR4_2400_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# Workload setup
system.workload = SEWorkload.init_compatible(binary_path)
process = Process()
process.cmd = [binary_path]
for cpu in system.cpu:
    cpu.workload = process
    cpu.createThreads()

# Instantiate the simulation
root = Root(full_system=False, system=system)
m5.instantiate()

# Run simulation
print(f"Starting simulation with {binary_path}...")
exit_event = m5.simulate(1000000000)  # Limit to 1B ticks
print(f"Simulation exited: {exit_event.getCause()} at tick {m5.curTick()}")
m5.stats.dump()
print("Statistics dumped to m5out/stats64.txt")
