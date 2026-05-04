"""
╔══════════════════════════════════════════════════════════╗
║          CPU SCHEDULING SIMULATOR                        ║
║          Operating Systems — BCA PBL Project             ║
║          Language: Python 3                              ║
╚══════════════════════════════════════════════════════════╝

Algorithms Implemented:
  1. FCFS  — First Come First Serve
  2. SJF   — Shortest Job First (Non-Preemptive)
  3. SRTF  — Shortest Remaining Time First (Preemptive SJF)
  4. RR    — Round Robin (configurable quantum)
  5. PRIO  — Priority Scheduling (Non-Preemptive)

Dependencies:
  pip install matplotlib tabulate
"""

import sys
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from tabulate import tabulate


# ══════════════════════════════════════════════════════════
#  SECTION 1: INPUT HANDLING
#  All user input is collected here with full validation.
# ══════════════════════════════════════════════════════════

def get_integer(prompt, min_val=None, max_val=None):
    """
    Read a validated integer from the user.
    Keeps asking until a valid value is entered.
    """
    while True:
        try:
            value = int(input(prompt))
            if min_val is not None and value < min_val:
                print(f"  [!] Value must be >= {min_val}. Try again.")
                continue
            if max_val is not None and value > max_val:
                print(f"  [!] Value must be <= {max_val}. Try again.")
                continue
            return value
        except ValueError:
            print("  [!] Invalid input. Please enter a whole number.")


def get_processes(need_priority=False):
    """
    Collect process data from the user.
    Each process has: PID, Arrival Time, Burst Time, (optional) Priority.

    Parameters:
        need_priority (bool): If True, also ask for priority value.

    Returns:
        list of dict: Each dict represents one process.
    """
    n = get_integer("\n  How many processes? ", min_val=1, max_val=20)
    processes = []

    print()
    for i in range(1, n + 1):
        print(f"  ── Process P{i} ──")
        at = get_integer(f"    Arrival Time  : ", min_val=0)
        bt = get_integer(f"    Burst Time    : ", min_val=1)
        priority = 0
        if need_priority:
            priority = get_integer(f"    Priority (1=highest, larger=lower): ", min_val=1)
        print()

        processes.append({
            'pid'     : f'P{i}',
            'at'      : at,
            'bt'      : bt,
            'priority': priority
        })

    return processes


def get_time_quantum():
    """Ask user for Round Robin time quantum."""
    return get_integer("  Time Quantum   : ", min_val=1)


# ══════════════════════════════════════════════════════════
#  SECTION 2: SCHEDULING ALGORITHMS
#  Each function returns:
#    results  — list of dicts (one per process) with CT, TAT, WT
#    timeline — list of tuples (pid, start_time, end_time) for Gantt chart
# ══════════════════════════════════════════════════════════

def fcfs(processes):
    """
    First Come First Serve (Non-Preemptive).

    Strategy: Execute processes in order of arrival.
    If two arrive at the same time, go by PID order.
    CPU sits idle if no process has arrived yet.

    Time Complexity: O(n log n) due to sorting.
    """
    # Sort by arrival time; use pid as tiebreaker
    procs = sorted(processes, key=lambda p: (p['at'], p['pid']))

    timeline = []   # Gantt chart segments
    results  = []   # Final metrics
    time     = 0    # Current clock time

    for p in procs:
        # If CPU is free before this process arrives → idle gap
        if time < p['at']:
            timeline.append(('IDLE', time, p['at']))
            time = p['at']

        start  = time
        time  += p['bt']          # Process runs to completion
        ct     = time             # Completion time
        tat    = ct  - p['at']   # Turnaround = Completion - Arrival
        wt     = tat - p['bt']   # Waiting    = Turnaround - Burst

        timeline.append((p['pid'], start, time))
        results.append({**p, 'ct': ct, 'tat': tat, 'wt': wt})

    return results, timeline


