def find_average_time_sjf(processes):
    n = len(processes)
    processes_sorted = sorted(processes, key=lambda x: x[1])
    waiting_time = [0] * n
    turnaround_time = [0] * n
    completion_time = processes_sorted[0][1]
    turnaround_time[0] = completion_time

    for i in range(1, n):
        waiting_time[i] = completion_time
        completion_time += processes_sorted[i][1]
        turnaround_time[i] = completion_time

    total_waiting_time = sum(waiting_time)
    total_turnaround_time = sum(turnaround_time)

    results = []
    for i in range(n):
        results.append({
            'id': processes_sorted[i][0],
            'burstTime': processes_sorted[i][1],
            'waitingTime': waiting_time[i],
            'turnaroundTime': turnaround_time[i]
        })

    return results, total_waiting_time / n, total_turnaround_time / n

# Example usage
if __name__ == "__main__":
    process_list = [('P1', 6), ('P2', 8), ('P3', 7), ('P4', 3)]
    results, avg_waiting_time, avg_turnaround_time = find_average_time_sjf(process_list)
    print("Results:", results)
    print("Average Waiting Time:", avg_waiting_time)
    print("Average Turnaround Time:", avg_turnaround_time)