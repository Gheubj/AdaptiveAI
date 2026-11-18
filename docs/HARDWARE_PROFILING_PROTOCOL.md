# Hardware Profiling Protocol

Host: AMD Ryzen 5 PRO 6650U, 6 physical/12 logical cores, 14.4 GiB RAM, Linux 7.0.0-31,
x86-64, integrated AMD GPU not used. Runtime: llama.cpp commit
`a300a9c33462f23d9d61e951650d249486f2b0f6`, native CPU/OpenMP, six inference threads,
context 2,048, temperature 0, seed 3407, concurrency one unless stated.

Cold-process means a newly started `llama-server` with an ordinary OS page cache; it is not a cold
disk-cache claim. Three process starts and ten warm repetitions per short/medium/long workload were
run. Warmup preceded timed warm requests. Streaming measured first content token, total latency,
token counts, decode throughput, child RSS, and available system RAM. Model switching is stop/start
and therefore includes the next model's load time. Concurrency one and two were observed in three
blocks. Energy is N/A: no readable `energy_uj` counter was exposed, so CPU utilization was not
misrepresented as energy.