def sjf_non_preemptive(processes):
    """
    Shortest Job First — Non-Preemptive (SJF).

    Strategy: Among all arrived processes, pick the one with smallest
    burst time. Once chosen, runs to completion without interruption.

    Time Complexity: O(n²) — one scan per process.
    """
    remaining = [p.copy() for p in processes]
    timeline  = []
    results   = []
    time      = 0

    while remaining:
        # All processes that have arrived by 'time'
        available = [p for p in remaining if p['at'] <= time]

        if not available:
            # No process ready → jump to next arrival
            next_arrival = min(p['at'] for p in remaining)
            timeline.append(('IDLE', time, next_arrival))
            time = next_arrival
            continue

        # Pick shortest burst; arrival time as secondary sort (FCFS for equal BT)
        chosen = min(available, key=lambda p: (p['bt'], p['at']))
        remaining.remove(chosen)

        start  = time
        time  += chosen['bt']
        ct     = time
        tat    = ct  - chosen['at']
        wt     = tat - chosen['bt']

        timeline.append((chosen['pid'], start, time))
        results.append({**chosen, 'ct': ct, 'tat': tat, 'wt': wt})

    return results, timeline


def sjf_preemptive(processes):
    """
    Shortest Remaining Time First — Preemptive SJF (SRTF).

    Strategy: At every time unit, pick the process with the
    least remaining burst time. Can preempt a running process
    if a shorter one arrives.

    Time Complexity: O(n * max_time) — simulates unit by unit.
    """
    procs = [p.copy() for p in processes]
    for p in procs:
        p['remaining'] = p['bt']   # Track remaining burst time

    timeline      = []
    results       = []
    time          = 0
    done_count    = 0
    n             = len(procs)
    current       = None    # Currently running process
    current_start = 0       # When current process segment started

    while done_count < n:
        # All arrived and not yet finished
        available = [p for p in procs if p['at'] <= time and p['remaining'] > 0]

        if not available:
            # CPU idle — jump ahead
            if current:
                timeline.append((current['pid'], current_start, time))
                current = None
            next_at = min(p['at'] for p in procs if p['remaining'] > 0)
            timeline.append(('IDLE', time, next_at))
            time = next_at
            continue

        # Pick process with shortest remaining time
        shortest = min(available, key=lambda p: (p['remaining'], p['at']))

        # If a different process takes over, save the old segment
        if current is not shortest:
            if current is not None:
                timeline.append((current['pid'], current_start, time))
            current       = shortest
            current_start = time

        # Execute for 1 unit
        shortest['remaining'] -= 1
        time += 1

        # Check if process just finished
        if shortest['remaining'] == 0:
            timeline.append((current['pid'], current_start, time))
            current = None
            ct  = time
            tat = ct  - shortest['at']
            wt  = tat - shortest['bt']
            results.append({**shortest, 'ct': ct, 'tat': tat, 'wt': wt})
            done_count += 1

    # Merge consecutive segments of the same process for a cleaner Gantt chart
    merged = []
    for seg in timeline:
        if merged and merged[-1][0] == seg[0] and merged[-1][2] == seg[1]:
            merged[-1] = (seg[0], merged[-1][1], seg[2])  # Extend segment
        else:
            merged.append(seg)

    return results, merged


