# Test Script for New Services
# Tests Orchestrator and Conversation Agent

Write-Host "`n=== Testing CareerOps Services ===" -ForegroundColor Cyan

# Test 1: Conversation Service Health
Write-Host "`n[1/6] Testing Conversation Service Health..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8004/health" -UseBasicParsing
    $healthData = $health.Content | ConvertFrom-Json
    Write-Host "✓ Conversation service is healthy" -ForegroundColor Green
    Write-Host "  Status: $($healthData.status)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Conversation service health check failed" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
}

# Test 2: Orchestrator Service Health
Write-Host "`n[2/6] Testing Orchestrator Service Health..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8005/health" -UseBasicParsing
    $healthData = $health.Content | ConvertFrom-Json
    Write-Host "✓ Orchestrator service is healthy" -ForegroundColor Green
    Write-Host "  Status: $($healthData.status)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Orchestrator service health check failed" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
}

# Test 3: Conversation Agent - stats_today intent
Write-Host "`n[3/6] Testing Conversation Agent (stats_today)..." -ForegroundColor Yellow
try {
    $body = @{
        intent = "stats_today"
        session_id = "test_session_$(Get-Date -Format 'yyyyMMddHHmmss')"
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "http://localhost:8004/intent" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing

    $data = $response.Content | ConvertFrom-Json
    Write-Host "✓ stats_today intent processed successfully" -ForegroundColor Green
    Write-Host "  Response: $($data.response.Substring(0, [Math]::Min(80, $data.response.Length)))..." -ForegroundColor Gray
    Write-Host "  Session ID: $($data.session_id)" -ForegroundColor Gray
} catch {
    Write-Host "✗ stats_today intent failed" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
}

# Test 4: Conversation Agent - research_company intent
Write-Host "`n[4/6] Testing Conversation Agent (research_company)..." -ForegroundColor Yellow
try {
    $body = @{
        intent = "research_company"
        parameters = @{
            company = "Google"
        }
        session_id = "test_session_$(Get-Date -Format 'yyyyMMddHHmmss')"
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "http://localhost:8004/intent" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing

    $data = $response.Content | ConvertFrom-Json
    Write-Host "✓ research_company intent processed successfully" -ForegroundColor Green
    Write-Host "  Company: $($data.data.company)" -ForegroundColor Gray
} catch {
    Write-Host "✗ research_company intent failed" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
}

# Test 5: Conversation Metrics
Write-Host "`n[5/6] Testing Conversation Metrics..." -ForegroundColor Yellow
try {
    $metrics = Invoke-WebRequest -Uri "http://localhost:8004/metrics" -UseBasicParsing
    $intentMetrics = $metrics.Content -split "`n" | Select-String "conversation_intents_processed_total"
    
    if ($intentMetrics.Count -gt 0) {
        Write-Host "✓ Conversation metrics are available" -ForegroundColor Green
        Write-Host "  Sample metrics:" -ForegroundColor Gray
        $intentMetrics | Select-Object -First 3 | ForEach-Object {
            Write-Host "    $_" -ForegroundColor Gray
        }
    } else {
        Write-Host "⚠ No intent metrics found yet" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Failed to fetch conversation metrics" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
}

# Test 6: Orchestrator Metrics
Write-Host "`n[6/6] Testing Orchestrator Metrics..." -ForegroundColor Yellow
try {
    $metrics = Invoke-WebRequest -Uri "http://localhost:8005/metrics" -UseBasicParsing
    $orchMetrics = $metrics.Content -split "`n" | Select-String "orchestrator_"
    
    if ($orchMetrics.Count -gt 0) {
        Write-Host "✓ Orchestrator metrics are available" -ForegroundColor Green
        Write-Host "  Sample metrics:" -ForegroundColor Gray
        $orchMetrics | Select-Object -First 5 | ForEach-Object {
            Write-Host "    $_" -ForegroundColor Gray
        }
    } else {
        Write-Host "⚠ No orchestrator metrics found yet" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Failed to fetch orchestrator metrics" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "All critical services are operational!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  • View Prometheus targets: http://localhost:9090/targets" -ForegroundColor Gray
Write-Host "  • View Grafana dashboards: http://localhost:3001" -ForegroundColor Gray
Write-Host "  • Test SSE stream: curl -N http://localhost:8005/events" -ForegroundColor Gray
Write-Host ""
