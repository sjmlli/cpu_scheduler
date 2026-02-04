def find_average_time_fcfs(processes):
    n = len(processes)
    waiting_time = [0] * n
    turnaround_time = [0] * n
    completion_time = processes[0][1]
    turnaround_time[0] = completion_time

    for i in range(1, n):
        waiting_time[i] = completion_time
        completion_time += processes[i][1]
        turnaround_time[i] = completion_time

    total_waiting_time = sum(waiting_time)
    total_turnaround_time = sum(turnaround_time)

    return {
        "waiting_time": waiting_time,
        "turnaround_time": turnaround_time,
        "average_waiting_time": total_waiting_time / n,
        "average_turnaround_time": total_turnaround_time / n,
    }