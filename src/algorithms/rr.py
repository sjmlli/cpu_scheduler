def find_average_time_rr(processes, quantum):
    n = len(processes)
    remaining_time = [p[1] for p in processes]
    waiting_time = [0] * n
    turnaround_time = [0] * n
    current_time = 0

    while True:
        done = True
        for i in range(n):
            if remaining_time[i] > 0:
                done = False
                if remaining_time[i] > quantum:
                    current_time += quantum
                    remaining_time[i] -= quantum
                else:
                    current_time += remaining_time[i]
                    waiting_time[i] = current_time - processes[i][1]
                    remaining_time[i] = 0

        if done:
            break

    for i in range(n):
        turnaround_time[i] = processes[i][1] + waiting_time[i]

    return waiting_time, turnaround_time

# Example usage
if __name__ == "__main__":
    process_list = [('P1', 24), ('P2', 3), ('P3', 3)]
    quantum = 4
    waiting_time, turnaround_time = find_average_time_rr(process_list, quantum)
    print("Process ID\tBurst Time\tWaiting Time\tTurnaround Time")
    for i in range(len(process_list)):
        print(f"{process_list[i][0]}\t\t{process_list[i][1]}\t\t{waiting_time[i]}\t\t{turnaround_time[i]}")