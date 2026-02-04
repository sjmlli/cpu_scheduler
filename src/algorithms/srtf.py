def find_average_time_srtf(processes, arrival_time):
    n = len(processes)
    remaining_time = [p[1] for p in processes]
    waiting_time = [0] * n
    turnaround_time = [0] * n
    completion_time = [0] * n
    complete = 0
    current_time = 0

    while complete != n:
        shortest = -1
        min_burst = float('inf')
        for i in range(n):
            if remaining_time[i] < min_burst and remaining_time[i] > 0:
                min_burst = remaining_time[i]
                shortest = i

        if shortest == -1:
            current_time += 1
            continue

        remaining_time[shortest] -= 1
        current_time += 1

        if remaining_time[shortest] == 0:
            complete += 1
            finish_time = current_time
            completion_time[shortest] = finish_time
            waiting_time[shortest] = finish_time - processes[shortest][1]
            turnaround_time[shortest] = finish_time

    return waiting_time, turnaround_time

def srtf_scheduling_example():
    process_list = [('P1', 8), ('P2', 4), ('P3', 9), ('P4', 5)]
    arrival_time = [0, 1, 2, 3]
    waiting_time, turnaround_time = find_average_time_srtf(process_list, arrival_time)

    print("Process ID\tBurst Time\tWaiting Time\tTurnaround Time")
    for i in range(len(process_list)):
        print(f"{process_list[i][0]}\t\t{process_list[i][1]}\t\t{waiting_time[i]}\t\t{turnaround_time[i]}")

srtf_scheduling_example()