def round_robin(processes, quantum):
    """
    Round Robin Scheduling.

    Strategy: Each process gets a fixed time slice (quantum).
    If not finished, it goes to the back of the ready queue.
    New arrivals during a time slice are added after current running process.

    Time Complexity: O(n * ceil(bt/quantum)) in the worst case.

    Parameters:
        quantum (int): Maximum CPU time per turn per process.
    """
    # Work on copies to avoid mutating original data
    procs = sorted([p.copy() for p in processes], key=lambda p: p['at'])
    for p in procs:
        p['remaining'] = p['bt']

    timeline      = []
    results       = []
    time          = 0
    done_count    = 0
    n             = len(procs)
    ready_queue   = []
    arrival_idx   = 0   # Pointer into sorted procs list

    # Load processes that arrive at time 0
    while arrival_idx < n and procs[arrival_idx]['at'] <= time:
        ready_queue.append(procs[arrival_idx])
        arrival_idx += 1

    while done_count < n:
        if not ready_queue:
            # CPU idle — skip to next arrival
            next_at = procs[arrival_idx]['at']
            timeline.append(('IDLE', time, next_at))
            time = next_at
            while arrival_idx < n and procs[arrival_idx]['at'] <= time:
                ready_queue.append(procs[arrival_idx])
                arrival_idx += 1
            continue

        p         = ready_queue.pop(0)
        exec_time = min(quantum, p['remaining'])  # Can't run longer than remaining
        start     = time
        time     += exec_time
        p['remaining'] -= exec_time

        timeline.append((p['pid'], start, time))

        # Add any processes that arrived during this time slice (before re-queuing current)
        while arrival_idx < n and procs[arrival_idx]['at'] <= time:
            ready_queue.append(procs[arrival_idx])
            arrival_idx += 1

        if p['remaining'] == 0:
            # Process completed
            ct  = time
            tat = ct  - p['at']
            wt  = tat - p['bt']
            results.append({**p, 'ct': ct, 'tat': tat, 'wt': wt})
            done_count += 1
        else:
            # Not finished — go to back of queue
            ready_queue.append(p)

    return results, timeline


def priority_non_preemptive(processes):
    """
    Priority Scheduling — Non-Preemptive.

    Strategy: Among all arrived processes, pick the one with highest
    priority (lowest priority number = highest priority).
    Once chosen, runs to completion.

    Tie-breaking: If equal priority, use FCFS (arrival time).

    Time Complexity: O(n²) — one scan per process.
    """
    remaining = [p.copy() for p in processes]
    timeline  = []
    results   = []
    time      = 0

    while remaining:
        available = [p for p in remaining if p['at'] <= time]

        if not available:
            next_at = min(p['at'] for p in remaining)
            timeline.append(('IDLE', time, next_at))
            time = next_at
            continue

        # Lower priority number = higher priority; arrival time breaks ties
        chosen = min(available, key=lambda p: (p['priority'], p['at']))
        remaining.remove(chosen)

        start  = time
        time  += chosen['bt']
        ct     = time
        tat    = ct  - chosen['at']
        wt     = tat - chosen['bt']

        timeline.append((chosen['pid'], start, time))
        results.append({**chosen, 'ct': ct, 'tat': tat, 'wt': wt})

    return results, timeline


# ══════════════════════════════════════════════════════════
#  SECTION 3: OUTPUT & DISPLAY FUNCTIONS
# ══════════════════════════════════════════════════════════

# Visual color palette for Gantt chart bars
COLORS = [
    '#3A86FF', '#FF006E', '#FB5607', '#8338EC',
    '#06D6A0', '#FFB703', '#E63946', '#2EC4B6',
    '#F77F00', '#4361EE'
]


def get_metrics(results):
    """Compute average TAT and WT from results list."""
    n       = len(results)
    avg_tat = sum(r['tat'] for r in results) / n
    avg_wt  = sum(r['wt']  for r in results) / n
    return round(avg_tat, 2), round(avg_wt, 2)


def print_results_table(results, algo_name):
    """
    Print a formatted table of scheduling results.
    Columns: Process | AT | BT | CT | TAT | WT
    Also prints Average TAT and Average WT below the table.

    Returns:
        (avg_tat, avg_wt) as a tuple of floats.
    """
    print(f"\n{'─' * 58}")
    print(f"  📊  {algo_name}")
    print(f"{'─' * 58}")

    # Sort by PID for consistent display order
    sorted_results = sorted(results, key=lambda r: r['pid'])

    headers = ["Process", "Arrival", "Burst", "Completion", "Turnaround", "Waiting"]
    rows = [
        [r['pid'], r['at'], r['bt'], r['ct'], r['tat'], r['wt']]
        for r in sorted_results
    ]

    print(tabulate(rows, headers=headers, tablefmt="grid"))

    avg_tat, avg_wt = get_metrics(results)
    print(f"\n  ➤  Average Turnaround Time (TAT) : {avg_tat}")
    print(f"  ➤  Average Waiting Time (WT)      : {avg_wt}")
    print(f"{'─' * 58}")

    return avg_tat, avg_wt


