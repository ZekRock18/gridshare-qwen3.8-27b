# Testing

[Wiki home](Home.md)

## GridShare Test Console

Select the existing `qwen38-27b-q3` endpoint. Paste the inner JSON only; the console adds the `input` wrapper:

```json
{
  "prompt": "In two sentences, explain what a GPU does.",
  "max_tokens": 96,
  "temperature": 0.7,
  "enable_thinking": false
}
```

This input is also saved in [test-input.json](../../test-input.json). The completed answer is preserved in the [API snapshot](../../logs/2026-10-26/gridshare-snapshot.json).

## Cold-start API test

The initial test took approximately 460 seconds end to end, exceeding the console's 300-second synchronous wait. For a cold start, use the asynchronous API. Supply your GridShare key locally through `GRIDSHARE_TOKEN`; do not commit it or substitute a GitHub token.

Run PowerShell from the repository root:

```powershell
$headers = @{Authorization = "Bearer $env:GRIDSHARE_TOKEN"}
$endpointId = '737cd73f-2425-46d1-978c-3df43f1de62c'
$body = @{input = (Get-Content test-input.json -Raw | ConvertFrom-Json)} | ConvertTo-Json -Depth 10
$job = Invoke-RestMethod "https://gridshare.in/v1/serverless/$endpointId/run-async" -Method Post -Headers $headers -ContentType 'application/json' -Body $body
do {
    Start-Sleep -Seconds 10
    $result = Invoke-RestMethod "https://gridshare.in/v1/serverless/requests/$($job.request_id)" -Headers $headers
    $result | ConvertTo-Json -Depth 20
} while ($result.status -in @('queued', 'pending', 'running', 'processing'))
```

Poll the same request instead of submitting duplicates during startup. A console timeout alone does not prove that the underlying request stopped.

## Local HTTP contract tests

```powershell
python -m pip install -r requirements.txt httpx==0.28.1
python -m unittest discover -s tests -v
```

The five tests cover readiness, a crashed model process, request-envelope forwarding, invalid inputs, and inference-server timeout handling. They mock inference and do not measure GPU performance.

## Completed live test

Request ID: `6e51190f-82e6-4cf2-9c0e-d290e8973099`.

Queued: `2026-10-26T08:14:05.772730+00:00`. Completed: `2026-10-26T08:21:46.050520+00:00`. Status: `completed`, empty error, finish reason `stop`.
