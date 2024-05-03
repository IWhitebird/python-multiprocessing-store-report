# Key Points
- Background Task Running on Separate Process, without blocking the main process
- Takes around 53 to 55 seconds to generate a report (PC Specs: 6 Core 12 Thread CPU Intel, 16GB RAM) with Postgres running on Docker and using 8 CPUs in multithreading
- Entire Data is Relationally Mapped
- Around 28-30ish DB calls when using 8 CPUs and 1 minute 40 seconds with 1 CPU
- Check Performance CSV for more info

# Algorithm for Calculating Time
- Get the request, make the report, and send it as a response
- Add a background task on a new process and join (wait for the process to end) on the background thread
- Assuming a timestamp around "2023-01-22 12:00:00.000000" as I found most data lying around that range. If I use the current time, all reports give 0.
- Get all stores
- Send store chunks to the process (using 500)
- Get all relevant data about those 500 stores
- Convert data into a map with store_id as the key
- Iterate over every store
    - Convert every store time (Monday to Sunday) to relevant UTC using the assumed earlier timestamp
    - Now you will get a map named "day_wise_start_end_time" that will contain *Day -> start_utc, end_utc*
    - Call the function "FinalResult" providing hours (1, 24, 7 * 24)
    - This will return the result, store it in a local CSV file
- FinalResult Function
    - Using the timestamp and loop, find the days that we need to check and add their start_time and end_time in a separate array
    - Sort the poll status
    - Now we have polls sorted and start_time and end_time from the separate array made earlier. Loop over the array
        - Here we assume that polls are roughly every hour, so a poll at time 'x' is relevant for 'x - 30 min' and 'x + 30 min'
        - Check the polls' start and end time, and add uptime and downtime respectively. Also, if we add uptime/downtime at time 'x', the start_time will be moved, allowing us to make fewer mistakes of overlapping hours
- Write the returned result in the CSV
- End of function: add that CSV to the report, mark it as successful, and commit it to the database
