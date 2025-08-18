import requests
import time

url = "http://3.90.236.235:3018/tasks/"
numberOfRequests = 500

totalTime = 0

def time_ms():
    return round(time.time() * 1000)

for i in range(numberOfRequests):
    startTime = time_ms()
    response = requests.get(url)
    request_time = time_ms() - startTime
    totalTime += request_time

    print(f'Request {i + 1} returned with status: {response.status_code} in {request_time}ms')

print(f'Average time {totalTime / numberOfRequests}')