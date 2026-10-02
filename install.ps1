# install.ps1 – Installer session-optimize-skillen til ~/.claude/skills/
$skillDir = "$HOME\.claude\skills\session-optimize"
$source = "$PSScriptRoot\SKILL.md"

New-Item -ItemType Directory -Force -Path $skillDir | Out-Null
Copy-Item -Path $source -Destination "$skillDir\SKILL.md" -Force

Write-Host "Skill installert til: $skillDir\SKILL.md" -ForegroundColor Green
Write-Host "Start Claude Code på nytt for å aktivere skillen." -ForegroundColor Yellow