def draw_gantt_chart(timeline, title):
    """
    Draw a horizontal Gantt chart using matplotlib.

    Each process gets a distinct color bar.
    IDLE time is shown in light gray.
    Time markers are placed at each event boundary.

    Parameters:
        timeline (list of tuples): (pid, start, end)
        title    (str)           : Chart title (algorithm name)
    """
    fig, ax = plt.subplots(figsize=(max(10, len(timeline) * 1.4), 3.5))
    fig.patch.set_facecolor('#1e1e2e')
    ax.set_facecolor('#1e1e2e')

    pid_color_map = {}
    color_idx     = 0

    for (pid, start, end) in timeline:
        if pid == 'IDLE':
            color     = '#4a4a6a'
            text_col  = '#aaaaaa'
            label_txt = 'IDLE'
        else:
            if pid not in pid_color_map:
                pid_color_map[pid] = COLORS[color_idx % len(COLORS)]
                color_idx += 1
            color     = pid_color_map[pid]
            text_col  = 'white'
            label_txt = pid

        width = end - start
        ax.barh(0, width, left=start, height=0.55,
                align='center', color=color,
                edgecolor='#2a2a3e', linewidth=1.5)

        # Only label if block is wide enough to fit text
        if width > 0:
            ax.text((start + end) / 2, 0, label_txt,
                    ha='center', va='center',
                    fontsize=9, fontweight='bold', color=text_col)

    # Time axis ticks — one tick per event boundary
    all_times = sorted(set(t for _, s, e in timeline for t in [s, e]))
    ax.set_xticks(all_times)
    ax.set_xticklabels([str(t) for t in all_times], color='white', fontsize=8)

    ax.set_xlim(timeline[0][1] - 0.1, timeline[-1][2] + 0.1)
    ax.set_yticks([])
    ax.tick_params(colors='white')
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#555577')

    ax.set_xlabel("Time  →", color='white', fontsize=10, labelpad=6)
    ax.set_title(f"Gantt Chart  —  {title}",
                 color='white', fontsize=12, fontweight='bold', pad=12)

    # Legend for processes (not IDLE)
    patches = [
        mpatches.Patch(color=c, label=pid)
        for pid, c in pid_color_map.items()
    ]
    if any(pid == 'IDLE' for pid, _, _ in timeline):
        patches.append(mpatches.Patch(color='#4a4a6a', label='IDLE'))

    ax.legend(handles=patches, loc='upper right',
              fontsize=8, facecolor='#2a2a3e',
              labelcolor='white', edgecolor='#555577')

    plt.tight_layout()
    plt.show()


def print_comparison_table(summary):
    """
    Print a side-by-side comparison of all algorithms.
    Highlights the best algorithm based on lowest Average WT.

    Parameters:
        summary (list of tuples): (algo_name, avg_tat, avg_wt)
    """
    print(f"\n{'═' * 62}")
    print("   📋  ALGORITHM COMPARISON SUMMARY")
    print(f"{'═' * 62}")

    headers = ["#", "Algorithm", "Avg TAT", "Avg WT"]
    rows    = [
        [i + 1, name, f"{tat:.2f}", f"{wt:.2f}"]
        for i, (name, tat, wt) in enumerate(summary)
    ]

    print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))

    best_algo = min(summary, key=lambda x: x[2])
    print(f"\n  ★  Best Algorithm (Lowest Avg WT) : {best_algo[0]}")
    print(f"     Avg WT = {best_algo[2]:.2f}   |   Avg TAT = {best_algo[1]:.2f}")
    print(f"\n  NOTE: Lowest Avg WT = less time processes spend waiting.")
    print(f"        This generally indicates better CPU utilization.")
    print(f"{'═' * 62}\n")


# ══════════════════════════════════════════════════════════
#  SECTION 4: ALGORITHM RUNNERS
#  These functions wire together: input → algorithm → output.
# ══════════════════════════════════════════════════════════

