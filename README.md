# Create a Python script to get and print the `status code` of the response of a list of URLs from a `.csv` file.

The script reads a list of URLs from a `.csv` file, queries each one, and prints the HTTP
status code alongside the URL.

## Some Design Decisions

- `HEAD` returns just the status line and headers, which I think is sufficient for this task. I am aware some Some servers return `405 Method Not Allowed` for HEAD requests, so the script retries with GET in that case.

- I assumed the CSV could contain blank rows, placeholder text, or malformed entries. I used `urlparse` to validate the urls before they hit the network.

- A fresh TCP connection per URL is the naive approach. Looking at the CSV, several URLs share the same root domain, reusing the underlying socket cuts overhead on those. `threading.local()` gives each worker its own session

- Most of the time is spent waiting on server responses. Running 10 requests concurrently means a slow server on one thread doesn't stall the others.

- `as_completed()` returns results in completion order, not submission order. Allocating `results = [None] * len(urls)` and writing each result to its original index preserves the input file's ordering in the output. Not sure this is necessary, but I want to keep the order.

- `ConnectionError`, `Timeout`, and the base `RequestException` are caught separately. A timeout and a DNS failure are different problems, that is why lumping them into a single "ERROR" string loses that information.

- The input file defaults to the constant at the top of the script but can be overridden, which is useful if you want to run it against a different list without editing the source. Again, not sure it is important, but just an edge case I thought of.

## Here is the output of the script:

![alt screenshot of the output of the script](output.png)
