def calculate_waiting_time(processes):
    waiting_time = [0] * len(processes)
    for i in range(1, len(processes)):
        waiting_time[i] = waiting_time[i - 1] + processes[i - 1][1]
    return waiting_time

def calculate_turnaround_time(processes, waiting_time):
    turnaround_time = [0] * len(processes)
    for i in range(len(processes)):
        turnaround_time[i] = processes[i][1] + waiting_time[i]
    return turnaround_time

def format_process_output(processes, waiting_time, turnaround_time):
    output = []
    for i in range(len(processes)):
        output.append({
            'id': processes[i][0],
            'burstTime': processes[i][1],
            'waitingTime': waiting_time[i],
            'turnaroundTime': turnaround_time[i]
        })
    return output