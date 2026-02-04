def find_average_time_priority(processes):
    n = len(processes)
    processes_sorted = sorted(processes, key=lambda x: x[2])
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

    result = []
    for i in range(n):
        result.append({
            'id': processes_sorted[i][0],
            'burstTime': processes_sorted[i][1],
            'priority': processes_sorted[i][2],
            'waitingTime': waiting_time[i],
            'turnaroundTime': turnaround_time[i]
        })

    return result, total_waiting_time / n, total_turnaround_time / n

# Example usage
if __name__ == "__main__":
    process_list = [('P1', 10, 3), ('P2', 1, 1), ('P3', 2, 4), ('P4', 1, 5), ('P5', 5, 2)]
    results, avg_waiting_time, avg_turnaround_time = find_average_time_priority(process_list)
    print("Results:", results)
    print(f"Average Waiting Time: {avg_waiting_time:.2f}")
    print(f"Average Turnaround Time: {avg_turnaround_time:.2f}")