def run_single_algorithm(choice):
    """
    Run one selected algorithm end-to-end.
    Collects input, runs algorithm, prints table and Gantt chart.

    Returns:
        tuple: (algo_name, avg_tat, avg_wt) for optional comparison use.
    """
    need_priority = (choice == 5)
    processes     = get_processes(need_priority=need_priority)

    if choice == 1:
        results, timeline = fcfs(processes)
        name = "FCFS — First Come First Serve"

    elif choice == 2:
        results, timeline = sjf_non_preemptive(processes)
        name = "SJF — Shortest Job First (Non-Preemptive)"

    elif choice == 3:
        results, timeline = sjf_preemptive(processes)
        name = "SRTF — Shortest Remaining Time First (Preemptive)"

    elif choice == 4:
        print()
        quantum           = get_time_quantum()
        results, timeline = round_robin(processes, quantum)
        name              = f"Round Robin (Time Quantum = {quantum})"

    elif choice == 5:
        results, timeline = priority_non_preemptive(processes)
        name = "Priority Scheduling (Non-Preemptive)"

    else:
        print("  [!] Invalid choice.")
        return None

    avg_tat, avg_wt = print_results_table(results, name)
    draw_gantt_chart(timeline, name)

    return (name, avg_tat, avg_wt)


def run_comparison_mode():
    """
    Run ALL algorithms on the same set of processes.
    Generates individual Gantt charts + tables, then
    displays a final side-by-side comparison table.
    """
    print("\n" + "═" * 62)
    print("   🔬  COMPARISON MODE — All Algorithms")
    print("   All algorithms will use the SAME process set.")
    print("   Priority values are needed for Priority Scheduling.")
    print("═" * 62)

    processes = get_processes(need_priority=True)

    print()
    quantum = get_time_quantum()

    summary = []

    algorithms = [
        ("FCFS",                       lambda: fcfs(processes)),
        ("SJF (Non-Preemptive)",       lambda: sjf_non_preemptive(processes)),
        ("SRTF (Preemptive SJF)",      lambda: sjf_preemptive(processes)),
        (f"Round Robin (Q={quantum})", lambda: round_robin(processes, quantum)),
        ("Priority (Non-Preemptive)",  lambda: priority_non_preemptive(processes)),
    ]

    for name, algo_func in algorithms:
        results, timeline = algo_func()
        avg_tat, avg_wt   = print_results_table(results, name)
        draw_gantt_chart(timeline, name)
        summary.append((name, avg_tat, avg_wt))

    print_comparison_table(summary)


# ══════════════════════════════════════════════════════════
#  SECTION 5: MAIN MENU
# ══════════════════════════════════════════════════════════

MENU = """
  ┌──────────────────────────────────────────────┐
  │          SELECT AN ALGORITHM                 │
  ├──────────────────────────────────────────────┤
  │   1.  FCFS   — First Come First Serve        │
  │   2.  SJF    — Shortest Job First (NP)       │
  │   3.  SRTF   — Preemptive SJF               │
  │   4.  RR     — Round Robin                  │
  │   5.  PRIO   — Priority Scheduling (NP)      │
  │   6.  ⚡     — Compare ALL Algorithms        │
  │   0.  Exit                                   │
  └──────────────────────────────────────────────┘"""

BANNER = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          CPU SCHEDULING SIMULATOR                        ║
║          Operating Systems — BCA PBL Project             ║
║                                                          ║
║  Algorithms: FCFS | SJF | SRTF | Round Robin | Priority  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""


def main():
    """Entry point. Shows banner and runs the menu loop."""
    print(BANNER)

    while True:
        print(MENU)
        choice = get_integer("  Your choice: ", min_val=0, max_val=6)

        if choice == 0:
            print("\n  👋  Exiting simulator. Goodbye!\n")
            sys.exit(0)

        elif 1 <= choice <= 5:
            run_single_algorithm(choice)

        elif choice == 6:
            run_comparison_mode()

        input("\n  [Press ENTER to return to menu...]")


def draw_gantt_chart(timeline, title):
    fig, ax = plt.subplots(figsize=(10, 2))

    for pid, start, end in timeline:
        ax.barh(0, end - start, left=start)
        ax.text((start + end) / 2, 0, pid, ha='center', va='center')

    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_yticks([])

    return fig 