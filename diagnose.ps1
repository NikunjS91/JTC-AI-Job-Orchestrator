# Diagnostic Script - Check What's Not Working

Write-Host "`n=== CareerOps Diagnostic Check ===" -ForegroundColor Cyan
Write-Host "Checking all services and endpoints...`n" -ForegroundColor Gray

# Check Docker containers
Write-Host "[1] Checking Docker Containers..." -ForegroundColor Yellow
try {
    $containers = docker ps --format "{{.Names}}: {{.Status}}" | Where-Object { $_ -match "orchestrator|conversation" }
    if ($containers) {
        $containers | ForEach-Object { Write-Host "  $_" -ForegroundColor Green }
    } else {
        Write-Host "  ✗ No orchestrator/conversation containers running!" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Docker error: $_" -ForegroundColor Red
}

# Check ports
Write-Host "`n[2] Checking Port Availability..." -ForegroundColor Yellow
$ports = @(8004, 8005)
foreach ($port in $ports) {
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue
        if ($connection.TcpTestSucceeded) {
            Write-Host "  ✓ Port $port is open" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Port $port is NOT accessible" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ✗ Port $port check failed: $_" -ForegroundColor Red
    }
}

# Check conversation service
Write-Host "`n[3] Testing Conversation Service..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8004/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "  ✓ Conversation service responding (HTTP $($response.StatusCode))" -ForegroundColor Green
    Write-Host "    Response: $($response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Conversation service NOT responding" -ForegroundColor Red
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Check orchestrator service
Write-Host "`n[4] Testing Orchestrator Service..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8005/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "  ✓ Orchestrator service responding (HTTP $($response.StatusCode))" -ForegroundColor Green
    Write-Host "    Response: $($response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Orchestrator service NOT responding" -ForegroundColor Red
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Check for errors in logs
Write-Host "`n[5] Checking for Errors in Logs..." -ForegroundColor Yellow
try {
    $orchLogs = docker logs deploy-orchestrator-1 --tail 50 2>&1
    $convLogs = docker logs deploy-conversation-1 --tail 50 2>&1
    
    $orchErrors = $orchLogs | Select-String -Pattern "error|exception|traceback" -CaseSensitive:$false
    $convErrors = $convLogs | Select-String -Pattern "error|exception|traceback" -CaseSensitive:$false
    
    if ($orchErrors) {
        Write-Host "  ⚠ Orchestrator errors found:" -ForegroundColor Yellow
        $orchErrors | Select-Object -First 5 | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
    } else {
        Write-Host "  ✓ No errors in orchestrator logs" -ForegroundColor Green
    }
    
    if ($convErrors) {
        Write-Host "  ⚠ Conversation errors found:" -ForegroundColor Yellow
        $convErrors | Select-Object -First 5 | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
    } else {
        Write-Host "  ✓ No errors in conversation logs" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠ Could not check logs: $_" -ForegroundColor Yellow
}

# Test conversation intent
Write-Host "`n[6] Testing Conversation Intent..." -ForegroundColor Yellow
try {
    $body = '{"intent":"stats_today"}' 
    $response = Invoke-WebRequest -Uri "http://localhost:8004/intent" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing `
        -TimeoutSec 5
    
    Write-Host "  ✓ Intent processing working (HTTP $($response.StatusCode))" -ForegroundColor Green
    $data = $response.Content | ConvertFrom-Json
    Write-Host "    Session: $($data.session_id)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Intent processing FAILED" -ForegroundColor Red
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Summary
Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "If you see RED ✗ marks above, those indicate what's not working." -ForegroundColor Yellow
Write-Host "Please share the specific error messages with me.`n" -ForegroundColor Yellow
