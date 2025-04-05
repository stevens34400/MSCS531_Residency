import os
import shutil
import argparse
from m5.util import addToPath
import m5
from m5.objects import *

# Adjust path to gem5 root
addToPath('../../..')

# Command-line arguments
parser = argparse.ArgumentParser(description="Gem5 Simulation Configuration")
parser.add_argument('--binary', default="./hello", help="Path to the binary to simulate")
parser.add_argument('--stats-dir', default="m5out/256_optimized", help="Directory for stats output")
parser.add_argument('--debug', action='store_true', help="Enable debug flags (Fetch, Decode, Exec)")
args = parser.parse_args()

# Verify binary exists
binary_path = args.binary
if not os.path.exists(binary_path):
    raise FileNotFoundError(f"Binary not found: {binary_path}")

# === Cache Configuration ===
class L1ICache(Cache):
    size = '256KiB'
    assoc = 2
    tag_latency = 1
    data_latency = 1
    response_latency = 1
    mshrs = 12
    tgts_per_mshr = 16
    prefetcher = StridePrefetcher(degree=4)

class L1DCache(Cache):
    size = '256KiB'
    assoc = 4
    tag_latency = 1
    data_latency = 1
    response_latency = 1
    mshrs = 12
    tgts_per_mshr = 16
    prefetcher = StridePrefetcher(degree=4)

class L2Cache(Cache):
    size = '2MiB'
    assoc = 16
    tag_latency = 8
    data_latency = 8
    response_latency = 8
    mshrs = 32
    tgts_per_mshr = 20
    prefetcher = StridePrefetcher(degree=8)

# === System Setup ===
system = System()
system.clk_domain = SrcClockDomain(clock='2GHz', voltage_domain=VoltageDomain(voltage='1.0V'))
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('2GiB')]
system.membus = SystemXBar(width=64)

# === CPU Configuration ===
system.cpu = [DerivO3CPU() for _ in range(4)]
for cpu in system.cpu:
    # Pipeline widths
    cpu.fetchWidth = 4
    cpu.decodeWidth = 4
    cpu.renameWidth = 4
    cpu.dispatchWidth = 4
    cpu.issueWidth = 4
    cpu.wbWidth = 4
    cpu.commitWidth = 4

    # Pipeline latencies
    cpu.fetchToDecodeDelay = 2
    cpu.decodeToRenameDelay = 1
    cpu.renameToIEWDelay = 3
    cpu.iewToCommitDelay = 2

    # Buffer and queue sizes
    cpu.fetchBufferSize = 32
    cpu.numROBEntries = 128
    cpu.LQEntries = 32
    cpu.SQEntries = 32

    # Branch predictor
    cpu.branchPred = TAGE()

    # Use default FU pool to avoid NameError
    cpu.fuPool = DefaultFUPool()

    cpu.numThreads = 1
    cpu.clk_domain = SrcClockDomain(clock='2GHz', voltage_domain=VoltageDomain(voltage='1.0V'))
    cpu.mmu = X86MMU()
    cpu.mmu.itb.size = 128
    cpu.mmu.dtb.size = 128

    # Interrupt controller
    cpu.createInterruptController()
    cpu.interrupts[0].pio = system.membus.mem_side_ports
    cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
    cpu.interrupts[0].int_responder = system.membus.mem_side_ports

    # Attach caches
    cpu.icache = L1ICache()
    cpu.dcache = L1DCache()
    cpu.icache.cpu_side = cpu.icache_port
    cpu.dcache.cpu_side = cpu.dcache_port

# L2 bus and cache
system.l2bus = L2XBar(width=64)
for cpu in system.cpu:
    cpu.icache.mem_side = system.l2bus.cpu_side_ports
    cpu.dcache.mem_side = system.l2bus.cpu_side_ports
system.l2cache = L2Cache()
system.l2cache.cpu_side = system.l2bus.mem_side_ports
system.l2cache.mem_side = system.membus.cpu_side_ports

# Memory controller
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR4_2400_16x4()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.dram.burst_length = 8
system.mem_ctrl.port = system.membus.mem_side_ports

# === Workload ===
system.workload = SEWorkload.init_compatible(binary_path)
process = Process()
process.cmd = [binary_path]
for cpu in system.cpu:
    cpu.workload = process
    cpu.createThreads()

# === Run Simulation ===
root = Root(full_system=False, system=system)

# Enable debugging if requested
if args.debug:
    m5.options.debug_flags = ['Fetch', 'Decode', 'Exec']
    print("Debugging enabled with flags: Fetch, Decode, Exec")

m5.instantiate()

print(f"Starting simulation with {binary_path}...")
exit_event = m5.simulate(1000000000)
print(f"Simulation ended: {exit_event.getCause()} at tick {m5.curTick()}")

# === Stats Management ===
m5.stats.dump()
default_stats = "m5out/stats.txt"
custom_folder = args.stats_dir
custom_stats = os.path.join(custom_folder, "stats.txt")
os.makedirs(custom_folder, exist_ok=True)
if os.path.exists(default_stats):
    shutil.move(default_stats, custom_stats)
    print(f"Stats saved to: {custom_stats}")
else:
    print("Warning: stats.txt not found in m5out!")
