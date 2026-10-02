# install.ps1 – Install the session-optimize skill to ~/.claude/skills/
$skillDir = "$HOME\.claude\skills\session-optimize"
$source = "$PSScriptRoot\SKILL.md"

New-Item -ItemType Directory -Force -Path $skillDir | Out-Null
Copy-Item -Path $source -Destination "$skillDir\SKILL.md" -Force

Write-Host "Skill installed to: $skillDir\SKILL.md" -ForegroundColor Green
Write-Host "Restart Claude Code to activate the skill." -ForegroundColor Yellow
